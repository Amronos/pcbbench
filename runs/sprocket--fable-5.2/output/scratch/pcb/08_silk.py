"""Silkscreen and fab layers: hide reference designators and values, trim footprint silkscreen that crosses
the board edge, add pin labels and polarity marks.
Idempotent: deletes every board-level text and circle on the silkscreen layers first."""
from pcblib import *
from kipy.board_types import BoardText, BoardCircle, BoardShape
from kipy.proto.board import board_types_pb2 as bt

k, b, doc = open_board()
SILK = (bt.BL_F_SilkS, bt.BL_B_SilkS)
old = [t for t in b.get_text() if t.layer in SILK] + \
      [s for s in b.get_shapes() if s.layer in SILK and isinstance(s, BoardCircle)]
if old:
    b.remove_items(old)

EDGE = 0.15                             # silkscreen to board edge
fpl = list(b.get_footprints())
for f in fpl:
    r, v = f.reference_field, f.value_field
    r.visible = False
    v.visible = False
    f.reference_field, f.value_field = r, v
    d = f.definition
    keep = []
    for it in d.items:
        if isinstance(it, BoardShape) and it.layer in SILK:
            bb = b.get_item_bounding_box(it)
            x1, y1 = bb.pos.x / 1e6 - X0, bb.pos.y / 1e6 - Y0
            x2, y2 = x1 + bb.size.x / 1e6, y1 + bb.size.y / 1e6
            if x1 < EDGE or y1 < EDGE or x2 > W - EDGE or y2 > H - EDGE:
                continue
        keep.append(it)
    if len(keep) != len(d.items):
        print(f.reference_field.text.value, 'silk items trimmed:', len(d.items) - len(keep))
        d.items = keep
b.update_items(fpl)

items = []


def text(s, x, y, size=0.8, back=False):
    t = BoardText()
    t.layer = bt.BL_B_SilkS if back else bt.BL_F_SilkS
    t.value, t.position = s, mm(X0 + x, Y0 + y)
    a = t.attributes
    a.size = Vector2.from_xy_mm(size, size)
    a.stroke_width = 150000
    a.mirrored = back
    t.attributes = a
    items.append(t)


def dot(x, y, r=0.15):
    c = BoardCircle()
    c.layer = bt.BL_F_SilkS
    c.center, c.radius_point = mm(X0 + x, Y0 + y), mm(X0 + x + r, Y0 + y)
    c.attributes.stroke.width = 150000
    c.attributes.fill.filled = True
    items.append(c)


# The top side has no room beside the header pads, so the pin names go on the bottom. Numbers are GPIOs.
J6 = ['5V', 'SYS', 'GND', '27', '26', '22', '21', '20', '19', '18', '17', '16']
J7 = ['3V3', 'EN', 'RUN', 'GND', '0', '1', '2', '3', '4', '5', '6', '7']
ALT = {(6, 3): 'A1', (6, 4): 'A0', (7, 8): 'SDA', (7, 9): 'SCL'}
for i in range(12):
    x = 12.6 + 2.54 * i
    text(J6[i], x, 3.4, back=True)
    text(J7[i], x, 22.0, back=True)
    if (6, i) in ALT:
        text(ALT[6, i], x, 4.7, back=True)
    if (7, i) in ALT:
        text(ALT[7, i], x, 20.7, back=True)

text('RP2350 DevBoard', 52, 10.0, size=1.5, back=True)
text('Wi-Fi  BLE  microSD  LiPo', 52, 12.6, size=1.0, back=True)
text('rev A', 52, 14.6, size=0.8, back=True)
text('BAT +', 6.2, 15.1, size=1.0, back=True)
text('BAT -', 6.2, 17.1, size=1.0, back=True)
text('LiPo 1S 4.2V', 6.2, 19.0, size=0.8, back=True)
text('USB', 4.2, 5.9, size=1.0, back=True)
text('microSD', 51, 5.0, size=1.0, back=True)
text('QWIIC', 46.6, 19.0, size=0.8, back=True)
text('SWD', 54.3, 19.0, size=0.8, back=True)
text('C  G  D', 54.3, 20.4, back=True)
text('BOOT', 73.0, 2.3)
text('RST', 72.6, 23.1)
text('+', 9.9, 13.9, size=1.0)
dot(23.45, 10.95)                       # L1 pad 1

b.create_items(items)
b.save()
print('texts', len(items), 'removed', len(old))
