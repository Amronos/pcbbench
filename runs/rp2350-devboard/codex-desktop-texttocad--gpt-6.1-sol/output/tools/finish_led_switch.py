from pathlib import Path
from cad import kicad_pcb
from kicode.board_types import ViaDrillFillingMode, ViaDrillCappingMode
from kicode.geometry import Vector2

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    vias = board.get_vias()
    for via in vias:
        via.padstack.drill.filled = ViaDrillFillingMode.VDFM_FILLED
        via.padstack.drill.capped = ViaDrillCappingMode.VDCM_CAPPED
    board.update_items(vias)
    texts = board.get_text()
    for text in texts:
        if text.value == 'RGB':
            text.position = Vector2.from_xy_mm(73, 23)
    board.update_items(texts)
    board.refill_zones()
