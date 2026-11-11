from collections import defaultdict
from pathlib import Path

from kipy import KiCad
from kipy.geometry import Vector2
from kipy.proto.common.types import base_types_pb2 as ct, enums_pb2 as ce
from kipy.proto.schematic import schematic_types_pb2 as st

from design import parts


ROOT = Path(__file__).resolve().parent.parent


def point(x, y):
    return Vector2.from_xy_mm(round(x / 1.27) * 1.27, round(y / 1.27) * 1.27)


def key(position):
    return position.x, position.y


def grid(refs, x, y, columns, dx=85.09, dy=31.75):
    return {ref: point(x + i % columns * dx, y + i // columns * dy)
            for i, ref in enumerate(refs)}


def positions():
    groups = defaultdict(list)
    for part in parts:
        groups[part.block].append(part.ref)
    special = {
        'U1': point(150, 110), 'U2': point(400, 95), 'U3': point(530, 95),
        'U5': point(680, 95), 'U6': point(820, 95), 'U8': point(680, 175),
        'U7': point(1010, 105), 'J3': point(1100, 410),
        'J1': point(100, 550), 'U4': point(245, 550),
        'J6': point(400, 550), 'J7': point(540, 550),
        'J4': point(690, 550), 'J5': point(820, 550), 'D1': point(950, 550),
    }
    result = dict(special)
    specs = {
        'MCU': (55, 220, 3), 'Memory': (400, 180, 2),
        'Power': (650, 240, 3), 'Radio': (970, 220, 2),
        'USB': (65, 650, 2), 'Peripherals': (665, 660, 4),
        'Test': (385, 660, 3), 'Mechanical': (1040, 650, 2),
    }
    for group, spec in specs.items():
        refs = [ref for ref in groups[group] if ref not in special]
        result.update(grid(refs, *spec))
    return result


def net_members(schematic):
    return {net.name: frozenset(item.value for sheet in net.proto.sheets for item in sheet.items)
            for net in schematic.get_netlist()}


def main():
    targets = positions()
    with KiCad(headless=True, timeout_ms=120000) as kicad:
        kicad.open_document(str(ROOT / 'sprocket2350.kicad_sch'), ct.DocumentType.DOCTYPE_SCHEMATIC)
        schematic = kicad.get_schematic()
        before = net_members(schematic)
        lines = schematic.get_lines()
        labels = schematic.get_labels()
        markers = schematic.get_no_connects()
        symbols = schematic.get_symbols()
        attached = {}
        claimed = set()
        for symbol in symbols:
            if symbol.transform.orientation != st.SSO_0:
                raise ValueError(f'{symbol.reference}: rotated symbol needs explicit pin transform')
            pins = []
            for child in symbol.proto.definition.items:
                if child.item.Is(st.SchematicPin.DESCRIPTOR):
                    pin = st.SchematicPin()
                    child.item.Unpack(pin)
                    pins.append((symbol.position.x + pin.position.x_nm,
                                 symbol.position.y + pin.position.y_nm))
            wires = [wire for wire in lines if key(wire.start) in pins or key(wire.end) in pins]
            endpoints = set(pins) | {key(p) for wire in wires for p in (wire.start, wire.end)}
            local_labels = [label for label in labels if key(label.position) in endpoints]
            no_connects = [marker for marker in markers if key(marker.position) in pins]
            items = [*wires, *local_labels, *no_connects]
            ids = {str(item.id) for item in items}
            if claimed & ids:
                raise ValueError(f'{symbol.reference}: shared wiring needs an explicit layout')
            claimed.update(ids)
            attached[symbol.reference] = (wires, local_labels, no_connects, pins)
        expected = {str(item.id) for item in [*lines, *labels, *markers]}
        if claimed != expected:
            raise ValueError('Unattached wiring or labels would be left behind')

        flags = sorted(symbol.reference for symbol in symbols if symbol.reference.startswith('#FLG'))
        targets.update(grid(flags, 400, 360, 2, dy=25.4))
        updates = []
        for symbol in symbols:
            wires, local_labels, no_connects, pins = attached[symbol.reference]
            destination = targets[symbol.reference]
            dx, dy = destination.x - symbol.position.x, destination.y - symbol.position.y
            for wire in wires:
                wire.start = Vector2.from_xy(wire.start.x + dx, wire.start.y + dy)
                wire.end = Vector2.from_xy(wire.end.x + dx, wire.end.y + dy)
            for item in [*local_labels, *no_connects]:
                item.position = Vector2.from_xy(item.position.x + dx, item.position.y + dy)
            if symbol.reference.startswith(('R', 'C', 'L')) and len(pins) == 2:
                for label in local_labels:
                    label.spin_style = st.SLSS_RIGHT
            for field in [symbol.reference_field, symbol.value_field, symbol.footprint_field,
                          symbol.datasheet_field, symbol.description_field, *symbol.user_fields]:
                field.text.position = Vector2.from_xy(field.text.position.x + dx, field.text.position.y + dy)
            symbol.position = destination
            x, y = destination.x / 1e6, destination.y / 1e6
            if symbol.reference.startswith(('R', 'C', 'L')):
                field_x, field_y = x + 5.08, y - 2.54
            else:
                field_x = x - 7.62
                field_y = min((py + dy) / 1e6 for _, py in pins) - 22.86 if pins else y - 10.16
            for field, offset in [(symbol.reference_field, 0), (symbol.value_field, 2.54)]:
                field.text.position = point(field_x, field_y + offset)
                field.text.attributes.angle = 0
                field.text.attributes.horizontal_alignment = ce.HA_LEFT
                field.allow_auto_place = False
            symbol.proto.ClearField('definition')
            updates.extend([symbol, *wires, *local_labels, *no_connects])

        headings = {
            'RP2350A and core supply': (30, 30),
            '16 MB flash + 8 MB PSRAM': (350, 30),
            'USB/battery power and charging': (620, 30),
            'Wi-Fi and Bluetooth LE companion': (940, 30),
            'USB-C device port': (30, 490),
            'GPIO / SWD / test access': (350, 490),
            'Storage and sensor interfaces': (620, 490),
        }
        notes = {
            'Firmware:': (350, 280), 'USB default': (620, 450),
            'UART0': (940, 450), 'Qwiic:': (620, 790),
        }
        for text in schematic.get_text():
            location = headings.get(text.value)
            if location is None:
                location = next(position for prefix, position in notes.items() if text.value.startswith(prefix))
            text.position = point(*location)
            text.text.attributes.horizontal_alignment = ce.HA_LEFT
            updates.append(text)
        schematic.update_items(updates)
        after = net_members(schematic)
        if before != after:
            raise ValueError('Layout changed net membership; refusing to save')
        page = schematic.get_page_settings()
        page.page_size = ct.PS_A0
        schematic.set_page_settings(page)
        schematic.save()
        print(f'Moved {len(symbols)} symbols with their wiring; all {len(before)} net memberships preserved')


if __name__ == '__main__':
    main()
