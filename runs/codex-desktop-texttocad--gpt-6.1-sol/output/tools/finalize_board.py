from pathlib import Path
import json
from cad import kicad_pcb
from kicode.board_types import BoardLayer, ViaDrillFillingMode, ViaDrillCappingMode
from kicode.geometry import Vector2
from kicode.util.units import from_mm

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / 'checks/drc-ground.json').read_text())
neck_ids = {item['uuid'] for finding in report['findings'] if finding['code'] == 'clearance'
            for item in finding['items'] if item['kind'] == 'track' and item['net'] == '+1V1'}
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    tracks = board.get_tracks()
    for track in tracks:
        if track.id.value in neck_ids:
            track.width = from_mm(0.15)
    board.update_items(tracks)
    vias = board.get_vias()
    for via in vias:
        via.padstack.drill.filled = ViaDrillFillingMode.VDFM_FILLED
        via.padstack.drill.capped = ViaDrillCappingMode.VDCM_CAPPED
    board.update_items(vias)
    footprints = board.get_footprints()
    for footprint in footprints:
        if footprint.reference_field.text.value == 'U6':
            footprint.definition.items = [item for item in footprint.definition.items
                                          if getattr(item, 'layer', None) != BoardLayer.BL_F_SilkS]
    board.update_items(footprints)
    positions = {'BAT+ GND NTC': (14, 7), '1S LiPo 4.2V ONLY': (22, 12),
                 'PWR': (8, 50), 'ESP RST': (56, 37.5), 'ESP BOOT': (65.5, 37.5)}
    texts = board.get_text()
    remove = []
    for text in texts:
        if text.value in positions:
            text.position = Vector2.from_xy_mm(*positions[text.value])
        if text.value == 'Qwiic / QT':
            text.value = 'Qwiic 3V3'
        if text.value == '3V3 I2C':
            remove.append(text)
    board.remove_items(remove)
    board.update_items([text for text in texts if text not in remove])
    board.refill_zones()
