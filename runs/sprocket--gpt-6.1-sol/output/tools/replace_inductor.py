import sys
from copy import deepcopy
from pathlib import Path

from design import configure_libraries
from kipy import KiCad
from kipy.geometry import Vector2

configure_libraries()
with KiCad(headless=True, file_path=str(Path(sys.argv[1]).resolve()), timeout_ms=60000) as k:
    k.load_all_libraries()
    k.wait_for_libraries()
    board = k.get_board()
    footprints = {
        footprint.reference_field.text.value: footprint for footprint in board.get_footprints()
    }
    inductor = footprints['L1']
    inductor.position = Vector2.from_xy_mm(122.5, 120)
    for ref, capacitor in footprints.items():
        if ref in {'C24', 'C26'}:
            capacitor.position = Vector2.from_xy_mm(126.1, capacitor.position.y / 1e6)
            board.update_items(capacitor)
    replacement = board.place_footprint_from_library(
        'Inductor_SMD:L_Bourns-SRN4018', inductor.position, inductor.orientation
    )
    nets = {pad.number: pad.net for pad in inductor.definition.pads}
    for pad in replacement.definition.pads:
        pad.net = nets[pad.number]
    inductor.proto.definition.CopyFrom(replacement.proto.definition)
    inductor.definition.items = deepcopy(replacement.definition.items)
    inductor.reference_field.text.value = 'L1'
    inductor.value_field.text.value = '2.2 µH'
    inductor.reference_field.visible = False
    inductor.value_field.visible = False
    board.remove_items(replacement)
    board.update_items(inductor)
    board.save()
