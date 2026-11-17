import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from kipy import KiCad
from kipy.common_types import HorizontalAlignment
from kipy.geometry import Vector2
from kipy.proto.common.types import base_types_pb2 as ct
from kipy.proto.schematic import schematic_types_pb2 as st
from kipy.schematic_types import SchematicText


ROOT = Path(__file__).resolve().parent.parent
V = Vector2.from_xy_mm
GRID = 1.27
PIN_STUBS = {
    st.SPO_RIGHT: (-2.54, 0, st.SLSS_LEFT),
    st.SPO_LEFT: (2.54, 0, st.SLSS_RIGHT),
    st.SPO_UP: (0, 2.54, st.SLSS_BOTTOM),
    st.SPO_DOWN: (0, -2.54, st.SLSS_UP),
}


def snap(x, y):
    return V(round(x / GRID) * GRID, round(y / GRID) * GRID)


def row(placements, refs, x, y, pitch=35):
    for i, ref in enumerate(refs.split()):
        placements[ref] = (x + i * pitch, y)


def placement():
    positions = {
        'U1': (90, 95), 'L2': (175, 55), 'R32': (210, 55),
        'Y1': (45, 180), 'R25': (85, 180), 'C3': (125, 180),
        'C4': (160, 180), 'R8': (195, 180), 'SW2': (235, 180),
        'U2': (315, 65), 'U3': (425, 65),
        'J1': (290, 185), 'D1': (375, 175), 'C34': (435, 185),
        'U4': (575, 65), 'J3': (690, 60),
        'C21': (735, 45), 'C22': (735, 85), 'C23': (735, 125),
        'U5': (575, 205), 'L1': (685, 195),
        'U6': (330, 340), 'SW3': (380, 400), 'SW4': (430, 400),
        'Q1': (565, 345), 'Q2': (625, 345),
        'J5': (65, 470), 'J4': (145, 460), 'J6': (220, 460),
        'D2': (200, 510), 'C33': (235, 510),
        'J2': (325, 475), 'C30': (295, 515),
    }
    row(positions, 'C5 C31 C32', 165, 90)
    row(positions, 'C6 C7 C8', 165, 120)
    row(positions, 'C9 C10 C11 C12 C13', 35, 230, 45)
    row(positions, 'C14 C15 C16 C17 C18', 35, 260, 45)
    row(positions, 'R5 C19 R6 C20', 285, 105, 50)
    row(positions, 'R7 SW1', 300, 130, 55)
    row(positions, 'R1 R2 R3 R4', 285, 235, 50)
    row(positions, 'R13 R14 R15 R16', 525, 110, 50)
    row(positions, 'R17 R18 R19 R20', 525, 140, 50)
    row(positions, 'C24 C25 C26 C27', 525, 250, 60)
    row(positions, 'R9 R10 R11 R12', 300, 290, 45)
    row(positions, 'C1 C28 C29', 405, 330, 40)
    row(positions, 'R33 R34', 405, 365, 40)
    row(positions, 'R35 R36 R23 R24 C2', 525, 400, 50)
    row(positions, 'R21 R22', 135, 505, 35)
    row(positions, 'R26 R27 R28', 390, 455, 40)
    row(positions, 'R29 R30 R31', 390, 490, 40)
    row(positions, '#FLG01 #FLG02 #FLG03 #FLG04', 540, 480, 60)
    return positions


HEADERS = [
    ('MCU / core', 25, 20), ('Core decoupling', 25, 205),
    ('QSPI flash / PSRAM', 275, 20), ('USB-C / protection', 275, 155),
    ('Charger / battery', 515, 20), ('3.3 V buck-boost', 515, 170),
    ('Radio', 275, 270), ('Battery sense', 515, 305),
    ('GPIO / I2C / SWD / RGB', 25, 430), ('microSD', 275, 430),
    ('Power flags', 515, 445),
]


def point(position):
    return position.x, position.y


def netlist(path, output):
    subprocess.run([
        'kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml',
        '-o', str(output), str(path),
    ], check=True, capture_output=True, text=True)
    root = ET.parse(output).getroot()
    for component in root.findall('components/comp'):
        for prop in component.findall('property'):
            if prop.attrib['name'] == 'Sheetfile':
                prop.attrib['value'] = Path(prop.attrib['value']).name
    components = {
        c.attrib['ref']: ET.tostring(c, encoding='unicode')
        for c in root.findall('components/comp')
    }
    nets = {
        net.attrib['name']: sorted(
            (n.attrib['ref'], n.attrib['pin']) for n in net.findall('node')
        ) for net in root.findall('nets/net')
    }
    return components, nets


def layout(source, output, render):
    source, output = source.resolve(), output.resolve()
    if source == output:
        raise ValueError('Use a separate output, then install the verified copy explicitly.')
    version = re.search(r'\(generator_version "([^"]+)"\)', source.read_text())
    installed = subprocess.check_output(['kicad-cli', 'version'], text=True).strip()
    if version and version.group(1) != '.'.join(installed.split('.')[:2]):
        raise ValueError(f'Format upgrade needs approval: {version.group(1)} -> {installed}')
    output.parent.mkdir(parents=True, exist_ok=True)
    before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    before = netlist(source, output.with_suffix('.before.xml'))
    positions = placement()
    with KiCad(headless=True, file_path=str(source), timeout_ms=30000) as kicad:
        sheet = kicad.get_schematic()
        if len(list(sheet.iter_sheets())) != 1:
            raise ValueError('This layout expects the existing flat schematic.')
        symbols = sheet.get_symbols()
        pin_nets = {
            (ref, pin): name for name, nodes in before[1].items()
            for ref, pin in nodes
        }
        radio_extras = [
            symbol for symbol in symbols
            if symbol.reference not in positions and any(
                pin_nets.get((symbol.reference, pin.number), '').rsplit('/', 1)[-1].startswith('RADIO_')
                for pin in symbol.definition.pins
            )
        ]
        if len(radio_extras) > 1:
            raise ValueError('Add positions for additional radio parts beyond the EN pulldown.')
        if radio_extras:
            positions[radio_extras[0].reference] = (465, 400)
        unknown = sorted(s.reference for s in symbols if s.reference not in positions)
        if unknown:
            raise ValueError(f'Add layout positions for new parts: {unknown}')
        ids = {s.reference: s.id.value for s in symbols}
        lines = sheet.get_lines()
        labels = sheet.get_labels()
        markers = sheet.get_no_connects()
        line_at = {}
        for line in lines:
            if line.type != st.SLT_WIRE:
                raise ValueError('Only pin-stub wiring is supported.')
            for endpoint in (line.start, line.end):
                line_at.setdefault(point(endpoint), []).append(line)
        label_at = {}
        for label in labels:
            label_at.setdefault(point(label.position), []).append(label)
        marker_at = {point(marker.position): marker for marker in markers}
        updates, moved = [], set()
        for symbol in symbols:
            old = symbol.position
            new = snap(*positions[symbol.reference])
            transform = symbol.transform
            if transform.orientation != st.SSO_0 or transform.mirror_x or transform.mirror_y:
                raise ValueError(f'Unexpected symbol transform: {symbol.reference}')
            delta = V((new.x - old.x) / 1e6, (new.y - old.y) / 1e6)
            pins = list(symbol.definition.pins)
            seen = set()
            for pin in pins:
                anchor = (old.x + pin.position.x, old.y + pin.position.y)
                if anchor in seen:
                    continue
                seen.add(anchor)
                new_anchor = V((anchor[0] + delta.x) / 1e6, (anchor[1] + delta.y) / 1e6)
                attached = line_at.get(anchor, [])
                if len(attached) > 1:
                    raise ValueError(f'Non-stub wiring at {symbol.reference}.{pin.number}')
                if attached:
                    line = attached[0]
                    end = line.end if point(line.start) == anchor else line.start
                    attached_labels = label_at.get(point(end), [])
                    if len(attached_labels) != 1:
                        raise ValueError(f'Expected one label at {symbol.reference}.{pin.number}')
                    label = attached_labels[0]
                    dx, dy, spin_style = PIN_STUBS[pin.orientation]
                    line.start = new_anchor
                    line.end = V(line.start.x / 1e6 + dx, line.start.y / 1e6 + dy)
                    label.position = line.end
                    label.text.attributes.size = V(1, 1)
                    label.spin_style = spin_style
                    updates.extend([line, label])
                    moved.update([line.id.value, label.id.value])
                elif anchor in label_at and symbol.reference.startswith('#'):
                    for label in label_at[anchor]:
                        label.position = new_anchor
                        updates.append(label)
                        moved.add(label.id.value)
                elif anchor in marker_at:
                    marker = marker_at[anchor]
                    marker.position = new_anchor
                    updates.append(marker)
                    moved.add(marker.id.value)
                else:
                    raise ValueError(f'Missing pin stub or NC: {symbol.reference}.{pin.number}')
            symbol.position = new
            for field in (
                symbol.reference_field, symbol.value_field, symbol.footprint_field,
                symbol.datasheet_field, symbol.description_field, *symbol.user_fields,
            ):
                field.text.position = V((field.text.position.x + delta.x) / 1e6,
                                        (field.text.position.y + delta.y) / 1e6)
            if symbol.reference.startswith('#'):
                symbol.reference_field.visible = False
                symbol.value_field.visible = False
            else:
                if symbol.reference.startswith(('R', 'C', 'L')):
                    top, right = 0, 0
                    offsets = (-1.5, 1.5)
                else:
                    top = min(pin.position.y for pin in pins) / 1e6
                    right = max(pin.position.x for pin in pins) / 1e6 if len(pins) > 4 else 0
                    offsets = (-7, -4.5)
                for field, dy in zip((symbol.reference_field, symbol.value_field), offsets):
                    field.text.position = V(new.x / 1e6 + right + 4, new.y / 1e6 + top + dy)
                    field.text.attributes.horizontal_alignment = HorizontalAlignment.HA_LEFT
                    field.text.attributes.angle = 0
                    field.text.attributes.size = V(1, 1)
            symbol.proto.ClearField('definition')
            updates.append(symbol)
        expected = {i.id.value for i in [*lines, *labels, *markers]}
        if moved != expected:
            raise ValueError('Unowned wiring or labels. Refusing a partial layout.')
        sheet.update_items(updates)
        header_names = {value for value, _, _ in HEADERS}
        previous_headers = [text for text in sheet.get_text() if text.value in header_names]
        if previous_headers:
            sheet.remove_items(previous_headers)
        headers = []
        for value, x, y in HEADERS:
            text = SchematicText()
            text.value = value
            text.position = snap(x, y)
            text.text.attributes.size = V(2, 2)
            text.text.attributes.bold = True
            text.text.attributes.horizontal_alignment = HorizontalAlignment.HA_LEFT
            headers.append(text)
        sheet.create_items(headers)
        page = sheet.get_page_settings()
        page.page_size = ct.PS_A1
        sheet.set_page_settings(page)
        sheet.save_as(str(output), overwrite=True, include_project=True)
    after = netlist(output, output.with_suffix('.after.xml'))
    if before != after:
        raise ValueError('Netlist or component data changed. Do not install this output.')
    with KiCad(headless=True, file_path=str(output), timeout_ms=30000) as kicad:
        after_ids = {s.reference: s.id.value for s in kicad.get_schematic().get_symbols()}
    if ids != after_ids:
        raise ValueError('Symbol UUIDs changed. Do not install this output.')
    if hashlib.sha256(source.read_bytes()).hexdigest() != before_hash:
        raise ValueError('Source changed during layout. Repeat against the new source.')
    report = {'symbols': len(ids), 'parts': sum(not r.startswith('#') for r in ids),
              'nets': len(after[1]), 'symbol_uuid_parity': True, 'netlist_parity': True,
              'source_unchanged': True, 'source_sha256': before_hash}
    print(json.dumps(report, indent=2))
    if render:
        subprocess.run(['kicad-cli', 'sch', 'export', 'png', '--dpi', '110',
                        '-o', str(output.parent / 'render'), str(output)], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT / 'sprocket2350.kicad_sch')
    parser.add_argument('--output', type=Path, default=ROOT / 'scratch/schematic-layout/sprocket2350.kicad_sch')
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    layout(args.source, args.output, args.render)
