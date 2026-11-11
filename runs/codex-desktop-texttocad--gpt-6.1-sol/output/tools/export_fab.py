from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
cad = str(Path.home() / '.local/bin/cad')
board = str(ROOT / 'Atlas2350.kicad_pcb')
verification = json.loads((ROOT / 'checks/verification.json').read_text())
if verification['status'] != 'PASS':
    raise SystemExit('Refusing manufacture export without passing verification')
for folder in ['gerbers', 'drill', 'assembly']:
    (ROOT / 'fab' / folder).mkdir(parents=True, exist_ok=True)
def run(*arguments):
    subprocess.run([cad, 'run', 'kicad-cli', *arguments], cwd=ROOT, check=True)
run('pcb', 'export', 'gerbers', '--layers', 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts,F.Paste',
    '--no-protel-ext', '--subtract-soldermask', '--check-zones', '-o', str(ROOT / 'fab/gerbers'), board)
run('pcb', 'export', 'drill', '--format', 'excellon', '--excellon-units', 'mm', '--excellon-zeros-format', 'decimal',
    '--excellon-oval-format', 'route', '--excellon-separate-th', '--generate-map', '--generate-report',
    '--report-path', str(ROOT / 'fab/drill/drill-report.txt'), '-o', str(ROOT / 'fab/drill'), board)
run('pcb', 'export', 'ipcd356', '-o', str(ROOT / 'fab/Atlas2350.ipc'), board)
run('pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--exclude-bom', '--exclude-dnp',
    '-o', str(ROOT / 'fab/assembly/kicad-native-position.csv'), board)
run('pcb', 'export', 'pdf', '--mode-single', '--layers', 'F.Fab,F.SilkS,Edge.Cuts', '--sketch-pads-on-fab-layers',
    '--sketch-pad-numbers', '--scale', '0', '-o', str(ROOT / 'fab/assembly/top-assembly-kicad.pdf'), board)
run('sch', 'export', 'pdf', '-o', str(ROOT / 'fab/schematic.pdf'), str(ROOT / 'Atlas2350.kicad_sch'))
