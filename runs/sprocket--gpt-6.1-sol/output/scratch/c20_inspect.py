import os
import sys
from shapely.geometry import box, Point, LineString
from shapely.affinity import rotate

sys.path.insert(0, os.environ['SPROCKET_KICAD_ROUTING_TOOLS'] + '/py_router')
from kicad_parser import parse_kicad_pcb

b = parse_kicad_pcb('scratch/clean.kicad_pcb')
cx, cy, r = 58.3, 52.8, 1.6
win = box(cx - r, cy - r, cx + r, cy + r)
ALL = {'F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'}
for f in b.footprints.values():
    for p in f.pads:
        if abs(p.global_x - cx) < r + 3 and abs(p.global_y - cy) < r + 3:
            g = rotate(box(p.global_x-p.size_x/2, p.global_y-p.size_y/2,
                           p.global_x+p.size_x/2, p.global_y+p.size_y/2),
                       p.rect_rotation, origin=(p.global_x, p.global_y))
            if g.intersects(win):
                print('PAD', f.reference, p.pad_number, p.net_name, p.layers,
                      round(p.global_x, 3), round(p.global_y, 3), p.size_x, p.size_y, p.rotation,
                      [round(v, 3) for v in g.bounds])
for t in b.segments:
    g = LineString([(t.start_x, t.start_y), (t.end_x, t.end_y)]).buffer(t.width/2)
    if g.intersects(win):
        print('TRK', t.layer, b.nets[t.net_id].name, t.start_x, t.start_y, t.end_x, t.end_y, t.width)
for v in b.vias:
    if Point(v.x, v.y).distance(win) < .5:
        print('VIA', b.nets[v.net_id].name, v.x, v.y, v.size, v.drill, getattr(v, 'layers', None))
print([k for k in dir(b) if not k.startswith('_')])
