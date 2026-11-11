#!/usr/bin/env python3
"""Generate the KiCad PCB (placement, outline, zones, silk) from design.py + the exported netlist.
Existing tracks/vias in the board file are preserved (unless --drop-routes)."""
import os, sys, uuid, copy, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import parse, dump, find, findall, Q
import design as D

S = '/home/ubuntu/.local/share/backplane/kicad/10.99.0-bp.4/share/kicad'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'boards', D.NAME)
PCB = os.path.join(OUT, D.NAME + '.kicad_pcb')
NS = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
def uid(*a): return Q(str(uuid.uuid5(NS, D.NAME + '/' + '/'.join(str(x) for x in a))))
OX, OY, W, H = D.OX, D.OY, D.W, D.H
netlist = json.load(open(os.path.join(ROOT, 'build', 'netlist.json')))
FIELDS = json.load(open(os.path.join(ROOT, 'build', 'fields.json')))
nets = sorted({n for pins in netlist.values() for n in pins.values()})
NETNO = {n: i + 1 for i, n in enumerate(nets)}
def net(n): return ['net', NETNO[n], Q(n)]

def rnd(v): return round(v, 4)
def rot_pt(x, y, a):
    r = math.radians(a); c, s = math.cos(r), math.sin(r)
    return x * c + y * s, -x * s + y * c

def footprint(p):
    lib, name = p['fp'].split(':')
    f = parse(open(f'{S}/footprints/{lib}.pretty/{name}.kicad_mod').read())
    x, y, rot = p['pos']
    ref = p['ref']
    back = p['layer'] == 'B'
    if back:   # only used for single-pad test points: swap F.* layers to B.*
        def flip(e):
            for i, v in enumerate(e):
                if isinstance(v, list): flip(v)
                elif isinstance(v, str) and v.startswith('F.') and v != 'F.Cu' or v == 'F.Cu': e[i] = Q('B.' + v[2:])
            if e and e[0] == 'effects' and find(e, 'justify') is None: e.append(['justify', 'mirror'])
        flip(f)
    out = ['footprint', Q(p['fp']), ['layer', Q('B.Cu' if back else 'F.Cu')], ['uuid', uid('fp', ref)],
           ['at', rnd(OX + x), rnd(OY + y), rot]]
    padn = {}
    for e in f[1:]:
        if not isinstance(e, list):
            continue
        k = e[0]
        if k in ('version', 'generator', 'generator_version', 'layer', 'embedded_fonts') or (k == 'model' and not p['bom']):
            continue
        e = copy.deepcopy(e)
        if k == 'property':
            if e[1] == 'Reference': e[2] = Q(ref)
            elif e[1] == 'Value': e[2] = Q(p['value'])
            elif e[1] == 'Datasheet': e[2] = Q(FIELDS[ref]['Datasheet'])
            elif e[1] == 'Description': e[2] = Q(FIELDS[ref]['Description'])
            at = find(e, 'at')
            if at is not None:
                a = (float(at[3]) if len(at) > 3 else 0) + rot
                at[:] = ['at', at[1], at[2], a % 360]
            if e[1] == 'Value' and find(e, 'hide') is None:
                e.insert(4, ['hide', 'yes'])
            if e[1] == 'Reference':
                # reference designators live on the fab layer only (dense board)
                find(e, 'layer')[1] = Q('B.Fab' if back else 'F.Fab')
                if find(e, 'hide') is None: e.insert(4, ['hide', 'yes'])
            e = [x for x in e if not (isinstance(x, list) and x[0] == 'uuid')] + [['uuid', uid('prop', ref, e[1])]]
        elif k == 'fp_text':
            at = find(e, 'at')
            a = (float(at[3]) if len(at) > 3 else 0) + rot
            at[:] = ['at', at[1], at[2], a % 360]
        elif k == 'pad':
            num = str(e[1])
            at = find(e, 'at')
            a = (float(at[3]) if len(at) > 3 else 0) + rot
            at[:] = ['at', at[1], at[2], a % 360] if a % 360 else ['at', at[1], at[2]]
            padn[num] = padn.get(num, 0) + 1
            n = netlist.get(ref, {}).get(num)
            if n is None and num in p['extra']: n = p['extra'][num]
            e = [x for x in e if not (isinstance(x, list) and x[0] in ('uuid', 'net'))]
            if n is not None and e[2] != 'np_thru_hole':
                e.append(net(n))
            e.append(['uuid', uid('pad', ref, num, padn[num])])
        elif k in ('fp_line', 'fp_rect', 'fp_circle', 'fp_arc', 'fp_poly'):
            ly = find(e, 'layer')[1]
            if ref in ('J5', 'J6') and ly == 'F.SilkS':
                continue
        out.append(e)
    # insert path / sheet info + extra properties after last property
    idx = max(i for i, x in enumerate(out) if isinstance(x, list) and x[0] == 'property')
    extra = []
    have = {x[1] for x in out if isinstance(x, list) and x[0] == 'property'}
    for k, v in (('Datasheet', FIELDS[ref]['Datasheet']), ('Description', FIELDS[ref]['Description']), ('MPN', p['mpn']),
                 ('Manufacturer', p['mfr']), ('LCSC', p['lcsc'])):
        if v and k not in have:
            extra.append(['property', Q(k), Q(v), ['at', 0, 0, rot], ['layer', Q('B.Fab' if back else 'F.Fab')], ['hide', 'yes'],
                          ['uuid', uid('prop', ref, k)], ['effects', ['font', ['size', 1, 1], ['thickness', 0.15]]]])
    extra += [['path', Q('/' + uid('sym', ref))], ['sheetname', Q('/')], ['sheetfile', Q(D.NAME + '.kicad_sch')]]
    out[idx + 1:idx + 1] = extra
    attr = find(out, 'attr')
    if not p['bom']:
        if attr is None:
            attr = ['attr']; out.insert(idx + 1 + len(extra), attr)
        for t in ('exclude_from_pos_files', 'exclude_from_bom'):
            if t not in attr: attr.append(t)
    return out

def pads_abs(p):
    """absolute pad centres {num: [(x, y, w, h)]} in board-local mm (for other scripts)"""
    lib, name = p['fp'].split(':')
    f = parse(open(f'{S}/footprints/{lib}.pretty/{name}.kicad_mod').read())
    x, y, rot = p['pos']; res = {}
    for e in findall(f, 'pad'):
        at = find(e, 'at'); sz = find(e, 'size')
        px, py = rot_pt(float(at[1]), float(at[2]), rot)
        a = ((float(at[3]) if len(at) > 3 else 0) + rot) % 180
        w, h = float(sz[1]), float(sz[2])
        if abs(a - 90) < 1: w, h = h, w
        res.setdefault(str(e[1]), []).append((rnd(x + px), rnd(y + py), w, h))
    return res

def gr_line(x1, y1, x2, y2, layer='Edge.Cuts', w=0.1):
    return ['gr_line', ['start', rnd(OX + x1), rnd(OY + y1)], ['end', rnd(OX + x2), rnd(OY + y2)],
            ['stroke', ['width', w], ['type', 'default']], ['layer', Q(layer)], ['uuid', uid('gl', layer, x1, y1, x2, y2)]]
def gr_arc(sx, sy, mx, my, ex, ey, layer='Edge.Cuts', w=0.1):
    return ['gr_arc', ['start', rnd(OX + sx), rnd(OY + sy)], ['mid', rnd(OX + mx), rnd(OY + my)],
            ['end', rnd(OX + ex), rnd(OY + ey)], ['stroke', ['width', w], ['type', 'default']], ['layer', Q(layer)],
            ['uuid', uid('ga', layer, sx, sy, ex, ey)]]
def gr_text(t, x, y, size=0.8, layer='F.SilkS', ang=0, just=None, thick=None):
    eff = ['effects', ['font', ['size', size, size], ['thickness', thick or round(size * 0.15, 3)]]]
    j = list(just or [])
    if layer.startswith('B.'): j.append('mirror')
    if j: eff.append(['justify'] + j)
    return ['gr_text', Q(t), ['at', rnd(OX + x), rnd(OY + y), ang], ['layer', Q(layer)], ['uuid', uid('gt', layer, t, x, y)], eff]

def zone(netname, layer, pts, prio=0, name='', clearance=0.2, minw=0.2, thermal=True, island=None):
    z = ['zone', ['net', NETNO[netname] if netname else 0], ['net_name', Q(netname or '')], ['layer', Q(layer)],
         ['uuid', uid('zone', netname, layer, name)], ['hatch', 'edge', 0.5]]
    if name: z.insert(4, ['name', Q(name)])
    if prio: z.append(['priority', prio])
    z.append(['connect_pads'] + ([] if thermal else ['yes']) + [['clearance', clearance]])
    z.append(['min_thickness', minw]); z.append(['filled_areas_thickness', 'no'])
    fill = ['fill', 'yes', ['thermal_gap', 0.25], ['thermal_bridge_width', 0.3]]
    if island is not None: fill += [['island_removal_mode', island]]
    z.append(fill)
    z.append(['polygon', ['pts'] + [['xy', rnd(OX + x), rnd(OY + y)] for x, y in pts]])
    return z

def keepout(layers, pts, name):
    return ['zone', ['net', 0], ['net_name', Q('')], ['layers'] + [Q(l) for l in layers], ['uuid', uid('ko', name)],
            ['name', Q(name)], ['hatch', 'edge', 0.5], ['connect_pads', ['clearance', 0]], ['min_thickness', 0.25],
            ['filled_areas_thickness', 'no'],
            ['keepout', ['tracks', 'not_allowed'], ['vias', 'not_allowed'], ['pads', 'allowed'],
             ['copperpour', 'not_allowed'], ['footprints', 'allowed']],
            ['fill', ['thermal_gap', 0.5], ['thermal_bridge_width', 0.5]],
            ['polygon', ['pts'] + [['xy', rnd(OX + x), rnd(OY + y)] for x, y in pts]]]

def header():
    cu = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
    layers = ['layers', [0, Q('F.Cu'), 'signal'], [4, Q('In1.Cu'), 'power'], [6, Q('In2.Cu'), 'power'], [2, Q('B.Cu'), 'signal'],
              [9, Q('F.Adhes'), 'user', Q('F.Adhesive')], [11, Q('B.Adhes'), 'user', Q('B.Adhesive')],
              [13, Q('F.Paste'), 'user'], [15, Q('B.Paste'), 'user'], [5, Q('F.SilkS'), 'user', Q('F.Silkscreen')],
              [7, Q('B.SilkS'), 'user', Q('B.Silkscreen')], [1, Q('F.Mask'), 'user'], [3, Q('B.Mask'), 'user'],
              [17, Q('Dwgs.User'), 'user', Q('User.Drawings')], [19, Q('Cmts.User'), 'user', Q('User.Comments')],
              [21, Q('Eco1.User'), 'user', Q('User.Eco1')], [23, Q('Eco2.User'), 'user', Q('User.Eco2')],
              [25, Q('Edge.Cuts'), 'user'], [27, Q('Margin'), 'user'], [31, Q('F.CrtYd'), 'user', Q('F.Courtyard')],
              [29, Q('B.CrtYd'), 'user', Q('B.Courtyard')], [35, Q('F.Fab'), 'user'], [33, Q('B.Fab'), 'user']]
    def cul(n): return ['layer', Q(n), ['type', Q('copper')], ['thickness', 0.035]]
    def die(n, t, th): return ['layer', Q(n), ['type', Q(t)], ['thickness', th], ['material', Q('FR4')],
                               ['epsilon_r', 4.4], ['loss_tangent', 0.02]]
    stack = ['stackup',
             ['layer', Q('F.SilkS'), ['type', Q('Top Silk Screen')], ['color', Q('White')]],
             ['layer', Q('F.Paste'), ['type', Q('Top Solder Paste')]],
             ['layer', Q('F.Mask'), ['type', Q('Top Solder Mask')], ['color', Q('Green')], ['thickness', 0.01]],
             cul('F.Cu'), die('dielectric 1', 'prepreg', 0.2), cul('In1.Cu'), die('dielectric 2', 'core', 1.065),
             cul('In2.Cu'), die('dielectric 3', 'prepreg', 0.2), cul('B.Cu'),
             ['layer', Q('B.Mask'), ['type', Q('Bottom Solder Mask')], ['color', Q('Green')], ['thickness', 0.01]],
             ['layer', Q('B.Paste'), ['type', Q('Bottom Solder Paste')]],
             ['layer', Q('B.SilkS'), ['type', Q('Bottom Silk Screen')], ['color', Q('White')]],
             ['copper_finish', Q('ENIG')], ['dielectric_constraints', 'no']]
    setup = ['setup', stack, ['pad_to_mask_clearance', 0], ['allow_soldermask_bridges_in_footprints', 'no'],
             ['tenting', 'front', 'back'], ['aux_axis_origin', OX, OY + H], ['grid_origin', OX, OY + H]]
    return [['version', 20241229], ['generator', Q('pcbnew')], ['generator_version', Q('9.0')],
            ['general', ['thickness', 1.6], ['legacy_teardrops', 'no']], ['paper', Q('A4')],
            ['title_block', ['title', Q('RP2350 Wi-Fi/BLE dev board')], ['date', Q('2026-11-10')], ['rev', Q('A')]],
            layers, setup, ['net', 0, Q('')]] + [['net', NETNO[n], Q(n)] for n in nets]

GEN = set()
def seg(netname, layer, w, a, b, tag):
    u = uid('seg', tag); GEN.add(str(u))
    return ['segment', ['start', rnd(OX + a[0]), rnd(OY + a[1])], ['end', rnd(OX + b[0]), rnd(OY + b[1])],
            ['width', w], ['layer', Q(layer)], ['net', NETNO[netname]], ['uuid', u]]
def via(netname, x, y, tag, size=0.6, drill=0.3):
    u = uid('via', tag); GEN.add(str(u))
    return ['via', ['at', rnd(OX + x), rnd(OY + y)], ['size', size], ['drill', drill], ['layers', Q('F.Cu'), Q('B.Cu')],
            ['net', NETNO[netname]], ['uuid', u]]
def kn(n): return n if n in D.PWR else '/' + n

def rect_dist(px, py, r):
    """distance from point to axis-aligned rect (cx, cy, w, h)"""
    dx = max(abs(px - r[0]) - r[2] / 2, 0); dy = max(abs(py - r[1]) - r[3] / 2, 0)
    return math.hypot(dx, dy)
def seg_dist(px, py, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]; L = vx * vx + vy * vy
    t = 0 if L == 0 else max(0, min(1, ((px - a[0]) * vx + (py - a[1]) * vy) / L))
    return math.hypot(px - a[0] - t * vx, py - a[1] - t * vy)

def generated_copper():
    """manual tracks/vias + automatic plane vias for power pads"""
    out = []; vias = []; segs = []          # vias: (net, x, y)  segs: (net, w, a, b)
    for i, (n, layer, w, pts) in enumerate(D.MAN_TRACKS):
        for j in range(len(pts) - 1):
            out.append(seg(kn(n), layer, w, pts[j], pts[j + 1], 'man%d.%d' % (i, j)))
            if layer != 'B.Cu': segs.append((kn(n), w, pts[j], pts[j + 1]) + ((1,) if layer == 'In2.Cu' else ()))
    for i, (n, x, y) in enumerate(D.MAN_VIAS):
        out.append(via(kn(n), x, y, 'man%d' % i)); vias.append((kn(n), x, y))
    # obstacle model: every pad as rect, with net; holes
    pads = []; holes = []
    for p in D.P:
        lib, name = p['fp'].split(':')
        f = parse(open(f'{S}/footprints/{lib}.pretty/{name}.kicad_mod').read())
        x, y, rot = p['pos']
        for e in findall(f, 'pad'):
            at = find(e, 'at'); sz = find(e, 'size')
            px, py = rot_pt(float(at[1]), float(at[2]), rot)
            a = ((float(at[3]) if len(at) > 3 else 0) + rot) % 180
            w, h = float(sz[1]), float(sz[2])
            if abs(a - 90) < 1: w, h = h, w
            num = str(e[1]); n = netlist.get(p['ref'], {}).get(num)
            if n is None and num in p['extra']: n = p['extra'][num]
            pads.append(dict(ref=p['ref'], num=num, net=n, r=(x + px, y + py, w, h), tht=e[2] != 'smd',
                             lib=name, cx=x, cy=y, back=p['layer'] == 'B'))
    def ok(net_, vx, vy, own):
        if not (0.65 <= vx <= W - 5.4 and 0.65 <= vy <= H - 0.65): return False
        for (x0, y0, x1, y1) in D.VIA_KEEPOUT:
            if x0 - 0.3 < vx < x1 + 0.3 and y0 - 0.3 < vy < y1 + 0.3: return False
        for q in pads:
            if q is own: continue
            d = rect_dist(vx, vy, q['r'])
            if q['tht']:
                if d < 0.3 + 0.25: return False
            elif q['net'] != net_:
                if d < 0.3 + 0.17: return False
            elif d < 0.3 - 0.05 and (q['r'][2] < 0.9 or q['r'][3] < 0.9):
                return False               # do not sit on small same-net pads (via-in-pad)
        for (n2, x2, y2) in vias:
            d = math.hypot(vx - x2, vy - y2)
            if d < (0.62 if n2 == net_ else 0.78): return False
        for sg in segs:
            n2, w2, a, b = sg[:4]
            if n2 != net_ and seg_dist(vx, vy, a, b) < 0.3 + w2 / 2 + 0.17: return False
        return True
    def stub_ok(net_, a, b, w, own):
        for q in pads:
            if q is own or q['net'] == net_ or q['back']: continue
            # sample the stub
            for k in range(7):
                t = k / 6
                if rect_dist(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, q['r']) < w / 2 + 0.16: return False
        for (n2, x2, y2) in vias:
            if n2 != net_ and seg_dist(x2, y2, a, b) < 0.3 + w / 2 + 0.16: return False
        for sg in segs:
            n2, w2, a2, b2 = sg[:4]
            if n2 == net_ or len(sg) > 4: continue
            for k in range(7):
                t = k / 6
                if seg_dist(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a2, b2) < (w + w2) / 2 + 0.16: return False
        return True
    failed = []
    todo = []
    for q in pads:
        if q['net'] not in D.PWR or q['net'] in ('VBUS', 'VBAT', 'VSYS') or q['tht'] or q['back']: continue
        key = (q['ref'], q['num'])
        if key in D.VIA_HINTS: todo.append((0, q, D.VIA_HINTS[key]))
        elif key in D.NO_AUTO_VIA: continue
        elif q['lib'].startswith(('C_0', 'R_0', 'LED_0', 'L_')): todo.append((1, q, None))
    todo.sort(key=lambda t: t[0])
    for _, q, hint in todo:
        px, py, w, h = q['r']; n = q['net']
        sw = min(0.3, w, h)
        if hint:
            cands = [hint]
        else:
            ux, uy = px - q['cx'], py - q['cy']; L = math.hypot(ux, uy) or 1; ux, uy = ux / L, uy / L
            if abs(ux) > abs(uy): ux, uy = (1 if ux > 0 else -1), 0
            else: ux, uy = 0, (1 if uy > 0 else -1)
            ext = (w if ux else h) / 2; side = (h if ux else w) / 2
            cands = []
            for dist in (0.5, 0.75, 1.0):
                cands.append((px + ux * (ext + dist), py + uy * (ext + dist)))
                for sgn in (1, -1):
                    cands.append((px - uy * sgn * (side + dist), py + ux * sgn * (side + dist)))
                    cands.append((px + ux * (ext + dist - 0.2) - uy * sgn * (side + 0.3), py + uy * (ext + dist - 0.2) + ux * sgn * (side + 0.3)))
        for (vx, vy) in cands:
            vx, vy = round(vx, 3), round(vy, 3)
            # reuse an existing same-net via that is close enough
            near = [v for v in vias if v[0] == n and math.hypot(v[1] - vx, v[2] - vy) < 0.62]
            if near:
                vx, vy = near[0][1], near[0][2]
                if stub_ok(n, (px, py), (vx, vy), sw, q):
                    out.append(seg(n, 'F.Cu', sw, (px, py), (vx, vy), 'pv%s.%s' % (q['ref'], q['num'])))
                    segs.append((n, sw, (px, py), (vx, vy))); break
                continue
            if (hint or ok(n, vx, vy, q)) and stub_ok(n, (px, py), (vx, vy), sw, q):
                out.append(via(n, vx, vy, 'pv%s.%s' % (q['ref'], q['num']))); vias.append((n, vx, vy))
                out.append(seg(n, 'F.Cu', sw, (px, py), (vx, vy), 'pv%s.%s' % (q['ref'], q['num'])))
                segs.append((n, sw, (px, py), (vx, vy))); break
        else:
            failed.append(q['ref'] + '.' + q['num'] + ' ' + n)
    if failed: print('  no plane via for:', ', '.join(failed))
    print('  generated copper: %d items, %d vias' % (len(out), len(vias)))
    json.dump(sorted(vias), open(os.path.join(ROOT, 'build', 'vias.json'), 'w'))
    return out

def old_routes():
    if not os.path.exists(PCB) or '--drop-routes' in sys.argv: return []
    e = parse(open(PCB).read())
    keep = []
    for x in e[1:]:
        if isinstance(x, list) and x[0] in ('segment', 'via', 'arc'):
            n = find(x, 'net')
            name = n[-1] if n is not None else None
            if isinstance(name, int) or (isinstance(name, str) and not isinstance(name, Q)):
                continue
            if name not in NETNO: continue
            if str(find(x, 'uuid')[1]) in GEN: continue
            if x[0] == 'segment':
                x = ['segment', find(x, 'start'), find(x, 'end'), find(x, 'width'), find(x, 'layer'), ['net', NETNO[name]], find(x, 'uuid')]
            elif x[0] == 'via':
                x = ['via', find(x, 'at'), find(x, 'size'), find(x, 'drill'), find(x, 'layers'), ['net', NETNO[name]], find(x, 'uuid')]
            else:
                n[:] = ['net', NETNO[name]]
            keep.append(x)
    return keep

def build():
    doc = ['kicad_pcb'] + header()
    for p in D.P:
        doc.append(footprint(p))
    r = 1.0; k = r * (1 - math.sqrt(0.5))
    doc += [gr_line(r, 0, W - r, 0), gr_line(W, r, W, H - r), gr_line(W - r, H, r, H), gr_line(0, H - r, 0, r),
            gr_arc(0, r, k, k, r, 0), gr_arc(W - r, 0, W - k, k, W, r), gr_arc(W, H - r, W - k, H - k, W - r, H),
            gr_arc(r, H, k, H - k, 0, H - r)]
    full = [(0, 0), (W, 0), (W, H), (0, H)]
    ax = W - 5.0
    doc.append(keepout(['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'], [(ax, -0.5), (W + 0.5, -0.5), (W + 0.5, H + 0.5), (ax, H + 0.5)],
                       'RM2 antenna keep-out'))
    doc.append(zone('GND', 'In1.Cu', full, name='GND plane', thermal=False))
    doc.append(zone('+3V3', 'In2.Cu', full, name='3V3 plane', thermal=False))
    if '--pours' in sys.argv:
        doc.append(zone('GND', 'F.Cu', full, name='GND top', island=0))
        doc.append(zone('GND', 'B.Cu', full, name='GND bottom', island=0))
    for z in getattr(D, 'ZONES', []):
        doc.append(zone(z['net'], z['layer'], z['pts'], prio=z.get('prio', 1), name=z['name'], thermal=False))
    for t in getattr(D, 'SILK', []):
        doc.append(gr_text(*t[:3], **(t[3] if len(t) > 3 else {})))
    doc += generated_copper()
    doc += old_routes()
    open(PCB, 'w').write(dump(doc) + '\n')
    print('pcb written:', len(D.P), 'footprints,', len(nets), 'nets')

if __name__ == '__main__':
    build()
