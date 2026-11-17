from pathlib import Path
from cad import kicad_pcb
from kicode.geometry import Vector2

ROOT = Path(__file__).resolve().parents[1]
PLACEMENT = {'C1': (29, 48.3), 'C2': (33, 48.3), 'C11': (31, 48.3),
             'C5': (31.4, 35.5), 'C6': (27.2, 36), 'C12': (29.6, 35.5), 'R16': (24.5, 46.5)}
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    footprints = board.get_footprints()
    for footprint in footprints:
        ref = footprint.reference_field.text.value
        if ref in PLACEMENT:
            footprint.position = Vector2.from_xy_mm(*PLACEMENT[ref])
    board.update_items(footprints)
