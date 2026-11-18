"""Generate the KiCad schematic from design.py. Rebuilds every sheet from scratch."""
import math
import os
import sys

from kipy import KiCad
import kipy.kicad as KK
import kipy.schematic_types as ST
from kipy.geometry import Vector2
from kipy.proto.common.types import base_types_pb2
from kipy.proto.common.types.enums_pb2 import HorizontalAlignment as HA
PageSize = base_types_pb2.PageSize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design as D  # noqa: E402

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "rp2350-devboard"
G = 2.54
PAGE_W, PAGE_H = 420.0, 297.0  # A3
X0, Y0, X1 = 20.0, 22.0, 400.0
GAP = 5.08

O = ST.SchematicSymbolOrientation
ORIENTS = [O.SSO_0, O.SSO_90, O.SSO_180, O.SSO_270]
OUTWARD = {ST.SchematicPinOrientation.SPO_RIGHT: (-1, 0), ST.SchematicPinOrientation.SPO_LEFT: (1, 0),
           ST.SchematicPinOrientation.SPO_UP: (0, 1), ST.SchematicPinOrientation.SPO_DOWN: (0, -1)}
SPIN = {(-1, 0): ST.SchematicLabelSpinStyle.SLSS_LEFT, (1, 0): ST.SchematicLabelSpinStyle.SLSS_RIGHT,
        (0, -1): ST.SchematicLabelSpinStyle.SLSS_UP, (0, 1): ST.SchematicLabelSpinStyle.SLSS_BOTTOM}
NET_SHEETS = D.sheets_of_net()


def rot(v, o):
    x, y = v
    return {O.SSO_0: (x, y), O.SSO_90: (y, -x), O.SSO_180: (-x, -y), O.SSO_270: (-y, x)}[o]


def mm(x, y):
    return Vector2.from_xy_mm(x, y)


def snap(v):
    return round(v / G) * G


def wire(a, b):
    w = ST.SchematicLine()
    w.start, w.end, w.type = mm(*a), mm(*b), ST.SchematicLineType.SLT_WIRE
    return w


def is_power(net):
    return net in D.POWER_SYMBOLS


def is_global(net):
    return net in ("VSYS", "VBAT") or is_power(net) or len(NET_SHEETS.get(net, ())) > 1


def label_len(net):
    return 0.95 * len(net) + (3.0 if is_global(net) else 0.8)


class Placed:
    """One symbol with its pins grouped by tip position, in coordinates relative to its origin."""

    def __init__(self, p, inst):
        self.p, self.inst = p, inst
        groups = {}
        for pin in inst.definition.pins:
            key = (round(pin.position.x / 1e6, 3), round(pin.position.y / 1e6, 3))
            groups.setdefault(key, []).append(pin)
        self.pins = []
        for (x, y), pins in groups.items():
            nets = {p["nets"].get(pin.number) for pin in pins} - {None}
            missing = [pin.number for pin in pins if pin.number not in p["nets"]]
            if missing and not nets:
                raise SystemExit(f"{p['ref']}: no net for pins {missing}")
            if len(nets) != 1:
                raise SystemExit(f"{p['ref']}: stacked pins {[q.number for q in pins]} get nets {nets}")
            self.pins.append(dict(pos=(x, y), out=OUTWARD[pins[0].orientation], net=nets.pop(),
                                  num=pins[0].number))
        self.two_pin = len(self.pins) == 2
        self.orient = self.choose_orientation() if self.two_pin else O.SSO_0

    def choose_orientation(self):
        def score(o):
            s = 0
            for pin in self.pins:
                dx, dy = rot(pin["out"], o)
                if pin["net"] == "GND":
                    s += 3 * dy
                elif is_power(pin["net"]) or pin["net"] in ("VSYS", "VBAT"):
                    s -= 2 * dy
                elif all(not is_power(q["net"]) for q in self.pins):
                    s += 1 if dy == 0 else 0
                    s += 1 if (pin["num"] == "1" and dx < 0) or (pin["num"] == "2" and dx > 0) else 0
            if self.p["lib"] == "Device:LED" and all(not is_power(q["net"]) for q in self.pins):
                s += 2 if o == O.SSO_180 else 0  # anode left so current flows left to right
            return s
        return max(ORIENTS, key=score)

    def rpins(self):
        for pin in self.pins:
            yield dict(pin, pos=rot(pin["pos"], self.orient), out=rot(pin["out"], self.orient))

    def bbox(self):
        xs, ys = [-G, G], [-G, G]
        for pin in self.rpins():
            (x, y), (dx, dy) = pin["pos"], pin["out"]
            xs.append(x)
            ys.append(y)
            n = pin["net"]
            if n == D.NC:
                continue
            if self.two_pin and dx == 0 and not is_power(n):
                ex, ey = x - G - label_len(n), y + dy * G
                xs.append(ex)
                ys.append(ey - 1.5)
                ys.append(ey + 1.5)
            elif self.two_pin and is_power(n):
                ys.append(y + dy * 5.0)
            else:
                L = 2 * G + label_len(n) + (0 if is_global(n) else 8)
                xs.append(x + dx * L)
                ys.append(y + dy * L)
                if dy:
                    xs += [x - 1.5, x + 1.5]
        if self.two_pin:
            vertical = any(pin["out"][1] for pin in self.rpins())
            if vertical:
                xs.append(G + 1.1 * max(len(self.p["ref"]), len(self.p["value"])) + 1)
            else:
                ys += [-2 * G - 1, 2 * G + 1]
        else:
            ys += [min(ys) - 2 * G, max(ys) + 2 * G]
        return min(xs), min(ys), max(xs), max(ys)


def set_field(field, x, y, align, angle, visible=True):
    field.text.position = mm(x, y)
    a = field.text.attributes
    a.angle = angle
    a.horizontal_alignment = align
    field.visible = visible


def build_sheet(sch, sheet_name, counters):
    ps = sch.get_page_settings()
    ps.page_size = PageSize.PS_A3
    sch.set_page_settings(ps)
    if sheet_name:
        tb = sch.get_title_block()
        tb.title = f"RP2350 dev board: {sheet_name}"
        tb.revision = "A"
        sch.set_title_block(tb)
    parts = [p for p in D.parts if p["sheet"] == sheet_name]
    placed = []
    for p in parts:
        inst = sch.place_symbol_from_library(p["lib"], mm(0, 0), reference=p["ref"])
        placed.append(Placed(p, inst))

    # shelf packing in design order
    x, y, row_h = X0, Y0, 0.0
    for pl in placed:
        bx0, by0, bx1, by1 = pl.bbox()
        w, h = bx1 - bx0, by1 - by0
        if x + w > X1 and x > X0:
            x, y, row_h = X0, y + row_h + GAP, 0.0
        pl.origin = (snap(x - bx0 + 1.27), snap(y - by0 + 1.27))
        x += w + GAP
        row_h = max(row_h, h)
    if y + row_h > PAGE_H - 40:
        print(f"warning: sheet {sheet_name} overflows page ({y + row_h:.0f} mm)")

    items = []
    for pl in placed:
        ox, oy = pl.origin
        inst, p = pl.inst, pl.p
        inst.position = mm(ox, oy)
        for f in [inst.reference_field, inst.value_field, inst.footprint_field, inst.datasheet_field,
                  inst.description_field]:
            f.text.position = mm(f.text.position.x / 1e6 + ox, f.text.position.y / 1e6 + oy)
        inst.transform.orientation = pl.orient
        inst.value = p["value"]
        inst.footprint_field.text.value = p["fp"]
        if p["ds"]:
            inst.datasheet_field.text.value = p["ds"]
        for name, val in [("Manufacturer", p["mfr"]), ("MPN", p["mpn"]), ("LCSC Part #", p["lcsc"])]:
            if val:
                f = ST.SchematicField()
                f.name, f.text.value, f.visible = name, val, False
                f.text.position = mm(ox, oy)
                inst.user_fields.append(f)
        if p["unpopulated"]:
            inst.attributes.exclude_from_bill_of_materials = True
            inst.attributes.exclude_from_position_files = True
            if p["nets"]:
                inst.attributes.do_not_populate = True
        if pl.two_pin:
            vertical = any(pin["out"][1] for pin in pl.rpins())
            L, C = HA.HA_LEFT, HA.HA_CENTER
            angle = 90 if pl.orient in (O.SSO_90, O.SSO_270) else 0
            if vertical:
                set_field(inst.reference_field, ox + G, oy - 1.27, L, angle)
                set_field(inst.value_field, ox + G, oy + 1.27, L, angle)
            else:
                set_field(inst.reference_field, ox, oy - 2 * G, C, angle)
                set_field(inst.value_field, ox, oy + 2 * G, C, angle)
        inst.proto.ClearField("definition")
        sch.update_items([inst])

        rp = list(pl.rpins())
        # IC power pins on the top/bottom edges: tie same-net neighbours with one wire and one symbol
        done = set()
        if not pl.two_pin:
            for side in [(0, -1), (0, 1)]:
                edge = sorted([q for q in rp if q["out"] == side], key=lambda q: q["pos"][0])
                i = 0
                while i < len(edge):
                    j = i
                    while j + 1 < len(edge) and edge[j + 1]["net"] == edge[i]["net"]:
                        j += 1
                    grp = edge[i:j + 1]
                    net = grp[0]["net"]
                    if is_power(net):
                        yy = oy + grp[0]["pos"][1] + side[1] * G
                        xs = [ox + q["pos"][0] for q in grp]
                        for q in grp:
                            qx = ox + q["pos"][0]
                            items.append(wire((qx, oy + q["pos"][1]), (qx, yy)))
                            if len(grp) > 1 and qx not in (xs[0], xs[-1]):
                                jn = ST.Junction()
                                jn.position = mm(qx, yy)
                                items.append(jn)
                            done.add(q["num"])
                        if len(grp) > 1:
                            items.append(wire((xs[0], yy), (xs[-1], yy)))
                        cx = snap((xs[0] + xs[-1]) / 2)
                        if cx not in xs and len(grp) > 1:
                            jn = ST.Junction()
                            jn.position = mm(cx, yy)
                            items.append(jn)
                        items.append(("power", net, (cx, yy), side))
                    i = j + 1

        tips = {(round(q["pos"][0], 2), round(q["pos"][1], 2)): q for q in rp if q["num"] not in done}

        def stub_len(q):
            """Local label text sits above (or left of) its wire, so clear a global label box on that side."""
            if pl.two_pin or is_global(q["net"]):
                return G
            (x, y), (dx, dy) = q["pos"], q["out"]
            nb = tips.get((round(x - G * abs(dy), 2), round(y - G * abs(dx), 2)))
            if nb and nb["out"] == q["out"] and is_global(nb["net"]):
                return G + math.ceil((label_len(nb["net"]) + 1) / G) * G
            return G

        for q in rp:
            if q["num"] in done:
                continue
            tx, ty = ox + q["pos"][0], oy + q["pos"][1]
            dx, dy = q["out"]
            net = q["net"]
            if net == D.NC:
                nc = ST.NoConnectMarker()
                nc.position = mm(tx, ty)
                items.append(nc)
                continue
            if pl.two_pin and is_power(net) and dy:
                items.append(("power", net, (tx, ty), (dx, dy)))
                continue
            if pl.two_pin and dy:
                ex, ey = tx - G, ty + dy * G
                items += [wire((tx, ty), (tx, ey)), wire((tx, ey), (ex, ey))]
                items.append(("label", net, (ex, ey), (-1, 0)))
                continue
            s = stub_len(q)
            ex, ey = tx + dx * s, ty + dy * s
            items.append(wire((tx, ty), (ex, ey)))
            items.append(("label", net, (ex, ey), (dx, dy)))

    real = []
    for it in items:
        if not isinstance(it, tuple):
            real.append(it)
            continue
        kind, net, (px, py), d = it
        if kind == "power":
            counters["pwr"] += 1
            orient = O.SSO_0 if (net == "GND") == (d == (0, 1)) else O.SSO_180
            sch.place_symbol_from_library(D.POWER_SYMBOLS[net], mm(px, py), orientation=orient,
                                          reference=f"#PWR{counters['pwr']:03d}")
        else:
            lab = ST.GlobalLabel() if is_global(net) else ST.LocalLabel()
            lab.text.value = net
            lab.position = mm(px, py)
            lab.spin_style = SPIN[d]
            real.append(lab)
    if real:
        sch.create_items(real)


def main():
    root_path = f"{PROJ}/{NAME}.kicad_sch"
    k = KiCad(headless=True, timeout_ms=120000)
    k.create_document(root_path, base_types_pb2.DocumentType.DOCTYPE_SCHEMATIC)
    sch = k.get_schematic()
    k.load_all_libraries(KK.LibraryType.LT_SYMBOL)
    k.wait_for_libraries()

    sheets = []
    for i, name in enumerate(D.SHEETS):
        sh = ST.SheetSymbol()
        sh.position = mm(30 + i * 70, 60)
        sh.size = mm(50, 25)
        sh.name_field.text.value = name
        sh.filename_field.text.value = f"{PROJ}/{D.SHEET_FILES[name]}.kicad_sch"
        sheets.append(sh)
    sch.create_items(sheets)

    counters = {"pwr": 0}
    flags = [("GND", "MCU"), ("+1V1", "MCU"), ("VREG_AVDD", "MCU"), ("VBUS", "USB & Power"), ("BB_VINA", "USB & Power")]
    for i, (net, sh) in enumerate(flags):
        D.parts.append(dict(ref=f"#FLG{i + 1:02d}", lib="power:PWR_FLAG", value="PWR_FLAG", fp="", nets={"1": net},
                            mfr="", mpn="", lcsc="", ds="", sheet=sh, unpopulated=False))

    hier = sch.get_hierarchy()
    children = {c.name: c for c in hier.root.children}
    for name in D.SHEETS:
        build_sheet(sch.for_sheet(children[name]), name, counters)
    build_sheet(sch, None, counters)  # fiducials live on the root sheet
    sch.save()

    syms = list(sch.get_sheet_symbols())
    for sh in syms:
        sh.filename_field.text.value = os.path.basename(sh.filename_field.text.value)
    sch.update_items(syms)
    sch.save()
    print("saved", root_path)


if __name__ == "__main__":
    main()
