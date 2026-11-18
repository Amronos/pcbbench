from pathlib import Path
import json
import subprocess
from cad import kicad_pcb

ROOT = Path(__file__).resolve().parents[1]
report_path = ROOT / 'checks/drc-final.json'
cad = str(Path.home() / '.local/bin/cad')
for iteration in range(30):
    with report_path.open('w') as output:
        subprocess.run([cad, 'kicad_pcb', 'drc', str(ROOT / 'Atlas2350.kicad_pcb'), '--json'], stdout=output)
    report = json.loads(report_path.read_text())
    identifiers = {item['uuid'] for finding in report['findings']
                   if finding['code'] in {'track_dangling', 'via_dangling'} for item in finding['items']}
    if not identifiers:
        if report['findings']:
            raise SystemExit(json.dumps(report['findings']))
        print(f'DRC clean after {iteration} pruning passes')
        break
    with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
        items = [item for item in list(board.get_tracks()) + list(board.get_vias()) if item.id.value in identifiers]
        board.remove_items(items)
        board.refill_zones()
else:
    raise SystemExit('Pruning exceeded iteration bound')
