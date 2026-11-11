import math
import os
import sys
from shapely.geometry import box, Point, LineString
from shapely.affinity import rotate
from shapely.strtree import STRtree

sys.path.insert(0, os.environ['SPROCKET_KICAD_ROUTING_TOOLS'] + '/py_router')
from kicad_parser import parse_kicad_pcb

CLR = .127
W = .127
VIA_D = float(os.environ.get('VIA_D', .45))
CU = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
CORE_VIA = (57.5, 52.6)
PACKAGES = {'0201': (.32, .46, .40), '0402': (.48, .56, .62)}

b = parse_kicad_pcb('scratch/clean.kicad_pcb')
objs = {l: [] for l in CU}
for f in b.footprints.values():
    if f.reference == 'C20':
        continue
    for p in f.pads:
        if not p.net_id:
            continue
        g = rotate(box(p.global_x-p.size_x/2, p.global_y-p.size_y/2,
                       p.global_x+p.size_x/2, p.global_y+p.size_y/2),
                   p.rect_rotation, origin=(p.global_x, p.global_y))
        layers = CU if '*.Cu' in p.layers else [l for l in p.layers if l in CU]
        for l in layers:
            objs[l].append((p.net_name, g, f'{f.reference}.{p.pad_number}'))
for t in b.segments:
    objs[t.layer].append((b.nets[t.net_id].name,
                          LineString([(t.start_x, t.start_y), (t.end_x, t.end_y)]).buffer(t.width/2),
                          f'trk {b.nets[t.net_id].name} {t.start_x},{t.start_y}-{t.end_x},{t.end_y}'))
for v in b.vias:
    for l in CU:
        objs[l].append((b.nets[v.net_id].name, Point(v.x, v.y).buffer(v.size/2),
                        f'via {b.nets[v.net_id].name} {v.x},{v.y}'))
trees = {l: STRtree([o[1] for o in objs[l]]) for l in CU}


def margin(geom, net, layers, extra=()):
    best = (9, None)
    for l in layers:
        for i in trees[l].query(geom.buffer(.6)):
            n, g, name = objs[l][i]
            if n != net:
                best = min(best, (geom.distance(g), name))
        if l == 'B.Cu':
            for n, g, name in extra:
                if n != net:
                    best = min(best, (geom.distance(g), name))
    return best


def frange(a, z, s):
    return [round(a + i*s, 3) for i in range(int(round((z-a)/s))+1)]


results = []
for pkg, (off, sx, sy) in PACKAGES.items():
    for ang in (0, 90, 180, 270):
        ux, uy = round(math.cos(math.radians(ang)), 6), round(math.sin(math.radians(ang)), 6)
        for x in frange(56.9, 59.6, .05):
            for y in frange(51.9, 53.6, .05):
                p1 = (x - ux*off, y - uy*off)
                p2 = (x + ux*off, y + uy*off)
                w, h = (sx, sy) if ux else (sy, sx)
                g1 = box(p1[0]-w/2, p1[1]-h/2, p1[0]+w/2, p1[1]+h/2)
                g2 = box(p2[0]-w/2, p2[1]-h/2, p2[0]+w/2, p2[1]+h/2)
                m1 = margin(g1, '/CORE_1V1', ['B.Cu'])
                if m1[0] < CLR:
                    continue
                m2 = margin(g2, '/GND', ['B.Cu'], [('/CORE_1V1', g1, 'C20.1')])
                if m2[0] < CLR:
                    continue
                core_len = 0 if g1.distance(Point(CORE_VIA).buffer(.225)) == 0 else math.dist(p1, CORE_VIA)
                core_trk = LineString([p1, CORE_VIA]).buffer(W/2)
                if core_len and margin(core_trk, '/CORE_1V1', ['B.Cu'], [('/GND', g2, 'C20.2')])[0] < CLR:
                    continue
                results.append(dict(pkg=pkg, ang=ang, c=(x, y), p1=p1, p2=p2, g1=g1, g2=g2,
                                    core_len=round(core_len, 3), m1=m1, m2=m2,
                                    core_trk=core_trk if core_len else None))
print('C20 B.Cu placements:', len(results))

vias = []
for vx in frange(55.8, 60.0, .05):
    for vy in frange(51.6, 54.2, .05):
        vg = Point(vx, vy).buffer(VIA_D/2)
        m = margin(vg, '/GND', CU)
        if m[0] >= CLR:
            vias.append(((vx, vy), vg, m))
print('GND via sites:', len(vias))

best = []
for r in results:
    extra = [('/CORE_1V1', r['g1'], 'C20.1')]
    if r['core_trk'] is not None:
        extra.append(('/CORE_1V1', r['core_trk'], 'C20 core trk'))
    for (vx, vy), vg, mv in vias:
        if math.dist(r['p2'], (vx, vy)) > 1.6:
            continue
        mv2 = margin(vg, '/GND', ['B.Cu'], extra)
        if mv2[0] < CLR:
            continue
        in_pad = r['g2'].contains(Point(vx, vy))
        glen = 0 if in_pad or vg.intersects(r['g2']) else math.dist(r['p2'], (vx, vy))
        if glen:
            trk = LineString([r['p2'], (vx, vy)]).buffer(W/2)
            mt = margin(trk, '/GND', ['B.Cu'], extra)
            if mt[0] < CLR:
                continue
        else:
            mt = (None, None)
        hole = math.dist((vx, vy), CORE_VIA)
        best.append((round(r['core_len'] + glen, 3), r['pkg'], r['ang'], r['c'],
                     tuple(round(v, 3) for v in r['p1']), tuple(round(v, 3) for v in r['p2']),
                     r['core_len'], (vx, vy), round(glen, 3), in_pad,
                     round(min(mv[0], mv2[0]), 3), mv if mv[0] < mv2[0] else mv2,
                     round(r['m1'][0], 3), r['m1'][1], round(r['m2'][0], 3), r['m2'][1],
                     mt, round(hole, 3)))
best.sort(key=lambda t: (t[0], -t[10]))
seen = set()
for row in best:
    key = (row[1], row[3], row[7])
    if key in seen:
        continue
    seen.add(key)
    print(row)
    if len(seen) > int(os.environ.get('N', 40)):
        break
