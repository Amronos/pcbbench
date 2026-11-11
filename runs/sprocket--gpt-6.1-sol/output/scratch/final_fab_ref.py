import sys
from pathlib import Path

from kipy import KiCad
from kipy.proto.common.types.base_types_pb2 import DocumentType

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from finish_layout import finish_text

with KiCad(headless=True, timeout_ms=120000) as kicad:
    kicad.open_document(str(ROOT / 'sprocket2350.kicad_pcb'), DocumentType.DOCTYPE_PCB)
    board = kicad.get_board()
    footprint = next(fp for fp in board.get_footprints() if fp.reference_field.text.value == 'U7')
    finish_text(footprint)
    board.update_items(footprint)
    board.save()
