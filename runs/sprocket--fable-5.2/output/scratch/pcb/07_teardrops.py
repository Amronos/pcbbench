"""Enable teardrops on every pad and via, then refill the zones. Run last, after all copper changes."""
from pcblib import *
from kipy.proto.board import board_types_pb2 as bt

k, b, doc = open_board()
fpl = list(b.get_footprints())
for f in fpl:
    for p in f.definition.pads:
        p.teardrop.mode = bt.PTM_ENABLED
b.update_items(fpl)
vias = list(b.get_vias())
for v in vias:
    v.teardrop.mode = bt.PTM_ENABLED
b.update_items(vias)
b.refill_zones(max_poll_seconds=120)
b.refill_zones(max_poll_seconds=120)
b.save()
print('teardrops on', len(fpl), 'footprints,', len(vias), 'vias')
