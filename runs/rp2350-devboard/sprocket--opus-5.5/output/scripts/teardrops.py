"""Enable teardrops on every pad and via. Run last, after all copper changes: kicad-python scripts/teardrops.py [board]"""
import sys
from pathlib import Path

from kipy import KiCad
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types import base_types_pb2

board_path = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parents[1] / "rp2350-devboard.kicad_pcb")
kicad = KiCad(headless=True, timeout_ms=300000)
kicad.open_document(str(board_path.resolve()), base_types_pb2.DocumentType.DOCTYPE_PCB)
board = kicad.get_board()

footprints = board.get_footprints()
for fp in footprints:
    for pad in fp.definition.pads:
        pad.proto.teardrop.mode = bt.PTM_ENABLED
vias = board.get_vias()
for via in vias:
    via.proto.teardrop.mode = bt.PTM_ENABLED
board.update_items(footprints + vias)
# a single fill leaves the teardrop count unsettled; the second fill matches what DRC's refill produces
board.refill_zones()
board.refill_zones()
board.save()
print(f"teardrops on {sum(len(f.definition.pads) for f in footprints)} pads and {len(vias)} vias")
