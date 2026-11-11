"""Make a board-edge variant of KiCad's ESP32-C6-MINI-1 footprint.

KiCad's stock footprint draws the full Espressif 'ideal' 15 mm antenna clearance as
courtyard, which cannot be met on a small board. This variant keeps the module
courtyard and adds an all-layer copper keepout under/around the antenna, for
placement with the antenna at the board edge (Espressif placement option)."""
import os, uuid
from sexp import parse, dumps, find, findall, Sym
import kilib
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'boards', 'rp2350-dev', 'lib', 'RP2350_Dev.pretty', 'ESP32-C6-MINI-1_BoardEdge.kicad_mod')

def U():
    return str(uuid.uuid4())

t = kilib.load_footprint('RF_Module:ESP32-C6-MINI-1')
t[1] = 'ESP32-C6-MINI-1_BoardEdge'
new = []
for e in t:
    if isinstance(e, list) and e and e[0] in ('fp_line', 'fp_rect', 'fp_poly'):
        l = find(e, 'layer')
        if l and l[1] == 'F.CrtYd':
            continue
    if isinstance(e, list) and e and e[0] == 'fp_line' and find(e, 'layer')[1] == 'F.SilkS':
        # keep silkscreen 0.3 mm inside the board edge (antenna end sits on the edge)
        for k in ('start', 'end'):
            p = find(e, k)
            if abs(float(p[2]) + 11.15) < 1e-6:
                p[2] = -10.85
    if isinstance(e, list) and e and e[0] == 'zone':
        continue  # drop stock 43 mm wide antenna keepout; replaced below
    if isinstance(e, list) and e and e[0] == 'descr':
        e = [Sym('descr'), 'ESP32-C6-MINI-1, module-only courtyard, antenna copper keepout for board-edge placement (derived from KiCad RF_Module:ESP32-C6-MINI-1)']
    new.append(e)
t = new
x0, x1, y0, y1 = -6.85, 6.85, -11.25, 5.85
crt = [Sym('fp_rect'), [Sym('start'), x0, y0], [Sym('end'), x1, y1],
       [Sym('stroke'), [Sym('width'), 0.05], [Sym('type'), Sym('solid')]], [Sym('fill'), Sym('no')],
       [Sym('layer'), 'F.CrtYd'], [Sym('uuid'), U()]]
# Antenna keepout: module antenna area (y -11.15..-5.6) plus 1 mm each side and 3 mm beyond the edge
kx0, kx1, ky0, ky1 = -7.85, 7.85, -14.25, -5.4
zone = [Sym('zone'), [Sym('net'), 0], [Sym('net_name'), ''], [Sym('layers'), '*.Cu'], [Sym('uuid'), U()],
        [Sym('name'), 'ANT_KEEPOUT'], [Sym('hatch'), Sym('edge'), 0.5],
        [Sym('connect_pads'), [Sym('clearance'), 0]],
        [Sym('min_thickness'), 0.25],
        [Sym('keepout'), [Sym('tracks'), Sym('not_allowed')], [Sym('vias'), Sym('not_allowed')],
         [Sym('pads'), Sym('not_allowed')], [Sym('copperpour'), Sym('not_allowed')],
         [Sym('footprints'), Sym('allowed')]],
        [Sym('placement'), [Sym('enabled'), Sym('no')], [Sym('sheetname'), '']],
        [Sym('fill'), [Sym('thermal_gap'), 0.5], [Sym('thermal_bridge_width'), 0.5]],
        [Sym('polygon'), [Sym('pts'), [Sym('xy'), kx0, ky0], [Sym('xy'), kx1, ky0], [Sym('xy'), kx1, ky1], [Sym('xy'), kx0, ky1]]]]
# insert before first pad
idx = next(i for i, e in enumerate(t) if isinstance(e, list) and e and e[0] == 'pad')
t[idx:idx] = [crt]
# zones go after pads (KiCad order: ... pads, zones, embedded, model)
idx2 = max(i for i, e in enumerate(t) if isinstance(e, list) and e and e[0] == 'pad') + 1
t[idx2:idx2] = [zone]
open(OUT, 'w').write(dumps(t) + '\n')
print('ok')
