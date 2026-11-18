import argparse
import os
from pathlib import Path

from kipy import KiCad
from kipy.board_types import BoardText
from kipy.geometry import Vector2
from kipy.proto.board import board_types_pb2 as bt

PLACEMENTS = [
    ("SPROCKET 2350", 119, 106),
    ("USB", 136, 109),
    ("LiPo + NTC", 108, 148),
    ("QWIIC 3V3", 122, 161),
    ("BOOT", 146, 147),
    ("RESET", 136, 147),
    ("ESP BOOT", 178, 135),
    ("ESP RESET", 178, 142),
]


def finalize(board_path):
    board_path = board_path.resolve(strict=True)
    model_directory = str(Path(os.environ["SPROCKET_KICAD_LIBRARIES"]) / "3dmodels")
    os.environ["KICAD10_3DMODEL_DIR"] = model_directory
    with KiCad(headless=True, file_path=str(board_path), timeout_ms=60000) as client:
        board = client.get_board()
        labels = {name for name, _, _ in PLACEMENTS}
        board.remove_items(
            [
                item
                for item in board.get_items()
                if isinstance(item, BoardText) and item.value in labels
            ]
        )
        for name, x, y in PLACEMENTS:
            text = BoardText()
            text.layer = bt.BL_F_SilkS
            text.position = Vector2.from_xy_mm(x, y)
            text.value = name
            text.attributes.size = Vector2.from_xy_mm(1, 1)
            text.attributes.stroke_width = 150000
            board.create_items(text)
        for footprint in board.get_footprints():
            for model in footprint.definition.models:
                filename = model.proto.filename.replace(
                    "${KICAD10_3DMODEL_DIR}", model_directory
                ).replace("${KIPRJMOD}", str(board_path.parent))
                if not Path(filename).exists():
                    print(
                        "MISSING MODEL", footprint.reference_field.text.value, filename
                    )
        board.refill_zones(block=True, max_poll_seconds=120)
        board.save()


def main():
    parser = argparse.ArgumentParser(
        description="Place silkscreen labels, check 3D models, and refill zones."
    )
    parser.add_argument("board", type=Path)
    args = parser.parse_args()
    finalize(args.board)


if __name__ == "__main__":
    main()
