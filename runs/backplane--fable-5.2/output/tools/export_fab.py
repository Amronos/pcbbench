#!/usr/bin/env python3
"""Generate everything PCBWay needs into fab/: gerbers + drill (zipped), BOM, centroid, assembly drawings."""
import os, sys, subprocess, csv, shutil, zipfile, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D
K = '/home/ubuntu/pcbbench-hub/bin/kicad-cli'
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
PRJ = os.path.join(ROOT, 'boards', D.NAME); PCB = os.path.join(PRJ, D.NAME + '.kicad_pcb'); SCH = os.path.join(PRJ, D.NAME + '.kicad_sch')
FAB = os.path.join(ROOT, 'fab')
def run(*a):
    r = subprocess.run([K] + list(a), capture_output=True, text=True)
    if r.returncode: print(r.stdout[-2000:], r.stderr[-2000:]); raise SystemExit('kicad-cli failed: ' + ' '.join(a))
shutil.rmtree(FAB, ignore_errors=True)
G = os.path.join(FAB, 'gerbers'); os.makedirs(G); os.makedirs(os.path.join(FAB, 'assembly')); os.makedirs(os.path.join(FAB, 'docs'))
layers = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'
run('pcb', 'export', 'gerbers', '-o', G + '/', '--layers', layers, '--subtract-soldermask', '--no-x2', '--use-drill-file-origin', PCB)
run('pcb', 'export', 'drill', '-o', G + '/', '--format', 'excellon', '--drill-origin', 'plot', '--excellon-units', 'mm',
    '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', PCB)
for f in os.listdir(G):
    if f.endswith('.gbrjob'): os.remove(os.path.join(G, f))
with zipfile.ZipFile(os.path.join(FAB, D.NAME + '-gerbers.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(G)): z.write(os.path.join(G, f), f)
# ---- position file (KiCad) -> PCBWay centroid
pos = os.path.join(FAB, 'assembly', 'kicad-pos.csv')
run('pcb', 'export', 'pos', '-o', pos, '--format', 'csv', '--units', 'mm', '--side', 'both', '--use-drill-file-origin',
    '--exclude-dnp', PCB)
rows = list(csv.DictReader(open(pos)))
byref = {p['ref']: p for p in D.P}
def key(r):
    import re
    m = re.match(r'([A-Z]+)(\d+)', r); return (m.group(1), int(m.group(2)))
with open(os.path.join(FAB, 'assembly', D.NAME + '-centroid.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Mid X (mm)', 'Mid Y (mm)', 'Layer', 'Rotation (deg)', 'Value', 'Package'])
    n = 0
    for r in sorted(rows, key=lambda r: key(r['Ref'])):
        p = byref[r['Ref']]
        if not p['bom']: continue
        w.writerow([r['Ref'], '%.3f' % float(r['PosX']), '%.3f' % float(r['PosY']), 'Top' if r['Side'] == 'top' else 'Bottom',
                    '%g' % float(r['Rot']), p['value'], p['fp'].split(':')[1]]); n += 1
os.remove(pos)
# ---- BOM (PCBWay template columns)
groups = {}
for p in D.P:
    if not p['bom']: continue
    groups.setdefault((p['mpn'], p['value'], p['fp']), []).append(p)
with open(os.path.join(FAB, 'assembly', D.NAME + '-bom.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['Item #', 'Designator', 'Qty', 'Manufacturer', 'Mfg Part #', 'Description / Value', 'Package/Footprint', 'Type',
                'LCSC Part # (reference)', 'Your Instructions / Notes'])
    tot = 0
    for i, (k, ps) in enumerate(sorted(groups.items(), key=lambda kv: key(kv[1][0]['ref'])), 1):
        p = ps[0]; refs = sorted((q['ref'] for q in ps), key=key); tot += len(ps)
        note = D.BOM_NOTES.get(p['ref'], '')
        w.writerow([i, ', '.join(refs), len(ps), p['mfr'], p['mpn'], p['desc'], p['fp'].split(':')[1], 'SMD', p['lcsc'], note])
print('BOM: %d lines, %d parts; centroid: %d placements' % (len(groups), tot, n))
assert tot == n, 'BOM and centroid disagree'
# ---- drawings
run('pcb', 'export', 'pdf', '-o', os.path.join(FAB, 'assembly', D.NAME + '-assembly-top.pdf'), '--layers', 'F.Fab,F.SilkS,Edge.Cuts',
    '--mode-single', '--include-border-title', PCB)
run('pcb', 'export', 'pdf', '-o', os.path.join(FAB, 'docs', D.NAME + '-fab-drawing.pdf'), '--layers', 'Edge.Cuts,Cmts.User,F.Cu,B.Cu',
    '--mode-single', '--include-border-title', PCB)
run('sch', 'export', 'pdf', '-o', os.path.join(FAB, 'docs', D.NAME + '-schematic.pdf'), SCH)
run('pcb', 'export', 'ipcd356', '-o', os.path.join(FAB, 'docs', D.NAME + '-netlist.ipc'), PCB)
for side in ('top', 'bottom'):
    run('pcb', 'render', '-o', os.path.join(FAB, 'docs', D.NAME + '-' + side + '.png'), '--side', side, '-w', '2400', '-h', '900',
        '--quality', 'basic', '--background', 'opaque', '--zoom', '2.6', PCB)
try:
    run('pcb', 'export', 'step', '-o', os.path.join(FAB, 'docs', D.NAME + '.step'), '--subst-models', '--force', PCB)
except SystemExit as e:
    print('STEP export skipped:', e)
print(sorted(os.listdir(G)))
