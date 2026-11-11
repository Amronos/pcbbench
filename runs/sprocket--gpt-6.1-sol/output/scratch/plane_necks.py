from kipy import KiCad
from kipy.proto.common.types.base_types_pb2 import DocumentType
from shapely.geometry import Polygon

with KiCad(headless=True) as k:
    k.open_document('/home/ubuntu/pcbbench-run/scratch/esd-repaired.kicad_pcb', DocumentType.DOCTYPE_PCB)
    for z in k.get_board().get_zones():
        if z.net.name != '/+3V3':
            continue
        for f in z.proto.filled_polygons:
            for p in f.shapes.polygons:
                poly = Polygon([(n.point.x_nm / 1e6, n.point.y_nm / 1e6) for n in p.outline.nodes],
                               [[(n.point.x_nm / 1e6, n.point.y_nm / 1e6) for n in h.nodes] for h in p.holes])
                eroded = poly.buffer(-0.064)
                pieces = list(eroded.geoms) if hasattr(eroded, 'geoms') else [eroded]
                if len(pieces) > 1:
                    print('polygon', poly.bounds, 'area', poly.area)
                    for part in sorted(pieces, key=lambda p: p.area)[:-1]:
                        print('severed', part.area, part.bounds)
