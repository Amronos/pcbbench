"""Specctra DSN export from our .kicad_pcb and SES import back to KiCad segments/vias.

Usage:
  python3 dsn.py export board.kicad_pcb out.dsn
  python3 dsn.py import board.kicad_pcb in.ses out_routes.sexp
"""
import sys, math, re, os
from sexp import parse, dumps, Sym, find, findall
from gen_pcb import xform

SIG_LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']
PLANE_NETS = {'In1.Cu': 'GND', 'In2.Cu': '+3V3'}

# net classes: (name, width_mm, clearance_mm, nets)
POWER_W = {'VBUS': 0.4, 'VSYS': 0.4, 'VBAT': 0.4, '+3V3': 0.3, 'GND': 0.3, '+1V1': 0.3,
           'VREG_LX': 0.4, 'USB_DP': 0.25, 'USB_DM': 0.25, 'USB_DP_MCU': 0.25, 'USB_DM_MCU': 0.25}
DEFAULT_W = 0.15
# router-only keepouts inside IC bodies (protect the copied RPi under-chip rings)
BODY_KEEPOUT = {'U4': 2.75}
CLEARANCE = 0.15
VIA_D, VIA_DRILL = 0.6, 0.3


def um(v):
    return round(v * 1000.0, 1)


def fmt(v):
    s = ('%.1f' % v)
    return s[:-2] if s.endswith('.0') else s


def q(s):
    return '"' + s.replace('"', '') + '"'


def pad_shapes(p, absrot, layers):
    """Return list of DSN shape strings (in pad-local coords, absolute orientation)."""
    shape = str(p[3])
    w, h = float(find(p, 'size')[1]), float(find(p, 'size')[2])
    out = []
    a = absrot % 360
    if shape == 'circle':
        for L in layers:
            out.append('(circle %s %s)' % (L, fmt(um(w))))
        return out
    if shape == 'oval':
        # stadium: path along long axis
        if w >= h:
            dx, dy, wd = (w - h) / 2, 0, h
        else:
            dx, dy, wd = 0, (h - w) / 2, w
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        x0, y0 = dx * c + dy * s, -dx * s + dy * c
        for L in layers:
            out.append('(path %s %s %s %s %s %s)' % (L, fmt(um(wd)), fmt(um(-x0)), fmt(um(y0)), fmt(um(x0)), fmt(um(-y0))))
        return out
    # rect / roundrect / trapezoid / custom: use rotated rectangle polygon
    if shape == 'custom':
        # use the primitives' bounding box together with the anchor
        prims = find(p, 'primitives')
        xs, ys = [-w / 2, w / 2], [-h / 2, h / 2]
        if prims:
            for g in prims[1:]:
                for pt in (find(g, 'pts') or [])[1:]:
                    xs.append(float(pt[1])); ys.append(float(pt[2]))
        corners = [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]
    else:
        corners = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    if a % 90 == 0:
        rx = [xform(x, y, 0, 0, a) for x, y in corners]
        xs = [c[0] for c in rx]; ys = [c[1] for c in rx]
        for L in layers:
            out.append('(rect %s %s %s %s %s)' % (L, fmt(um(min(xs))), fmt(um(-max(ys))), fmt(um(max(xs))), fmt(um(-min(ys)))))
    else:
        rx = [xform(x, y, 0, 0, a) for x, y in corners]
        pts = ' '.join('%s %s' % (fmt(um(x)), fmt(um(-y))) for x, y in rx)
        for L in layers:
            out.append('(polygon %s 0 %s)' % (L, pts))
    return out


def pad_layers(p, fp_side):
    ls = list(find(p, 'layers')[1:])
    if any(l in ('*.Cu', 'F&B.Cu') for l in ls) or find(p, 'drill') is not None and str(p[2]) == 'thru_hole':
        return list(SIG_LAYERS)
    return [l for l in ls if l in SIG_LAYERS]


def fp_pose(fp):
    at = find(fp, 'at')
    if at is not None:
        return float(at[1]), float(at[2]), (float(at[3]) if len(at) > 3 else 0.0)
    tr = find(fp, 'transform')
    t = find(tr, 'translate'); r = find(tr, 'rotate')
    return float(t[1]), float(t[2]), (float(r[1]) if r else 0.0)


def zone_layers(z):
    l = find(z, 'layer')
    ls = [l[1]] if l else list(find(z, 'layers')[1:])
    if any('*' in x for x in ls):
        return ['signal']
    return [x for x in ls if x in SIG_LAYERS]


def export(pcb_path, dsn_path):
    t = parse(open(pcb_path).read())
    lines = []
    padstacks = {}
    images = []
    places = []
    nets = {}
    # outline bbox from Edge.Cuts
    xs, ys = [], []
    for g in findall(t, 'gr_line') + findall(t, 'gr_arc'):
        if find(g, 'layer')[1] == 'Edge.Cuts':
            for k in ('start', 'end'):
                xs.append(float(find(g, k)[1])); ys.append(float(find(g, k)[2]))
    bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
    for fp in findall(t, 'footprint'):
        ref = [p[2] for p in findall(fp, 'property') if p[1] == 'Reference'][0]
        X, Y, R = fp_pose(fp)
        side = find(fp, 'layer')[1]
        img = 'IMG_' + ref
        pins = []
        seen = {}
        for p in findall(fp, 'pad'):
            if str(p[2]) == 'np_thru_hole':
                # mechanical hole -> keepout
                pat = find(p, 'at')
                hx, hy = xform(float(pat[1]), float(pat[2]), X, Y, R)
                d = float(find(p, 'size')[1])
                pins.append(('keepout', hx - X, hy - Y, d))
                continue
            num = p[1]
            if num == '' and not any('Cu' in str(l) for l in find(p, 'layers')[1:]):
                continue  # paste-only aperture
            if num == '':
                # unnumbered copper pad (fiducial): keep the router out of it
                pat = find(p, 'at')
                hx, hy = xform(float(pat[1]), float(pat[2]), X, Y, R)
                d = float(find(p, 'size')[1])
                pins.append(('keepout', hx - X, hy - Y, d + 1.0))
                continue
            pat = find(p, 'at')
            lx, ly = float(pat[1]), float(pat[2])
            absrot = float(pat[3]) if len(pat) > 3 else 0.0
            ax, ay = xform(lx, ly, X, Y, R)
            layers = pad_layers(p, side)
            if not layers:
                continue
            shapes = pad_shapes(p, absrot, layers)
            key = ' '.join(shapes)
            if key not in padstacks:
                padstacks[key] = 'PS%d' % len(padstacks)
            ps = padstacks[key]
            n = seen.get(num, 0)
            seen[num] = n + 1
            pid = num if n == 0 else '%s@%d' % (num, n)
            pins.append((ps, ax - X, ay - Y, pid))
            netn = find(p, 'net')
            if netn is not None and netn[1] and not netn[1].startswith('unconnected-'):
                nets.setdefault(netn[1], []).append('%s-%s' % (ref, pid))
        # footprint keepout zones (absolute coords)
        kos = []
        local = find(fp, 'transform') is not None
        for z in findall(fp, 'zone'):
            if find(z, 'keepout') is not None:
                pts = [(float(a[1]), float(a[2])) for a in find(find(z, 'polygon'), 'pts')[1:]]
                if local:
                    pts = [xform(x, y, X, Y, R) for x, y in pts]
                kos.append((zone_layers(z), pts))
        if ref in BODY_KEEPOUT:
            hw = BODY_KEEPOUT[ref]
            kos.append((['signal'], [xform(x, y, X, Y, R) for x, y in [(-hw, -hw), (hw, -hw), (hw, hw), (-hw, hw)]]))
        images.append((img, pins))
        places.append((ref, img, X, Y, kos))
    # board-level zones
    planes = []
    keepouts = []
    fixed_polys = []
    for z in findall(t, 'zone'):
        pts = [(float(a[1]), float(a[2])) for a in find(find(z, 'polygon'), 'pts')[1:]]
        if find(z, 'keepout') is not None:
            keepouts.append((zone_layers(z), pts))
            continue
        layer = find(z, 'layer')
        layer = layer[1] if layer else None
        net = find(z, 'net')[1]
        nm = find(z, 'name')
        nm = nm[1] if nm else ''
        if layer in PLANE_NETS and PLANE_NETS[layer] == net:
            planes.append((net, layer, pts))
        elif nm.startswith('RPi_') and net not in PLANE_NETS.values():
            fills = findall(z, 'filled_polygon')
            if not fills:
                print('WARNING: zone %s not filled; skipping' % nm)
            for fpoly in fills:
                fpts = [(float(a[1]), float(a[2])) for a in find(fpoly, 'pts')[1:] if a[0] == 'xy']
                fixed_polys.append((net, find(fpoly, 'layer')[1], fpts))
    for ref, img, X, Y, kos in places:
        keepouts.extend(kos)
    # thin keepout strips along the outline so routes keep the 0.25 mm copper-to-edge rule
    e = 0.15
    for pts in ([(bx0, by0), (bx1, by0), (bx1, by0 + e), (bx0, by0 + e)],
                [(bx0, by1 - e), (bx1, by1 - e), (bx1, by1), (bx0, by1)],
                [(bx0, by0), (bx0 + e, by0), (bx0 + e, by1), (bx0, by1)],
                [(bx1 - e, by0), (bx1, by0), (bx1, by1), (bx1 - e, by1)]):
        keepouts.append((['signal'], pts))
    # wiring (existing copper)
    wires = []
    import json as _json
    fixed = set(_json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixed_uuids.json'))))
    for s in findall(t, 'segment'):
        st, en = find(s, 'start'), find(s, 'end')
        typ = 'protect' if find(s, 'uuid')[1] in fixed else 'route'
        wires.append('(wire (path %s %s %s %s %s %s) (net %s) (type %s))' % (
            find(s, 'layer')[1], fmt(um(float(find(s, 'width')[1]))), fmt(um(float(st[1]))), fmt(um(-float(st[2]))),
            fmt(um(float(en[1]))), fmt(um(-float(en[2]))), q(find(s, 'net')[1]), typ))
    vias_fixed = []
    for v in findall(t, 'via'):
        at = find(v, 'at')
        d = float(find(v, 'size')[1]); dr = float(find(v, 'drill')[1])
        vname = 'VIA_%d_%d' % (round(d * 1000), round(dr * 1000))
        vias_fixed.append((vname, d, float(at[1]), float(at[2]), find(v, 'net')[1],
                           'protect' if find(v, 'uuid')[1] in fixed else 'route'))
    for net, layer, pts in fixed_polys:
        wires.append('(wire (poly %s 0 %s) (net %s) (type protect))' % (
            layer, ' '.join('%s %s' % (fmt(um(x)), fmt(um(-y))) for x, y in pts + [pts[0]]), q(net)))

    o = []
    o.append('(pcb %s' % q(pcb_path.split('/')[-1]))
    o.append('  (parser (string_quote ") (space_in_quoted_tokens on) (host_cad "KiCad") (host_version "10"))')
    o.append('  (resolution um 10)')
    o.append('  (unit um)')
    o.append('  (structure')
    for i, L in enumerate(SIG_LAYERS):
        typ = os.environ.get('PLANE_TYPE', 'signal') if L in PLANE_NETS else 'signal'
        o.append('    (layer %s (type %s) (property (index %d)))' % (L, typ, i))
    o.append('    (boundary (path pcb 0 %s %s %s %s %s %s %s %s %s %s))' % (
        fmt(um(bx0)), fmt(um(-by0)), fmt(um(bx1)), fmt(um(-by0)), fmt(um(bx1)), fmt(um(-by1)),
        fmt(um(bx0)), fmt(um(-by1)), fmt(um(bx0)), fmt(um(-by0))))
    for net, layer, pts in planes:
        o.append('    (plane %s (polygon %s 0 %s))' % (q(net), layer, ' '.join('%s %s' % (fmt(um(x)), fmt(um(-y))) for x, y in pts)))
    for lays, pts in keepouts:
        P = ' '.join('%s %s' % (fmt(um(x)), fmt(um(-y))) for x, y in pts)
        for L in lays:
            o.append('    (keepout "" (polygon %s 0 %s))' % (L, P))
        o.append('    (via_keepout "" (polygon %s 0 %s))' % ('signal' if (lays == ['signal'] or len(lays) > 1) else lays[0], P))
    vname = 'VIA_%d_%d' % (round(VIA_D * 1000), round(VIA_DRILL * 1000))
    o.append('    (via %s)' % vname)
    o.append('    (rule (width %s) (clearance %s) (clearance %s (type default_smd)) (clearance %s (type smd_smd)))' % (
        fmt(um(DEFAULT_W)), fmt(um(CLEARANCE)), fmt(um(CLEARANCE)), fmt(um(CLEARANCE))))
    o.append('  )')
    o.append('  (placement')
    for ref, img, X, Y, kos in places:
        o.append('    (component %s (place %s %s %s front 0))' % (img, q(ref), fmt(um(X)), fmt(um(-Y))))
    o.append('  )')
    o.append('  (library')
    for img, pins in images:
        o.append('    (image %s' % img)
        for pin in pins:
            if pin[0] == 'keepout':
                _, x, y, d = pin
                o.append('      (keepout "" (circle signal %s %s %s))' % (fmt(um(d + 0.2)), fmt(um(x)), fmt(um(-y))))
            else:
                ps, x, y, pid = pin
                o.append('      (pin %s %s %s %s)' % (ps, q(pid), fmt(um(x)), fmt(um(-y))))
        o.append('    )')
    for key, name in padstacks.items():
        o.append('    (padstack %s' % name)
        for sh in key.split(') ('):
            sh = sh.strip()
            if not sh.startswith('('):
                sh = '(' + sh
            if not sh.endswith(')'):
                sh = sh + ')'
            o.append('      (shape %s)' % sh)
        o.append('      (attach off))')
    vias = {vname: VIA_D}
    for vn, d, x, y, net, _t in vias_fixed:
        vias[vn] = d
    for vn, d in vias.items():
        o.append('    (padstack %s' % vn)
        for L in SIG_LAYERS:
            o.append('      (shape (circle %s %s))' % (L, fmt(um(d))))
        o.append('      (attach off))')
    o.append('  )')
    o.append('  (network')
    for net, pins in sorted(nets.items()):
        o.append('    (net %s (pins %s))' % (q(net), ' '.join(pins)))
    # classes
    classes = {}
    for net in nets:
        w = POWER_W.get(net, DEFAULT_W)
        classes.setdefault(w, []).append(net)
    plane_nets = set(PLANE_NETS.values())
    classes = {}
    for net in nets:
        w = POWER_W.get(net, DEFAULT_W)
        classes.setdefault((w, net in plane_nets), []).append(net)
    for i, ((w, isplane), ns) in enumerate(sorted(classes.items())):
        layers = '' if isplane or os.environ.get('INNER_ROUTING') else ' (use_layer F.Cu B.Cu)'
        o.append('    (class C%d %s (circuit (use_via %s)%s) (rule (width %s) (clearance %s)))' % (
            i, ' '.join(q(n) for n in ns), vname, layers, fmt(um(w)), fmt(um(CLEARANCE))))
    o.append('  )')
    o.append('  (wiring')
    for w in wires:
        o.append('    ' + w)
    for vn, d, x, y, net, typ in vias_fixed:
        o.append('    (via %s %s %s (net %s) (type %s))' % (vn, fmt(um(x)), fmt(um(-y)), q(net), typ))
    o.append('  )')
    o.append(')')
    open(dsn_path, 'w').write('\n'.join(o) + '\n')
    print('DSN written: %d components, %d nets, %d padstacks, %d fixed wires' % (len(places), len(nets), len(padstacks), len(wires)))


def import_ses(pcb_path, ses_path, out_path):
    t = parse(open(pcb_path).read())
    import json as _json
    fixed = set(_json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixed_uuids.json'))))
    existing = set()
    for s in findall(t, 'segment'):
        if find(s, 'uuid')[1] not in fixed:
            continue
        st, en = find(s, 'start'), find(s, 'end')
        a = (round(float(st[1]), 3), round(float(st[2]), 3)); b = (round(float(en[1]), 3), round(float(en[2]), 3))
        existing.add((find(s, 'layer')[1], a, b)); existing.add((find(s, 'layer')[1], b, a))
    exvias = set((round(float(find(v, 'at')[1]), 3), round(float(find(v, 'at')[2]), 3)) for v in findall(t, 'via')
                 if find(v, 'uuid')[1] in fixed)
    txt = open(ses_path).read()
    s = parse(txt)
    routes = find(s, 'routes')
    res = find(routes, 'resolution')
    scale = float(res[2])  # units per um
    def mm(v):
        return float(v) / scale / 1000.0
    out = []
    nseg = nvia = 0
    import uuid
    for net in findall(find(routes, 'network_out'), 'net'):
        name = net[1]
        for w in findall(net, 'wire'):
            p = find(w, 'path')
            if p is None:
                continue
            layer = p[1]; width = mm(p[2])
            coords = [float(v) for v in p[3:]]
            pts = [(mm(coords[i]), -mm(coords[i + 1])) for i in range(0, len(coords), 2)]
            for a, b in zip(pts, pts[1:]):
                ka = (round(a[0], 3), round(a[1], 3)); kb = (round(b[0], 3), round(b[1], 3))
                if (layer, ka, kb) in existing or ka == kb:
                    continue
                out.append([Sym('segment'), [Sym('start'), round(a[0], 4), round(a[1], 4)],
                            [Sym('end'), round(b[0], 4), round(b[1], 4)], [Sym('width'), round(width, 4)],
                            [Sym('layer'), layer], [Sym('net'), name], [Sym('uuid'), str(uuid.uuid4())]])
                nseg += 1
        for v in findall(net, 'via'):
            vn = v[1]
            x, y = mm(v[2]), -mm(v[3])
            if (round(x, 3), round(y, 3)) in exvias:
                continue
            m = re.match(r'VIA_(\d+)_(\d+)', vn)
            d, dr = (int(m.group(1)) / 1000.0, int(m.group(2)) / 1000.0) if m else (VIA_D, VIA_DRILL)
            out.append([Sym('via'), [Sym('at'), round(x, 4), round(y, 4)], [Sym('size'), d], [Sym('drill'), dr],
                        [Sym('layers'), 'F.Cu', 'B.Cu'], [Sym('net'), name], [Sym('uuid'), str(uuid.uuid4())]])
            nvia += 1
    open(out_path, 'w').write('\n'.join(dumps(e) for e in out) + '\n')
    print('imported %d segments, %d vias' % (nseg, nvia))


if __name__ == '__main__':
    if sys.argv[1] == 'export':
        export(sys.argv[2], sys.argv[3])
    else:
        import_ses(sys.argv[2], sys.argv[3], sys.argv[4])
