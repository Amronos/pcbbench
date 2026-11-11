from kipy import KiCad
from kipy.board_types import Track
from kipy.geometry import Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType

v = Vector2.from_xy_mm
with KiCad(headless=True, timeout_ms=120000) as k:
    k.open_document('/home/ubuntu/pcbbench-run/scratch/merged.kicad_pcb', DocumentType.DOCTYPE_PCB)
    b = k.get_board()
    remove = {'cc5e97b2-19f8-4559-bfd4-bceb0cd067ad',
              'e4f1b4b9-ad33-4f3c-9dc3-60758cd03cf6',
              '3f68284b-f392-4a56-9749-14cbf98a7c10',
              '746911e3-55e5-42fb-a9b0-707a33c56309',
              '4b728529-6632-465e-928e-ee0f9cb23a7a'}
    for item in b.get_tracks() + b.get_vias():
        if item.id.value in remove:
            b.remove_items(item)
    for footprint in b.get_footprints():
        ref = footprint.reference_field.text.value
        if ref == 'C5':
            footprint.position = v(60.58, 46.2)
            b.update_items(footprint)
        if ref == 'L1':
            for shape in footprint.definition.shapes:
                if shape.id.value == 'fcb0eaa3-7285-4a36-ba30-9b08f13b2b19':
                    shape.proto.shape.circle.center.x_nm -= 300000
                    shape.proto.shape.circle.radius_point.x_nm -= 300000
            b.update_items(footprint)
    for via in b.get_vias():
        if via.net.name == '/GND' and via.position == v(60.2, 45.25):
            via.position = v(60.58, 45.25)
            b.update_items(via)
        if via.id.value == 'f09bb506-f436-4f4c-9d0e-33f315638dff':
            via.position = v(57, 53.2)
            b.update_items(via)
    for track in b.get_tracks():
        updated = False
        if track.net.name == '/VREG_AVDD':
            if track.start == v(60.2, 47.15):
                track.start = v(60.58, 47.15)
                updated = True
            if track.end == v(60.2, 47.15):
                track.end = v(60.58, 47.15)
                updated = True
        if track.net.name == '/GND' and track.layer == bt.BL_B_Cu:
            if track.start == v(58.22, 53.05):
                track.start = v(58.22, 53.3)
                updated = True
            if track.end == v(58.22, 53.05):
                track.end = v(58.22, 53.3)
                updated = True
        if updated:
            b.update_items(track)
    nets = {net.name: net for net in b.get_nets()}
    routes = [('/CORE_1V1', bt.BL_In2_Cu, .25,
               [(57.8, 47.6), (57.95, 47.75), (57.95, 50.5),
                (57.4, 51.05), (56.3, 51.05), (56, 50.75)]),
              ('/GND', bt.BL_B_Cu, .127,
               [(58.22, 53.3), (57, 53.3), (57, 53.2)])]
    for name, layer, width, points in routes:
        for start, end in zip(points, points[1:]):
            track = Track()
            track.net = nets[name]
            track.layer = layer
            track.width = round(width * 1e6)
            track.start, track.end = v(*start), v(*end)
            b.create_items(track)
    b.refill_zones(block=True, max_poll_seconds=120)
    b.save()
