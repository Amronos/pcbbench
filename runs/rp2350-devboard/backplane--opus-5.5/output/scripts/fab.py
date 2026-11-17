"""Generate PCBWay fabrication + assembly outputs into fab/."""
import os, subprocess, csv, shutil, zipfile, json, glob
import design
from sexp import parse, find, findall

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
B = os.path.join(ROOT, 'boards', design.PROJECT)
PCB = os.path.join(B, design.PROJECT + '.kicad_pcb')
SCH = os.path.join(B, design.PROJECT + '.kicad_sch')
FAB = os.path.join(ROOT, 'fab')
K = '/home/ubuntu/pcbbench-hub/bin/kicad-cli'


def run(*a):
    print('+', ' '.join(a))
    subprocess.run(list(a), check=True, capture_output=True)


def main():
    if os.path.exists(FAB):
        shutil.rmtree(FAB)
    g = os.path.join(FAB, 'gerbers')
    os.makedirs(g)
    layers = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'
    run(K, 'pcb', 'export', 'gerbers', '-o', g + '/', '--layers', layers, '--subtract-soldermask',
        '--use-drill-file-origin', PCB)
    run(K, 'pcb', 'export', 'drill', '-o', g + '/', '--format', 'excellon', '--excellon-separate-th',
        '--drill-origin', 'plot', '--generate-map', '--map-format', 'pdf', '--excellon-units', 'mm',
        '--generate-report', '--report-path', g + '/' + design.PROJECT + '-drill-report.txt', PCB)
    # zip for upload
    zf = os.path.join(FAB, design.PROJECT + '-gerbers.zip')
    with zipfile.ZipFile(zf, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(g)):
            z.write(os.path.join(g, f), f)
    # position file (KiCad CSV, mm) + PCBWay-style CPL
    pos = os.path.join(FAB, design.PROJECT + '-pos-kicad.csv')
    run(K, 'pcb', 'export', 'pos', '-o', pos, '--format', 'csv', '--units', 'mm', '--side', 'both',
        '--exclude-dnp', '--use-drill-file-origin', PCB)
    comps = {c['ref']: c for c in design.resolve()}
    fps = board_footprints()
    rows = []
    with open(pos) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    with open(os.path.join(FAB, design.PROJECT + '-CPL-pcbway.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Designator', 'Footprint', 'Mid X(mm)', 'Mid Y(mm)', 'Layer', 'Rotation', 'Comment'])
        for r in rows:
            ref = r['Ref']
            w.writerow([ref, r['Package'], r['PosX'], r['PosY'], 'Top' if r['Side'] == 'top' else 'Bottom',
                        r['Rot'], comps[ref]['value'] if ref in comps else r['Val']])
    # BOM
    groups = {}
    for ref, c in comps.items():
        if not c['in_bom'] or c['dnp']:
            continue
        key = (c['mpn'], c['value'])
        groups.setdefault(key, []).append(c)
    def refkey(r):
        import re
        m = re.match(r'([A-Z]+)(\d+)', r)
        return (m.group(1), int(m.group(2))) if m else (r, 0)
    bom = []
    for key, cs in groups.items():
        refs = sorted((c['ref'] for c in cs), key=refkey)
        c = cs[0]
        side = fps.get(c['ref'], {}).get('side', 'top')
        tht = fps.get(c['ref'], {}).get('tht', False)
        note = ''
        if c['ref'] in ('J6', 'J7'):
            note = 'THT: insert from BOTTOM side (plastic body under the board), solder on top side'
        if c['mpn'] == 'AOTA-B201610S3R3-101-T':
            note = 'Polarity-marked inductor: dot must match footprint pin 1 marking (RP2350 VREG requirement)'
        if c['ref'].startswith('U7'):
            note = 'Module: no copper/parts under antenna; antenna overhangs board edge region'
        if c['ref'].startswith('D') and c['ref'] in ('D1', 'D3'):
            note = 'Polarity: cathode = pin 1'
        import re as _re
        fpn = c['fp'].split(':')[1]
        m = _re.search(r'(0402|0603|0805)', fpn)
        pkg = m.group(1) if m and c['ref'][0] in 'RCL' and not c['ref'].startswith('L') else fpn
        bom.append(dict(refs=refs, qty=len(refs), mfr=c['mfr'], mpn=c['mpn'], value=c['value'],
                        desc=c.get('bomdesc') or c['desc'], fp=pkg, lcsc=c['lcsc'],
                        type='THT' if tht else 'SMD', side=side, note=note))
    bom.sort(key=lambda b: refkey(b['refs'][0]))
    hdr = ['Item #', 'Designator', 'Qty', 'Manufacturer', 'Mfg Part #', 'Description / Value',
           'Package/Footprint', 'Type', 'Side', 'LCSC Part #', 'Your Instructions / Notes']
    with open(os.path.join(FAB, design.PROJECT + '-BOM-pcbway.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(hdr)
        for i, b in enumerate(bom):
            w.writerow([i + 1, ','.join(b['refs']), b['qty'], b['mfr'], b['mpn'], '%s - %s' % (b['value'], b['desc']),
                        b['fp'], b['type'], b['side'], b['lcsc'], b['note']])
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'BOM'
        ws.append(hdr)
        for c in ws[1]:
            c.font = Font(bold=True)
        for i, b in enumerate(bom):
            ws.append([i + 1, ','.join(b['refs']), b['qty'], b['mfr'], b['mpn'], '%s - %s' % (b['value'], b['desc']),
                       b['fp'], b['type'], b['side'], b['lcsc'], b['note']])
        for col, wdt in zip('ABCDEFGHIJK', [6, 40, 5, 24, 26, 60, 34, 6, 7, 12, 60]):
            ws.column_dimensions[col].width = wdt
        wb.save(os.path.join(FAB, design.PROJECT + '-BOM-pcbway.xlsx'))
    except ImportError:
        print('openpyxl missing: xlsx BOM skipped')
    # assembly drawings + schematic PDF
    run(K, 'pcb', 'export', 'pdf', '-o', os.path.join(FAB, design.PROJECT + '-assembly-top.pdf'),
        '--layers', 'F.Fab,Edge.Cuts', '--common-layers', 'F.CrtYd', '--include-border-title', PCB)
    run(K, 'pcb', 'export', 'pdf', '-o', os.path.join(FAB, design.PROJECT + '-assembly-bottom.pdf'),
        '--layers', 'B.Fab,Edge.Cuts', '--mirror', '--include-border-title', PCB)
    run(K, 'sch', 'export', 'pdf', '-o', os.path.join(FAB, design.PROJECT + '-schematic.pdf'), SCH)
    # IPC-356 netlist for electrical test, STEP model
    run(K, 'pcb', 'export', 'ipcd356', '-o', os.path.join(FAB, design.PROJECT + '-ipc356.d356'), PCB)
    run(K, 'pcb', 'export', 'step', '-o', os.path.join(FAB, design.PROJECT + '.step'), '--subst-models',
        '--no-dnp', '--force', PCB)
    # stack-up, reports, renders
    try:
        run(K, 'pcb', 'export', 'stackup', '-o', os.path.join(FAB, 'stackup.csv'), '--format', 'csv', PCB)
    except subprocess.CalledProcessError:
        pass
    subprocess.run([K, 'pcb', 'drc', '--schematic-parity', '--severity-all', '-o', os.path.join(FAB, 'drc-report.txt'), PCB],
                   capture_output=True)
    subprocess.run([K, 'sch', 'erc', '--severity-all', '-o', os.path.join(FAB, 'erc-report.txt'), SCH], capture_output=True)
    rd = os.path.join(FAB, 'renders')
    os.makedirs(rd, exist_ok=True)
    for side in ('top', 'bottom'):
        subprocess.run([K, 'pcb', 'render', '-o', os.path.join(rd, side + '.png'), '--side', side, '-w', '2000',
                        '-h', '1000', '--quality', 'high', '--zoom', '2.0', PCB], capture_output=True)
    subprocess.run([K, 'pcb', 'render', '-o', os.path.join(rd, 'iso.png'), '--side', 'top', '-w', '2000', '-h', '1200',
                    '--quality', 'high', '--rotate', '-40,0,25', '--zoom', '1.6', '--perspective', PCB], capture_output=True)
    print('fab outputs in', FAB)
    print('BOM lines:', len(bom), 'placed parts:', len(rows))


def board_footprints():
    t = parse(open(PCB).read())
    out = {}
    for fp in findall(t, 'footprint'):
        ref = [p[2] for p in findall(fp, 'property') if p[1] == 'Reference'][0]
        a = find(fp, 'attr')
        out[ref] = dict(side='bottom' if find(fp, 'layer')[1] == 'B.Cu' else 'top',
                        tht=bool(a and 'through_hole' in [str(x) for x in a]))
    return out


if __name__ == '__main__':
    main()
