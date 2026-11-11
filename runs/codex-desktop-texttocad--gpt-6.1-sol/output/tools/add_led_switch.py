from pathlib import Path
from cad import kicad_pcb
from kicode.board_types import BoardLayer
from kicode.geometry import Angle, Vector2

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    removed = []
    for track in board.get_tracks():
        if track.net.name == 'VSYS' and track.layer == BoardLayer.BL_F_Cu:
            points = [(point.x / 1e6, point.y / 1e6) for point in [track.start, track.end]]
            if all(point[0] > 74 and 25 < point[1] < 33 for point in points):
                removed.append(track)
    for via in board.get_vias():
        x, y = via.position.x / 1e6, via.position.y / 1e6
        if via.net.name == 'VSYS' and x > 74 and 25 < y < 33:
            removed.append(via)
    board.remove_items(removed)
    result = board.import_netlist(str(ROOT / 'checks/Atlas2350.net'))
    print(result)
    changed = []
    for footprint in board.get_footprints():
        ref = footprint.reference_field.text.value
        if ref in {'U10', 'C45'}:
            footprint.position = Vector2.from_xy_mm(77, 23 if ref == 'U10' else 20)
            footprint.orientation = Angle.from_degrees(0 if ref == 'U10' else 90)
            footprint.reference_field.visible = False
            footprint.value_field.visible = False
            changed.append(footprint)
    board.update_items(changed)
    board.refill_zones()
