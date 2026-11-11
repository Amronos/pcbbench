from kipy import KiCad
from kipy.board_types import Track
from kipy.geometry import Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType

v = Vector2.from_xy_mm
with KiCad(headless=True,timeout_ms=120000) as k:
    k.open_document('/home/ubuntu/pcbbench-run/scratch/clean-esd.kicad_pcb',DocumentType.DOCTYPE_PCB)
    b = k.get_board()
    ground = next(n for n in b.get_nets() if n.name == '/GND')
    via = next(via for via in b.get_vias() if via.position == v(36.8625,34))
    via.position = v(37.8,34.65)
    via.net = ground
    b.update_items(via)
    track = Track()
    track.net = ground
    track.layer = bt.BL_F_Cu
    track.width = 127000
    track.start = v(36.8625,34)
    track.end = v(37.8,34.65)
    b.create_items(track)
    b.refill_zones(block=True,max_poll_seconds=120)
    b.save()
