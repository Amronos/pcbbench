from kipy import KiCad
from kipy.proto.common.types.base_types_pb2 import DocumentType
from shapely.geometry import Point, Polygon

with KiCad(headless=True) as k:
    k.open_document('/home/ubuntu/pcbbench-run/scratch/filled.kicad_pcb', DocumentType.DOCTYPE_PCB)
    b = k.get_board()
    vias = [v for v in b.get_vias() if v.net.name == '/GND']
    pads = [p for p in b.get_pads() if p.net.name == '/GND']
    tracks = [t for t in b.get_tracks() if t.net.name == '/GND']
    for zone in b.get_zones():
        if zone.is_rule_area() or zone.net.name != '/GND':
            continue
        for filled in zone.proto.filled_polygons:
            for raw in filled.shapes.polygons:
                points = [(n.point.x_nm / 1e6, n.point.y_nm / 1e6) for n in raw.outline.nodes]
                holes = [[(n.point.x_nm/1e6,n.point.y_nm/1e6) for n in hole.nodes] for hole in raw.holes]
                poly = Polygon(points, holes)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                for poly in poly.geoms if hasattr(poly,'geoms') else [poly]:
                    vv = [v for v in vias if poly.distance(Point(v.position.x/1e6, v.position.y/1e6)) < v.diameter/2e6]
                    if vv:
                        continue
                    pp = [p for p in pads if poly.distance(Point(p.position.x/1e6, p.position.y/1e6)) < 0.4]
                    tt = [t for t in tracks if poly.distance(Point((t.start.x+t.end.x)/2e6, (t.start.y+t.end.y)/2e6)) < t.width/2e6]
                    if pp or tt:
                        print('layer', filled.layer, 'area', poly.area, 'bounds', poly.bounds,
                          'pads', [(p.number,p.position.x/1e6,p.position.y/1e6) for p in pp],
                          'tracks', [(str(t.id),t.start.x/1e6,t.start.y/1e6,t.end.x/1e6,t.end.y/1e6) for t in tt])
