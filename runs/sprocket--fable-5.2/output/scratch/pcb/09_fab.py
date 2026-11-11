"""Write everything PCBWay needs into fab/: Gerbers, drills, BOM and centroid in PCBWay's column layout,
assembly drawings and renders. Reads the schematic for the BOM and the board for everything else."""
import csv, os, re, shutil, subprocess, zipfile
from pcblib import *
from kipy.proto.board.board_commands_pb2 import BOT_DRILL

# centroid coordinates from the board's bottom-left corner
k, b, doc = open_board()
b.set_origin(BOT_DRILL, mm(X0, Y0 + H))
b.save()

THT = {'J6', 'J7'}
BOARD, SCH = f'{ROOT}/rp2350-devboard.kicad_pcb', f'{ROOT}/rp2350-devboard.kicad_sch'
FAB = f'{ROOT}/fab'
GERB = f'{FAB}/gerbers'


def cli(*a):
    subprocess.run(['kicad-cli', *a], check=True, stdout=subprocess.DEVNULL)


shutil.rmtree(GERB, ignore_errors=True)
os.makedirs(GERB)
LAYERS = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
cli('pcb', 'export', 'gerbers', '--layers', LAYERS, '--no-protel-ext', '--check-zones', '-o', GERB + '/', BOARD)
cli('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-units', 'mm', '--excellon-separate-th',
    '--excellon-oval-format', 'route', '--generate-map', '--map-format', 'pdf', '-o', GERB + '/', BOARD)
with zipfile.ZipFile(f'{FAB}/rp2350-devboard-gerbers.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for n in sorted(os.listdir(GERB)):
        z.write(f'{GERB}/{n}', n)

# ---- BOM, one line per part number, PCBWay's sample columns plus sourcing columns
raw = '/tmp/rp2350-bom-raw.csv'
F = ['Reference', 'Value', 'Footprint', 'Manufacturer', 'MPN', 'Description', 'LCSC Part #', 'Digikey Part #',
     'Mouser Part #', 'Datasheet', '${QUANTITY}', '${DNP}']
cli('sch', 'export', 'bom', '--fields', ','.join(F), '--group-by', 'Value,Footprint,MPN', '--ref-range-delimiter', '',
    '-o', raw, SCH)
NOTES = {
    'J6': 'Fit on the BOTTOM side, pins pointing down. Through-hole, solder from the top.',
    'J1': 'Shell legs are plated through-hole: pin-in-paste or hand solder after reflow.',
    'L1': 'Polarised inductor: the dot on the part goes to pad 1 (+1V1), marked with a dot on the silkscreen.',
    'U5': 'Approved alternate: Diodes AP2112K-3.3TRG1 (same SOT-23-5 pinout).',
    'U7': 'Raspberry Pi RM2 radio module, LGA. Keep the antenna end free of metal.',
    'D2': 'Green LED, cathode at pad 1.',
    'D3': 'Amber LED, cathode at pad 1.',
    'D1': 'Addressable RGB LED, pin 1 mark on silkscreen.',
}
rows = list(csv.DictReader(open(raw, encoding='utf-8')))
with open(f'{FAB}/bom-pcbway.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Item #', '*Designator', '*Qty', 'Manufacturer', '*Mfg Part #', 'Description / Value',
                '*Package/Footprint', 'Type', 'Your Instructions / Notes', 'Substitutes allowed', 'LCSC',
                'Digi-Key', 'Mouser', 'Datasheet'])
    for i, r in enumerate(rows, 1):
        refs = r['Reference'].split(',')
        pkg = r['Footprint'].split(':')[1]
        m = re.search(r'_(0402|0603)_', pkg)
        note = ' '.join(NOTES[x] for x in refs if x in NOTES)
        passive = refs[0][0] in 'RC' and m
        w.writerow([i, ','.join(refs), r['QUANTITY'], r['Manufacturer'], r['MPN'],
                    f"{r['Value']}, {r['Description'].split(', script generated')[0]}", m.group(1) if m else pkg,
                    'thru-hole' if set(refs) & THT else 'SMD', note,
                    ('Yes, same value, size and 1% tolerance' if refs[0][0] == 'R' else 'Yes, same value, size, voltage and dielectric') if passive else ('Yes, see notes' if 'alternate' in note else 'No'),
                    r['LCSC Part #'], r['Digikey Part #'], r['Mouser Part #'], r['Datasheet']])

# ---- centroid: one file per side, mm. Machine-placed parts only: J1 counts although its shell legs are
# through-hole, the pin headers and fiducials do not.
for side in ('front', 'back'):
    out = f'{FAB}/centroid-{"top" if side == "front" else "bottom"}.csv'
    cli('pcb', 'export', 'pos', '--side', side, '--format', 'csv', '--units', 'mm',
        '--use-drill-file-origin', '-o', out, BOARD)
    pos = [p for p in csv.DictReader(open(out)) if not p['Ref'].startswith('FID') and p['Ref'] not in THT]
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Designator', 'Comment', 'Footprint', 'Mid X (mm)', 'Mid Y (mm)', 'Rotation', 'TB'])
        for p in pos:
            w.writerow([p['Ref'], p['Val'], p['Package'], p['PosX'], p['PosY'], p['Rot'], 'T' if side == 'front' else 'B'])
    if not pos:
        os.remove(out)

# ---- assembly drawings and renders
for side, layers, extra in (('top', 'F.Fab,Edge.Cuts', []), ('bottom', 'B.Fab,Edge.Cuts', ['--mirror'])):
    cli('pcb', 'export', 'pdf', '--layers', layers, '--mode-single', '--ibt', '--sp', '--scale', '0', *extra,
        '-o', f'{FAB}/assembly-{side}.pdf', BOARD)
for name, view in (('top', ['--side', 'top']), ('bottom', ['--side', 'bottom']),
                   ('iso', ['--rotate', '-40,0,-25', '--perspective'])):
    cli('pcb', 'render', *view, '--width', '1800', '--height', '700', '--zoom', '1.5', '--quality', 'basic',
        '--background', 'opaque', '-o', f'{FAB}/render-{name}.png', BOARD)
print('fab written:', sorted(os.listdir(FAB)))
