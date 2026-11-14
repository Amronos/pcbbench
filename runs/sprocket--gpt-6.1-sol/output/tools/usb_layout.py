import sys
from itertools import pairwise
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Track, Via, Zone
from kipy.geometry import PolygonWithHoles, PolyLine, PolyLineNode, Vector2
from kipy.proto.board import board_types_pb2 as bt
from shapely.geometry import LineString
from shapely.ops import unary_union

PATHS = {
    '/USB_CONN_DP': [
        [
            (135.05, 110.8625),
            (135.05, 113.1375),
            (135.05, 114.0),
            (136.03, 114.98),
            (136.03, 119.0),
            (139.6, 122.57),
            (139.6, 123.79),
        ],
        [(135.25, 107.045), (135.25, 108.6), (135.05, 108.8), (135.05, 110.8625)],
        [(136.25, 107.045), (136.25, 108.1), (135.25, 108.1)],
    ],
    '/USB_CONN_DM': [
        [
            (136.95, 110.8625),
            (136.95, 113.1375),
            (136.95, 114.0),
            (136.4, 114.55),
            (136.4, 118.8467),
            (140.6, 123.0467),
            (140.6, 123.79),
        ],
        [(136.75, 107.045), (136.75, 108.6), (136.95, 108.8), (136.95, 110.8625)],
    ],
    '/USB_DP': [
        [(139.6, 124.81), (139.6, 125.05), (140.4, 125.85), (141.4, 125.85), (141.4, 126.55)]
    ],
    '/USB_DM': [
        [
            (140.6, 124.81),
            (140.6, 125.0),
            (140.9, 125.3),
            (141.65, 125.3),
            (141.65, 125.8),
            (141.8, 125.95),
            (141.8, 126.55),
        ]
    ],
}
CLEARANCE_ZONE_NAME = 'USB top pour clearance'


with KiCad(headless=True, file_path=str(Path(sys.argv[1]).resolve()), timeout_ms=60000) as k:
    board = k.get_board()
    nets = {net.name: net for net in board.get_nets()}
    board.remove_items(
        [
            item
            for item in [*board.get_tracks(), *board.get_vias()]
            if item.net.name in PATHS
        ]
    )
    board.remove_items([zone for zone in board.get_zones() if zone.name == CLEARANCE_ZONE_NAME])
    copper = []

    def add_tracks(net, points, layer, width):
        for start, end in pairwise(points):
            track = Track()
            track.net = nets[net]
            track.layer = layer
            track.start = Vector2.from_xy_mm(*start)
            track.end = Vector2.from_xy_mm(*end)
            track.width = width
            copper.append(track)

    for net, branches in PATHS.items():
        for points in branches:
            add_tracks(net, points, bt.BL_F_Cu, 220000 if net.startswith('/USB_CONN') else 140000)
    corridor = unary_union(
        [
            LineString(branches[0]).buffer(0.61, join_style=2)
            for net, branches in PATHS.items()
            if net.startswith('/USB_CONN')
        ]
    )
    zone = Zone()
    zone.type = bt.ZT_RULE_AREA
    zone.layers = [bt.BL_F_Cu]
    zone.name = CLEARANCE_ZONE_NAME
    zone.proto.rule_area_settings.keepout_copper = True
    outline = PolygonWithHoles()
    polyline = PolyLine()
    for x, y in corridor.exterior.coords:
        polyline.append(PolyLineNode.from_point(Vector2.from_xy_mm(x, y)))
    outline.outline = polyline
    zone.outline = outline
    board.create_items(zone)
    for x, y in [(135.75, 107.65), (136.95, 109)]:
        via = Via()
        via.net = nets['/USB_CONN_DM']
        via.position = Vector2.from_xy_mm(x, y)
        via.diameter = 450000
        via.drill_diameter = 200000
        copper.append(via)
    for layer, points in [
        (bt.BL_F_Cu, [(135.75, 107.045), (135.75, 107.65)]),
        (bt.BL_B_Cu, [(135.75, 107.65), (136.95, 108.85), (136.95, 109)]),
        (bt.BL_F_Cu, [(136.95, 109), (136.95, 110.8625)]),
    ]:
        add_tracks('/USB_CONN_DM', points, layer, 180000)
    board.create_items(copper)
    board.save()
