import sys
from itertools import pairwise
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Track, Via
from kipy.geometry import Vector2
from kipy.proto.board import board_types_pb2 as bt

TAG = 'sprocket-core-power-joins'

with KiCad(headless=True, file_path=str(Path(sys.argv[1]).resolve()), timeout_ms=60000) as k:
    board = k.get_board()
    net = next(net for net in board.get_nets() if net.name == '/3V3')
    board.remove_items(
        [
            item
            for item in [*board.get_tracks(), *board.get_vias()]
            if any(prop.key == TAG for prop in item.proto.custom_properties)
        ]
    )
    copper = []
    for points in [
        [(140.6, 126.55), (140.6, 127.05), (141.2, 127.65), (141.2, 127.85)],
        [(141, 126.55), (141, 127.05), (141.2, 127.25), (141.2, 127.85)],
        [(142.485, 125.39), (142.6, 125.505), (142.6, 126.55)],
    ]:
        for start, end in pairwise(points):
            track = Track()
            track.net = net
            track.layer = bt.BL_F_Cu
            track.width = 140000
            track.start = Vector2.from_xy_mm(*start)
            track.end = Vector2.from_xy_mm(*end)
            copper.append(track)
    for x, y in [(141.2, 127.85), (142.485, 125.39), (145.2, 122.625)]:
        via = Via()
        via.net = net
        via.position = Vector2.from_xy_mm(x, y)
        via.diameter = 450000
        via.drill_diameter = 200000
        copper.append(via)
    for item in copper:
        item.proto.custom_properties.add(key=TAG, value='1')
    board.create_items(copper)
    board.refill_zones(block=True, max_poll_seconds=120)
    board.save()
