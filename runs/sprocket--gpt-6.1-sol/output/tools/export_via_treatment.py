import argparse
import csv
import math
from dataclasses import dataclass
from html import escape
from pathlib import Path

from kipy import KiCad
from kipy.board_types import BoardSegment, to_concrete_board_shape
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType
from shapely.geometry import LineString, Point, Polygon


ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / 'sprocket2350.kicad_pcb'
TREATMENT = 'IPC4761 Type VII; resin filled; copper capped; planar'
OUTER_LAYERS = (bt.BL_F_Cu, bt.BL_B_Cu)
COLUMNS = ('id', 'uuid', 'type', 'reference', 'pad', 'exposed_smd_pads', 'net',
           'x_mm', 'y_mm', 'drill_x_mm', 'drill_y_mm', 'rotation_deg',
           'diameter_mm', 'start_layer', 'end_layer', 'saved_capping', 'saved_filling', 'treatment')


def xy(point):
    return point.x / 1e6, point.y / 1e6


def pair(point):
    return f'{point[0]:.9f},{point[1]:.9f}'


def ring_points(ring):
    points = []
    for node in ring.nodes:
        if not node.has_point:
            raise ValueError('Pad containment requires tessellated API polygons; '
                             'encountered an arc or unknown polygon node')
        points.append(xy(node.point))
    return points


def copper_polygon(shape):
    if shape is None:
        raise ValueError('KiCad returned no polygon for an exposed SMD copper pad')
    polygon = Polygon(ring_points(shape.outline),
                      [ring_points(hole) for hole in shape.holes])
    if polygon.is_empty or not polygon.is_valid:
        raise ValueError('KiCad returned an empty or invalid pad copper polygon')
    return polygon


@dataclass(frozen=True)
class Drill:
    x: float
    y: float
    width: float
    height: float
    angle: float

    def centerline(self):
        radius = min(self.width, self.height) / 2
        dx, dy = self.width / 2 - radius, self.height / 2 - radius
        radians = math.radians(self.angle)
        dx, dy = (dx * math.cos(radians) + dy * math.sin(radians),
                  dy * math.cos(radians) - dx * math.sin(radians))
        if dx == dy == 0:
            return Point(self.x, self.y)
        return LineString([(self.x - dx, self.y - dy),
                           (self.x + dx, self.y + dy)])

    def within(self, copper):
        # A circle or round-ended slot is a centerline swept by its drill radius.
        # Distance tests avoid a polygon approximation that can miss slot/circle edges.
        line = self.centerline()
        return (copper.covers(line)
                and line.distance(copper.boundary) >= min(self.width, self.height) / 2)

    def svg(self):
        line = self.centerline()
        radius = min(self.width, self.height) / 2
        if isinstance(line, Point):
            return f'<circle cx="{self.x:.9f}" cy="{self.y:.9f}" r="{radius:.9f}"/>'
        start, end = line.coords
        return (f'<path d="M {pair(start)} L {pair(end)}" fill="none" '
                f'stroke-width="{2 * radius:.9f}" stroke-linecap="round"/>')


def pad_drill(pad):
    drill = pad.padstack.drill
    width, height = xy(drill.diameter)
    if width <= 0 or height <= 0:
        raise ValueError(f'PTH pad {pad.id.value} has no positive drill dimensions')
    if drill.shape == bt.DS_CIRCLE:
        if width != height:
            raise ValueError(f'Circular drill {pad.id.value} has unequal dimensions')
    elif drill.shape != bt.DS_OBLONG:
        raise ValueError(f'Unsupported drill shape on pad {pad.id.value}: {drill.shape}')
    # The installed API returns board coordinates despite Pad.position's docstring.
    x, y = xy(pad.position)
    return Drill(x, y, width, height, pad.padstack.angle.degrees)


def outline_svg(shape):
    if isinstance(shape, BoardSegment):
        return f'<path d="M {pair(xy(shape.start))} L {pair(xy(shape.end))}"/>'
    raise ValueError(f'Unsupported Edge.Cuts geometry: {type(shape).__name__}')


def collect(board):
    rows, drills, seen = [], [], set()

    def add(item, kind, drill, reference='', matches=()):
        uuid = item.id.value
        if not uuid or uuid in seen:
            raise ValueError(f'Missing or duplicate drilled item UUID: {uuid!r}')
        seen.add(uuid)
        span = item.padstack.drill
        row = dict.fromkeys(COLUMNS, '')
        row.update(uuid=uuid, type=kind, reference=reference,
                   pad=getattr(item, 'number', ''), exposed_smd_pads='; '.join(matches),
                   net=item.net.name, x_mm=f'{drill.x:.6f}', y_mm=f'{drill.y:.6f}',
                   drill_x_mm=f'{drill.width:.6f}', drill_y_mm=f'{drill.height:.6f}',
                   rotation_deg=f'{drill.angle % 360:.6f}',
                   start_layer=bt.BoardLayer.Name(span.start_layer),
                   end_layer=bt.BoardLayer.Name(span.end_layer), treatment=TREATMENT)
        if kind == 'via':
            row['diameter_mm'] = f'{item.diameter / 1e6:.6f}'
        row['saved_capping'] = bt.ViaDrillCappingMode.Name(span.capped)
        row['saved_filling'] = bt.ViaDrillFillingMode.Name(span.filled)
        rows.append(row)
        drills.append(drill)

    for via in sorted(board.get_vias(), key=lambda item: item.id.value):
        diameter = via.drill_diameter / 1e6
        if diameter <= 0:
            raise ValueError(f'Via {via.id.value} has no positive drill diameter')
        x, y = xy(via.position)
        add(via, 'via', Drill(x, y, diameter, diameter, 0))

    footprints = sorted(board.get_footprints(), key=lambda fp: fp.reference_field.text.value)
    for fp in footprints:
        pads = list(fp.definition.pads)
        plated = [pad for pad in pads if pad.pad_type == bt.PT_PTH]
        if not plated:
            continue
        copper = []
        for layer in OUTER_LAYERS:
            mask = bt.BL_F_Mask if layer == bt.BL_F_Cu else bt.BL_B_Mask
            exposed = [pad for pad in pads if pad.pad_type == bt.PT_SMD
                       and layer in pad.padstack.layers and mask in pad.padstack.layers
                       and not pad.padstack.is_masked(layer)]
            if exposed:
                polygons = board.get_pad_shapes_as_polygons(exposed, layer)
                if len(polygons) != len(exposed):
                    raise ValueError('KiCad returned an incomplete pad polygon response')
                copper.extend((pad, layer, copper_polygon(shape))
                              for pad, shape in zip(exposed, polygons))
        for pad in sorted(plated, key=lambda item: item.id.value):
            drill = pad_drill(pad)
            matches = sorted({f'{smd.number}@{bt.BoardLayer.Name(layer)[3:].replace("_", ".")}'
                              for smd, layer, polygon in copper
                              if smd.number == pad.number and layer in pad.padstack.layers
                              and drill.within(polygon)})
            if pad.fab_property == bt.PFP_HEATSINK or matches:
                add(pad, 'plated thermal hole', drill, fp.reference_field.text.value, matches)

    raw_shapes = list(board.get_shapes())
    raw_shapes.extend(shape for fp in footprints for shape in fp.definition.shapes)
    edges = {}
    for raw in raw_shapes:
        if raw.layer != bt.BL_Edge_Cuts:
            continue
        shape = to_concrete_board_shape(raw)
        if shape is None:
            raise ValueError(f'Unsupported Edge.Cuts geometry on {raw.id.value}')
        edges[raw.id.value] = shape
    if not edges:
        raise ValueError('Board has no Edge.Cuts geometry')
    outline = [outline_svg(shape) for shape in edges.values()]
    bounds = [shape.bounding_box() for shape in edges.values()]
    for index, row in enumerate(rows, 1):
        row['id'] = f'H{index:04d}'
    return rows, drills, outline, bounds


def render_svg(rows, drills, outline, bounds):
    points = [xy(box.pos) for box in bounds]
    points += [xy(box.pos + box.size) for box in bounds]
    points += [(drill.x - drill.width, drill.y - drill.height) for drill in drills]
    points += [(drill.x + drill.width, drill.y + drill.height) for drill in drills]
    left, top = min(x for x, _ in points) - 2, min(y for _, y in points) - 2
    right, bottom = max(x for x, _ in points) + 8, max(y for _, y in points) + 2
    legend_y = bottom + 2
    elements = [f'<svg xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="{left:.9f} {top:.9f} {right-left:.9f} {bottom-top+7:.9f}">',
                '<title>Via treatment map, absolute board coordinates in mm, +Y down</title>',
                '<g fill="none" stroke="#222" stroke-width="0.12">', *outline, '</g>']
    for row, drill in zip(rows, drills):
        color = '#1769aa' if row['type'] == 'via' else '#b34b00'
        title = escape('; '.join(f'{key}={value}' for key, value in row.items() if value))
        elements.extend([f'<g fill="{color}" stroke="{color}" stroke-width="0.04">',
                         f'<title>{title}</title>', drill.svg(), '</g>',
                         f'<text x="{drill.x + max(drill.width, drill.height)/2 + 0.15:.9f}" '
                         f'y="{drill.y:.9f}" font-size="0.55" fill="{color}">'
                         f'{escape(row["id"])}</text>'])
    for offset, text in enumerate((TREATMENT + ' required for every listed hole.',
                                   'Blue: actual vias. Orange: footprint plated thermal holes.',
                                   'IDs match via_treatment.csv. mm, +Y down. Not release approval.')):
        elements.append(f'<text x="{left:.9f}" y="{legend_y + offset * 1.4:.9f}" '
                        f'font-size="0.8">{escape(text)}</text>')
    return '\n'.join([*elements, '</svg>', ''])


def export(board, output):
    rows, drills, outline, bounds = collect(board)
    svg = render_svg(rows, drills, outline, bounds)
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'via_treatment.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    (output / 'via_treatment.svg').write_text(svg, encoding='utf-8')
    return rows


def main():
    parser = argparse.ArgumentParser(
        description='Read sprocket2350.kicad_pcb with kipy and export via_treatment.csv '
                    'and an annotated Edge.Cuts SVG. All vias and marked or contained footprint '
                    'thermal holes require IPC4761 Type VII. Does not save CAD or run DRC.')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--board', type=Path, default=BOARD, help='PCB snapshot to inspect read-only.')
    args = parser.parse_args()
    with KiCad(headless=True, timeout_ms=120000) as kicad:
        kicad.open_document(str(args.board.resolve()), DocumentType.DOCTYPE_PCB)
        rows = export(kicad.get_board(), args.output)
    vias = sum(row['type'] == 'via' for row in rows)
    print(f'{vias} vias, {len(rows) - vias} plated thermal holes in {args.output}')


if __name__ == '__main__':
    main()
