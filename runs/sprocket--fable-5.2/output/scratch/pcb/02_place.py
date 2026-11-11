"""Board outline and footprint placement. Coordinates are mm relative to the board's top-left corner.
Idempotent: sets absolute positions, redraws the outline."""
import json, sys
from pcblib import *
from kipy.board_types import BoardSegment, BoardArc, FootprintInstance
from kipy.proto.board import board_types_pb2 as bt
from kipy.util.board_layer import BoardLayer as BL

PLACE = json.load(open(f'{ROOT}/scratch/pcb/place.json'))

k, b, doc = open_board()

# ---- outline: rectangle with rounded corners
old = [s for s in b.get_shapes() if s.layer == bt.BL_Edge_Cuts]
if old:
    b.remove_items(old)
R = 1.0
x1, y1, x2, y2 = X0, Y0, X0 + W, Y0 + H
items = []
for a, c in (((x1 + R, y1), (x2 - R, y1)), ((x2, y1 + R), (x2, y2 - R)), ((x2 - R, y2), (x1 + R, y2)), ((x1, y2 - R), (x1, y1 + R))):
    s = BoardSegment()
    s.layer, s.start, s.end = bt.BL_Edge_Cuts, mm(*a), mm(*c)
    s.attributes.stroke.width = 100000
    items.append(s)
q = R * (1 - 0.70710678)
for st, mid, en in (((x2 - R, y1), (x2 - q, y1 + q), (x2, y1 + R)), ((x2, y2 - R), (x2 - q, y2 - q), (x2 - R, y2)),
                    ((x1 + R, y2), (x1 + q, y2 - q), (x1, y2 - R)), ((x1, y1 + R), (x1 + q, y1 + q), (x1 + R, y1))):
    a = BoardArc()
    a.layer, a.start, a.mid, a.end = bt.BL_Edge_Cuts, mm(*st), mm(*mid), mm(*en)
    a.attributes.stroke.width = 100000
    items.append(a)
b.create_items(items)

# ---- footprints
F = fps(b)
park = 0
upd = []
for ref, f in sorted(F.items()):
    if ref in PLACE:
        x, y, rot = PLACE[ref][:3]
        back = len(PLACE[ref]) > 3 and PLACE[ref][3] == 'B'
    else:
        x, y, rot, back = 2 + (park % 30) * 2.5, 32 + (park // 30) * 4, 0, False
        park += 1
    if back != (f.layer == bt.BL_B_Cu):
        f = b.flip_items([f])[0]
    f.position = mm(X0 + x, Y0 + y)
    f.orientation = Angle.from_degrees(rot)
    upd.append(f)
b.update_items(upd)
b.save()
print('placed', len(PLACE), 'parked', park)
