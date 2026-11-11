"""Re-import the netlist after a schematic change. Matches by reference, so placement survives.
Run 02_place.py afterwards to place new parts."""
from pcblib import *
from kipy.proto.board import board_commands_pb2 as bc

k, b, doc = open_board()
r = b.import_netlist(NET, match_mode=bc.NMM_REFERENCE)
print(r.error_count, r.warning_count, r.new_footprint_count)
print(r.report[-2500:])
b.save()
