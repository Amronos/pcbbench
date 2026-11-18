from pathlib import Path
from cad import kicad_pcb
from kicode.geometry import Vector2

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    connector = next(part for part in board.get_footprints() if part.reference_field.text.value == 'J6')
    for pad in connector.definition.pads:
        if pad.number:
            pad.padstack.drill.diameter = Vector2.from_xy_mm(0.7, 0.7)
    board.update_items(connector)
    board.refill_zones()
