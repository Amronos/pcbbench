"""Small helper layer over kipy for generating the schematic."""
from kipy import KiCad
from kipy.proto.common.types import DocumentType
from kipy.proto.common.types import enums_pb2 as en
from kipy.geometry import Vector2
from kipy.schematic_types import LocalLabel, GlobalLabel, SchematicLine, NoConnectMarker, Junction, SchematicText
from kipy.proto.schematic import schematic_types_pb2 as st

O = {0: st.SSO_0, 90: st.SSO_90, 180: st.SSO_180, 270: st.SSO_270}
mm = Vector2.from_xy_mm
POWER = {'GND': 'power:GND', '+3V3': 'power:+3V3', 'VBUS': 'power:VBUS', '+1V1': 'power:+1V1', 'VBAT': 'power:+BATT'}
UP_NETS = {'+3V3', 'VBUS', '+1V1', 'VBAT'}


def rot(x, y, o):
    return {0: (x, y), 90: (y, -x), 180: (-x, -y), 270: (-y, x)}[o]


OUT = {1: (-1, 0), 2: (1, 0), 3: (0, 1), 4: (0, -1)}  # pin orientation -> outward direction (y down)


class Part:
    def __init__(self, inst, x, y, o):
        self.inst, self.x, self.y, self.o = inst, x, y, o
        self.pins = {}
        for p in inst.definition.pins:
            px, py = rot(p.position.x / 1e6, p.position.y / 1e6, o)
            dx, dy = rot(*OUT[p.orientation], o)
            self.pins.setdefault(p.number, (round(x + px, 3), round(y + py, 3), dx, dy))
            self.pins.setdefault(p.name, (round(x + px, 3), round(y + py, 3), dx, dy))


class Sch:
    def __init__(self, path, create=True):
        self.k = KiCad(headless=True, timeout_ms=60000)
        self.doc = (self.k.create_document if create else self.k.open_document)(path, DocumentType.DOCTYPE_SCHEMATIC)
        self.s = self.k.get_schematic()
        self.k.load_all_libraries()
        self.k.wait_for_libraries()
        from kipy.proto.common.types import base_types_pb2 as bt
        ps = self.s.get_page_settings()
        ps.page_size = bt.PS_A3
        self.s.set_page_settings(ps)
        self.items = []
        self.parts = {}
        self.npwr = 0

    def place(self, lib, ref, x, y, o=0, value=None, fp=None, fields=None, refpos=None, valpos=None, dnp=False,
              ds=None, hide_value=False):
        inst = self.s.place_symbol_from_library(lib, mm(x, y), orientation=O[o], reference=ref)
        inst.proto.ClearField('definition')
        full = self.s.get_items_by_id(inst.id)[0]
        part = Part(full, x, y, o)
        if value is not None:
            inst.value = value
        if fp is not None:
            inst.footprint_field.proto.text.text = fp
        if ds:
            inst.datasheet_field.proto.text.text = ds
        for name, text in (fields or {}).items():
            if not text:
                continue
            f = inst.proto.user_fields.add()
            f.CopyFrom(inst.footprint_field.proto)
            f.name = name
            f.text.text = text
            f.text.attributes.visible = False
            f.visible = False
        for fld, pos in ((inst.reference_field, refpos), (inst.value_field, valpos)):
            if pos:
                a = fld.proto.text.attributes
                fld.proto.text.position.x_nm = int(round((x + pos[0]) * 1e6))
                fld.proto.text.position.y_nm = int(round((y + pos[1]) * 1e6))
                al = pos[2] if len(pos) > 2 else 'l'
                if o in (90, 180):
                    al = {'l': 'r', 'r': 'l', 'c': 'c'}[al]
                a.horizontal_alignment = {'l': en.HA_LEFT, 'c': en.HA_CENTER, 'r': en.HA_RIGHT}[al]
                a.vertical_alignment = en.VA_CENTER
                a.angle.value_degrees = (pos[3] if len(pos) > 3 else 0) + (90 if o in (90, 270) else 0)
        if hide_value:
            inst.value_field.proto.text.attributes.visible = False
            inst.value_field.proto.visible = False
        self.s.update_items([inst])
        if ref:
            self.parts[ref] = part
        return part

    def wire(self, *pts):
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            w = SchematicLine()
            w.start, w.end = mm(*a), mm(*b)
            w.proto.type = st.SLT_WIRE
            self.items.append(w)

    def junction(self, x, y):
        j = Junction()
        j.position = mm(x, y)
        self.items.append(j)

    def label(self, net, x, y, d):
        l = LocalLabel()
        l.position = mm(x, y)
        l.proto.text.text = net
        l.proto.spin_style = {(-1, 0): st.SLSS_LEFT, (1, 0): st.SLSS_RIGHT, (0, -1): st.SLSS_UP, (0, 1): st.SLSS_BOTTOM}[d]
        self.items.append(l)

    def power(self, net, x, y, side=None):
        """Power symbol with its pin at x,y; GND hangs down, supplies point up, or sideways along `side`."""
        self.npwr += 1
        o, kw = 0, {}
        if side:
            left = side[0] < 0
            o = (90 if left else 270) if net in UP_NETS else (270 if left else 90)
            kw = dict(valpos=(-3.3 if left else 3.3, 0, 'r' if left else 'l'))
        self.place(POWER[net], f'#PWR{self.npwr:03d}', x, y, o, **kw)

    def flag(self, x, y, o=0):
        self.npwr += 1
        self.place('power:PWR_FLAG', f'#FLG{self.npwr:03d}', x, y, o)

    def net_at(self, net, x, y, d, L=2.54, side=False):
        """Attach net to a point with outward direction d."""
        dx, dy = d
        if net in POWER:
            want = (0, -1) if net in UP_NETS else (0, 1)
            if d == want:
                self.wire((x, y), (x + dx * L, y + dy * L))
                self.power(net, x + dx * L, y + dy * L)
            elif dx != 0:
                ex = x + dx * L
                self.wire((x, y), (ex, y))
                self.power(net, ex, y, d if side else None)
            else:  # pin points the wrong vertical way: jog sideways
                ey = y + dy * 2.54
                self.wire((x, y), (x, ey), (x + 2.54, ey), (x + 2.54, ey + want[1] * 2.54))
                self.power(net, x + 2.54, ey + want[1] * 2.54)
        else:
            ex, ey = x + dx * L, y + dy * L
            self.wire((x, y), (ex, ey))
            self.label(net, ex, ey, d)

    def net(self, ref, pin, net, L=2.54, side=False):
        x, y, dx, dy = self.parts[ref].pins[pin]
        self.net_at(net, x, y, (dx, dy), L, side)

    def nets(self, ref, mapping, L=2.54, side=False):
        for pin, net in mapping.items():
            if net is None:
                self.nc(ref, pin)
            else:
                self.net(ref, pin, net, L, side)

    def nc(self, ref, pin):
        x, y, _, _ = self.parts[ref].pins[pin]
        n = NoConnectMarker()
        n.position = mm(x, y)
        self.items.append(n)

    def pin(self, ref, pin):
        return self.parts[ref].pins[pin][:2]

    def text(self, s, x, y, size=1.27, bold=False):
        t = SchematicText()
        t.proto.text.position.x_nm = int(x * 1e6)
        t.proto.text.position.y_nm = int(y * 1e6)
        t.proto.text.text = s
        a = t.proto.text.attributes
        a.size.x_nm = a.size.y_nm = int(size * 1e6)
        a.horizontal_alignment = en.HA_LEFT
        a.vertical_alignment = en.VA_BOTTOM
        a.bold = bold
        a.visible = True
        a.multiline = True
        self.items.append(t)

    def box(self, x1, y1, x2, y2):
        for a, b in (((x1, y1), (x2, y1)), ((x2, y1), (x2, y2)), ((x2, y2), (x1, y2)), ((x1, y2), (x1, y1))):
            w = SchematicLine()
            w.start, w.end = mm(*a), mm(*b)
            w.proto.type = st.SLT_GRAPHIC
            self.items.append(w)

    def flush(self):
        if self.items:
            self.s.create_items(self.items)
            self.items = []

    def save(self):
        self.flush()
        self.s.save()
