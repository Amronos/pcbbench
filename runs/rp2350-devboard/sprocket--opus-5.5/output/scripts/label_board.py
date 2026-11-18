"""Write header pin names and the board name on B.Silkscreen, and the board's title block.
Re-running replaces every text on B.Silkscreen. Usage: kicad-python scripts/label_board.py [board]"""
import sys
from pathlib import Path

from kipy import KiCad
from kipy.board_types import BoardText
from kipy.common_types import TextAttributes
from kipy.geometry import Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types import base_types_pb2
from kipy.proto.common.types import enums_pb2

import placement as PL

BX, BY = 100.0, 50.0
NAME, REV = "RP2350 DEV BOARD", "A"
PIN_GAP = 1.3
# header ref: (side of the pins the names go on, alignment of the mirrored text)
HDR = {"J5": (1, enums_pb2.HA_RIGHT), "J6": (-1, enums_pb2.HA_LEFT)}
TITLE = [(NAME, 47.4, 1.2), (f"rev {REV}", 49.4, 1.0)]


def text(value, x, y, height, align):
    t = BoardText()
    t.layer = bt.BoardLayer.BL_B_SilkS
    t.value = value
    t.position = Vector2.from_xy_mm(BX + x, BY + y)
    a = TextAttributes()
    a.size = Vector2.from_xy_mm(height, height)
    a.stroke_width = int(0.15e6)
    a.mirrored = True
    a.horizontal_alignment = align
    a.vertical_alignment = enums_pb2.VA_CENTER
    t.attributes = a
    return t


def label(net):
    return net.lstrip("+").replace("_", " ")


board_path = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parents[1] / "rp2350-devboard.kicad_pcb")
kicad = KiCad(headless=True, timeout_ms=300000)
kicad.open_document(str(board_path.resolve()), base_types_pb2.DocumentType.DOCTYPE_PCB)
board = kicad.get_board()

board.remove_items([t for t in board.get_text() if isinstance(t, BoardText) and t.layer == bt.BoardLayer.BL_B_SilkS])
texts = []
for fp in board.get_footprints():
    ref = fp.reference_field.text.value
    if ref not in HDR:
        continue
    side, align = HDR[ref]
    for pad in fp.definition.pads:
        x, y = pad.position.x / 1e6 - BX + side * PIN_GAP, pad.position.y / 1e6 - BY
        texts.append(text(label(pad.net.name), x, y, 0.9, align))
for value, y, height in TITLE:
    texts.append(text(value, PL.W / 2, y, height, enums_pb2.HA_CENTER))
board.create_items(texts)
title = board.get_title_block_info()
title.title, title.revision = "RP2350 dev board", REV
board.set_title_block_info(title)
board.save()
print("wrote", len(texts), "texts")
