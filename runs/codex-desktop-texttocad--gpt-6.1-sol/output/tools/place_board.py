from copy import deepcopy
from pathlib import Path
import json
from cad import kicad_pcb
from kicode.board_types import BoardLayer, BoardSegment, BoardText, Zone
from kicode.geometry import Angle, Vector2
from kicode.util.units import from_mm

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'Atlas2350.kicad_pcb'
parts = {part['ref']: part for part in json.loads((ROOT / 'design.json').read_text())}
PLACEMENT = {
    'J2': (7, 14, 270), 'U4': (17, 19, 0), 'C28': (12.5, 19.5, 180),
    'C18': (12.5, 17, 0), 'C16': (17, 15, 90), 'C29': (15, 15, 90),
    'C30': (21, 20, 180), 'R8': (21, 23, 0), 'R9': (21, 25, 0),
    'R7': (21, 16, 0), 'R6': (17, 23.5, 0), 'R5': (15, 22, 90),
    'TP10': (12, 23, 0), 'TP1': (24, 20, 0), 'TP2': (24, 23, 0),
    'TP3': (24, 17, 0), 'TP4': (24, 26, 0),
    'U5': (17, 31, 180), 'L1': (22, 31, 90), 'C31': (18, 27, 90),
    'C17': (16, 27, 90), 'C32': (16, 35, 270), 'C33': (13, 35, 270),
    'R42': (13, 32.5, 0), 'R43': (13, 30.5, 0), 'R40': (20, 35, 90),
    'C42': (19.5, 33.5, 90), 'R39': (15, 38, 0),
    'F1': (11, 32, 0), 'R1': (10, 46, 0), 'R2': (10, 48, 0),
    'R3': (24.5, 41.2, 0), 'R4': (23, 40, 0), 'R16': (24.5, 45, 0),
    'R14': (16, 47, 0), 'C13': (35.4, 41.8, 0), 'R17': (36, 43, 0),
    'C38': (38, 46, 0), 'C39': (41, 41, 90), 'C12': (29.6, 36.8, 90),
    'C5': (31.4, 36.8, 90), 'C6': (27.2, 36.8, 90),
    'C25': (24.5, 38, 180), 'C7': (24.2, 39.2, 180), 'C9': (24.2, 37.3, 180),
    'FB1': (27.6, 33.8, 90), 'C10': (25.5, 36.8, 90), 'C37': (25.5, 34.8, 90),
    'R10': (35, 19, 90), 'R11': (37, 19, 90), 'C19': (39, 19, 90),
    'R12': (35, 22, 90), 'R13': (37, 22, 90), 'C20': (39, 22, 90),
    'R38': (40, 16, 0), 'C41': (42, 16, 0), 'U9': (36, 16, 0),
    'C40': (33, 16, 90), 'SW3': (68, 32, 0), 'SW4': (56, 32, 0),
    'R32': (71, 28, 0), 'D1': (75, 27, 0), 'C24': (75, 31, 90),
    'R33': (73, 33, 90), 'C36': (77, 31, 90),
    'R29': (64, 49, 0), 'R30': (66, 49, 0), 'R31': (73, 49.5, 0),
    'H3': (56, 70, 0), 'TP7': (45, 55, 0), 'C22': (53, 4, 0),
    'C34': (51.5, 1.8, 0), 'R20': (53, 8, 0), 'C21': (51, 8, 0),
    'R41': (21, 14, 0), 'C43': (33, 56, 90),
    'F1': (7, 28, 0), 'R42': (13, 31, 0), 'R43': (13, 29, 0),
    'C33': (12, 35, 270), 'C42': (17.5, 34, 0), 'R40': (20, 37, 0),
    'C26': (27, 29, 180), 'TP5': (25, 26, 0), 'TP7': (46, 55, 0),
    'C18': (14.5, 17, 0), 'C8': (24, 47, 90), 'C9': (24.2, 35.5, 180),
    'C25': (23, 37.5, 180), 'C7': (24.2, 38.9, 180), 'R4': (23, 41, 0),
    'R17': (36, 41.8, 90), 'C13': (35.4, 40.5, 0), 'C39': (42, 41, 90),
    'U5': (17, 31, 180), 'L1': (12.5, 31, 90), 'F1': (6.5, 25.5, 0),
    'C32': (16, 26.5, 90), 'C33': (19, 26.5, 90), 'C31': (17, 35, 270),
    'C17': (19.5, 33.5, 0), 'R42': (20.5, 29, 90), 'R43': (20.5, 27, 90),
    'C42': (20.5, 31.5, 0), 'R40': (21, 35.5, 0),
    'R3': (24.3, 41.6, 0), 'R4': (24.3, 40.4, 0), 'U8': (11.5, 40, 0),
    'C13': (35.4, 42, 0), 'R17': (36.7, 42.7, 90),
    'C8': (24.2, 42.8, 180), 'C9': (24.2, 44, 180),
    'TP5': (25, 24.5, 0), 'TP7': (44.3, 59, 0),
    'C18': (12.5, 21.5, 0), 'C26': (25.5, 30, 90),
    'R17': (35.6, 44, 0), 'TP5': (26, 21, 0), 'C26': (24.5, 30, 90),
    'R17': (37.2, 40, 0), 'C4': (34.7, 38.3, 0),
    'R42': (22, 29, 90), 'R43': (22, 27, 90), 'C42': (21, 31.5, 0),
    'C44': (54, 2, 270), 'C34': (51, 5.5, 0), 'C22': (54, 4.5, 180),
    'C32': (16, 26.1, 90), 'C33': (19, 26.1, 90), 'R9': (21, 21.8, 0),
    'R6': (19, 23, 0),
    'C30': (21, 20, 0),
}


def place(footprint, position):
    zones = [item for item in footprint.definition.items if isinstance(item, Zone)]
    outlines = [deepcopy(zone.proto.outline) for zone in zones]
    footprint.position = Vector2.from_xy_mm(*position[:2])
    footprint.orientation = Angle.from_degrees(position[2])
    for zone, outline in zip(zones, outlines):
        zone.proto.outline.CopyFrom(outline)


with kicad_pcb.edit(str(BOARD)) as board:
    result = board.import_netlist(str(ROOT / 'checks' / 'Atlas2350.net'))
    print(f'Netlist import: {result.error_count} errors, {result.warning_count} mechanical-pad warnings')
    rules = board.get_design_rules().rules
    for attribute, millimetres in {'min_clearance': 0.127, 'min_track_width': 0.15,
                                   'min_connection_width': 0.15, 'min_via_size': 0.6,
                                   'min_through_drill': 0.3, 'min_via_annular_width': 0.15,
                                   'copper_edge_clearance': 0.25, 'hole_to_hole_min': 0.25,
                                   'hole_clearance': 0.178, 'silk_clearance': 0.15}.items():
        setattr(rules.constraints, attribute, from_mm(millimetres))
    board.set_design_rules(rules)
    footprints = board.get_footprints()
    for footprint in footprints:
        ref = footprint.reference_field.text.value
        place(footprint, PLACEMENT.get(ref, parts[ref]['board']))
        if ref == 'U6':
            for pad in footprint.definition.pads:
                if pad.number == '19' and pad.padstack.drill.diameter.x:
                    pad.padstack.drill.diameter = Vector2.from_xy_mm(0.3, 0.3)
        footprint.reference_field.visible = False
        footprint.value_field.visible = False
    board.update_items(footprints)
    existing_edges = [item for item in board.get_shapes() if item.layer == BoardLayer.BL_Edge_Cuts]
    if not existing_edges:
        outline = [(2, 0), (78, 0), (80, 2), (80, 73), (78, 75), (2, 75), (0, 73), (0, 2)]
        shapes = []
        for start, end in zip(outline, outline[1:] + outline[:1]):
            segment = BoardSegment()
            segment.start = Vector2.from_xy_mm(*start)
            segment.end = Vector2.from_xy_mm(*end)
            segment.layer = BoardLayer.BL_Edge_Cuts
            segment.attributes.stroke.width = from_mm(0.05)
            shapes.append(segment)
        board.create_items(shapes)
    if not board.get_text():
        lettering = [('ATLAS2350  REV A', 27, 7, 1.5), ('RP2350 / Wi-Fi / BLE', 27, 10, 1.0),
                     ('USB-C', 11, 37, 1.0), ('BAT+ GND NTC', 12, 10, 1.0),
                     ('1S LiPo 4.2V ONLY', 14, 12, 1.0), ('Qwiic / QT', 71, 43, 1.0),
                     ('3V3 I2C', 72, 45, 1.0), ('RGB', 75, 23, 1.0),
                     ('RESET', 40, 59, 1.0), ('BOOTSEL', 40, 67, 1.0),
                     ('ESP UART0', 64, 21, 1.0), ('ESP RST', 57, 35, 1.0),
                     ('ESP BOOT', 64, 35, 1.0), ('SWD', 44, 25, 1.0),
                     ('GPIO / 3V3 ONLY', 49, 45, 1.0), ('microSD', 67, 46, 1.0),
                     ('PWR', 8, 59, 1.0)]
        texts = []
        for value, x, y, size in lettering:
            text = BoardText()
            text.value = value
            text.position = Vector2.from_xy_mm(x, y)
            text.layer = BoardLayer.BL_F_SilkS
            text.attributes.size = Vector2.from_xy_mm(size, size)
            text.attributes.stroke_width = from_mm(0.15)
            texts.append(text)
        board.create_items(texts)
    print(f'Placed {len(footprints)} footprints on 80x75mm board')
