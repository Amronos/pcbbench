import argparse
import os
from pathlib import Path

from kipy import KiCad
from kipy.board_types import BoardSegment, Zone
from kipy.geometry import Angle, PolygonWithHoles, PolyLine, PolyLineNode, Vector2
from kipy.kicad import DocumentType
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.schematic import schematic_types_pb2 as st
from kipy.schematic_types import (
    LocalLabel,
    NoConnectMarker,
    SchematicField,
    SchematicLine,
)

ROOT = Path(__file__).resolve().parent.parent
V = Vector2.from_xy_mm
parts = []
RFP = 'Resistor_SMD:R_0402_1005Metric'
CFP = 'Capacitor_SMD:C_0402_1005Metric'


def part(ref, lib, value, mpn, mfr, fp, nets, pos, rot=0, ds=''):
    parts.append({
        'ref': ref, 'lib': lib, 'value': value, 'mpn': mpn, 'mfr': mfr,
        'fp': fp, 'nets': {str(pin): net for pin, net in nets.items()},
        'pos': pos, 'rot': rot, 'ds': ds,
    })


def r(ref, value, a, b, pos, rot=0):
    code = {
        '27 Ω': '27R', '33 Ω': '33R', '1 kΩ': '1K', '10 kΩ': '10K',
        '100 kΩ': '100K', '4.7 kΩ': '4K7', '5.1 kΩ': '5K1',
        '2.94 kΩ': '2K94', '2.0 kΩ': '2K', '3.83 kΩ': '3K83',
        '46.4 kΩ': '46K4', '220 Ω': '220R', '330 Ω': '330R', '0 Ω': '0R', '2.2 kΩ': '2K2',
    }[value]
    part(ref, 'Device:R', value, 'RC0402FR-07' + code + 'L', 'Yageo',
         RFP, {1: a, 2: b}, pos, rot, 'https://www.yageo.com/en/Product/Index/rchip')


def c(ref, value, a, pos, rot=0):
    choices = {
        '100 nF': ('GRM155R71C104KA88D', CFP),
        '1 µF': ('GRM155R61A105KE15D', CFP),
        '10 µF': ('GRM21BR61A106KE19L', 'Capacitor_SMD:C_0805_2012Metric'),
        '22 µF': ('GRM21BR60J226ME39L', 'Capacitor_SMD:C_0805_2012Metric'),
        '15 pF': ('GRM1555C1H150JA01D', CFP),
        '4.7 µF': ('GRM188R61A475KE15D', 'Capacitor_SMD:C_0603_1608Metric'),
    }
    mpn, fp = choices[value]
    part(ref, 'Device:C', value, mpn, 'Murata', fp, {1: a, 2: 'GND'},
         pos, rot, 'https://www.murata.com/en-us/products/capacitor/mlcc')

def configure_libraries():
    libraries = Path(os.environ['SPROCKET_KICAD_LIBRARIES'])
    for kind, folder in [('SYMBOL', 'symbols'), ('FOOTPRINT', 'footprints'), ('3DMODEL', '3dmodels')]:
        os.environ[f'KICAD10_{kind}_DIR'] = str(libraries / folder)


def schematic():
    configure_libraries()
    path = str(ROOT / 'sprocket2350.kicad_sch')
    with KiCad(headless=True, timeout_ms=30000) as kicad:
        kicad.create_document(path, DocumentType.DOCTYPE_SCHEMATIC)
        kicad.get_schematic().save()
    with KiCad(headless=True, file_path=path, timeout_ms=30000) as kicad:
        kicad.load_all_libraries()
        kicad.wait_for_libraries()
        sheet = kicad.get_schematic()
        page = sheet.get_page_settings()
        page.page_size = 6
        sheet.set_page_settings(page)
        for i, record in enumerate(parts):
            if i < 8:
                x, y = 75 + (i % 4) * 180, 100 + (i // 4) * 145
            else:
                x, y = 35 + ((i - 8) % 12) * 65, 370 + ((i - 8) // 12) * 38
            x, y = round(x / 1.27) * 1.27, round(y / 1.27) * 1.27
            symbol = sheet.place_symbol_from_library(record['lib'], V(x, y), reference=record['ref'])
            pins = list(symbol.definition.pins)
            symbol.value = record['value']
            symbol.footprint_field.text.value = record['fp']
            symbol.datasheet_field.text.value = record['ds']
            fields = []
            for name, value in [('Manufacturer', record['mfr']), ('MPN', record['mpn'])]:
                field = SchematicField()
                field.name = name
                field.text.value = value
                field.visible = False
                fields.append(field)
            symbol.user_fields = fields
            for field, dy in [(symbol.reference_field, -4), (symbol.value_field, -1.5)]:
                if i >= 8:
                    field.text.position = V(x + 4, y + dy)
                field.text.attributes.angle = 0
                field.text.attributes.size = V(1, 1)
            symbol.proto.ClearField('definition')
            sheet.update_items(symbol)
            items = []
            seen = set()
            for pin in pins:
                px, py = x + pin.position.x / 1e6, y + pin.position.y / 1e6
                if (px, py) in seen:
                    continue
                seen.add((px, py))
                net = record['nets'].get(pin.number)
                if not net:
                    marker = NoConnectMarker()
                    marker.position = V(px, py)
                    items.append(marker)
                    continue
                dx, dy = {
                    st.SPO_RIGHT: (-5.08, 0), st.SPO_LEFT: (5.08, 0),
                    st.SPO_UP: (0, 5.08), st.SPO_DOWN: (0, -5.08),
                }[pin.orientation]
                wire = SchematicLine()
                wire.start = V(px, py)
                wire.end = V(px + dx, py + dy)
                wire.type = st.SLT_WIRE
                items.append(wire)
                label = LocalLabel()
                label.position = wire.end
                label.text.value = net
                label.text.attributes.size = V(1, 1)
                label.text.attributes.visible = True
                label.spin_style = st.SLSS_LEFT if dx <= 0 else st.SLSS_RIGHT
                items.append(label)
            sheet.create_items(items)
        for i, (net, xy) in enumerate([
            ('GND', (20.32, 20.32)), ('VBUS', (40.64, 20.32)),
            ('1V1', (60.96, 20.32)), ('VREG_AVDD', (81.28, 20.32)),
        ]):
            sheet.place_symbol_from_library('power:PWR_FLAG', V(*xy), reference=f'#FLG0{i + 1}')
            label = LocalLabel()
            label.position = V(*xy)
            label.text.value = net
            label.text.attributes.size = V(1, 1)
            label.spin_style = st.SLSS_LEFT
            sheet.create_items(label)
        sheet.save()


def board():
    configure_libraries()
    path = str(ROOT / 'sprocket2350.kicad_pcb')
    with KiCad(headless=True, timeout_ms=30000) as kicad:
        kicad.create_document(path, DocumentType.DOCTYPE_PCB)
        kicad.get_board().save()
    with KiCad(headless=True, file_path=path, timeout_ms=30000) as kicad:
        kicad.load_all_libraries()
        kicad.wait_for_libraries()
        pcb = kicad.get_board()
        result = pcb.import_netlist(str(ROOT / 'fab/sprocket2350.net'))
        print('Import', result.error_count, result.warning_count, result.new_footprint_count)
        copper_layers = [bt.BL_F_Cu, bt.BL_In1_Cu, bt.BL_In2_Cu, bt.BL_B_Cu]
        pcb.set_enabled_layers(4, [
            *copper_layers, bt.BL_F_Paste, bt.BL_B_Paste, bt.BL_F_Mask, bt.BL_B_Mask,
            bt.BL_F_SilkS, bt.BL_B_SilkS, bt.BL_F_Fab, bt.BL_B_Fab,
            bt.BL_F_CrtYd, bt.BL_B_CrtYd, bt.BL_Edge_Cuts,
        ])
        records = {record['ref']: record for record in parts}
        for footprint in pcb.get_footprints():
            record = records[footprint.reference_field.text.value]
            footprint.position = V(*record['pos'])
            footprint.orientation = Angle.from_degrees(record['rot'])
            footprint.reference_field.visible = False
            footprint.value_field.visible = False
            footprint.definition.items = [
                item for item in footprint.definition.items
                if getattr(item, 'layer', None) != bt.BL_F_SilkS
            ]
            pcb.update_items(footprint)
        for start, end in [
            ((100, 100), (185, 100)), ((185, 100), (185, 165)),
            ((185, 165), (100, 165)), ((100, 165), (100, 100)),
        ]:
            line = BoardSegment()
            line.start = V(*start)
            line.end = V(*end)
            line.layer = bt.BL_Edge_Cuts
            line.attributes.stroke.width = 50000
            pcb.create_items(line)
        rules = pcb.get_design_rules().rules
        for name, value in [
            ('min_clearance', 0.11), ('min_track_width', 0.11),
            ('min_via_annular_width', 0.1), ('min_via_size', 0.45),
            ('min_through_drill', 0.2), ('copper_edge_clearance', 0.3),
            ('hole_clearance', 0.2), ('hole_to_hole_min', 0.25),
        ]:
            setattr(rules.constraints, name, int(value * 1e6))
        pcb.set_design_rules(rules)
        nets = {net.name: net for net in pcb.get_nets()}
        outline = PolyLine()
        for x, y in [(100.3, 100.3), (184.7, 100.3), (184.7, 164.7), (100.3, 164.7)]:
            node = PolyLineNode()
            node.point = V(x, y)
            outline.append(node)
        outline.closed = True
        polygon = PolygonWithHoles()
        polygon.outline = outline
        for layer, net, priority in [
            *((layer, nets['/GND'], 0) for layer in copper_layers),
            (bt.BL_In2_Cu, nets['/3V3'], 1),
        ]:
            zone = Zone()
            zone.net = net
            zone.layers = [layer]
            zone.outline = polygon
            zone.priority = priority
            zone.clearance = 150000
            zone.min_thickness = 150000
            zone.island_mode = bt.IRM_ALWAYS
            zone.proto.copper_settings.connection.zone_connection = bt.ZCS_FULL
            pcb.create_items(zone)
        pcb.save()


if __name__ == '__main__':
    import sys

    parser = argparse.ArgumentParser(description='Generate the prototype schematic or PCB.')
    parser.add_argument('document', choices=['sch', 'pcb'])
    args = parser.parse_args()
    sys.modules['design'] = sys.modules[__name__]
    from circuits import define

    define()
    if args.document == 'sch':
        schematic()
    else:
        board()
