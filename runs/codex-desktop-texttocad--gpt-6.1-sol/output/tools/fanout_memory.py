from pathlib import Path
from cad import kicad_pcb
from kicode.board_types import BoardLayer, Track, Via
from kicode.geometry import Vector2
from kicode.util.units import from_mm

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    net = next(net for net in board.get_nets() if net.name == 'QSPI_IO2')
    track = Track()
    track.start = Vector2.from_xy_mm(26.55, 44)
    track.end = Vector2.from_xy_mm(27.4, 44)
    track.width = from_mm(0.15)
    track.layer = BoardLayer.BL_F_Cu
    track.net = net
    via = Via()
    via.position = track.end
    via.diameter = from_mm(0.6)
    via.drill_diameter = from_mm(0.3)
    via.net = net
    board.create_items([track, via])
    board.refill_zones()
