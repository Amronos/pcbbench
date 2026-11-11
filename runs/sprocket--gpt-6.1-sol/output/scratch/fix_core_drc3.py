from kipy import KiCad
from kipy.board_types import Via
from kipy.geometry import Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType

v = Vector2.from_xy_mm
with KiCad(headless=True, timeout_ms=120000) as k:
    k.open_document('/home/ubuntu/pcbbench-run/scratch/merged.kicad_pcb', DocumentType.DOCTYPE_PCB)
    b = k.get_board()
    for track in b.get_tracks():
        if track.id.value in {'25d7c5cd-6380-42af-8e5a-07b14eb0f41f',
                              '9c0e1b1d-4739-42ce-a079-b9bdc2cc6b36',
                              '7c016232-54db-49c5-9889-81ed7e04f73b'}:
            b.remove_items(track)
        elif track.net.name == '/VREG_AVDD':
            changed = False
            if track.start.x == 63300000:
                track.start = Vector2.from_xy(63320000, track.start.y)
                changed = True
            if track.end.x == 63300000:
                track.end = Vector2.from_xy(63320000, track.end.y)
                changed = True
            if changed:
                b.update_items(track)
    via = Via()
    via.position = v(62.6, 46.825)
    via.net = next(net for net in b.get_nets() if net.name == '/+3V3')
    via.diameter, via.drill_diameter = 450000, 150000
    via.proto.pad_stack.drill.start_layer = bt.BL_F_Cu
    via.proto.pad_stack.drill.end_layer = bt.BL_B_Cu
    b.create_items(via)
    b.refill_zones(block=True, max_poll_seconds=120)
    b.save()
