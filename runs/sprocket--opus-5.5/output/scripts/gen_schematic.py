"""Draw the hierarchical schematic from design.py. Needs a running `kicad-cli api-server`.

Every pin gets a short wire stub ending in a power symbol, a label, or a no-connect marker.
"""
import os
import sys

from kipy import KiCad
from kipy.common_types import PageSettings, TitleBlockInfo
from kipy.geometry import Vector2
from kipy.proto.common.types import base_types_pb2
from kipy.proto.common.types import enums_pb2
from kipy.proto.schematic import schematic_types_pb2 as sp
from kipy.schematic import Schematic
import kipy.schematic_types as st

sys.path.insert(0, os.path.dirname(__file__))
import design  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "rp2350_dev"
MM = 1_000_000
STUB = 2.54
POWER_SYMBOLS = {"GND": ("power:GND", (0, 1)), "+3V3": ("power:+3V3", (0, -1)),
                 "+1V1": ("power:+1V1", (0, -1))}
ORIENT = {0: sp.SSO_0, 90: sp.SSO_90, 180: sp.SSO_180, 270: sp.SSO_270}
PIN_DIR = {sp.SPO_RIGHT: (1, 0), sp.SPO_LEFT: (-1, 0), sp.SPO_UP: (0, -1), sp.SPO_DOWN: (0, 1)}
SPIN = {(-1, 0): sp.SLSS_LEFT, (1, 0): sp.SLSS_RIGHT, (0, -1): sp.SLSS_UP, (0, 1): sp.SLSS_BOTTOM}
# nets ERC sees without a power-output driver
PWR_FLAGS = {"power": ["GND", "VBUS"], "mcu": ["+1V1", "VREG_AVDD"]}


def rotate(v, rot):
    x, y = v
    return {0: (x, y), 90: (y, -x), 180: (-x, -y), 270: (-y, x)}[rot]


def pt(x, y):
    return Vector2.from_xy(round(x * MM), round(y * MM))


def net_sheets():
    used = {}
    for sheet, parts in design.SHEETS.items():
        for p in parts:
            for n in p["nets"].values():
                used.setdefault(n, set()).add(sheet)
    for sheet, nets in PWR_FLAGS.items():
        for n in nets:
            used.setdefault(n, set()).add(sheet)
    return used


def terminal(net, x, y, d, is_global):
    """Items that end a stub at (x, y) whose outward direction is d.

    Power symbols only point up or down; sideways power pins get a global label with the power net's name.
    """
    if net in POWER_SYMBOLS and d[0] == 0:
        lib, body = POWER_SYMBOLS[net]
        rot = next(r for r in ORIENT if rotate(body, r) == d)
        return [], (lib, x, y, rot)
    is_global = is_global or net in POWER_SYMBOLS
    lb = st.GlobalLabel() if is_global else st.LocalLabel()
    lb.position = pt(x, y)
    lb.proto.text.text = net
    lb.proto.spin_style = SPIN[d]
    if is_global:
        lb.proto.shape = sp.SLSH_PASSIVE
    return [lb], None


def junction(x, y):
    j = st.Junction()
    j.position = pt(x, y)
    return j


def on_segment(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    if abs((bx - ax) * (py - ay) - (by - ay) * (px - ax)) > 1e-6:
        return False
    return min(ax, bx) < px < max(ax, bx) or min(ay, by) < py < max(ay, by)


def connect(ends, used):
    """Wire facing pins of the same net directly, join adjacent power pins, and label the rest."""
    items, powers = [], []
    count = {}
    for e in ends:
        count[e["net"]] = count.get(e["net"], 0) + 1
    points = [(e["x"], e["y"]) for e in ends]

    def needs_terminal(net, n_ends):
        return net in POWER_SYMBOLS or len(used[net]) > 1 or count[net] > n_ends

    def add_terminal(net, x, y, d):
        its, pw = terminal(net, x, y, d, len(used[net]) > 1)
        items.extend(its)
        if pw:
            powers.append(pw)

    pending = []
    for e in ends:
        if e["net"] == "NC":
            nc = st.NoConnectMarker()
            nc.position = pt(e["x"], e["y"])
            items.append(nc)
        else:
            pending.append(e)

    paired = set()
    for i, a in enumerate(pending):
        if i in paired:
            continue
        best = None
        for j, b in enumerate(pending):
            if j <= i or j in paired or b["net"] != a["net"] or b["ref"] == a["ref"]:
                continue
            if b["d"] != (-a["d"][0], -a["d"][1]):
                continue
            dx, dy = b["x"] - a["x"], b["y"] - a["y"]
            along, across = (dx * a["d"][0], dy) if a["d"][0] else (dy * a["d"][1], dx)
            if abs(across) > 1e-6 or along <= 0 or along > 50:
                continue
            if any(on_segment(p, (a["x"], a["y"]), (b["x"], b["y"])) for p in points):
                continue
            if best is None or along < best[1]:
                best = (j, along)
        if best is None:
            continue
        j, dist = best
        b = pending[j]
        paired |= {i, j}
        half = round(dist / 2 / 1.27) * 1.27
        mx, my = a["x"] + a["d"][0] * half, a["y"] + a["d"][1] * half
        items += [wire(a["x"], a["y"], mx, my), wire(mx, my, b["x"], b["y"])]
        if needs_terminal(a["net"], 2):
            d = (0, 1) if a["net"] == "GND" else (0, -1)
            if a["d"][0] == 0:
                d = (1, 0)
            sx, sy = mx + d[0] * STUB, my + d[1] * STUB
            items += [wire(mx, my, sx, sy), junction(mx, my)]
            add_terminal(a["net"], sx, sy, d)
        else:
            c = min(a, b, key=lambda e: e["npins"])
            lb = st.LocalLabel()
            lb.position = pt(c["x"] + c["d"][0] * STUB, c["y"] + c["d"][1] * STUB)
            lb.proto.text.text = a["net"]
            lb.proto.spin_style = SPIN[c["d"]] if c["d"][1] == 0 else sp.SLSS_RIGHT
            items.append(lb)

    runs = {}
    rest = []
    for i, e in enumerate(pending):
        if i in paired:
            continue
        if e["net"] in POWER_SYMBOLS:
            across = e["y"] if e["d"][0] == 0 else e["x"]
            runs.setdefault((e["ref"], e["net"], e["d"], round(across, 3)), []).append(e)
        else:
            rest.append([e])
    groups = []
    for (ref, net, d, across), es in runs.items():
        key = (lambda e: e["x"]) if d[0] == 0 else (lambda e: e["y"])
        side = [key(e) for e in ends if e["ref"] == ref and e["d"] == d and e["net"] != net
                and round(e["y"] if d[0] == 0 else e["x"], 3) == across]
        es.sort(key=key)
        run = [es[0]]
        for e in es[1:]:
            if not any(key(run[-1]) < s < key(e) for s in side):
                run.append(e)
            else:
                groups.append(run)
                run = [e]
        groups.append(run)
    for run in groups + rest:
        stub_ends = []
        for e in run:
            d = e["d"]
            sx, sy = e["x"] + d[0] * STUB, e["y"] + d[1] * STUB
            items.append(wire(e["x"], e["y"], sx, sy))
            stub_ends.append((sx, sy))
        for k in range(1, len(stub_ends)):
            items.append(wire(*stub_ends[k - 1], *stub_ends[k]))
        for p in stub_ends[1:-1]:
            items.append(junction(*p))
        mid = stub_ends[len(stub_ends) // 2]
        add_terminal(run[0]["net"], *mid, run[0]["d"])
    return items, powers


def wire(x1, y1, x2, y2):
    w = st.SchematicLine()
    w.proto.type = sp.SLT_WIRE
    w.start, w.end = pt(x1, y1), pt(x2, y2)
    return w


def add_field(sym, name, value):
    f = sym.proto.user_fields.add()
    f.name = name
    f.text.text = value
    f.text.position.CopyFrom(sym.proto.position)
    f.text.attributes.size.x_nm = f.text.attributes.size.y_nm = round(1.27 * MM)
    f.visible = False


def text(x, y, s, size=1.27, bold=False):
    t = st.SchematicText()
    t.proto.text.text = s
    t.proto.text.position.CopyFrom(pt(x, y).proto)
    a = t.proto.text.attributes
    a.size.x_nm = a.size.y_nm = round(size * MM)
    a.horizontal_alignment = enums_pb2.HA_LEFT
    a.vertical_alignment = enums_pb2.VA_TOP
    a.bold = bold
    a.visible = True
    return t


def title_block(title):
    tb = TitleBlockInfo()
    tb.title = "RP2350 Wi-Fi/BLE LiPo dev board"
    tb.revision = "A"
    tb.proto.comment1 = title
    return tb


def draw_sheet(sub, sheet, used):
    ends = []
    for p in design.SHEETS[sheet]:
        sym = sub.place_symbol_from_library(p["lib"], pt(p["x"], p["y"]), orientation=ORIENT[p["rot"]],
                                            reference=p["ref"])
        pins = list(sym.definition.pins)
        nets = {}
        for key, net in p["nets"].items():
            match = [q for q in pins if (q.name == key[1:] if key.startswith("@") else q.number == key)]
            if not match:
                raise SystemExit(f"{p['ref']}: no pin {key}")
            for q in match:
                nets[q.number] = net
        missing = [f"{q.number}:{q.name}" for q in pins if q.number not in nets]
        if missing and p["nets"]:
            raise SystemExit(f"{p['ref']}: unmapped pins {missing}")
        part_ends = {}
        for q in pins:
            if q.number not in nets:
                continue
            lx, ly = rotate((q.position.x / MM, q.position.y / MM), p["rot"])
            d = rotate(PIN_DIR[q.orientation], p["rot"])
            key = (round(lx, 3), round(ly, 3))
            if key in part_ends and part_ends[key]["net"] != nets[q.number]:
                raise SystemExit(f"{p['ref']}: stacked pins on different nets at {key}")
            part_ends[key] = dict(ref=p["ref"], net=nets[q.number], d=(-d[0], -d[1]), npins=len(pins),
                                  x=round(p["x"] + lx, 3), y=round(p["y"] + ly, 3))
        ends += part_ends.values()

        sym.value = p["value"]
        sym.proto.footprint_field.text.text = p["fp"]
        sym.proto.footprint_field.visible = False
        if p["datasheet"]:
            sym.proto.datasheet_field.text.text = p["datasheet"]
        sym.proto.datasheet_field.visible = False
        if p["desc"]:
            sym.proto.description_field.text.text = p["desc"]
        sym.proto.description_field.visible = False
        if p["mpn"]:
            add_field(sym, "Manufacturer", p["mfr"])
            add_field(sym, "MPN", p["mpn"])
        for name, value in design.DISTRIBUTORS.get(p["mpn"], {}).items():
            add_field(sym, name, value)
        sym.attributes.exclude_from_bill_of_materials = not p["in_bom"]
        sym.attributes.do_not_populate = p["dnp"]
        sym.attributes.exclude_from_position_files = not p["in_bom"]
        sym.proto.ClearField("definition")
        sub.update_items([sym])

    items, powers = connect(ends, used)
    for i, net in enumerate(PWR_FLAGS.get(sheet, [])):
        x, y = 20.32 + i * 15.24, 264.16
        sub.place_symbol_from_library("power:PWR_FLAG", pt(x, y), reference="#FLG")
        its, pw = terminal(net, x, y + STUB, (0, 1), len(used[net]) > 1)
        items += its + [wire(x, y, x, y + STUB)]
        if pw:
            powers.append(pw)

    for lib, x, y, rot in powers:
        sub.place_symbol_from_library(lib, pt(x, y), orientation=ORIENT[rot], reference="#PWR")

    items.append(text(12.7, 12.7, design.SHEET_TITLES[sheet], size=3, bold=True))
    for i, line in enumerate(design.NOTES.get(sheet, [])):
        items.append(text(12.7, 22.86 + i * 5.08, line, size=1.778))
    sub.create_items(items)


def main():
    k = KiCad(timeout_ms=60000)
    root_path = os.path.join(ROOT, f"{NAME}.kicad_sch")
    doc = k.create_document(root_path, base_types_pb2.DOCTYPE_SCHEMATIC)
    k.load_all_libraries()
    k.wait_for_libraries(timeout_s=120)
    sch = Schematic(k._client, doc)

    sheets = list(design.SHEETS)
    syms = []
    for i, s in enumerate(sheets):
        sh = st.SheetSymbol()
        sh.position = pt(38.1 + (i % 2) * 101.6, 50.8 + (i // 2) * 50.8)
        sh.size = pt(76.2, 25.4)
        sh.proto.name_field.name = "Sheetname"
        sh.proto.name_field.text.text = s
        sh.proto.filename_field.name = "Sheetfile"
        sh.proto.filename_field.text.text = os.path.join(ROOT, f"{s}.kicad_sch")
        syms.append(sh)
    sch.create_items(syms)
    a3 = base_types_pb2.PageSettings()
    a3.page_size = base_types_pb2.PS_A3
    sch.set_page_settings(PageSettings(a3))
    sch.set_title_block(title_block("Top level"))
    root_items = [text(38.1, 25.4, "RP2350 Wi-Fi/BLE LiPo development board", size=3, bold=True)]
    for i, s in enumerate(sheets):
        root_items.append(text(38.1 + (i % 2) * 101.6, 78.74 + (i // 2) * 50.8, design.SHEET_TITLES[s]))
    sch.create_items(root_items)

    used = net_sheets()
    children = sch.get_hierarchy().top_level_sheets[0].children
    for child in children:
        sub = sch.for_sheet(child)
        sub.set_page_settings(PageSettings(a3))
        sub.set_title_block(title_block(design.SHEET_TITLES[child.name]))
        draw_sheet(sub, child.name, used)
    sch.save()
    for ss in sch.get_sheet_symbols():
        ss.proto.filename_field.text.text = os.path.basename(ss.proto.filename_field.text.text)
        sch.update_items([ss])
    sch.save()


if __name__ == "__main__":
    main()
