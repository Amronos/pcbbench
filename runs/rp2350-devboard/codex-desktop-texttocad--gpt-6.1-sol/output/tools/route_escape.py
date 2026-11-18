from pathlib import Path
import sys
from cad import kicad_pcb
from cad.kicad import route

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    entries = []
    for name in sys.argv[1:]:
        entries.append({'net': name, 'layers': ['F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu'], 'width': 0.15})
    result = route(board, entries, layers={'F.Cu': 1, 'B.Cu': 1, 'In1.Cu': 5, 'In2.Cu': 3}, via_cost=2)
    print('\n'.join(result.human_lines()))
    board.refill_zones()
