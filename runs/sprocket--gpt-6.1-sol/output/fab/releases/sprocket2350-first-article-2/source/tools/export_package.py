import argparse
import csv
import re
import runpy
from collections import defaultdict
from pathlib import Path

from kipy import KiCad
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType

ROOT = Path(__file__).resolve().parent.parent
BOARD = ROOT / 'sprocket2350.kicad_pcb'
STATUSES = ('UNRELEASED', 'FIRST_ARTICLE')
MOUNTING = {bt.FMS_SMD: 'SMT', bt.FMS_THROUGH_HOLE: 'Through-hole'}


def reference_order(ref):
    return tuple(int(piece) if piece.isdigit() else piece
                 for piece in re.split(r'(\d+)', ref))


def read_components(board=BOARD, status=STATUSES[0]):
    board = Path(board).resolve()
    parts = runpy.run_path(str(board.parent / 'tools/design.py'))['parts']
    expected = {part.ref: part for part in parts}
    if len(expected) != len(parts):
        raise ValueError('Duplicate references in tools/design.py')
    with KiCad(headless=True, timeout_ms=120000) as kicad:
        kicad.open_document(str(board), DocumentType.DOCTYPE_PCB)
        footprints = kicad.get_board().get_footprints()
        actual = {fp.reference_field.text.value: fp for fp in footprints}
        if len(actual) != len(footprints) or actual.keys() != expected.keys():
            raise ValueError(
                f'PCB references differ from tools/design.py: '
                f'missing={sorted(expected.keys() - actual.keys())}, '
                f'extra={sorted(actual.keys() - expected.keys())}; '
                f'check for duplicate PCB references')

        components = []
        for ref in sorted(expected, key=reference_order):
            part, fp = expected[ref], actual[ref]
            if part.manufacturer in {'PCB copper', 'PCB hole'}:
                continue
            fields = {field.name: field.text.value for field in fp.texts_and_fields
                      if hasattr(field, 'name')}
            metadata = {
                'Value': (fp.value_field.text.value, part.value),
                'Footprint': (str(fp.definition.id), part.footprint),
                'Manufacturer': (fields.get('Manufacturer'), part.manufacturer),
                'MPN': (fields.get('MPN'), part.mpn),
            }
            for name, (saved, defined) in metadata.items():
                if not defined or saved != defined:
                    raise ValueError(f'{ref} {name}: PCB={saved!r}, design={defined!r}')
            if (fp.attributes.do_not_populate
                    or fp.attributes.exclude_from_bill_of_materials):
                raise ValueError(f'{ref} is fitted in design.py but excluded on the PCB')
            if fp.layer not in {bt.BL_F_Cu, bt.BL_B_Cu}:
                raise ValueError(f'{ref} is not on a supported assembly side')
            if fp.attributes.mounting_style not in MOUNTING:
                raise ValueError(f'{ref} has no supported mounting style')
            components.append({
                'Reference': ref,
                'Value': part.value,
                'Footprint': part.footprint,
                'Manufacturer': part.manufacturer,
                'MPN': part.mpn,
                'Datasheet': part.datasheet,
                'Assembly': MOUNTING[fp.attributes.mounting_style],
                'Side': 'Top' if fp.layer == bt.BL_F_Cu else 'Bottom',
                'X_mm': f'{fp.position.x / 1e6:.6f}',
                'Y_mm': f'{fp.position.y / 1e6:.6f}',
                'Rotation_deg': f'{fp.orientation.degrees % 360:.6f}',
                'Status': status,
            })
    return components


def write_csv(path, columns, rows):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description='Export all fitted SMT and through-hole BOM/placement rows. '
                    'Coordinates are absolute KiCad footprint anchors in mm, +Y down; '
                    'bottom coordinates are not mirrored. Verify assembler rotations. '
                    'Does not save CAD or verify release.')
    parser.add_argument('--output', type=Path, default=ROOT / 'fab' / 'unreleased')
    parser.add_argument('--board', type=Path, default=BOARD,
                        help='PCB snapshot. Part definitions come from its sibling tools/design.py.')
    parser.add_argument('--status', choices=STATUSES, default=STATUSES[0],
                        help='CSV label only, not release approval. Default: UNRELEASED.')
    args = parser.parse_args()
    components = read_components(args.board, args.status)
    bom_columns = ['Value', 'Footprint', 'Manufacturer', 'MPN', 'Datasheet', 'Assembly']
    grouped = defaultdict(list)
    for component in components:
        grouped[tuple(component[column] for column in bom_columns)].append(component['Reference'])
    bom = [dict(zip(bom_columns, key), References=', '.join(refs),
                Quantity=len(refs), Status=args.status) for key, refs in grouped.items()]
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / 'BOM.csv', ['References', 'Quantity', *bom_columns, 'Status'], bom)
    placement_columns = ['Reference', 'Value', 'Footprint', 'MPN', 'Assembly', 'Side',
                         'X_mm', 'Y_mm', 'Rotation_deg', 'Status']
    write_csv(args.output / 'placement.csv', placement_columns,
              [{column: component[column] for column in placement_columns}
               for component in components])
    print(f'{args.status}: {len(components)} fitted parts, {len(bom)} BOM rows in {args.output}')


if __name__ == '__main__':
    main()
