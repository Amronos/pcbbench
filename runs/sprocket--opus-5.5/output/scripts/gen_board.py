"""Create the board: layers, netlist import, outline and placement, then write design rules.

`create` needs a freshly restarted `kicad-cli api-server` and rebuilds the board from scratch, so run it only
before routing. `rules` edits the .kicad_pro directly because the headless API cannot open the project.
"""
import copy
import json
import os
import subprocess
import sys

from kipy import KiCad
from kipy.board import Board
from kipy.board_types import BoardSegment, BoardArc, BoardText, Zone
from kipy.geometry import Angle, PolygonWithHoles, PolyLine, PolyLineNode, Vector2
from kipy.proto.board import board_commands_pb2 as bc
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types import base_types_pb2
from kipy.proto.common.types import enums_pb2

sys.path.insert(0, os.path.dirname(__file__))
from design import LEFT, RIGHT  # noqa: E402
from placement import OUTLINE_W, OUTLINE_H, CORNER_R, KEEPOUT_Y  # noqa: E402
from placer import place  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "rp2350_dev"
MM = 1_000_000
ORIGIN = (100.0, 50.0)  # board top-left corner in KiCad page coordinates
COPPER = [bt.BL_F_Cu, bt.BL_In1_Cu, bt.BL_In2_Cu, bt.BL_B_Cu]

# PCBWay standard 4-layer capabilities, with margin: 0.1 mm track/space, 0.2 mm drill, 0.15 mm annular ring
FAB_MINIMUMS = dict(min_clearance=0.1, min_track_width=0.1, min_connection=0.1, min_via_annular_width=0.15,
                    min_via_diameter=0.5, min_through_hole_diameter=0.2, min_copper_edge_clearance=0.3,
                    min_hole_clearance=0.15, min_hole_to_hole=0.25)
# name -> (track, clearance, via diameter, via drill, nets). 0.5/0.2 vias fit between the RP2350's 0.4 mm pads.
NET_CLASSES = {
    "Default": (0.127, 0.127, 0.5, 0.2, []),
    "Supply": (0.25, 0.127, 0.5, 0.2, ["+3V3", "+1V1"]),
    "Power": (0.4, 0.15, 0.6, 0.3, ["VBUS", "VSYS", "VBAT"]),
}


def rules():
    path = os.path.join(ROOT, f"{NAME}.kicad_pro")
    with open(path) as f:
        pro = json.load(f)
    pro["board"]["design_settings"]["rules"].update(FAB_MINIMUMS)
    ns = pro["net_settings"]
    default = next(c for c in ns["classes"] if c["name"] == "Default")
    classes = []
    for i, (name, (track, clearance, via, drill, _)) in enumerate(NET_CLASSES.items()):
        c = copy.deepcopy(default)
        c.update(name=name, track_width=track, clearance=clearance, via_diameter=via, via_drill=drill,
                 diff_pair_width=0.2, diff_pair_gap=0.2)
        if name != "Default":
            c["priority"] = i
        classes.append(c)
    ns["classes"] = classes
    ns["netclass_patterns"] = [{"netclass": name, "pattern": n}
                               for name, (*_, nets) in NET_CLASSES.items() for n in nets]
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)
        f.write("\n")


def pt(x, y):
    return Vector2.from_xy(round((ORIGIN[0] + x) * MM), round((ORIGIN[1] + y) * MM))


def outline():
    w, h, r = OUTLINE_W, OUTLINE_H, CORNER_R
    items = []
    for (x1, y1), (x2, y2) in [((r, 0), (w - r, 0)), ((w, r), (w, h - r)), ((w - r, h), (r, h)), ((0, h - r), (0, r))]:
        s = BoardSegment()
        s.start, s.end = pt(x1, y1), pt(x2, y2)
        items.append(s)
    k = 1 - 2 ** -0.5
    for (sx, sy), (mx, my), (ex, ey) in [
        ((0, r), (r * k, r * k), (r, 0)),
        ((w - r, 0), (w - r * k, r * k), (w, r)),
        ((w, h - r), (w - r * k, h - r * k), (w - r, h)),
        ((r, h), (r * k, h - r * k), (0, h - r)),
    ]:
        a = BoardArc()
        a.start, a.mid, a.end = pt(sx, sy), pt(mx, my), pt(ex, ey)
        items.append(a)
    for it in items:
        it.layer = bt.BL_Edge_Cuts
        it.attributes.stroke.width = round(0.05 * MM)
    return items


def rect(x1, y1, x2, y2):
    line = PolyLine()
    for x, y in [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]:
        line.append(PolyLineNode.from_point(pt(x, y)))
    line.closed = True
    poly = PolygonWithHoles()
    poly.outline = line
    return poly


PLANES = {bt.BL_In2_Cu: "+3V3"}  # layer -> net; every other copper layer pours GND


def zones(nets):
    items = []
    for layer in COPPER:
        z = Zone()
        z.type = bt.ZT_COPPER
        name = PLANES.get(layer, "GND")
        z.net, z.layers, z.priority, z.name = nets[name], [layer], 0, name
        z.outline = rect(0, 0, OUTLINE_W, OUTLINE_H)
        z.clearance = round(0.15 * MM)
        z.min_thickness = round(0.15 * MM)
        z.island_mode = bt.IRM_ALWAYS
        z.proto.copper_settings.connection.zone_connection = bt.ZCS_FULL
        items.append(z)
    # RM2 antenna: no metal on any layer between the module's antenna end and the board edge
    k = Zone()
    k.type = bt.ZT_RULE_AREA
    k.name, k.layers = "RM2 antenna keepout", COPPER
    k.outline = rect(0, 0, OUTLINE_W, KEEPOUT_Y)
    s = k.proto.rule_area_settings
    s.keepout_copper = s.keepout_vias = s.keepout_tracks = s.keepout_pads = True
    items.append(k)
    return items


def create():
    pcb = os.path.join(ROOT, f"{NAME}.kicad_pcb")
    net = "/tmp/scratch/board.net"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net,
                    os.path.join(ROOT, f"{NAME}.kicad_sch")], check=True, capture_output=True)
    k = KiCad(timeout_ms=120000)
    doc = k.create_document(pcb, base_types_pb2.DOCTYPE_PCB)
    k.load_all_libraries()
    k.wait_for_libraries(timeout_s=120)
    board = Board(k._client, doc)
    board.set_enabled_layers(4, board.get_enabled_layers())
    res = board.import_netlist(net, match_mode=bc.NMM_REFERENCE, delete_extra_footprints=True)
    print("netlist import:", res)
    board.create_items(outline())
    # Gerbers, drill and centroid files measure from the bottom-left corner
    board.set_origin(bc.BOT_DRILL, pt(0, OUTLINE_H))

    poses, _, _ = place()
    fps = {f.reference_field.text.value: f for f in board.get_footprints()}
    moved = []
    for ref, (x, y, rot) in poses.items():
        f = fps[ref]
        f.position = pt(x, y)
        f.orientation = Angle.from_degrees(rot)
        moved.append(f)
    board.update_items(moved)
    board.create_items(zones({n.name: n for n in board.get_nets()}))
    board.save()


# header net -> short silkscreen label
SHORT = {"+3V3": "3V3", "3V3_EN": "EN", "I2C_SDA": "SDA", "I2C_SCL": "SCL", "SWDIO": "DIO", "SWCLK": "CLK"}
HEADER_X, HEADER_Y, PITCH = (1.27, OUTLINE_W - 1.27), 7.62, 2.54


def label(text, x, y, layer, size=0.8):
    t = BoardText()
    t.value, t.layer, t.position = text, layer, pt(x, y)
    a = t.attributes
    a.size = Vector2.from_xy(round(size * MM), round(size * MM))
    a.stroke_width = round(0.15 * MM)
    a.horizontal_alignment = enums_pb2.HA_CENTER
    a.vertical_alignment = enums_pb2.VA_CENTER
    a.mirrored = layer == bt.BL_B_SilkS
    t.attributes = a
    return t


def silk():
    """Hide reference and value text, then label the header pins (back) and the user-facing parts (front)."""
    k = KiCad(timeout_ms=120000)
    doc = k.open_document(os.path.join(ROOT, f"{NAME}.kicad_pcb"), base_types_pb2.DOCTYPE_PCB)
    board = Board(k._client, doc)
    board.remove_items([t for t in board.get_text() if isinstance(t, BoardText)])
    fps = board.get_footprints()
    for f in fps:
        f.reference_field.visible = False
        f.value_field.visible = False
        if f.reference_field.text.value in ("J5", "J6"):
            # the header outlines run off the board edge; the pads and back labels are enough
            d = f.definition
            d.items = [i for i in d.items if getattr(i, "layer", None) != bt.BL_F_SilkS]
    board.update_items(fps)

    items = []
    for nets, hx, dx in ((LEFT, HEADER_X[0], 2.9), (RIGHT, HEADER_X[1], -2.9)):
        for i, net in enumerate(nets):
            name = SHORT.get(net, net.removeprefix("GPIO"))
            items.append(label(name, hx + dx, HEADER_Y + PITCH * i, bt.BL_B_SilkS))
    pad = {(f.reference_field.text.value, p.number): p.position for f in fps for p in f.definition.pads}
    # no free front space beside the JST pads, so the battery polarity goes on the back, behind each pad
    for number, text in (("1", "- GND"), ("2", "+ BAT")):
        pos = pad[("J4", number)]
        items.append(label(text, pos.x / MM - ORIGIN[0], pos.y / MM - ORIGIN[1], bt.BL_B_SilkS, 1.0))
    for ref, text in (("SW1", "BOOT"), ("SW2", "RST")):
        pos = next(f.position for f in fps if f.reference_field.text.value == ref)
        items.append(label(text, 2.9, pos.y / MM - ORIGIN[1], bt.BL_F_SilkS))
    items.append(label("RP2350 Wi-Fi LiPo\ndev board rev A", OUTLINE_W / 2, OUTLINE_H - 13, bt.BL_B_SilkS, 1.0))
    board.create_items(items)
    board.save()


def teardrops():
    """Enable teardrops on every pad and via. Run after the last copper change."""
    k = KiCad(timeout_ms=120000)
    board = Board(k._client, k.open_document(os.path.join(ROOT, f"{NAME}.kicad_pcb"), base_types_pb2.DOCTYPE_PCB))

    def enable(td):
        td.mode = bt.PTM_ENABLED
        td.best_length_ratio, td.max_length.value_nm = 0.5, MM
        td.best_width_ratio, td.max_width.value_nm = 1.0, 2 * MM
        td.max_track_width_ratio = 0.9
        td.allow_multiple_track_segments = td.prefer_zone_connection = True

    fps = board.get_footprints()
    for f in fps:
        for p in f.definition.pads:
            enable(p.proto.teardrop)
    vias = board.get_vias()
    for v in vias:
        enable(v.proto.teardrop)
    board.update_items(fps)
    board.update_items(vias)
    board.save()


if __name__ == "__main__":
    {"create": create, "rules": rules, "silk": silk, "teardrops": teardrops}[sys.argv[1]]()
