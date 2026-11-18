from pathlib import Path
from cad import kicad_pcb
from kicode.board_types import BoardLayer, Track, Via
from kicode.geometry import Vector2
from kicode.util.units import from_mm

ROOT = Path(__file__).resolve().parents[1]
with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    mcu = next(part for part in board.get_footprints() if part.reference_field.text.value == 'U1')
    items = []
    skip = {1, 6, 11, 20, 21, 22, 23, 30, 38, 39, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 61}
    for pad in mcu.definition.pads:
        if not pad.number:
            continue
        number = int(pad.number)
        if number in skip:
            continue
        position = (pad.position.x / 1e6, pad.position.y / 1e6)
        if number <= 15:
            target = (position[0], 46.4 if number % 2 == 0 else 44.5)
        elif number <= 29:
            target = (34.4 if number % 2 == 0 else 32.5, position[1])
        elif number <= 43:
            target = (position[0], 37.65 if number % 2 == 0 else 39.45)
        else:
            target = (27.25 if number % 2 else 25.6, position[1])
        if number == 15:
            target = (33.5, 46.15)
        if number == 31:
            target = (33.5, 37.85)
        if number == 43:
            target = (27.3, 37.3)
        if number == 17:
            target = (32.7, 44.4)
        if number == 13:
            target = (31.95, 44.4)
        if 24 <= number <= 29:
            target = (32.5 if number % 2 == 0 else 34.4, position[1] if number % 2 == 0 else position[1] - 0.2)
        if number == 25:
            target = (35.25, 40)
        if number == 27:
            target = (34.4, 40.1)
        if number == 29:
            target = (34.4, 39.35)
        points = [position, target]
        if number == 43:
            points = [position, (28, 38), target]
        if number == 25:
            points = [position, (34.05, 41.2), target]
        if number == 27:
            points = [position, (34.1, 40.4), target]
        if number == 29:
            points = [position, (34.15, 39.6), target]
        if number == 13:
            points = [position, (32, 44.45), target]
        for start, end in zip(points, points[1:]):
            track = Track()
            track.start = Vector2.from_xy_mm(*start)
            track.end = Vector2.from_xy_mm(*end)
            track.width = from_mm(0.15)
            track.layer = BoardLayer.BL_F_Cu
            track.net = pad.net
            items.append(track)
        via = Via()
        via.position = track.end
        via.diameter = from_mm(0.6)
        via.drill_diameter = from_mm(0.3)
        via.net = pad.net
        items.append(via)
    board.create_items(items)
    board.refill_zones()
