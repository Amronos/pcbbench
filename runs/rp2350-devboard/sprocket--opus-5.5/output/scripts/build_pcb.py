"""Create the board from the schematic netlist: outline, layers, rules, placement, pours, keepouts, and the few
tracks that must follow a reference layout.

It rebuilds rp2350-devboard.kicad_pcb from scratch, so run it only before routing."""
import fnmatch
import json
import math
import os
import re
import subprocess
import sys

from kipy import KiCad
from kipy.board_types import BoardArc, BoardSegment, Track, Via, Zone
from kipy.geometry import Angle, PolygonWithHoles, PolyLine, PolyLineNode, Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types import base_types_pb2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hand_routes as HR  # noqa: E402
import placement as PL  # noqa: E402

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "rp2350-devboard"
PCB = f"{PROJ}/{NAME}.kicad_pcb"
BX, BY = 100.0, 50.0
R_CORNER = 1.0
L = bt.BoardLayer
COPPER = [L.BL_F_Cu, L.BL_In1_Cu, L.BL_In2_Cu, L.BL_B_Cu]

# PCBWay standard 4-layer service (pcbway.com/capabilities), with margin above its minimums
MIN = dict(clearance=0.127, track=0.127, via_size=0.45, via_annular=0.15, drill=0.2, hole_clearance=0.19,
           hole_to_hole=0.25, edge=0.25)
NET_CLASSES = {  # name: (track, clearance, patterns)
    "Default": (0.15, 0.15, []),
    "Supply": (0.25, 0.15, ["GND", "+3V3", "+1V1", "*VREG_AVDD"]),
    "Power": (0.4, 0.15, ["VBUS", "VSYS", "VBAT", "*BAT_CONN", "*BB_L1", "*BB_L2"]),
    "USB": (0.2, 0.15, ["USB_D?", "*USB_D?_MCU"]),
    "VregLX": (0.14, 0.15, ["*VREG_LX"]),
}
# Raspberry Pi's regulator layout runs VREG_LX between the pads of the VREG_VIN and DVDD capacitors
CUSTOM_RULES = """(version 1)
(rule "VREG_LX between capacitor pads"
  (condition "A.NetName == '/MCU/VREG_LX'")
  (constraint clearance (min 0.127mm)))
"""
# F.Cu 1 oz / 0.2 mm prepreg / In1 / 1.065 mm core / In2 / 0.2 mm prepreg / B.Cu: PCBWay's 1.6 mm 4-layer build
STACKUP = """		(stackup
			(layer "F.SilkS" (type "Top Silk Screen"))
			(layer "F.Paste" (type "Top Solder Paste"))
			(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
			(layer "F.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 1" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "In1.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
			(layer "In2.Cu" (type "copper") (thickness 0.035))
			(layer "dielectric 3" (type "prepreg") (thickness 0.2) (material "FR4") (epsilon_r 4.4) (loss_tangent 0.02))
			(layer "B.Cu" (type "copper") (thickness 0.035))
			(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
			(layer "B.Paste" (type "Bottom Solder Paste"))
			(layer "B.SilkS" (type "Bottom Silk Screen"))
			(copper_finish "ENIG")
			(dielectric_constraints no)
		)
"""
# Switch-node keepouts on the layers below them; pours stay allowed. SW_VREG allows vias because its capacitors'
# GND pads have no other way to the ground plane.
KEEPOUTS = {
    "SW_BUCKBOOST": ((13.6, 46.94, 17.2, 50.94), ["tracks", "vias"]),
    "SW_VREG": ((10.4, 32.44, 13.1, 37.34), ["tracks"]),
}
GND_ZONE_CLEARANCE = 0.2


def P(x, y):
    return Vector2.from_xy_mm(BX + x, BY + y)


def nm(v):
    return round(v * 1e6)


def outline_shapes():
    w, h, r = PL.W, PL.H, R_CORNER
    segs = [((r, 0), (w - r, 0)), ((w, r), (w, h - r)), ((w - r, h), (r, h)), ((0, h - r), (0, r))]
    arcs = [((0, r), (r, 0), (r, r)), ((w - r, 0), (w, r), (w - r, r)), ((w, h - r), (w - r, h), (w - r, h - r)),
            ((r, h), (0, h - r), (r, h - r))]
    out = []
    for a, b in segs:
        s = BoardSegment()
        s.start, s.end, s.layer = P(*a), P(*b), L.BL_Edge_Cuts
        s.attributes.stroke.width = 100000
        out.append(s)
    for a, b, c in arcs:
        mid = (c[0] + (a[0] + b[0] - 2 * c[0]) / math.sqrt(2), c[1] + (a[1] + b[1] - 2 * c[1]) / math.sqrt(2))
        arc = BoardArc()
        arc.start, arc.mid, arc.end, arc.layer = P(*a), P(*mid), P(*b), L.BL_Edge_Cuts
        arc.attributes.stroke.width = 100000
        out.append(arc)
    return out


def polygon(pts):
    line = PolyLine()
    for x, y in pts:
        line.append(PolyLineNode.from_point(P(x, y)))
    line.closed = True
    poly = PolygonWithHoles()
    poly.outline = line
    return poly


def zone(net, layer, priority, pts):
    z = Zone()
    z.net, z.layers, z.priority = net, [layer], priority
    z.outline = polygon(pts)
    z.clearance = nm(GND_ZONE_CLEARANCE)
    z.min_thickness = nm(0.2)
    z.island_mode = bt.IRM_ALWAYS
    z.proto.copper_settings.connection.zone_connection = bt.ZCS_FULL
    return z


def inward_vias(u1, nets):
    """A via under the package for each power pin whose neighbours both escape outward, joined by a short stub."""
    cx, cy = u1.position.x / 1e6, u1.position.y / 1e6
    items = []
    for pad in u1.definition.pads:
        if pad.number not in PL.INWARD_VIAS:
            continue
        shift = PL.INWARD_VIAS[pad.number]
        px, py = pad.position.x / 1e6, pad.position.y / 1e6
        dx, dy = px - cx, py - cy
        if abs(dx) > abs(dy):
            knee = (cx + math.copysign(2.8, dx), py)
            vx, vy = cx + math.copysign(2.45, dx), py - math.copysign(shift, dy)
        else:
            knee = (px, cy + math.copysign(2.8, dy))
            vx, vy = px - math.copysign(shift, dx), cy + math.copysign(2.45, dy)
        v = Via()
        v.position = Vector2.from_xy_mm(vx, vy)
        v.diameter, v.drill_diameter = nm(0.6), nm(0.3)
        v.net = nets[pad.net.name]
        items.append(v)
        pts = [pad.position, Vector2.from_xy_mm(*knee), v.position]
        for a, b in zip(pts, pts[1:]):
            t = Track()
            t.start, t.end = a, b
            t.layer, t.width, t.net = L.BL_F_Cu, nm(0.2), v.net
            items.append(t)
    return items


def vreg_lx_track(fps, nets):
    """VREG_LX from pin 48 straight down between the C12 and C13 pads, then to L1 pad 2 (hwdesign figure 4)."""
    pin = next(p for p in fps["U1"].definition.pads if p.number == "48")
    lpad = next(p for p in fps["L1"].definition.pads if p.number == "2")
    x0, y0 = pin.position.x / 1e6, pin.position.y / 1e6
    lx, ly = lpad.position.x / 1e6, lpad.position.y / 1e6
    pts = [(x0, y0), (x0, ly - 1.15), (lx + 0.2, ly - 0.55), (lx, ly)]
    out = []
    for (ax, ay), (bx_, by_) in zip(pts, pts[1:]):
        t = Track()
        t.start, t.end = Vector2.from_xy_mm(ax, ay), Vector2.from_xy_mm(bx_, by_)
        t.layer, t.width, t.net = L.BL_F_Cu, nm(NET_CLASSES["VregLX"][0]), nets[pin.net.name]
        out.append(t)
    return out


def build_board():
    k = KiCad(headless=True, timeout_ms=300000)
    k.create_document(PCB, base_types_pb2.DocumentType.DOCTYPE_PCB)
    b = k.get_board()
    tech = [L.BL_F_SilkS, L.BL_B_SilkS, L.BL_F_Mask, L.BL_B_Mask, L.BL_F_Paste, L.BL_B_Paste, L.BL_F_Fab, L.BL_B_Fab,
            L.BL_F_CrtYd, L.BL_B_CrtYd, L.BL_Edge_Cuts, L.BL_Dwgs_User, L.BL_Cmts_User, L.BL_Margin]
    b.set_enabled_layers(4, COPPER + tech)

    rules = b.get_design_rules().rules
    c = rules.proto.constraints
    c.min_clearance.value_nm = nm(MIN["clearance"])
    c.min_connection_width.value_nm = nm(MIN["track"])
    c.min_track_width.value_nm = nm(MIN["track"])
    c.min_via_annular_width.value_nm = nm(MIN["via_annular"])
    c.min_via_size.value_nm = nm(MIN["via_size"])
    c.min_through_drill.value_nm = nm(MIN["drill"])
    c.hole_clearance.value_nm = nm(MIN["hole_clearance"])
    c.hole_to_hole_min.value_nm = nm(MIN["hole_to_hole"])
    c.copper_edge_clearance.value_nm = nm(MIN["edge"])
    b.set_design_rules(rules)

    netlist = f"/tmp/{NAME}-import.net"
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", netlist,
                    f"{PROJ}/{NAME}.kicad_sch"], check=True, capture_output=True)
    r = b.import_netlist(netlist)
    print("netlist import:", r.error_count, "errors", r.warning_count, "warnings")

    b.create_items(outline_shapes())

    fps = {f.reference_field.text.value: f for f in b.get_footprints()}
    missing = set(fps) - set(PL.FIXED)
    if missing:
        print("unplaced:", sorted(missing))
    for ref, (x, y, rot) in PL.FIXED.items():
        f = fps[ref]
        f.position = P(x, y)
        f.orientation = Angle.from_degrees(rot)
    for f in fps.values():
        f.reference_field.visible = False
        f.value_field.visible = False
    b.update_items(list(fps.values()))

    fps = {f.reference_field.text.value: f for f in b.get_footprints()}
    nets = {n.name: n for n in b.get_nets()}
    outline = [(0, 0), (PL.W, 0), (PL.W, PL.H), (0, PL.H)]
    zones = [zone(nets["GND"], layer, 0, outline) for layer in COPPER]
    zones.append(zone(nets["+3V3"], L.BL_In2_Cu, 1, outline))
    copper = inward_vias(fps["U1"], nets) + vreg_lx_track(fps, nets) + hand_routes(nets)
    for item in copper:  # the router never rips locked copper
        item.locked = True
    b.create_items(zones + copper)
    b.save()
    print("saved", PCB)


def class_width(net_name):
    for track, _, patterns in list(NET_CLASSES.values())[1:]:
        if any(fnmatch.fnmatch(net_name, p) for p in patterns):
            return track
    return NET_CLASSES["Default"][0]


def hand_routes(nets):
    def net(short):
        return next(n for name, n in nets.items() if name == short or name.endswith("/" + short))

    items = []
    for short, runs in HR.ROUTES.items():
        n = net(short)
        for layer, pts in runs:
            for a, b in zip(pts, pts[1:]):
                t = Track()
                t.start, t.end = P(*a), P(*b)
                t.layer = L.BL_F_Cu if layer == HR.F else L.BL_B_Cu
                t.width, t.net = nm(class_width(n.name)), n
                items.append(t)
    for short, points in HR.VIAS.items():
        for x, y in points:
            v = Via()
            v.position = P(x, y)
            v.diameter, v.drill_diameter = nm(0.6), nm(0.3)
            v.net = net(short)
            items.append(v)
    return items


def write_project_rules():
    """Net classes live in the .kicad_pro and the stackup in the board's setup block; kipy can write neither."""
    pro_path = f"{PROJ}/{NAME}.kicad_pro"
    pro = json.load(open(pro_path))
    ns = pro["net_settings"]
    default = next(c for c in ns["classes"] if c["name"] == "Default")
    classes, patterns = [], []
    for i, (name, (track, clearance, pats)) in enumerate(NET_CLASSES.items()):
        cls = dict(default, name=name, track_width=track, clearance=clearance, via_diameter=0.6, via_drill=0.3,
                   diff_pair_width=0.2, diff_pair_gap=0.15, diff_pair_via_gap=0.25)
        if name != "Default":
            cls["priority"] = i
        classes.append(cls)
        patterns += [{"netclass": name, "pattern": p} for p in pats]
    ns["classes"], ns["netclass_patterns"] = classes, patterns
    json.dump(pro, open(pro_path, "w"), indent=2)

    open(f"{PROJ}/{NAME}.kicad_dru", "w").write(CUSTOM_RULES)

    pcb = open(PCB).read()
    pcb = re.sub(r"\t\t\(stackup\n.*?\n\t\t\)\n", "", pcb, flags=re.S)
    pcb = pcb.replace("\t(setup\n", "\t(setup\n" + STACKUP, 1)
    open(PCB, "w").write(pcb)


def add_keepouts():
    tool = f"{os.environ['SPROCKET_KICAD_ROUTING_TOOLS']}/py_router/add_rule_area.py"
    for name, ((x0, y0, x1, y1), forbid) in KEEPOUTS.items():
        subprocess.run(["kicad-python", tool, PCB, PCB, "--name", name, "--rect", str(BX + x0), str(BY + y0),
                        str(BX + x1), str(BY + y1), "--layers", "In2.Cu", "B.Cu", "--forbid", *forbid],
                       check=True, capture_output=True)


def main():
    build_board()
    write_project_rules()
    add_keepouts()


if __name__ == "__main__":
    main()
