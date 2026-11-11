import os
import sys
import math
from shapely.geometry import box, Point, LineString
from shapely.affinity import rotate
from shapely.strtree import STRtree

sys.path.insert(0, os.environ['SPROCKET_KICAD_ROUTING_TOOLS'] + '/py_router')
from kicad_parser import parse_kicad_pcb

b = parse_kicad_pcb('scratch/clean.kicad_pcb')
ref, layer = sys.argv[1:3]
target = {'C5': (57.8, 49.15), 'C6': (56.6, 49.55), 'C20': (57.5, 52.6)}[ref]
net = {'C5': '/VREG_AVDD', 'C6': '/+3V3', 'C20': '/CORE_1V1'}[ref]
objects = []
for f in b.footprints.values():
    if f.reference in {'C5', 'C6', 'C20'}:
        continue
    for p in f.pads:
        if p.net_id and (layer in p.layers or '*.Cu' in p.layers):
            g = box(p.global_x-p.size_x/2, p.global_y-p.size_y/2,
                    p.global_x+p.size_x/2, p.global_y+p.size_y/2)
            objects.append((p.net_name, rotate(g, p.rect_rotation,
                                              origin=(p.global_x,p.global_y))))
for t in b.segments:
    n = b.nets[t.net_id].name
    if t.layer == layer and n not in {'/VREG_AVDD', '/VREG_LX'}:
        objects.append((n, LineString([(t.start_x,t.start_y),(t.end_x,t.end_y)]).buffer(t.width/2)))
for v in b.vias:
    n = b.nets[v.net_id].name
    if n not in {'/VREG_AVDD', '/VREG_LX'}:
        objects.append((n, Point(v.x,v.y).buffer(v.size/2)))
tree = STRtree([g for n,g in objects])
offset, sx, sy = (.775,.9,.95) if ref == 'C20' else (.95,1,1.45)
found=[]
for angle in [0,90,180,270]:
    for ix in range(round((target[0]-4)*10),round((target[0]+4)*10)):
        for iy in range(round((target[1]-5)*10),round((target[1]+3)*10)):
            x,y=ix/10,iy/10
            dx,dy={0:(-offset,0),90:(0,offset),180:(offset,0),270:(0,-offset)}[angle]
            points=[(x+dx,y+dy,net),(x-dx,y-dy,'/GND')]
            ok=True
            for px,py,n in points:
                g=rotate(box(px-sx/2,py-sy/2,px+sx/2,py+sy/2),angle,origin=(px,py))
                if any(objects[i][0]!=n and g.distance(objects[i][1])<.127
                       for i in tree.query(g.buffer(.127))):
                    ok=False;break
            if ok:
                found.append((round(math.hypot(points[0][0]-target[0],points[0][1]-target[1]),3),x,y,angle,points))
print(sorted(found)[:20])
