from pathlib import Path
from cad import kicad_pcb
from kicode.board_types import BoardLayer, Track, Via
from kicode.geometry import Vector2
from kicode.util.units import from_mm

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    nets = {net.name: net for net in board.get_nets()}
    items = []
    def path(net, points, width=0.15):
        for start, end in zip(points, points[1:]):
            track = Track()
            track.start = Vector2.from_xy_mm(*start)
            track.end = Vector2.from_xy_mm(*end)
            track.width = from_mm(width)
            track.layer = BoardLayer.BL_F_Cu
            track.net = nets[net]
            items.append(track)
    def via(net, position):
        item = Via()
        item.position = Vector2.from_xy_mm(*position)
        item.diameter = from_mm(0.6)
        item.drill_diameter = from_mm(0.3)
        item.net = nets[net]
        items.append(item)
    via('+3V3', (24.68, 42.8))
    path('+3V3', [(33.45, 43.2), (32.95, 43.2), (32.65, 42.9), (32.2, 42.9)])
    via('+3V3', (32.2, 42.9))
    path('VBAT', [(15.5625, 18.75), (15.65, 18.75), (15.65, 19)], 0.3)
    path('VBAT', [(15.5625, 19.25), (15.65, 19.25), (15.65, 19)], 0.3)
    via('VBAT', (15.65, 19))
    via('SD_MISO', (64.175, 54.275))
    via('SD_DAT1', (63.075, 54.275))
    via('SD_DETECT', (62.125, 54.275))
    board.create_items(items)
    board.refill_zones()
