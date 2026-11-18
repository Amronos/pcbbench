from pathlib import Path
import json
import sys
from cad import kicad_pcb

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / sys.argv[1]).read_text())
movable = {'FLASH_CS', '+1V1', 'I2C_SCL', 'RGB_DATA', 'CHG_ISET', 'USB_SUSPEND_EN', 'SD_CS', 'SD_MOSI'}
identifiers = set()
for finding in report['findings']:
    if finding['code'] not in {'clearance', 'shorting_items', 'hole_to_hole', 'hole_clearance'}:
        continue
    for item in finding['items']:
        if item['net'] in movable and item['kind'] in {'track', 'via'}:
            identifiers.add(item['uuid'])
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    items = [item for item in list(board.get_tracks()) + list(board.get_vias()) if item.id.value in identifiers]
    board.remove_items(items)
    board.refill_zones()
    print(f'Removed {len(items)} obstructing segments/vias')
