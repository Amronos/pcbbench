from pathlib import Path
from cad import kicad_pcb
from kicode.geometry import Vector2

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    tracks = board.get_tracks()
    for track in tracks:
        if track.id.value == '79db5ce9-bc7d-46be-b0a4-b46c9294a130':
            track.end = Vector2.from_xy_mm(32.695, 42.64)
    board.update_items(tracks)
    texts = board.get_text()
    for text in texts:
        if text.value == 'BAT+ GND NTC':
            text.position = Vector2.from_xy_mm(13, 5)
    board.update_items(texts)
    board.refill_zones()
