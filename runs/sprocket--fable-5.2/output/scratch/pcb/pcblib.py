"""Shared helpers for the board scripts."""
from kipy import KiCad
from kipy.proto.common.types import DocumentType
from kipy.geometry import Vector2, Angle
from kipy.board_types import BoardLayer

ROOT = '/home/ubuntu/pcbbench-run'
PCB = f'{ROOT}/rp2350-devboard.kicad_pcb'
NET = f'{ROOT}/scratch/rp2350-devboard.net'
X0, Y0 = 100.0, 100.0          # board top-left corner, absolute mm
W, H = 76.2, 25.4              # board size
KEEP = 5.0                     # copper-free strip at the antenna end


def mm(x, y):
    return Vector2.from_xy_mm(x, y)


def open_board(create=False, path=PCB):
    k = KiCad(headless=True, timeout_ms=120000)
    doc = (k.create_document if create else k.open_document)(path, DocumentType.DOCTYPE_PCB)
    return k, k.get_board(), doc


def fps(board):
    return {f.reference_field.text.value: f for f in board.get_footprints()}
