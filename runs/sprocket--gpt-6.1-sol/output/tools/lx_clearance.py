import argparse
from pathlib import Path

from kipy import KiCad
from kipy.geometry import PolyLine, PolyLineNode, Vector2
from kipy.proto.board import board_types_pb2 as bt

CUTOUTS = {
    bt.BL_F_Cu: [(141.8, 121.7), (144.25, 121.7), (144.25, 123.95), (141.8, 123.95)],
    bt.BL_In1_Cu: [
        (141.9, 121.8),
        (144.1, 121.8),
        (144.1, 123.8),
        (143.95, 123.8),
        (143.95, 124.1),
        (143.25, 124.1),
        (143.25, 127.0),
        (142.75, 127.0),
        (142.75, 123.8),
        (141.9, 123.8),
    ],
}


def lx_clearance(board_path):
    board_path = board_path.resolve(strict=True)
    with KiCad(headless=True, file_path=str(board_path), timeout_ms=60000) as client:
        board = client.get_board()
        zones = board.get_zones()
        for layer, points in CUTOUTS.items():
            zone = next(
                zone
                for zone in zones
                if zone.net
                and zone.net.name == "/GND"
                and layer in zone.layers
                and zone.priority == 0
                and not zone.is_rule_area()
            )
            outline = zone.outline
            cutout = PolyLine()
            for point in points:
                cutout.append(PolyLineNode.from_point(Vector2.from_xy_mm(*point)))
            cutout.closed = True
            if not any(hole.proto == cutout.proto for hole in outline.holes):
                outline.add_hole(cutout)
                zone.outline = outline
                board.update_items(zone)
        board.refill_zones(block=True, max_poll_seconds=120)
        board.save()


def main():
    parser = argparse.ArgumentParser(
        description="Add LX clearance cutouts to GND zones."
    )
    parser.add_argument("board", type=Path)
    args = parser.parse_args()
    lx_clearance(args.board)


if __name__ == "__main__":
    main()
