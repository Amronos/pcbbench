import argparse
import os
from pathlib import Path

from kipy import KiCad
from kipy.board_types import BoardText
from kipy.geometry import Vector2, Vector3D
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType


def enable_teardrops(item):
    td = item.proto.teardrop
    td.mode = bt.PTM_ENABLED
    td.max_length.value_nm = 1000000
    td.max_width.value_nm = 2000000
    td.best_length_ratio = 0.5
    td.best_width_ratio = 1
    td.max_track_width_ratio = 0.9
    td.allow_multiple_track_segments = True


def finish_text(footprint):
    ref = footprint.reference_field.text.value
    footprint.reference_field.visible = False
    footprint.value_field.visible = False
    bottom = footprint.layer == bt.BL_B_Cu
    fab_layer = bt.BL_B_Fab if bottom else bt.BL_F_Fab
    footprint.reference_field.layer = fab_layer
    footprint.reference_field.text.attributes.mirrored = bottom
    value_layers = {bt.BL_F_Fab, bt.BL_B_Fab, bt.BL_F_SilkS, bt.BL_B_SilkS}
    # KiCad cannot hide free text, so remove duplicate value labels, not the value field.
    footprint.definition.items = [
        item for item in footprint.definition.items
        if not (isinstance(item, BoardText) and item.layer in value_layers
                and item.value in {'${VALUE}', footprint.value_field.text.value})
    ]
    for text in footprint.definition.texts:
        if not isinstance(text, BoardText) or text.value != '${REFERENCE}':
            continue
        text.layer = fab_layer
        text.attributes.mirrored = bottom
        text.position = Vector2.from_xy(footprint.position.x,
                                       footprint.position.y - (4000000 if ref == 'J4' else 0))
        if ref == 'U7':
            text.position = Vector2.from_xy(footprint.position.x, footprint.position.y + 4000000)
        if ref in {'J3', 'J6', 'J7'}:
            pads = [pad for pad in footprint.definition.pads if pad.number]
            if not pads:
                raise ValueError(f'{ref}: no numbered pads for reference placement')
            text.position = Vector2.from_xy(round(sum(pad.position.x for pad in pads) / len(pads)),
                                           round(sum(pad.position.y for pad in pads) / len(pads)))
        text.attributes.angle = 0
        size = 500000 if ref.startswith(('FID', 'TP', 'H')) else 700000
        if str(footprint.definition.id).endswith('C_0201_0603Metric'):
            size = 250000
        text.attributes.size = Vector2.from_xy(size, size)


def resolve_models(footprint, root, library):
    ref = footprint.reference_field.text.value
    for model in footprint.definition.models:
        relative = model.filename.removeprefix('${KIPRJMOD}/lib/3d/').split('}/', 1)[-1]
        local = root / 'lib/3d' / relative
        if not Path(relative).is_absolute() and local.is_file():
            model.filename = '${KIPRJMOD}/lib/3d/' + relative
            if ref == 'J2':
                model.rotation = Vector3D.from_xyz(270, 0, 0)
                model.offset = Vector3D.from_xyz(0, -3.2, 0)
            continue
        resolved = Path(os.path.expandvars(model.filename.replace('${KIPRJMOD}', str(root))))
        if not resolved.is_absolute():
            resolved = root / resolved
        if not resolved.is_file() and library is not None:
            resolved = library / relative
        if not resolved.is_file():
            raise ValueError(f'{ref}: missing 3D model {model.filename}')
        resolved = resolved.resolve()
        if library is not None and resolved.is_relative_to(library.resolve()):
            model.filename = '${KICAD10_3DMODEL_DIR}/' + resolved.relative_to(library.resolve()).as_posix()


def finish_board(board, root, library, teardrops=False):
    for footprint in board.get_footprints():
        finish_text(footprint)
        resolve_models(footprint, root, library)
        if teardrops:
            for pad in footprint.definition.pads:
                enable_teardrops(pad)
        board.update_items(footprint)
    for via in board.get_vias():
        via.proto.pad_stack.drill.capped = bt.VDCM_CAPPED
        via.proto.pad_stack.drill.filled = bt.VDFM_FILLED
        if teardrops:
            enable_teardrops(via)
        board.update_items(via)


def main():
    parser = argparse.ArgumentParser(description='Finish board labels, models, and filled/capped vias.')
    parser.add_argument('board', type=Path)
    parser.add_argument('--teardrops', action='store_true')
    args = parser.parse_args()
    path = args.board.resolve()
    libraries = os.environ.get('SPROCKET_KICAD_LIBRARIES')
    library = Path(libraries) / '3dmodels' if libraries else None
    with KiCad(headless=True, timeout_ms=120000) as k:
        k.open_document(str(path), DocumentType.DOCTYPE_PCB)
        board = k.get_board()
        finish_board(board, path.parent, library, args.teardrops)
        board.refill_zones(block=True, max_poll_seconds=120)
        board.save()


if __name__ == '__main__':
    main()
