import argparse
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Footprint3DModel
from kipy.geometry import Vector3D

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "U1": ("rpi_rp2350a.step", "QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm", (0, 0, 0), 0),
    "U4": ("RGT0016C.stp", "VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm", (0, 0, 0), 0),
    "U5": ("DRC0010J.stp", "Texas_DRC0010J", (0, 0, 0), 0),
    "J1": (
        "TYPE-C-31-M-12.3dshapes/USB-C_SMD-TYPE-C-31-M-12_1.step",
        "USB_C_Receptacle_HRO_TYPE-C-31-M-12",
        (0, -1.05, 0),
        180,
    ),
    "J3": (
        "S3B-PH-SM4-TB.3dshapes/CONN-SMD_PH2.00-WS-3P.step",
        "JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal",
        (2, -2.9, 0),
        0,
    ),
    "D2": (
        "WS2812C-2020-V6.3dshapes/LED-SMD_4P-L2.2-W2.0-P1.00_WS2815C-2020-4P.wrl",
        "LED_WS2812B-2020_PLCC4_2.0x2.0mm",
        (0, 0, 0),
        0,
    ),
}


def attach(board_path, references=tuple(MODELS)):
    board_path = board_path.resolve(strict=True)
    if board_path == ROOT / "sprocket2350.kicad_pcb":
        raise ValueError("The root board is protected. Pass a board copy.")
    unknown_refs = set(references) - MODELS.keys()
    if unknown_refs:
        raise ValueError(
            f"No selected visualization model for: {', '.join(sorted(unknown_refs))}"
        )
    for ref in references:
        (ROOT / "lib/3d" / MODELS[ref][0]).resolve(strict=True)

    with KiCad(headless=True, file_path=str(board_path), timeout_ms=60000) as client:
        board = client.get_board()
        footprints = {
            footprint.reference_field.text.value: footprint
            for footprint in board.get_footprints()
        }
        updates = []
        for ref in references:
            footprint = footprints[ref]
            filename, expected_footprint, offset_mm, rotation_z = MODELS[ref]
            if footprint.definition.id.name != expected_footprint:
                raise ValueError(f"{ref}: expected footprint {expected_footprint}")
            model = Footprint3DModel()
            model.filename = f"${{KIPRJMOD}}/lib/3d/{filename}"
            model.scale = Vector3D.from_xyz(1, 1, 1)
            model.offset = Vector3D.from_xyz(*offset_mm)
            model.rotation = Vector3D.from_xyz(0, 0, rotation_z)
            model.visible = True
            model.opacity = 1
            footprint.definition.items = [
                item
                for item in footprint.definition.items
                if not isinstance(item, Footprint3DModel)
            ] + [model]
            updates.append(footprint)
        board.update_items(updates)
        board.save()


def main():
    parser = argparse.ArgumentParser(
        description="Attach visualization-only 3D models to a board copy."
    )
    parser.add_argument("board", type=Path)
    parser.add_argument(
        "--refs", nargs="+", choices=sorted(MODELS), default=list(MODELS)
    )
    args = parser.parse_args()
    references = list(dict.fromkeys(args.refs))
    try:
        attach(args.board, references)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"{error}\n")
    print(
        f"Attached visualization-only models to {args.board}: {', '.join(references)}"
    )


if __name__ == "__main__":
    main()
