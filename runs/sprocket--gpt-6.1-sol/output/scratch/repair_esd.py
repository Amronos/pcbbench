import argparse
from kipy import KiCad
from kipy.board_types import Track
from kipy.geometry import Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType

parser = argparse.ArgumentParser()
parser.add_argument('board')
args = parser.parse_args()
v = Vector2.from_xy_mm
with KiCad(headless=True, timeout_ms=120000) as k:
    k.open_document(args.board, DocumentType.DOCTYPE_PCB)
    b = k.get_board()
    remove = {'b72d7bf1-9f22-4e47-81c3-a2b02738b7a5',
              'dbc62135-9ca1-4300-a4e7-de5bbd88799d',
              'f87c0310-a05b-49ff-bca1-3116da65010a'}
    duplicates = []
    for track in b.get_tracks():
        if track.id.value in remove:
            b.remove_items(track)
        elif track.net.name == '/GND' and track.layer == bt.BL_B_Cu and {
                (track.start.x, track.start.y), (track.end.x, track.end.y)
        } == {(71500000, 23000000), (71500000, 25300000)}:
            duplicates.append(track)
    for track in duplicates[1:]:
        b.remove_items(track)
    power = next(net for net in b.get_nets() if net.name == '/VBUS')
    points = [(29.25, 38.9), (32.45, 35.7), (39.7, 35.7),
              (39.7, 34.85), (38.85, 34)]
    for start, end in zip(points, points[1:]):
        track = Track()
        track.net = power
        track.layer = bt.BL_In2_Cu
        track.width = 500000
        track.start, track.end = v(*start), v(*end)
        b.create_items(track)
    b.refill_zones(block=True, max_poll_seconds=120)
    b.save()
