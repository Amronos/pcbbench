from pathlib import Path
from cad import kicad_pcb
from kicode.board_types import BoardLayer, Track, Zone, ZoneConnectionStyle
from kicode.geometry import Vector2, PolyLine, PolyLineNode, PolygonWithHoles
from kicode.util.units import from_mm

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    ground = next(net for net in board.get_nets() if net.name == 'GND')
    track = Track()
    track.start = Vector2.from_xy_mm(27.5, 40.8)
    track.end = Vector2.from_xy_mm(28.5, 40.8)
    track.width = from_mm(0.3)
    track.layer = BoardLayer.BL_F_Cu
    track.net = ground
    board.create_items(track)
    zones = [zone for zone in board.get_zones() if not zone.is_rule_area()]
    for zone in zones:
        zone.name = 'Stitched GND pour; signal escape corridors'
    board.update_items(zones)
    for layer in [BoardLayer.BL_F_Cu, BoardLayer.BL_B_Cu]:
        if any(layer in zone.layers for zone in zones):
            continue
        zone = Zone()
        zone.name = 'Outer GND stitching pour'
        zone.layers = [layer]
        zone.net = ground
        zone.clearance = from_mm(0.127)
        zone.min_thickness = from_mm(0.15)
        zone.connection.zone_connection = ZoneConnectionStyle.ZCS_FULL
        polygon = PolygonWithHoles()
        line = PolyLine()
        line.nodes.extend(PolyLineNode.from_point(Vector2.from_xy_mm(*point)) for point in
                          [(2, 0), (78, 0), (80, 2), (80, 73), (78, 75), (2, 75), (0, 73), (0, 2)])
        polygon.outline = line
        zone.outline = polygon
        board.create_items(zone)
    board.refill_zones()
