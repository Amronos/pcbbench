from kipy import KiCad
from kipy.board_types import Track
from kipy.geometry import Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType

v = Vector2.from_xy_mm
with KiCad(headless=True, timeout_ms=120000) as k:
    k.open_document('/home/ubuntu/pcbbench-run/scratch/merged.kicad_pcb', DocumentType.DOCTYPE_PCB)
    b = k.get_board()
    remove = {'5a0cade1-f7ef-4c80-8052-bcb2720861ff',
              'bc7c0030-31e2-4ac1-93d3-12fdd3aeab76',
              'ecc537d4-0592-4589-8036-a14a49a2e031'}
    for track in b.get_tracks():
        if track.id.value in remove or (track.net.name == '/VREG_AVDD'
                                       and track.start == v(61.3, 46.2)):
            b.remove_items(track)
    for footprint in b.get_footprints():
        ref = footprint.reference_field.text.value
        if ref == 'R6':
            footprint.position = v(62.6, 46)
            b.update_items(footprint)
        if ref == 'L1':
            for shape in footprint.definition.shapes:
                if shape.id.value == 'fcb0eaa3-7285-4a36-ba30-9b08f13b2b19':
                    shape.proto.shape.circle.center.CopyFrom(v(59.35, 45.5).proto)
                    shape.proto.shape.circle.radius_point.CopyFrom(v(59.35, 45.62).proto)
            b.update_items(footprint)
    for via in b.get_vias():
        if via.id.value == 'f09bb506-f436-4f4c-9d0e-33f315638dff':
            via.position = v(57.05, 53.2)
            b.update_items(via)
        elif via.id.value == 'def9bb29-eba3-4a2e-85e8-fc02e4403db3':
            via.position = v(61, 48.05)
            b.update_items(via)
    for track in b.get_tracks():
        if track.net.name == '/GND' and track.layer == bt.BL_B_Cu:
            updated = False
            for field in ('start', 'end'):
                point = getattr(track, field)
                if point.y == 53300000 and 57000000 <= point.x <= 58220000:
                    setattr(track, field, Vector2.from_xy(point.x if point.x != 57000000 else 57050000, 53160000))
                    updated = True
                elif point == v(57, 53.2):
                    setattr(track, field, v(57.05, 53.2))
                    updated = True
            if updated:
                b.update_items(track)
    nets = {net.name: net for net in b.get_nets()}
    routes = [('/VREG_AVDD', .2, [(62.6, 45.175), (63.3, 45.175),
                                (63.3, 47.8), (61.5, 47.8), (60.58, 47.15)]),
              ('/+3V3', .127, [(62.6, 46.825), (62, 46.85)])]
    for name, width, points in routes:
        for start, end in zip(points, points[1:]):
            track = Track()
            track.net = nets[name]
            track.layer = bt.BL_F_Cu
            track.width = round(width * 1e6)
            track.start, track.end = v(*start), v(*end)
            b.create_items(track)
    b.refill_zones(block=True, max_poll_seconds=120)
    b.save()
