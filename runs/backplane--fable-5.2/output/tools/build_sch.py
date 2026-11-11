#!/usr/bin/env python3
"""Generate the KiCad schematic from design.py."""
import os, sys, uuid, copy, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import parse, dump, find, findall, Q
import design as D

S = '/home/ubuntu/.local/share/backplane/kicad/10.99.0-bp.4/share/kicad'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'boards', D.NAME)
NS = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
def uid(*a): return Q(str(uuid.uuid5(NS, D.NAME + '/' + '/'.join(str(x) for x in a))))
ROOT = uid('root')
G = 1.27
def snap(v): return round(round(v / G) * G, 4)

# ---------------------------------------------------------------- library symbols
_cache = {}
def raw_sym(lib, name):
    if lib == D.NAME:
        e = parse(open(os.path.join(OUT, D.NAME + '.kicad_sym')).read())
    else:
        e = parse(open(f'{S}/symbols/{lib}.kicad_symdir/{name}.kicad_sym').read())
    for s in findall(e, 'symbol'):
        if s[1] == name: return s
    raise KeyError(lib + ':' + name)

def load_sym(lib, name):
    """flattened copy (extends resolved)"""
    key = lib + ':' + name
    if key in _cache: return _cache[key]
    s = copy.deepcopy(raw_sym(lib, name))
    ext = find(s, 'extends')
    if ext:
        par = copy.deepcopy(load_sym(lib, ext[1]))
        pname = par[1]
        par[1] = Q(name)
        for u in findall(par, 'symbol'):
            u[1] = Q(u[1].replace(pname, name, 1))
        for prop in findall(s, 'property'):
            for i, x in enumerate(par):
                if isinstance(x, list) and x[0] == 'property' and x[1] == prop[1]:
                    par[i] = prop; break
            else:
                idx = max(i for i, x in enumerate(par) if isinstance(x, list) and x[0] == 'property')
                par.insert(idx + 1, prop)
        s = par
    _cache[key] = s
    return s

def sym_pins(s):
    out = []
    for u in findall(s, 'symbol'):
        for p in findall(u, 'pin'):
            at = find(p, 'at')
            out.append(dict(num=str(find(p, 'number')[1]), name=str(find(p, 'name')[1]), type=p[1],
                            x=float(at[1]), y=float(at[2]), a=int(float(at[3])), hide=find(p, 'hide') is not None))
    return out

# ---------------------------------------------------------------- output helpers
items = []
libs = {}
FIELDS = {}
pwr_n = [0]
def font(size=1.27, just=None, hide=False):
    e = ['effects', ['font', ['size', size, size]]]
    if just: e.append(['justify'] + just)
    if hide: e.append(['hide', 'yes'])
    return e
def wire(x1, y1, x2, y2):
    items.append(['wire', ['pts', ['xy', x1, y1], ['xy', x2, y2]], ['stroke', ['width', 0], ['type', 'default']],
                  ['uuid', uid('w', x1, y1, x2, y2)]])
def label(name, x, y, ang):
    just = {0: ['left', 'bottom'], 180: ['right', 'bottom'], 90: ['left', 'bottom'], 270: ['right', 'bottom']}[ang]
    items.append(['label', Q(name), ['at', x, y, ang], font(1.27, just), ['uuid', uid('l', name, x, y)]])
def noconn(x, y):
    items.append(['no_connect', ['at', x, y], ['uuid', uid('nc', x, y)]])
def text(t, x, y, size=1.5, bold=False):
    f = ['font', ['size', size, size]]
    if bold: f.append(['bold', 'yes'])
    items.append(['text', Q(t), ['exclude_from_sim', 'no'], ['at', x, y, 0],
                  ['effects', f, ['justify', 'left', 'bottom']], ['uuid', uid('t', t, x, y)]])
def rect(x1, y1, x2, y2):
    items.append(['rectangle', ['start', x1, y1], ['end', x2, y2], ['stroke', ['width', 0.25], ['type', 'dash']],
                  ['fill', ['type', 'none']], ['uuid', uid('r', x1, y1)]])

def place(libid, ref, value, x, y, rot=0, fields=None, fp='', hide_val=False, refpos=None, valpos=None,
          bom=True, board=True):
    lib, name = libid.split(':')
    s = load_sym(lib, name)
    libs[libid] = s
    u = uid('sym', ref)
    e = ['symbol', ['lib_id', Q(libid)], ['at', x, y, rot], ['unit', 1], ['exclude_from_sim', 'no'],
         ['in_bom', 'yes' if bom else 'no'], ['on_board', 'yes' if board else 'no'], ['dnp', 'no'], ['uuid', u]]
    def lp(pn):
        for p in findall(s, 'property'):
            if p[1] == pn:
                a = find(p, 'at'); return float(a[1]), float(a[2]), int(float(a[3]))
        return 0, 0, 0
    def prop(pn, val, pos=None, hide=False, just=None):
        if pos is None:
            px, py, pa = lp(pn); pos = (x + px, y - py, pa)
        e.append(['property', Q(pn), Q(val), ['at', pos[0], pos[1], pos[2] if len(pos) > 2 else 0], font(1.27, just, hide)])
    prop('Reference', ref, refpos, hide=ref.startswith('#'))
    prop('Value', value, valpos, hide=hide_val)
    prop('Footprint', fp, (x, y, 0), hide=True)
    ds = [p for p in findall(s, 'property') if p[1] == 'Datasheet']
    prop('Datasheet', ds[0][2] if ds else '', (x, y, 0), hide=True)
    FIELDS[ref] = {'Datasheet': str(ds[0][2]) if ds else '', 'Description': (fields or {}).get('Description', '')}
    prop('Description', (fields or {}).get('Description', ''), (x, y, 0), hide=True)
    for k, v in (fields or {}).items():
        if k != 'Description' and v: prop(k, v, (x, y, 0), hide=True)
    for p in sym_pins(s):
        e.append(['pin', Q(p['num']), ['uuid', uid('pin', ref, p['num'])]])
    e.append(['instances', ['project', Q(D.NAME), ['path', Q('/' + ROOT), ['reference', Q(ref)], ['unit', 1]]]])
    items.append(e)
    return s

def power(net, x, y):
    pwr_n[0] += 1
    libid = {'GND': 'power:GND', '+3V3': 'power:+3V3', '+1V1': 'power:+1V1', 'VBUS': 'power:VBUS',
             'VBAT': D.NAME + ':VBAT', 'VSYS': D.NAME + ':VSYS'}[net]
    place(libid, '#PWR%03d' % pwr_n[0], net, x, y, bom=False)

flag_n = [0]
def pwr_flag(x, y):
    flag_n[0] += 1
    place('power:PWR_FLAG', '#FLG%02d' % flag_n[0], 'PWR_FLAG', x, y, bom=False)

def pin_xy(sx, sy, rot, p):
    """schematic coords of a pin's connection point and outward direction"""
    dx, dy = p['x'], -p['y']
    ox, oy = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[p['a']]   # outward dir (screen)
    for _ in range(rot // 90):       # CCW on screen: (dx,dy)->(dy,-dx)
        dx, dy = dy, -dx
        ox, oy = oy, -ox
    return snap(sx + dx), snap(sy + dy), ox, oy

def connect(net, x, y, ox, oy, stub=2.54, ptype=''):
    if net is None:
        if ptype != 'no_connect': noconn(x, y)
        return
    if net in D.PWR:
        if (ox, oy) in ((0, -1), (0, 1)) and ((net == 'GND') == (oy == 1)):
            power(net, x, y)
        else:
            ex, ey = x + ox * stub, y + oy * stub
            wire(x, y, ex, ey); power(net, ex, ey)
        return
    ex, ey = snap(x + ox * stub), snap(y + oy * stub)
    wire(x, y, ex, ey)
    label(net, ex, ey, {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[(ox, oy)])

# ---------------------------------------------------------------- place every part
def fields(p):
    f = {'Description': p['desc']}
    if p['mpn']: f['MPN'] = p['mpn']; f['Manufacturer'] = p['mfr']
    if p['lcsc']: f['LCSC'] = p['lcsc']
    return f

for p in D.P:
    sch = p['sch']
    x, y = snap(sch[0]), snap(sch[1])
    lib, name = p['lib'].split(':')
    s = load_sym(lib, name)
    pins = sym_pins(s)
    two = name in ('R', 'C', 'L')
    rot = 0
    kw = {}
    if two and len(sch) > 2 and sch[2] == 'h':
        rot = 90
        kw = dict(refpos=(x - 2.8, y - 1.9, 90), valpos=(x + 2.8, y - 1.9, 90))
    elif two:
        kw = dict(refpos=(x + 1.8, y - 1.2, 0), valpos=(x + 1.8, y + 1.3, 0))
    place(p['lib'], p['ref'], p['value'], x, y, rot, fields(p), p['fp'], bom=p['bom'], **kw)
    if two:
        for it in items[-1]:
            if isinstance(it, list) and it[0] == 'property' and it[1] in ('Reference', 'Value'):
                eff = find(it, 'effects')
                if rot != 90: eff.append(['justify', 'left'])
    seen = {}
    bus = {}
    if not two:
        for pn in pins:
            net = p['nets'].get(pn['num'])
            if net in D.PWR and pn['a'] == 270 and net != 'GND':
                px, py, ox, oy = pin_xy(x, y, rot, pn); bus.setdefault(net, set()).add((px, py))
        bus = {n: sorted(v) for n, v in bus.items() if len(v) > 1}
        for n, pts in bus.items():
            yb = pts[0][1] - 5.08
            for (px, py) in pts: wire(px, py, px, yb)
            for a, b in zip(pts, pts[1:]): wire(a[0], yb, b[0], yb)
            for (px, py) in pts[1:-1]: items.append(['junction', ['at', px, yb], ['diameter', 0], ['color', 0, 0, 0, 0], ['uuid', uid('j', px, yb)]])
            power(n, pts[0][0], yb)
    for pn in pins:
        net = p['nets'].get(pn['num'], 'MISSING')
        if net == 'MISSING':
            raise SystemExit('%s: pin %s (%s) has no net assignment' % (p['ref'], pn['num'], pn['name']))
        px, py, ox, oy = pin_xy(x, y, rot, pn)
        key = (px, py)
        if key in seen:
            if seen[key] != net: raise SystemExit('%s: stacked pins with different nets at %s' % (p['ref'], key))
            continue
        seen[key] = net
        if net in bus and (px, py) in bus[net]: continue
        stub = 1.27 if two else 2.54
        if name in ('LED', 'SW_Push', 'Crystal_GND24', 'TestPoint'): stub = 2.54
        connect(net, px, py, ox, oy, stub, pn['type'])
    extra = set(p['nets']) - {pn['num'] for pn in pins}
    if extra: raise SystemExit('%s: nets given for unknown pins %s' % (p['ref'], extra))

# power flags (nets that are sourced by a connector or through a passive)
fx = 80
for net in ('VBUS', 'GND', '+1V1'):
    X, Y = snap(fx), snap(272)
    pwr_flag(X, Y)
    wire(X, Y, X + 5.08, Y); power(net, X + 5.08, Y)
    fx += 20
X, Y = snap(fx), snap(272)
pwr_flag(X, Y); wire(X, Y, X + 5.08, Y); label('VREG_AVDD', X + 5.08, Y, 0)

for (x1, y1, x2, y2, title) in D.BLOCKS:
    rect(x1, y1, x2, y2); text(title, x1 + 2, y1 + 5, 2.0, True)
for (x, y, t) in getattr(D, 'NOTES', []):
    text(t, x, y, 1.3)

# ---------------------------------------------------------------- write
doc = ['kicad_sch', ['version', 20250114], ['generator', Q('eeschema')], ['generator_version', Q('9.0')],
       ['uuid', ROOT], ['paper', Q('A3')],
       ['title_block', ['title', Q('RP2350 Wi-Fi/BLE dev board')], ['date', Q('2026-11-10')], ['rev', Q('A')],
        ['comment', 1, Q('RP2350A + 16MB flash + 8MB PSRAM + RM2 radio + LiPo charger + microSD + Qwiic')],
        ['comment', 2, Q('Generated from tools/design.py')]]]
ls = ['lib_symbols']
for libid in sorted(libs):
    s = copy.deepcopy(libs[libid]); s[1] = Q(libid); ls.append(s)
doc.append(ls)
doc += items
doc.append(['sheet_instances', ['path', Q('/'), ['page', Q('1')]]])
doc.append(['embedded_fonts', 'no'])
open(os.path.join(OUT, D.NAME + '.kicad_sch'), 'w').write(dump(doc) + '\n')
json.dump(FIELDS, open(os.path.join(OUT, '..', '..', 'build', 'fields.json'), 'w'))
print('schematic written:', len(D.P), 'parts')
