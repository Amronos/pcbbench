from pathlib import Path
import json
import sys
from cad import kicad_pcb

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / sys.argv[1]).read_text())
identifiers = {item['uuid'] for finding in report['findings']
               if finding['code'] in {'via_dangling', 'track_dangling'} for item in finding['items']}
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    items = [item for item in list(board.get_tracks()) + list(board.get_vias()) if item.id.value in identifiers]
    board.remove_items(items)
    board.refill_zones()
    print(f'Removed {len(items)} unused vias and dangling stubs')
