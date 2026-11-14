import argparse
import hashlib
import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZipFile

from kipy import KiCad
from kipy.board_types import Field, Track, Via, Zone
from kipy.geometry import PolygonWithHoles
from kipy.proto.board import board_types_pb2 as bt
from shapely.affinity import rotate
from shapely.affinity import translate as move_shape
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

SOURCE_BOARD = 'RPI-RP2350A-MINIMAL_R4-S1_public/RPI-RP2350A-MINIMAL_R4-S1.kicad_pcb'
DEFAULT_ARCHIVE = Path('/tmp/rp-minimal.zip')
PARTS = {
    'L1': ('L2', 'Abracon_AOTA_B201610S_Reversed'),
    'C7': ('C5', 'C_0402_Reference_Wide'),
    'C6': ('C32', 'C_0402_Reference_Wide'),
    'C9': ('C31', 'C_0402_Reference'),
    'R3': ('R32', 'R_0402_Reference'),
}
NETS = {
    '/VREG_LX': '/CORE_LX',
    '/VREG_AVDD': '/VREG_AVDD',
    '+1V1': '/1V1',
    '+3V3': '/3V3',
    'GND': '/GND',
}
CAPACITOR_MPN = 'GRM155R60J475ME47D'
TAG = 'sprocket-reference-core'
LIBRARY = Path(__file__).resolve().parents[1] / 'lib/RP2350_Core.pretty'
CORE = box(100.15, 91.7, 104.65, 97.35)


def xy(point):
    return point.x / 1e6, point.y / 1e6


def connection_points(item):
    return [item.position] if isinstance(item, Via) else [item.start, item.end]


def copper_layers(item, board):
    if isinstance(item, Zone):
        return set(item.layers)
    if isinstance(item, Track):
        return {item.layer}
    return set(board.get_enabled_layers())


def zone_shape(zone):
    def points(line):
        if any(node.HasField('arc') for node in line.nodes):
            raise ValueError('Core zone contains an unsupported arc')
        return [(n.point.x_nm / 1e6, n.point.y_nm / 1e6) for n in line.nodes]

    polygons = []
    for polygon in zone.proto.outline.polygons:
        polygons.append(Polygon(points(polygon.outline), [points(h) for h in polygon.holes]))
    return unary_union(polygons)


def copper_shape(item):
    if isinstance(item, Via):
        return Point(xy(item.position)).buffer(item.diameter / 2e6)
    if isinstance(item, Track):
        return LineString([xy(item.start), xy(item.end)]).buffer(item.width / 2e6)
    return zone_shape(item)


def tagged(item):
    return any(p.key == TAG for p in item.proto.custom_properties)


def translate(item, delta):
    if isinstance(item, Via):
        item.position += delta
    elif isinstance(item, Track):
        item.start += delta
        item.end += delta
    else:
        for polygon in item.proto.outline.polygons:
            PolygonWithHoles(proto_ref=polygon).move(delta)
        item.proto.ClearField('filled_polygons')
        item.proto.filled = False


def source_core(archive, directory):
    with ZipFile(archive) as zipped:
        data = zipped.read(SOURCE_BOARD)
    source = directory / 'official.kicad_pcb'
    source.write_bytes(data)
    with KiCad(headless=True, file_path=str(source), timeout_ms=60000) as kicad:
        board = kicad.get_board()
        footprints = {f.reference_field.text.value: f for f in board.get_footprints()}
        copper = []
        for item in [*board.get_tracks(), *board.get_vias(), *board.get_zones()]:
            name = item.net.name if item.net else ''
            if name not in NETS and not (isinstance(item, Zone) and item.is_rule_area()):
                continue
            if isinstance(item, Zone):
                selected = CORE.covers(zone_shape(item))
            else:
                selected = all(CORE.covers(Point(xy(p))) for p in connection_points(item))
                if isinstance(item, Track):
                    selected &= item.layer == bt.BL_F_Cu
            if selected:
                copper.append(deepcopy(item))
        return footprints, copper, hashlib.sha256(data).hexdigest()


def library_footprints(directory):
    files = sorted({name for _, name in PARTS.values()})
    text = '(kicad_pcb (version 20261031) (generator pcbnew) (generator_version "10.99")\n'
    text += '(layers (0 "F.Cu" signal) (2 "B.Cu" signal))\n'
    for name in files:
        footprint = (LIBRARY / f'{name}.kicad_mod').read_text()
        text += footprint.replace(f'(footprint "{name}"', f'(footprint "RP2350_Core:{name}"', 1)
    text += ')\n'
    path = directory / 'library.kicad_pcb'
    path.write_text(text)
    with KiCad(headless=True, file_path=str(path), timeout_ms=60000) as kicad:
        return {f.definition.id.name: deepcopy(f) for f in kicad.get_board().get_footprints()}


def revise(path, archive=DEFAULT_ARCHIVE):
    path = path.resolve()
    if path == Path(__file__).resolve().parents[1] / 'sprocket2350.kicad_pcb':
        raise ValueError('Make a scratch copy first; the root board is not an output')
    if path.name == 'main-signal.kicad_pcb':
        raise ValueError('Do not edit the active routing board')
    version = re.search(r'\(generator_version "([^"]+)"\)', path.read_text())
    if not version or not version.group(1).startswith('10.99'):
        raise ValueError('Target must already be converted to KiCad 10.99 before saving')
    with TemporaryDirectory(prefix='rp2350-core-') as temporary:
        directory = Path(temporary)
        source, copper, digest = source_core(archive, directory)
        libraries = library_footprints(directory)
        with KiCad(headless=True, file_path=str(path), timeout_ms=60000) as kicad:
            board = kicad.get_board()
            target = {f.reference_field.text.value: f for f in board.get_footprints()}
            required = {'U1', *(ref for ref, _ in PARTS.values())}
            if missing := required - target.keys():
                raise ValueError(f'Missing footprints: {sorted(missing)}')
            if target['U1'].orientation.degrees != source['U1'].orientation.degrees:
                raise ValueError('U1 orientation must match the official reference')
            delta = target['U1'].position - source['U1'].position
            nets = {n.name: n for n in board.get_nets()}
            if missing := set(NETS.values()) - nets.keys():
                raise ValueError(f'Missing nets: {sorted(missing)}')
            u1_pads = {
                p.number: p for p in board.get_pads()
                if p.parent.value == target['U1'].id.value
            }
            for number in ('46', '47', '48', '49', '50'):
                official = next(p for p in source['U1'].definition.pads if p.number == number)
                pad = u1_pads[number]
                if (
                    pad.position != official.position + delta
                    or pad.net.name != NETS[official.net.name]
                ):
                    raise ValueError(f'U1 pin {number} does not match reference coordinates/net')
            old_pads = [deepcopy(p) for ref, _ in PARTS.values() for p in target[ref].definition.pads]
            replacements = []
            for source_ref, (ref, library_name) in PARTS.items():
                existing = target[ref]
                new = deepcopy(libraries[library_name])
                new.orientation = source[source_ref].orientation
                new.position = source[source_ref].position + delta
                expected = {p.number: p.net for p in existing.definition.pads if p.number}
                official_pads = {p.number: p for p in source[source_ref].definition.pads}
                for pad in new.definition.pads:
                    original_number = {'1': '2', '2': '1'}[pad.number] if ref == 'L2' else pad.number
                    original = official_pads[original_number]
                    if expected[pad.number].name != NETS[original.net.name]:
                        raise ValueError(f'{ref} pad {pad.number} net conflicts with schematic')
                    if (
                        pad.position != original.position + delta
                        or pad.padstack.proto.copper_layers != original.padstack.proto.copper_layers
                    ):
                        raise ValueError(f'{ref} pad {pad.number} library differs from official copper')
                    pad.net = expected[pad.number]
                existing.orientation = new.orientation
                existing.position = new.position
                fields = [deepcopy(i) for i in existing.definition.items if isinstance(i, Field)]
                existing.proto.definition.CopyFrom(new.proto.definition)
                existing.definition.items = deepcopy(new.definition.items)
                for item in existing.definition.items:
                    if isinstance(item, Field):
                        item.proto.text.id.value = str(uuid4())
                    elif hasattr(item, 'id') and 'value' in item.proto.id.DESCRIPTOR.fields_by_name:
                        item.proto.id.value = str(uuid4())
                    if hasattr(item, 'parent'):
                        item.proto.parent.value = existing.id.value
                for field in fields:
                    existing.definition.add_item(field)
                for field in existing.texts_and_fields:
                    if hasattr(field, 'name') and field.name == 'MPN' and ref.startswith('C'):
                        field.text.value = CAPACITOR_MPN
                replacements.append(existing)
            for item in copper:
                item.proto.ClearField('id')
                item.proto.ClearField('parent')
                if not (isinstance(item, Zone) and item.is_rule_area()):
                    item.net = nets[NETS[item.net.name]]
                translate(item, delta)
                item.proto.custom_properties.add(key=TAG, value='official')

            scope = move_shape(CORE, xoff=delta.x / 1e6, yoff=delta.y / 1e6)
            occupied = [
                (item.net.name, copper_layers(item, board), copper_shape(item))
                for item in copper
                if not (isinstance(item, Zone) and item.is_rule_area())
            ]
            for footprint in replacements:
                for pad in footprint.definition.pads:
                    layer = pad.padstack.proto.copper_layers[0]
                    shape = box(
                        -layer.size.x_nm / 2e6, -layer.size.y_nm / 2e6,
                        layer.size.x_nm / 2e6, layer.size.y_nm / 2e6,
                    )
                    shape = rotate(shape, -pad.padstack.angle.degrees, origin=(0, 0))
                    occupied.append((pad.net.name, {bt.BL_F_Cu}, move_shape(shape, *xy(pad.position))))
            remove = []
            conflicts = []
            switch_zone = next(z for z in copper if isinstance(z, Zone) and z.net.name == '/CORE_LX')
            switch_shape = copper_shape(switch_zone)
            for item in [*board.get_tracks(), *board.get_vias(), *board.get_zones()]:
                shape = copper_shape(item)
                if tagged(item):
                    remove.append(item)
                    continue
                name = item.net.name if item.net else ''
                local = scope.intersects(shape)
                own_net = name in {'/CORE_LX', '/VREG_AVDD'}
                moved_connection = isinstance(item, (Track, Via)) and any(
                    name == pad.net.name
                    and any(
                        Point(xy(p)).distance(Point(xy(pad.position))) < 0.001
                        for p in connection_points(item)
                    )
                    for pad in old_pads
                )
                local_shared = local and name in {'/1V1', '/GND', '/3V3'} and (
                    not isinstance(item, Zone) or scope.covers(shape))
                layers = copper_layers(item, board)
                collision = local and isinstance(item, (Track, Via)) and any(
                    net != name
                    and layers & used_layers
                    and shape.distance(used_shape) < 0.15 - 1e-6
                    for net, used_layers, used_shape in occupied
                )
                if local and isinstance(item, (Track, Via)):
                    collision |= shape.intersects(switch_shape)
                if own_net or moved_connection or local_shared or collision:
                    remove.append(item)
                    if collision and not (own_net or moved_connection or local_shared):
                        conflicts.append({'id': item.id.value, 'net': item.net.name})

            keepout = Zone()
            keepout.type = bt.ZT_RULE_AREA
            keepout.layers = [
                layer for layer in board.get_enabled_layers()
                if bt.BL_F_Cu <= layer <= bt.BL_B_Cu
            ]
            keepout.proto.outline.CopyFrom(switch_zone.proto.outline)
            keepout.proto.rule_area_settings.keepout_tracks = True
            keepout.proto.rule_area_settings.keepout_vias = True
            keepout.name = 'RP2350 LX, no crossing tracks or vias'
            keepout.proto.custom_properties.add(key=TAG, value='switch keepout')
            copper.append(keepout)
            board.remove_items(remove)
            board.remove_items([target[ref] for ref, _ in PARTS.values()])
            placed = board.create_items(replacements)
            if len(placed) != len(replacements):
                raise RuntimeError('KiCad did not replace all core footprints')
            created = board.create_items(copper)
            if len(created) != len(copper):
                raise RuntimeError('KiCad did not create all reference copper items')
            board.refill_zones(max_poll_seconds=120)
            board.save()
            return {
                'board': str(path), 'source': SOURCE_BOARD, 'source_sha256': digest,
                'translation_mm': xy(delta),
                'placements': {
                    f.reference_field.text.value: [*xy(f.position), f.orientation.degrees]
                    for f in replacements
                },
                'created': dict(Counter(type(i).__name__ for i in copper)),
                'removed': dict(Counter(type(i).__name__ for i in remove)),
                'scoped_signal_conflicts': conflicts,
                'capacitor_mpn': CAPACITOR_MPN,
            }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Copy the official RP2350 regulator core into a scratch board.')
    parser.add_argument('board', type=Path)
    parser.add_argument('--archive', type=Path, default=DEFAULT_ARCHIVE)
    args = parser.parse_args()
    print(json.dumps(revise(args.board, args.archive), indent=2))
