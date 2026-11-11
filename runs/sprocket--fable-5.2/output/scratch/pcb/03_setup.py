"""Design rules (PCBWay standard 4-layer), GND pours and keep-outs. Idempotent. Run 03b_netclasses.py after it."""
from pcblib import *
from kipy.board_types import Zone
from kipy.geometry import PolygonWithHoles, PolyLine, PolyLineNode
from kipy.proto.board import board_types_pb2 as bt

k, b, doc = open_board()
N = lambda v: int(round(v * 1e6))

# ---- design rules: PCBWay standard process, see scratch/pcbway-notes.md
rules = b.get_design_rules().rules
c = rules.constraints
c.min_clearance = N(0.127)
c.min_track_width = N(0.127)
c.min_connection_width = N(0.127)
c.min_via_annular_width = N(0.15)
c.min_via_size = N(0.55)
c.min_through_drill = N(0.25)
c.copper_edge_clearance = N(0.3)
c.hole_clearance = N(0.25)
c.hole_to_hole_min = N(0.5)
c.min_silk_text_height = N(0.8)
c.min_silk_text_thickness = N(0.15)
rules.constraints = c
b.set_design_rules(rules)

# ---- zones
old = [z for z in b.get_zones() if z.name.startswith('GEN_')]
if old:
    b.remove_items(old)


def poly(x1, y1, x2, y2):
    pl = PolyLine()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        pl.append(PolyLineNode.from_point(mm(X0 + x, Y0 + y)))
    pl.closed = True
    p = PolygonWithHoles()
    p.outline = pl
    return p


nets = {n.name: n for n in b.get_nets()}
CU = [bt.BL_F_Cu, bt.BL_In1_Cu, bt.BL_In2_Cu, bt.BL_B_Cu]
# In1 is the solid ground plane, In2 the 3.3 V plane; the outer layers are flooded with ground
PLANE = {bt.BL_In2_Cu: '+3V3'}
zones = []
for layer in CU:
    z = Zone()
    net = PLANE.get(layer, 'GND')
    z.name = f'GEN_{net}_' + b.get_layer_name(layer)
    z.net, z.layers, z.priority = nets[net], [layer], 0
    z.outline = poly(-0.5, -0.5, W + 0.5, H + 0.5)
    z.clearance = N(0.2)
    z.min_thickness = N(0.2)
    z.island_mode = bt.IRM_ALWAYS
    cs = z.proto.copper_settings.connection
    cs.zone_connection = bt.ZCS_PTH_THERMAL
    cs.thermal_spokes.width.value_nm = N(0.4)
    cs.thermal_spokes.gap.value_nm = N(0.3)
    zones.append(z)


def keepout(name, layers, box, copper):
    z = Zone()
    z.type = bt.ZT_RULE_AREA
    z.name = name
    z.layers = layers
    z.outline = poly(*box)
    r = z.rule_area_settings
    r.keepout_tracks = r.keepout_vias = True
    r.keepout_copper = copper
    r.keepout_pads = r.keepout_footprints = False
    z.rule_area_settings = r
    zones.append(z)


# RM2 antenna: the last 5 mm of the board carries no copper on any layer
keepout('GEN_ANTENNA', CU, (W - KEEP, -1, W + 1, H + 1), True)
# microSD socket: no top-layer tracks or vias under the body (Hirose keep-out areas are inside it)
keepout('GEN_SD_BODY', [bt.BL_F_Cu], (50.9 - 6.2, 0.5, 50.9 + 6.2, 15.6), False)
b.create_items(zones)
b.save()
print('zones', len(zones))
