"""Create the board file: 4 copper layers, import the netlist."""
import os
from pcblib import *
from kipy.proto.board import board_types_pb2 as bt

assert not os.path.exists(PCB), 'board exists; this script only creates it'
k, b, doc = open_board(create=True)
layers = [l for l in b.get_enabled_layers() if l not in (bt.BL_In1_Cu, bt.BL_In2_Cu)]
cu = [bt.BL_F_Cu, bt.BL_In1_Cu, bt.BL_In2_Cu, bt.BL_B_Cu]
b.set_enabled_layers(4, sorted(set(layers) | set(cu)))
r = b.import_netlist(NET)
print(r.error_count, r.warning_count, r.new_footprint_count)
print(r.report[-3000:])
b.save()
