from pathlib import Path
from kipy import KiCad
from kipy.board_types import Track, Via
from kipy.geometry import Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType

path = Path('/home/ubuntu/pcbbench-run/scratch/ground-fixed.kicad_pcb')
v = Vector2.from_xy_mm
with KiCad(headless=True, timeout_ms=120000) as k:
    k.open_document(str(path), DocumentType.DOCTYPE_PCB)
    b = k.get_board()
    ground = next(n for n in b.get_nets() if n.name == '/GND')
    for via in b.get_vias():
        if via.net.name == '/ADC3' and via.position == v(57.5,51.0):
            b.remove_items(via)
    for track in b.get_tracks():
        endpoints = {(track.start.x,track.start.y),(track.end.x,track.end.y)}
        if track.net.name == '/ADC3' and endpoints == {(58450000,51000000),(57500000,51000000)}:
            b.remove_items(track)
    for points in [[(57.4,49.55),(57.4,49.95),(57.8,50.35),(57.8,50.8),(57.4,50.95)],
                   [(30.4,57.5),(31.15,57.5),(31.15,57.75)]]:
        for start,end in zip(points,points[1:]):
            track = Track()
            track.net = ground
            track.layer = bt.BL_F_Cu
            track.width = 127000
            track.start = v(*start)
            track.end = v(*end)
            b.create_items(track)
        via = Via()
        via.net = ground
        via.position = v(*points[-1])
        via.diameter = 450000
        via.drill_diameter = 150000
        b.create_items(via)
    track = Track()
    track.net = ground
    track.layer = bt.BL_F_Cu
    track.width = 127000
    track.start = v(36.8625,34)
    track.end = v(37.8,34.65)
    b.create_items(track)
    via = Via()
    via.net = ground
    via.position = v(37.8,34.65)
    via.diameter = 450000
    via.drill_diameter = 150000
    b.create_items(via)
    b.refill_zones(block=True,max_poll_seconds=120)
    b.save()
