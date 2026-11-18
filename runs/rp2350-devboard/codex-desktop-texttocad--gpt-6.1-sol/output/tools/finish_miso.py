from pathlib import Path
from cad import kicad_pcb
from kicode.board_types import BoardLayer, Track, Via
from kicode.geometry import Vector2
from kicode.util.units import from_mm

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    board.remove_items([via for via in board.get_vias() if via.net.name == 'SD_MISO' and via.position == Vector2.from_xy_mm(34.4, 44.8)])
    net = next(net for net in board.get_nets() if net.name == 'SD_MISO')
    items = []
    for start, end in zip([(34.4, 44.8), (35.1, 44.8)], [(35.1, 44.8), (35.6, 44.3)]):
        track = Track()
        track.start = Vector2.from_xy_mm(*start)
        track.end = Vector2.from_xy_mm(*end)
        track.width = from_mm(0.15)
        track.layer = BoardLayer.BL_F_Cu
        track.net = net
        items.append(track)
    via = Via()
    via.position = Vector2.from_xy_mm(35.6, 44.3)
    via.diameter = from_mm(0.6)
    via.drill_diameter = from_mm(0.3)
    via.net = net
    items.append(via)
    board.create_items(items)
    board.refill_zones()
