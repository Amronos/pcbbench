#!/usr/bin/env python3
"""Grid maze router (A*, F.Cu + B.Cu) that finishes whatever is still unconnected.
Reads the saved board, routes the DRC ratsnest one connection at a time, appends tracks/vias."""
import sys, os, json, math, heapq, subprocess, uuid, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv_saved = sys.argv; sys.argv = sys.argv[:1]
import numpy as np
from sexpr import parse, find, findall, Q
import design as D
import build_pcb as BP
K = '/home/ubuntu/pcbbench-hub/bin/kicad-cli'
PCB = BP.PCB
G = 0.05
NX, NY = int(round(D.W / G)) + 1, int(round(D.H / G)) + 1
CLR = 0.15
WIDE = {'VBUS': 0.4, 'VBAT': 0.4, 'VSYS': 0.4, '+3V3': 0.25, 'GND': 0.25, '+1V1': 0.25}
S = BP.S

def pad_model():
    pads = []
    for p in D.P:
        lib, name = p['fp'].split(':')
        f = parse(open(f'{S}/footprints/{lib}.pretty/{name}.kicad_mod').read())
        x, y, rot = p['pos']
        for e in findall(f, 'pad'):
            at = find(e, 'at'); sz = find(e, 'size')
            px, py = BP.rot_pt(float(at[1]), float(at[2]), rot)
            a = ((float(at[3]) if len(at) > 3 else 0) + rot) % 180
            w, h = float(sz[1]), float(sz[2])
            if abs(a - 90) < 1: w, h = h, w
            num = str(e[1]); n = BP.netlist.get(p['ref'], {}).get(num)
            if e[2] == 'np_thru_hole': n = '<npth>'
            layers = 'FB' if e[2] != 'smd' else ('B' if p['layer'] == 'B' else 'F')
            pads.append((n, (x + px, y + py, w, h), layers))
    return pads

def board_copper():
    e = parse(open(PCB).read())
    segs, vias = [], []
    for x in e[1:]:
        if not isinstance(x, list): continue
        if x[0] == 'segment':
            s, t = find(x, 'start'), find(x, 'end')
            segs.append((str(find(x, 'net')[-1]), (float(s[1]) - D.OX, float(s[2]) - D.OY),
                         (float(t[1]) - D.OX, float(t[2]) - D.OY), float(find(x, 'width')[1]),
                         {'F.Cu': 'F', 'B.Cu': 'B'}.get(str(find(x, 'layer')[1]), 'I')))
        elif x[0] == 'via':
            a = find(x, 'at'); vias.append((str(find(x, 'net')[-1]), float(a[1]) - D.OX, float(a[2]) - D.OY))
    return segs, vias

def box(x0, y0, x1, y1):
    return (max(0, int(math.floor(x0 / G))), max(0, int(math.floor(y0 / G))),
            min(NX, int(math.ceil(x1 / G)) + 1), min(NY, int(math.ceil(y1 / G)) + 1))

def mark_rect(a, r, m):
    i0, j0, i1, j1 = box(r[0] - r[2] / 2 - m, r[1] - r[3] / 2 - m, r[0] + r[2] / 2 + m, r[1] + r[3] / 2 + m)
    if i1 <= i0 or j1 <= j0: return
    xs = np.arange(i0, i1) * G; ys = np.arange(j0, j1) * G
    dx = np.maximum(np.abs(xs - r[0]) - r[2] / 2, 0)[None, :]; dy = np.maximum(np.abs(ys - r[1]) - r[3] / 2, 0)[:, None]
    a[j0:j1, i0:i1] |= (dx * dx + dy * dy) < m * m

def mark_seg(a, p, q, m):
    i0, j0, i1, j1 = box(min(p[0], q[0]) - m, min(p[1], q[1]) - m, max(p[0], q[0]) + m, max(p[1], q[1]) + m)
    if i1 <= i0 or j1 <= j0: return
    xs = (np.arange(i0, i1) * G)[None, :]; ys = (np.arange(j0, j1) * G)[:, None]
    vx, vy = q[0] - p[0], q[1] - p[1]; L = vx * vx + vy * vy
    t = np.clip(((xs - p[0]) * vx + (ys - p[1]) * vy) / L, 0, 1) if L > 0 else 0
    d2 = (xs - p[0] - t * vx) ** 2 + (ys - p[1] - t * vy) ** 2
    a[j0:j1, i0:i1] |= d2 < m * m

class Board:
    def __init__(self):
        self.pads = pad_model(); self.segs, self.vias = board_copper()
    def grids(self, net, w):
        """blocked[layer] for tracks of width w, and via-forbidden map"""
        tm = CLR + w / 2 + 0.04; vm = CLR + 0.3 + 0.04
        blk = {l: np.zeros((NY, NX), bool) for l in 'FB'}; vb = np.zeros((NY, NX), bool)
        em = 0.3 + w / 2
        for a in (blk['F'], blk['B'], vb):
            e = int(round((0.3 + 0.3) / G)) if a is vb else int(round(em / G))
            a[:e, :] = True; a[-e:, :] = True; a[:, :e] = True; a[:, int((D.W - 5.0) / G) - e:] = True
        for (n, r, layers) in self.pads:
            if n == net: continue
            for l in layers: mark_rect(blk[l], r, tm)
            mark_rect(vb, r, vm + (0.1 if layers == 'FB' else 0))
        for (n, p, q, sw, l) in self.segs:
            if l == 'I':
                if n != net: mark_seg(vb, p, q, vm + sw / 2)
                continue
            if n == net: continue
            mark_seg(blk[l], p, q, tm + sw / 2); mark_seg(vb, p, q, vm + sw / 2)
        for (n, x, y) in self.vias:
            if n == net:
                mark_seg(vb, (x, y), (x, y), 0.6 + 0.02)      # keep new vias off existing same-net vias
                continue
            for l in 'FB': mark_seg(blk[l], (x, y), (x, y), tm + 0.3)
            mark_seg(vb, (x, y), (x, y), 0.3 + 0.3 + 0.25 + 0.02)
        for (x0, y0, x1, y1) in getattr(D, 'MAZE_NO_VIA', []):
            i0, j0, i1, j1 = box(x0, y0, x1, y1); vb[j0:j1, i0:i1] = True
        vb |= blk['F'] | blk['B']
        own = {l: np.zeros((NY, NX), bool) for l in 'FB'}
        for (n, r, layers) in self.pads:
            if n == net:
                for l in layers: mark_rect(own[l], (r[0], r[1], 0.02, 0.02), 0.06)
        for (n, p, q, sw, l) in self.segs:
            if n == net and l != 'I': mark_seg(own[l], p, q, 0.06)
        ownv = [(int(round(x / G)), int(round(y / G))) for (n, x, y) in self.vias if n == net]
        for (i, j) in ownv:
            for l in 'FB': own[l][j, i] = True
        return blk, vb, own, set(ownv)

    def route(self, net, src, dst, w):
        """src/dst: (x, y, layers). returns list of (layer, [(x,y)...]) and new vias, or None"""
        blk, vb, own, ownv = self.grids(net, w)
        LI = {'F': 0, 'B': 1}
        B = [blk['F'], blk['B']]; O = [own['F'], own['B']]
        si, sj = int(round(src[0] / G)), int(round(src[1] / G)); ti, tj = int(round(dst[0] / G)), int(round(dst[1] / G))
        goals = {(ti, tj, LI[l]) for l in dst[2]}
        for l in dst[2]: O[LI[l]][tj, ti] = True
        for l in src[2]: O[LI[l]][sj, si] = True
        heap = []; g = {}; par = {}
        for l in src[2]:
            s = (si, sj, LI[l]); g[s] = 0; heapq.heappush(heap, (0, 0, s))
        VIA = int(1.6 / G); R2 = math.sqrt(2)
        def h(i, j):
            dx, dy = abs(i - ti), abs(j - tj); return max(dx, dy) + 0.414 * min(dx, dy)
        found = None; cnt = 0
        while heap:
            f, gc, s = heapq.heappop(heap)
            if gc > g.get(s, 1e18): continue
            if s in goals: found = s; break
            cnt += 1
            if cnt > 20000000:
                print('    (search limit)'); break
            i, j, l = s
            for di, dj, c in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, R2), (1, -1, R2), (-1, 1, R2), (-1, -1, R2)):
                a, b = i + di, j + dj
                if a < 0 or b < 0 or a >= NX or b >= NY: continue
                if O[l][b, a] and O[l][j, i]: c *= 0.05      # travelling on own copper is nearly free
                elif B[l][b, a] or B[l][j, i]: continue
                elif di and dj and (B[l][j, a] or B[l][b, i]): continue
                n = (a, b, l); ng = gc + c
                if ng < g.get(n, 1e18):
                    g[n] = ng; par[n] = s; heapq.heappush(heap, (ng + h(a, b), ng, n))
            n = (i, j, 1 - l)
            if (i, j) in ownv: c = 0.1
            elif not vb[j, i] and not B[1 - l][j, i] and not B[l][j, i]: c = VIA
            else: c = None
            if c is not None:
                ng = gc + c
                if ng < g.get(n, 1e18):
                    g[n] = ng; par[n] = s; heapq.heappush(heap, (ng + h(i, j), ng, n))
        if not found: return None
        path = [found]
        while path[-1] in par: path.append(par[path[-1]])
        path.reverse()
        tracks = []; newv = []; cur = [path[0]]
        for a, b in zip(path, path[1:]):
            if a[2] != b[2]:
                if (a[0], a[1]) not in ownv: newv.append((a[0] * G, a[1] * G))
                if len(cur) > 1: tracks.append(cur)
                cur = [b]
            elif O[a[2]][a[1], a[0]] and O[b[2]][b[1], b[0]]:
                if len(cur) > 1: tracks.append(cur)
                cur = [b]
            else: cur.append(b)
        if len(cur) > 1: tracks.append(cur)
        out = []
        for t in tracks:
            l = 'FB'[t[0][2]]
            # drop the parts that run on existing own copper, simplify collinear points
            pts = [(c[0], c[1]) for c in t]
            keep = [pts[0]]
            for k in range(1, len(pts) - 1):
                d1 = (pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]); d2 = (pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
                if d1 != d2: keep.append(pts[k])
            keep.append(pts[-1])
            out.append((l, [(round(i * G, 3), round(j * G, 3)) for i, j in keep]))
        return out, newv

def unconnected():
    subprocess.run([K, 'pcb', 'drc', '--format', 'json', '--severity-error', '--refill-zones', '--save-board', '-o', '/tmp/mz.json', PCB],
                   capture_output=True)
    j = json.load(open('/tmp/mz.json')); res = []
    for v in j.get('unconnected_items', []):
        it = []
        for i in v['items']:
            d = i['description']; m = re.search(r'\[([^\]]+)\]', d)
            lay = 'FB' if ('PTH' in d or d.startswith('Via')) else ('B' if 'on B.Cu' in d else 'F')
            it.append((m.group(1), i['pos']['x'] - D.OX, i['pos']['y'] - D.OY, lay))
        res.append(it)
    return res, [v for v in j.get('violations', [])]

def main():
    pf = os.path.join(BP.ROOT, 'build', 'prio.json')
    prio = json.load(open(pf)) if os.path.exists(pf) else []
    failed_nets = []
    done_fail = set()
    for rnd in range(25):
        unc, _ = unconnected()
        unc = [u for u in unc if (u[0][0], round(u[0][1], 2), round(u[0][2], 2), round(u[1][1], 2), round(u[1][2], 2)) not in done_fail]
        if not unc: break
        unc.sort(key=lambda u: (prio.index(u[0][0]) if u[0][0] in prio else 999, min(math.hypot(u[k][1] - D.MX, u[k][2] - D.MY) for k in (0, 1)) > 4.5, math.hypot(u[0][1] - u[1][1], u[0][2] - u[1][2])))
        bd = Board(); add = []; touched = set()
        for u in unc:
            net = u[0][0]
            if net in touched: continue          # one connection per net per round (ratsnest changes)
            touched.add(net)
            w = WIDE.get(net, 0.15)
            r = bd.route(net, (u[0][1], u[0][2], u[0][3]), (u[1][1], u[1][2], u[1][3]), w)
            if r is None and w > 0.25:
                w = 0.25; r = bd.route(net, (u[0][1], u[0][2], u[0][3]), (u[1][1], u[1][2], u[1][3]), w)
            key = (net, round(u[0][1], 2), round(u[0][2], 2), round(u[1][1], 2), round(u[1][2], 2))
            if r is None:
                print('  FAILED', net, u); done_fail.add(key)
                if net not in failed_nets: failed_nets.append(net)
                continue
            tracks, newv = r; L = 0
            for l, pts in tracks:
                for a, b in zip(pts, pts[1:]):
                    bd.segs.append((net, a, b, w, l)); L += math.hypot(a[0] - b[0], a[1] - b[1])
                    add.append('\t(segment (start %.4f %.4f) (end %.4f %.4f) (width %.3f) (layer "%s") (net "%s") (uuid "%s"))' % (
                        a[0] + D.OX, a[1] + D.OY, b[0] + D.OX, b[1] + D.OY, w, 'F.Cu' if l == 'F' else 'B.Cu', net, uuid.uuid4()))
            for (x, y) in newv:
                bd.vias.append((net, x, y))
                add.append('\t(via (at %.4f %.4f) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "%s") (uuid "%s"))' % (
                    x + D.OX, y + D.OY, net, uuid.uuid4()))
            print('  routed %-12s %.1f mm, %d vias' % (net, L, len(newv)), flush=True)
        t = open(PCB).read().rstrip()
        assert t.endswith(')')
        open(PCB, 'w').write(t[:-1].rstrip() + '\n' + '\n'.join(add) + '\n)\n')
        print('round', rnd, 'added', len(add), 'items')
    unc, viol = unconnected()
    print('remaining unconnected:', len(unc), ' drc errors:', len(viol))
    json.dump([n for n in failed_nets if n not in prio] + prio, open(pf, 'w'))
    sys.exit(0 if not unc else 3)

if __name__ == '__main__':
    main()
