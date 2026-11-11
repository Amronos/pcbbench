import argparse
from collections import defaultdict
from math import cos, pi
from pathlib import Path

from kipy import KiCad
from kipy.board_types import ArcTrack, Zone
from kipy.geometry import PolyLine, PolyLineNode, PolygonWithHoles, Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType
from shapely.geometry import LineString
from shapely.ops import unary_union

NAME = 'USB side-ground spacing'
GAP_MM = 0.3
USB_NETS = {'/USB_D_P', '/USB_D_N', '/MCU_USB_P', '/MCU_USB_N'}
BUFFER_SEGMENTS = 32


def outline(ring):
    line = PolyLine()
    for x, y in list(ring.coords)[:-1]:
        line.append(PolyLineNode.from_point(Vector2.from_xy_mm(x, y)))
    line.closed = True
    return line


def usb_keepouts(tracks):
    corridors = defaultdict(list)
    for track in tracks:
        if track.net.name in USB_NETS and track.layer in {bt.BL_F_Cu, bt.BL_B_Cu}:
            if isinstance(track, ArcTrack):
                raise ValueError('USB arc tracks are unsupported; existing keepouts left unchanged')
            center = LineString([(track.start.x / 1e6, track.start.y / 1e6),
                                 (track.end.x / 1e6, track.end.y / 1e6)])
            # Circumscribe the round buffer, including nanometer coordinate rounding.
            radius = (track.width / 2e6 + GAP_MM) / cos(pi / (4 * BUFFER_SEGMENTS)) + 1e-6
            corridors[track.layer].append(center.buffer(radius, quad_segs=BUFFER_SEGMENTS))
    if not corridors:
        raise ValueError('No front/back USB tracks found; existing keepouts left unchanged')
    zones = []
    for layer, shapes in corridors.items():
        merged = unary_union(shapes)
        polygons = list(merged.geoms) if hasattr(merged, 'geoms') else [merged]
        for polygon in polygons:
            zone = Zone()
            zone.type = bt.ZT_RULE_AREA
            zone.name = NAME
            zone.layers = [layer]
            shape = PolygonWithHoles()
            shape.outline = outline(polygon.exterior)
            for ring in polygon.interiors:
                shape.add_hole(outline(ring))
            zone.outline = shape
            zone.proto.rule_area_settings.keepout_copper = True
            zones.append(zone)
    return zones


def replace_usb_keepouts(board):
    zones = usb_keepouts(board.get_tracks())
    previous = [zone for zone in board.get_zones() if zone.is_rule_area() and zone.name == NAME]
    board.create_items(zones)
    if previous:
        board.remove_items(previous)


def main():
    parser = argparse.ArgumentParser(description='Keep copper pours 0.3 mm from outer-layer USB tracks.')
    parser.add_argument('board', type=Path)
    args = parser.parse_args()
    with KiCad(headless=True, timeout_ms=120000) as k:
        k.open_document(str(args.board.resolve()), DocumentType.DOCTYPE_PCB)
        board = k.get_board()
        replace_usb_keepouts(board)
        board.refill_zones(block=True, max_poll_seconds=120)
        board.save()


if __name__ == '__main__':
    main()
