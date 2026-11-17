from pathlib import Path
import math
import sys
from cad import kicad_pcb
from kicode.board_types import BoardLayer, Track, Via, Zone, PadType, ZoneConnectionStyle, ViaDrillFillingMode, ViaDrillCappingMode
from kicode.geometry import Vector2, PolyLine, PolyLineNode, PolygonWithHoles
from kicode.util.units import from_mm

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'Atlas2350.kicad_pcb'


with kicad_pcb.edit(str(BOARD)) as board:
    if '--reset' in sys.argv:
        board.remove_items(list(board.get_tracks()) + list(board.get_vias()) +
                           [zone for zone in board.get_zones() if not zone.is_rule_area()])
    nets = {net.name: net for net in board.get_nets()}
    footprints = {footprint.reference_field.text.value: footprint for footprint in board.get_footprints()}
    pads = {(ref, pad.number): pad for ref, footprint in footprints.items()
            for pad in footprint.definition.pads if pad.number}
    existing_tracks = {(track.net.name, track.layer, track.start.x, track.start.y, track.end.x, track.end.y)
                       for track in board.get_tracks()}
    existing_vias = {(via.net.name, via.position.x, via.position.y) for via in board.get_vias()}
    items = []

    def at(ref, number):
        position = pads[ref, str(number)].position
        return position.x / 1e6, position.y / 1e6

    def tracks(net, points, width=0.15, layer=BoardLayer.BL_F_Cu):
        for start, end in zip(points, points[1:]):
            start_nm = tuple(round(value * 1e6) for value in start)
            end_nm = tuple(round(value * 1e6) for value in end)
            if start_nm == end_nm:
                continue
            key = (net, layer, *start_nm, *end_nm)
            if key in existing_tracks or (net, layer, *end_nm, *start_nm) in existing_tracks:
                continue
            track = Track()
            track.start = Vector2.from_xy(*start_nm)
            track.end = Vector2.from_xy(*end_nm)
            track.width = from_mm(width)
            track.layer = layer
            track.net = nets[net]
            items.append(track)
            existing_tracks.add(key)

    def via(net, position):
        key = (net, *(round(value * 1e6) for value in position))
        if key in existing_vias:
            return
        item = Via()
        item.position = Vector2.from_xy_mm(*position)
        item.diameter = from_mm(0.6)
        item.drill_diameter = from_mm(0.3)
        item.net = nets[net]
        item.padstack.drill.filled = ViaDrillFillingMode.VDFM_FILLED
        item.padstack.drill.capped = ViaDrillCappingMode.VDCM_CAPPED
        items.append(item)
        existing_vias.add(key)

    tracks('USB_D+', [at('J1', 'A6'), (7.1, 39.75), (7.25, 39.6), (8.2, 39.6),
                      (8.65, 40.05), (8.65, 40.9)])
    tracks('USB_D+', [at('J1', 'B6'), (7.1, 40.75), (7.25, 40.9), (8.65, 40.9)])
    tracks('USB_D+', [(8.65, 40.9), (8.65, 39.65), (9.25, 39.05), at('U8', '1')])
    tracks('USB_D+', [at('U8', '1'), (10.3625, 37.4), (12.4, 37.4),
                      (13.8, 38.8), (13.8, 41.6), at('R3', '1')])
    tracks('USB_D-', [at('J1', 'B7'), (7.25, 39.25), (7.6, 38.9), (7.8, 38.9)])
    tracks('USB_D-', [at('J1', 'A7'), (7.65, 40.25)])
    for position in [(7.8, 38.9), (7.65, 40.25), (9.2, 40.95), (14.6, 40.6)]:
        via('USB_D-', position)
    tracks('USB_D-', [(7.8, 38.9), (7.65, 39.05), (7.65, 40.25)], layer=BoardLayer.BL_B_Cu)
    tracks('USB_D-', [(7.65, 40.25), (8.5, 40.25), (9.2, 40.95)], layer=BoardLayer.BL_B_Cu)
    tracks('USB_D-', [(9.2, 40.95), (14.25, 40.95), (14.6, 40.6)], layer=BoardLayer.BL_B_Cu)
    tracks('USB_D-', [(9.2, 40.95), at('U8', '3')])
    tracks('USB_D-', [(14.6, 40.6), (14.6, 41.3), (22.89, 41.3), at('R4', '1')])
    tracks('USB_PHY_D+', [at('R3', '2'), at('U1', '52')])
    tracks('USB_PHY_D-', [at('R4', '2'), (25.3, 40.4), (26.1, 41.2), at('U1', '51')])

    tracks('XIN', [at('U1', '21'), (34.3, 42.8), (34.7, 43.2),
                   (36.8, 43.2), (37.45, 43.85), at('Y1', '1')])
    tracks('XIN', [at('Y1', '1'), (37.9, 44.6), (37.52, 44.98), at('C38', '1')])
    tracks('XOUT', [at('U1', '22'), (34.05, 42.4), (34.4, 42.05),
                    (34.4, 41.6), (36, 40), at('R17', '1')])
    tracks('XTAL_OUT', [at('R17', '2'), (37.95, 40), at('Y1', '3')])
    tracks('XTAL_OUT', [at('Y1', '3'), (41.33, 42.15), at('C39', '1')])

    tracks('BUCK_L1', [at('U5', '11'), (15.1, 31.5)], 0.3)
    tracks('BUCK_L1', [(15.1, 31.5), (13.185, 31.5), at('L1', '1')], 0.6)
    tracks('BUCK_L2', [at('U5', '9'), (15.1, 30.5)], 0.3)
    tracks('BUCK_L2', [(15.1, 30.5), (13.185, 30.5), at('L1', '2')], 0.6)
    tracks('VSYS', [at('U5', '12'), at('U5', '13'), (16.725, 33.05)], 0.3)
    cap_input = at('C31', '1')
    tracks('VSYS', [(16.725, 33.05), (16.725, cap_input[1] - 0.275), cap_input], 0.6)
    tracks('+3V3', [at('U5', '7'), at('U5', '8'), (16.225, 28.8)], 0.3)
    cap_output = at('C32', '1')
    tracks('+3V3', [(16.225, 28.8), (16.225, cap_output[1] + 0.225), cap_output], 0.6)
    tracks('+3V3', [cap_output, at('C33', '1')], 0.6)
    tracks('VSYS', [at('U4', '10'), at('U4', '11')], 0.3)
    tracks('VSYS', [at('U4', '10'), (19.25, 19.25)], 0.3)
    tracks('VSYS', [(19.25, 19.25), (20, 20), at('C30', '1')], 0.6)
    tracks('VBAT', [at('U4', '2'), at('U4', '3')], 0.3)

    for ref, footprint in footprints.items():
        if ref in {'U1', 'U4', 'U5'}:
            continue
        for pad in footprint.definition.pads:
            if pad.net.name == 'GND' and pad.pad_type == PadType.PT_SMD:
                via('GND', (pad.position.x / 1e6, pad.position.y / 1e6))
    for position in [(29.1, 41.1), (30.9, 41.1), (29.1, 42.9), (30.9, 42.9),
                     (27.5, 39.6), (27.5, 40.8), (17, 19), (17.4, 30.9)]:
        via('GND', position)
    tracks('GND', [at('U1', '47'), (27.5, 39.6)], 0.3)
    tracks('GND', [at('U1', '50'), (27.5, 40.8)], 0.3)
    tracks('GND', [at('U4', '4'), (16.05, 19.75), (16.3, 19.5)], 0.15)
    tracks('GND', [(16.3, 19.5), (17, 19.5), (17, 19)], 0.3)
    tracks('GND', [at('U4', '8'), (17.75, 19.9375), (17.25, 19.4375)], 0.15)
    tracks('GND', [(17.25, 19.4375), (17, 19.1875), (17, 19)], 0.3)
    tracks('GND', [at('U5', '4'), (17.4, 30.25), (17.4, 30.9)], 0.3)
    tracks('GND', [at('U5', '6'), (17.225, 30.725), (17.4, 30.9)], 0.3)
    tracks('GND', [at('U5', '15'), (17.725, 32.1), (17.5, 31.875),
                   (17.5, 31), (17.4, 30.9)], 0.15)
    for position in [(10, 3), (20, 3), (35, 3), (44, 3), (10, 8), (35, 12), (44, 12),
                     (2, 21), (28, 20), (2, 33), (19, 40), (20, 45), (16, 60),
                     (23, 66), (34, 69), (60, 44), (70, 44), (77, 47), (58, 46),
                     (77, 55), (60, 65), (72, 68), (66, 73), (30, 73), (45, 72),
                     (7, 72), (2, 60), (8, 38), (8.1, 42), (14.6, 39.5)]:
        via('GND', position)
    board.create_items(items)
    for layer in [BoardLayer.BL_In1_Cu, BoardLayer.BL_In2_Cu]:
        if not any(zone.net.name == 'GND' and layer in zone.layers for zone in board.get_zones() if not zone.is_rule_area()):
            zone = Zone()
            zone.name = 'Continuous GND reference plane'
            zone.layers = [layer]
            zone.net = nets['GND']
            zone.clearance = from_mm(0.127)
            zone.min_thickness = from_mm(0.15)
            zone.connection.zone_connection = ZoneConnectionStyle.ZCS_FULL
            outline = PolygonWithHoles()
            line = PolyLine()
            line.nodes.extend(PolyLineNode.from_point(Vector2.from_xy_mm(*position))
                              for position in [(2, 0), (78, 0), (80, 2), (80, 73), (78, 75), (2, 75), (0, 73), (0, 2)])
            outline.outline = line
            zone.outline = outline
            board.create_items(zone)
    board.refill_zones()
    print(f'Foundation: {len(items)} new copper items; inner GND planes refilled')
