from pathlib import Path
from cad import kicad_pcb
from cad.kicad import route
from kicode.board_types import BoardLayer

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    tracks = [track for track in board.get_tracks() if track.net.name == 'FLASH_CS'
              and track.layer not in {BoardLayer.BL_F_Cu, BoardLayer.BL_B_Cu}]
    board.remove_items(tracks)
    result = route(board, [{'net': 'FLASH_CS', 'layers': ['F.Cu', 'B.Cu'], 'width': 0.15}],
                   layers=['F.Cu', 'B.Cu'], via_cost=2)
    print('\n'.join(result.human_lines()))
    board.refill_zones()
