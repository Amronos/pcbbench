from pathlib import Path
import sys
from cad import kicad_pcb

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    names = set(sys.argv[1:])
    board.remove_items([item for item in list(board.get_tracks()) + list(board.get_vias()) if item.net.name in names])
    board.refill_zones()
