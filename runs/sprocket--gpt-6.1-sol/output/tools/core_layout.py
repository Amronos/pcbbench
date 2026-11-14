import sys
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Via
from kipy.geometry import Angle, Vector2
from kipy.proto.board import board_types_pb2 as bt

PLACEMENTS = {
    'J1': (136, 103, 180),
    'D1': (136, 112, 90),
    'R1': (129, 110, 90),
    'R2': (129, 112, 90),
    'C34': (139, 110, 0),
    'R3': (139.6, 124.3, 270),
    'R4': (140.6, 124.3, 270),
    'C28': (157.5, 104, 180),
    'C29': (160.3, 104, 180),
    'R5': (151, 124, 90),
    'C17': (135.0, 121.5, 90),
}
RESET_NETS = {
    '/USB_DP',
    '/USB_DM',
    '/USB_CONN_DP',
    '/USB_CONN_DM',
    '/QSPI_CLK',
    '/FLASH_CS',
    '/CC1',
    '/CC2',
    '/VBUS',
    '/RADIO_TX',
    '/SD_CS',
    '/QSPI_D2',
    '/QSPI_D3',
    '/QSPI_D1',
    '/QSPI_D0',
    '/GP6',
    '/RADIO_EN',
}
POWER_NETS = {'/3V3', '/GND'}
OBSOLETE_POWER_TRACKS = {
    '21c5e5c9-b7ed-400a-a9ca-0b0e2ee97da6',
    'fdc1dee0-f353-4bb8-bb21-a46405b55bee',
}


def in_usb_fanout(point):
    return 139900000 < point.x < 142400000 and 122000000 < point.y < 126000000


def in_old_decoupling_area(point):
    return 159000000 < point.x < 161000000 and 111000000 < point.y < 113000000


with KiCad(headless=True, file_path=str(Path(sys.argv[1]).resolve()), timeout_ms=60000) as k:
    board = k.get_board()
    footprints = board.get_footprints()
    moved = {
        footprint.id.value
        for footprint in footprints
        if footprint.reference_field.text.value in PLACEMENTS
    }
    old_pads = [
        pad
        for pad in board.get_pads()
        if pad.parent.value in moved and pad.net.name in POWER_NETS
    ]

    def at_moved_pad(point):
        return any(
            abs(point.x - pad.position.x) < 500000
            and abs(point.y - pad.position.y) < 500000
            for pad in old_pads
        )

    removed = []
    for item in [*board.get_tracks(), *board.get_vias()]:
        is_via = isinstance(item, Via)
        points = [item.position] if is_via else [item.start, item.end]
        net = item.net.name
        if (
            net in RESET_NETS
            or (net in POWER_NETS and any(at_moved_pad(point) for point in points))
            or (
                net == '/GND'
                and is_via
                and 128000000 < item.position.x < 144000000
                and item.position.y < 118000000
            )
            or (net in {'/3V3', '/1V1'} and all(in_usb_fanout(point) for point in points))
            or (
                net == '/3V3'
                and not is_via
                and (
                    all(in_old_decoupling_area(point) for point in points)
                    or item.id.value in OBSOLETE_POWER_TRACKS
                )
            )
        ):
            removed.append(item)
    board.remove_items(removed)
    board.remove_items(
        [
            zone
            for zone in board.get_zones()
            if zone.proto.copper_settings.teardrop.type in {bt.ZTDT_VIA_PAD, bt.ZTDT_TRACK_END}
        ]
    )
    for footprint in footprints:
        ref = footprint.reference_field.text.value
        if ref in PLACEMENTS:
            x, y, rotation = PLACEMENTS[ref]
            footprint.position = Vector2.from_xy_mm(x, y)
            footprint.orientation = Angle.from_degrees(rotation)
            board.update_items(footprint)
    board.save()
