"""Generate the KiCad PCB (placement, nets, zones, outline, RPi core copy) from design.py."""
import os, math, uuid, copy, sys, json
from sexp import parse, dumps, Sym, find, findall
import kilib, design
from gen_sch import uid, SHEET_UUID, ROOT_UUID

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.join(HERE, '..', 'boards', design.PROJECT)
PCB_PATH = os.path.join(BOARD_DIR, design.PROJECT + '.kicad_pcb')
RPI_PCB = os.path.join(HERE, '..', 'third_party', 'RPi-RP2350A-Minimal', 'RPI-RP2350A-MINIMAL_R4-S1.kicad_pcb')

OX, OY = 100.0, 100.0         # board origin (top-left) in page coordinates
BW, BH = 80.0, 38.0           # board size
CORNER_R = 1.5

# ---------------------------------------------------------------- placement
U4X, U4Y = 40.0, 16.0          # RP2350 centre (board-local)

PLACE = {
    # ref: (x, y, rot, side)   board-local mm, rot in degrees CCW
    # --- USB-C, ESD, CC
    'J1': (3.675, 8.5, 270, 'F'),
    'U1': (11.4, 8.5, 180, 'F'),
    'R1': (10.0, 5.6, 0, 'F'),
    'R2': (10.0, 11.4, 0, 'F'),
    # --- BQ24074 charger
    'U2': (15.4, 16.0, 0, 'F'),
    'C1': (17.0, 12.6, 0, 'F'),
    'R5': (13.8, 12.6, 0, 'F'),
    'R4': (19.4, 14.4, 90, 'F'),
    'C2': (19.4, 17.4, 90, 'F'),
    'R3': (11.6, 13.8, 90, 'F'),
    'C3': (11.6, 16.6, 90, 'F'),
    'R6': (14.6, 19.4, 90, 'F'),
    'R7': (17.4, 19.4, 90, 'F'),
    'D1': (11.6, 20.2, 0, 'F'),
    'R8': (11.6, 21.6, 0, 'F'),
    'J2': (5.2, 26.0, 270, 'F'),
    # --- LDO
    'U3': (15.6, 25.0, 0, 'F'),
    'C5': (12.6, 24.0, 90, 'F'),
    'R11': (12.6, 26.8, 90, 'F'),
    'C6': (18.8, 23.6, 90, 'F'),
    'C7': (18.8, 26.8, 90, 'F'),
    # --- VBAT divider (close to GPIO29)
    'R9': (34.2, 5.6, 0, 'F'),
    'R10': (34.2, 7.0, 0, 'F'),
    'C4': (36.4, 6.3, 90, 'F'),
    # --- core extras
    'C21': (31.9, 20.9, 0, 'F'),
    'U6': (33.6, 27.4, 90, 'F'),
    'C25': (31.9, 23.0, 0, 'F'),
    'R19': (29.4, 30.6, 90, 'F'),
    'SW1': (11.6, 2.6, 0, 'F'),
    'SW2': (17.6, 2.6, 0, 'F'),
    'R20': (21.2, 5.6, 90, 'F'),
    'J3': (55.5, 3.3, 180, 'F'),
    # --- ESP32-C6
    'U7': (68.85, 10.0, 270, 'F'),
    'C26': (61.0, 2.0, 0, 'F'),
    'C27': (61.0, 3.4, 0, 'F'),
    'R21': (61.0, 4.8, 0, 'F'),
    'C28': (61.0, 6.2, 0, 'F'),
    'R22': (61.0, 13.6, 0, 'F'),
    'R23': (61.0, 15.0, 0, 'F'),
    'TP1': (60.4, 8.6, 0, 'F'),
    'TP2': (60.4, 10.8, 0, 'F'),
    # --- LEDs
    'D2': (57.2, 9.6, 0, 'F'),
    'C31': (57.2, 11.9, 0, 'F'),
    'D3': (51.4, 9.4, 180, 'F'),
    'R32': (51.4, 11.0, 180, 'F'),
    # --- microSD
    'J4': (56.0, 28.5, 0, 'F'),
    'C30': (55.9, 18.6, 90, 'F'),
    'R24': (57.2, 18.6, 90, 'F'),
    'R25': (58.4, 18.6, 90, 'F'),
    'R26': (59.6, 18.6, 90, 'F'),
    'R27': (60.8, 18.6, 90, 'F'),
    'R28': (62.0, 18.6, 90, 'F'),
    'R29': (63.2, 18.6, 90, 'F'),
    'C29': (65.2, 19.6, 90, 'F'),
    # --- Qwiic
    'J5': (76.5, 28.0, 90, 'F'),
    'R30': (71.4, 25.8, 90, 'F'),
    'R31': (72.6, 25.8, 90, 'F'),
    # --- headers (bottom side, body under the board)
    'J6': (22.0, 1.6, 270, 'B'),
    'J7': (19.0, 36.4, 270, 'B'),
    'FID1': (8.0, 35.6, 0, 'F'),
    'FID2': (78.0, 35.6, 0, 'F'),
    'FID3': (47.0, 6.0, 0, 'F'),
}

# hand pre-routes (board-local mm): net, layer, width, polyline
J1X = PLACE['J1'][0] + 3.68   # USB4105 signal pad centre column
J1Y = PLACE['J1'][1]
PREROUTES = [
    # D-: B7 (y-0.75) -> ESD pin 4 ; A7 (y+0.25) joined to B7 by a loop under the receptacle
    ('USB_DM', 'F.Cu', 0.25, [(J1X, J1Y - 0.75), (PLACE['U1'][0] - 1.1, J1Y - 0.75)]),
    ('USB_DM', 'F.Cu', 0.2, [(J1X, J1Y - 0.75), (J1X - 0.9, J1Y - 0.75), (J1X - 0.9, J1Y + 0.25), (J1X, J1Y + 0.25)]),
    # D+: A6 (y-0.25) and B6 (y+0.75) joined just behind the pads -> ESD pin 6
    ('USB_DP', 'F.Cu', 0.25, [(J1X, J1Y - 0.25), (J1X + 1.1, J1Y - 0.25), (J1X + 1.1, J1Y + 0.75)]),
    ('USB_DP', 'F.Cu', 0.25, [(J1X, J1Y + 0.75), (PLACE['U1'][0] - 1.1, J1Y + 0.75)]),
]
# Tie the RPi under-chip +1V1 ring segments together (the reference relied on one continuous
# ring fill; with our clearances it fragments) -- 0.2 mm track inside the ring, under the QFN body.
PREROUTES.append(('+1V1', 'F.Cu', 0.2, [(U4X - 2.15, U4Y - 0.5), (U4X - 2.0, U4Y - 0.5), (U4X - 2.0, U4Y - 2.0),
                                         (U4X + 2.0, U4Y - 2.0), (U4X + 2.0, U4Y - 0.2), (U4X + 2.1495, U4Y - 0.2)]))
# ESD VBUS pin 5 is boxed in by the data lines: drop it to a via under the SOT-23 body
PREVIAS = [('VBUS', PLACE['U1'][0], PLACE['U1'][1])]
PREROUTES.append(('VBUS', 'F.Cu', 0.3, [(PLACE['U1'][0] - 1.1375, PLACE['U1'][1]), (PLACE['U1'][0], PLACE['U1'][1])]))


def preroute_items():
    out = []
    for net, layer, w, pts in PREROUTES:
        for a, b in zip(pts, pts[1:]):
            out.append([Sym('segment'), [Sym('start'), round(OX + a[0], 4), round(OY + a[1], 4)],
                        [Sym('end'), round(OX + b[0], 4), round(OY + b[1], 4)], [Sym('width'), w],
                        [Sym('layer'), layer], [Sym('net'), net], [Sym('uuid'), uid('pre', net, a, b)]])
    for net, x, y in PREVIAS:
        out.append([Sym('via'), [Sym('at'), OX + x, OY + y], [Sym('size'), 0.6], [Sym('drill'), 0.3],
                    [Sym('layers'), 'F.Cu', 'B.Cu'], [Sym('net'), net], [Sym('uuid'), uid('previa', net, x, y)]])
    return out


# ----------------------------------------------------------------- helpers
LAYER_SWAP = {}
for a, b in [('F.Cu', 'B.Cu'), ('F.SilkS', 'B.SilkS'), ('F.Fab', 'B.Fab'), ('F.CrtYd', 'B.CrtYd'),
             ('F.Mask', 'B.Mask'), ('F.Paste', 'B.Paste'), ('F.Adhes', 'B.Adhes'),
             ('F.Silkscreen', 'B.Silkscreen'), ('F.Courtyard', 'B.Courtyard')]:
    LAYER_SWAP[a] = b
    LAYER_SWAP[b] = a


def xform(lx, ly, X, Y, R):
    """footprint-local -> board (KiCad convention: R CCW on screen, y down)."""
    a = math.radians(R)
    return X + lx * math.cos(a) + ly * math.sin(a), Y - lx * math.sin(a) + ly * math.cos(a)


def rpi_xform(x, y):
    """RPi minimal-design coords -> our board-local coords (rotate +90 about U1)."""
    return U4X + (y - 100.0), U4Y - (x - 100.0)


def mirror_fp(node):
    """Flip a footprint definition to the back side (KiCad stores back-side fps y-mirrored)."""
    def walk(n):
        for i, e in enumerate(n):
            if isinstance(e, list) and e:
                k = e[0]
                if k in ('layer',) and len(e) > 1 and e[1] in LAYER_SWAP:
                    e[1] = LAYER_SWAP[e[1]]
                elif k == 'layers':
                    for j in range(1, len(e)):
                        if e[j] in LAYER_SWAP:
                            e[j] = LAYER_SWAP[e[j]]
                elif k in ('start', 'end', 'center', 'mid', 'xy') and len(e) >= 3:
                    e[2] = -float(e[2])
                elif k == 'at' and len(e) >= 3:
                    e[2] = -float(e[2])
                    if len(e) >= 4:
                        e[3] = -float(e[3])
                elif k == 'model':
                    continue
                if k == 'effects':
                    j = find(e, 'justify')
                    if j is None:
                        e.append([Sym('justify'), Sym('mirror')])
                    elif Sym('mirror') not in j:
                        j.append(Sym('mirror'))
                if k not in ('model',):
                    walk(e)
    walk(node)


def fp_pads_board(fpnode, X, Y, R):
    """Return pad list with board coordinates from a (possibly mirrored) local footprint node."""
    out = []
    for p in findall(fpnode, 'pad'):
        at = find(p, 'at')
        lx, ly = float(at[1]), float(at[2])
        prot = float(at[3]) if len(at) > 3 else 0.0
        bx, by = xform(lx, ly, X, Y, R)
        out.append(dict(num=p[1], kind=str(p[2]), shape=str(p[3]), x=bx, y=by, rot=prot + R,
                        size=(float(find(p, 'size')[1]), float(find(p, 'size')[2])),
                        layers=list(find(p, 'layers')[1:]), node=p,
                        drill=find(p, 'drill')))
    return out


def ref_of(fp):
    for p in findall(fp, 'property'):
        if p[1] == 'Reference':
            return p[2]


# ------------------------------------------------------------ build board
def build():
    comps = design.resolve()
    byref = {c['ref']: c for c in comps}
    rpi = parse(open(RPI_PCB).read())
    rpi_fp = {ref_of(f): f for f in findall(rpi, 'footprint')}

    items = []
    placed = {}
    for c in comps:
        if c['rpi']:
            f = rpi_fp[c['rpi']]
            at = find(f, 'at')
            rx, ry = float(at[1]), float(at[2])
            rr = float(at[3]) if len(at) > 3 else 0.0
            x, y = rpi_xform(rx, ry)
            pos = (x, y, (rr + 90) % 360, 'F')
        else:
            if c['ref'] not in PLACE:
                print('WARNING: no placement for', c['ref'])
                continue
            pos = PLACE[c['ref']]
        placed[c['ref']] = pos
        items.append(make_footprint(c, *pos))
    return comps, placed, items, rpi


def make_footprint(c, x, y, rot, side):
    lib = kilib.load_footprint(c['fp'])
    X, Y = OX + x, OY + y
    sheet = next(s for s in design.SHEETS if s[0] == c['sheet'])
    node = [Sym('footprint'), c['fp'], [Sym('layer'), 'F.Cu' if side == 'F' else 'B.Cu'],
            [Sym('uuid'), uid('fp', c['ref'])], [Sym('at'), X, Y, rot]]
    body = []
    for e in lib[2:]:
        if not isinstance(e, list) or not e:
            continue
        k = e[0]
        if k in ('version', 'generator', 'generator_version', 'layer', 'uuid'):
            continue
        e = copy.deepcopy(e)
        if k == 'property':
            if e[1] == 'Reference':
                e[2] = c['ref']
                lay = find(e, 'layer')
                if lay is not None and 'Silk' in lay[1]:
                    if find(e, 'hide') is None:
                        e.insert(3, [Sym('hide'), Sym('yes')])
                    else:
                        find(e, 'hide')[1] = Sym('yes')
            elif e[1] == 'Value':
                e[2] = c['value']
            elif e[1] == 'Footprint':
                e[2] = c['fp']
            elif e[1] == 'Description':
                e[2] = c['desc']
            elif e[1] == 'Datasheet':
                e[2] = kilib.symbol_prop(c['sym'], 'Datasheet') or ''
                if e[2] == '~':
                    e[2] = ''
        body.append(e)
    # extra properties
    extra = []
    if not any(e[0] == 'property' and e[1] == 'Datasheet' for e in body):
        ds = kilib.symbol_prop(c['sym'], 'Datasheet') or ''
        extra.append([Sym('property'), 'Datasheet', '' if ds == '~' else ds, [Sym('at'), 0, 0, 0], [Sym('layer'), 'F.Fab'],
                      [Sym('hide'), Sym('yes')], [Sym('uuid'), uid('prop', c['ref'], 'Datasheet')],
                      [Sym('effects'), [Sym('font'), [Sym('size'), 1, 1], [Sym('thickness'), 0.15]]]])
    if not any(e[0] == 'property' and e[1] == 'Description' for e in body):
        extra.append([Sym('property'), 'Description', c['desc'], [Sym('at'), 0, 0, 0], [Sym('layer'), 'F.Fab'],
                      [Sym('hide'), Sym('yes')], [Sym('uuid'), uid('prop', c['ref'], 'Description')],
                      [Sym('effects'), [Sym('font'), [Sym('size'), 1, 1], [Sym('thickness'), 0.15]]]])
    for k, v in (('MPN', c['mpn']), ('Manufacturer', c['mfr']), ('LCSC', c['lcsc'])):
        extra.append([Sym('property'), k, v, [Sym('at'), 0, 0, 0], [Sym('layer'), 'F.Fab'], [Sym('hide'), Sym('yes')],
                      [Sym('uuid'), uid('prop', c['ref'], k)],
                      [Sym('effects'), [Sym('font'), [Sym('size'), 1, 1], [Sym('thickness'), 0.15]]]])
    # insert extra properties after last property
    last = max([i for i, e in enumerate(body) if e[0] == 'property'] or [-1])
    body[last + 1:last + 1] = extra
    if side == 'B':
        tmp = [Sym('x')] + body
        mirror_fp(tmp)
        body = tmp[1:]
    # rotate text and pads (absolute angles in board file); attach nets; zones -> absolute
    for e in body:
        k = e[0]
        if k in ('property', 'fp_text', 'pad'):
            at = find(e, 'at')
            if at is not None:
                a0 = float(at[3]) if len(at) > 3 else 0.0
                while len(at) < 4:
                    at.append(0.0)
                at[3] = (a0 + rot) % 360
        if k == 'pad':
            net = c['pinnets'].get(e[1]) if e[1] else None
            if e[1] and e[1] in c['pinnets'] and net is None:
                pin = next(p for p in c['pinlist'] if p['number'] == e[1])
                net = 'unconnected-(%s-%s-Pad%s)' % (c['ref'], pin['name'], e[1])
            # strip existing uuid, add ours
            e[:] = [z for z in e if not (isinstance(z, list) and z and z[0] in ('net', 'uuid'))]
            if net:
                e.append([Sym('net'), net])
            e.append([Sym('uuid'), uid('pad', c['ref'], e[1], len(e))])
        if k == 'zone':
            for poly in findall(e, 'polygon'):
                pts = find(poly, 'pts')
                for p in pts[1:]:
                    bx, by = xform(float(p[1]), float(p[2]), X, Y, rot)
                    p[1], p[2] = round(bx, 4), round(by, 4)
    attrs = []
    node += body
    # sheet path linking to schematic symbol
    node.append([Sym('path'), '/' + SHEET_UUID[c['sheet']] + '/' + uid('sym', c['ref'])])
    node.append([Sym('sheetname'), '/' + sheet[1] + '/'])
    node.append([Sym('sheetfile'), sheet[2]])
    # attributes: exclude from BOM/pos where needed
    a = find(node, 'attr')
    if a is None:
        a = [Sym('attr')]
        node.append(a)
    if not c['in_bom'] and Sym('exclude_from_bom') not in a:
        a.append(Sym('exclude_from_bom'))
    if c['ref'].startswith('TP') or c['ref'].startswith('FID'):
        if Sym('exclude_from_pos_files') not in a:
            a.append(Sym('exclude_from_pos_files'))
    return node


# --------------------------------------------------------------- copy RPi
RPI_NETS = {
    '+3V3': '+3V3', '+1V1': '+1V1', 'GND': 'GND', '/VREG_LX': 'VREG_LX', '/VREG_AVDD': 'VREG_AVDD',
    '/XIN': 'XIN', '/XOUT': 'XOUT', 'Net-(C4-Pad1)': 'XOSC_R',
    'Net-(U1-USB_DP)': 'USB_DP_MCU', 'Net-(U1-USB_DM)': 'USB_DM_MCU',
}
# region of the RPi board (their coords) that we copy
RPI_REGION = (86.5, 110.0, 80.5, 114.5)


def in_region(x, y):
    x0, x1, y0, y1 = RPI_REGION
    return x0 <= x <= x1 and y0 <= y <= y1


PRUNED = os.path.join(HERE, 'pruned_uuids.json')


def copy_rpi_copper(rpi, our_pads):
    """Copy RPi tracks/vias/zones for core nets. Returns (items, dropped_count)."""
    out = []
    dropped = 0
    pruned = set(json.load(open(PRUNED))) if os.path.exists(PRUNED) else set()
    for s in findall(rpi, 'segment'):
        net = find(s, 'net')[1]
        if net not in RPI_NETS:
            continue
        st, en = find(s, 'start'), find(s, 'end')
        x0, y0, x1, y1 = float(st[1]), float(st[2]), float(en[1]), float(en[2])
        if not (in_region(x0, y0) and in_region(x1, y1)):
            dropped += 1
            continue
        a = rpi_xform(x0, y0); b = rpi_xform(x1, y1)
        if math.hypot(a[0] - b[0], a[1] - b[1]) < 0.02 or uid('rseg', x0, y0, x1, y1) in pruned:
            continue
        out.append([Sym('segment'), [Sym('start'), OX + a[0], OY + a[1]], [Sym('end'), OX + b[0], OY + b[1]],
                    [Sym('width'), float(find(s, 'width')[1])], [Sym('layer'), find(s, 'layer')[1]],
                    [Sym('net'), RPI_NETS[net]], [Sym('uuid'), uid('rseg', x0, y0, x1, y1)]])
    for v in findall(rpi, 'via'):
        net = find(v, 'net')[1]
        if net not in RPI_NETS:
            continue
        at = find(v, 'at')
        x, y = float(at[1]), float(at[2])
        if not in_region(x, y):
            continue
        a = rpi_xform(x, y)
        out.append([Sym('via'), [Sym('at'), OX + a[0], OY + a[1]], [Sym('size'), float(find(v, 'size')[1])],
                    [Sym('drill'), float(find(v, 'drill')[1])], [Sym('layers'), 'F.Cu', 'B.Cu'],
                    [Sym('net'), RPI_NETS[net]], [Sym('uuid'), uid('rvia', x, y)]])
    for z in findall(rpi, 'zone'):
        net = find(z, 'net')[1]
        if net not in RPI_NETS:
            continue
        pts = [(float(p[1]), float(p[2])) for p in find(find(z, 'polygon'), 'pts')[1:]]
        if not all(in_region(x, y) for x, y in pts):
            continue
        prio = find(z, 'priority')
        cp = find(z, 'connect_pads')
        newpts = [rpi_xform(x, y) for x, y in pts]
        zone = [Sym('zone'), [Sym('net'), RPI_NETS[net]], [Sym('layer'), find(z, 'layer')[1]],
                [Sym('uuid'), uid('rzone', pts[0][0], pts[0][1], net)], [Sym('name'), 'RPi_' + RPI_NETS[net]],
                [Sym('hatch'), Sym('edge'), 0.5],
                [Sym('priority'), int(prio[1]) + 10 if prio else 10], copy.deepcopy(cp),
                [Sym('min_thickness'), float(find(z, 'min_thickness')[1])],
                [Sym('fill'), Sym('yes'), [Sym('thermal_gap'), 0.2], [Sym('thermal_bridge_width'), 0.25],
                 [Sym('island_removal_mode'), 0]],
                [Sym('polygon'), [Sym('pts')] + [[Sym('xy'), round(OX + x, 4), round(OY + y, 4)] for x, y in newpts]]]
        out.append(zone)
    return out, dropped


# ---------------------------------------------------------------- outline
def rounded_rect(x0, y0, x1, y1, r, layer='Edge.Cuts', w=0.1):
    out = []
    def line(a, b):
        out.append([Sym('gr_line'), [Sym('start'), a[0], a[1]], [Sym('end'), b[0], b[1]],
                    [Sym('stroke'), [Sym('width'), w], [Sym('type'), Sym('solid')]], [Sym('layer'), layer],
                    [Sym('uuid'), uid('edge', a, b)]])
    def arc(s, m, e):
        out.append([Sym('gr_arc'), [Sym('start'), s[0], s[1]], [Sym('mid'), m[0], m[1]], [Sym('end'), e[0], e[1]],
                    [Sym('stroke'), [Sym('width'), w], [Sym('type'), Sym('solid')]], [Sym('layer'), layer],
                    [Sym('uuid'), uid('edgearc', s, e)]])
    k = r * (1 - math.sqrt(0.5))
    line((x0 + r, y0), (x1 - r, y0)); arc((x1 - r, y0), (x1 - k, y0 + k), (x1, y0 + r))
    line((x1, y0 + r), (x1, y1 - r)); arc((x1, y1 - r), (x1 - k, y1 - k), (x1 - r, y1))
    line((x1 - r, y1), (x0 + r, y1)); arc((x0 + r, y1), (x0 + k, y1 - k), (x0, y1 - r))
    line((x0, y1 - r), (x0, y0 + r)); arc((x0, y0 + r), (x0 + k, y0 + k), (x0 + r, y0))
    return out


def zone(net, layer, pts, prio=0, name='', clearance=0.2, min_th=0.2, thermal=True, layers=None):
    z = [Sym('zone'), [Sym('net'), net]]
    if layers:
        z.append([Sym('layers')] + layers)
    else:
        z.append([Sym('layer'), layer])
    z += [[Sym('uuid'), uid('zone', net, layer, name)], [Sym('name'), name or ('%s_%s' % (net, layer))],
          [Sym('hatch'), Sym('edge'), 0.5], [Sym('priority'), prio],
          [Sym('connect_pads'), [Sym('clearance'), clearance]] if thermal else
          [Sym('connect_pads'), Sym('yes'), [Sym('clearance'), clearance]],
          [Sym('min_thickness'), min_th],
          [Sym('fill'), Sym('yes'), [Sym('thermal_gap'), 0.25], [Sym('thermal_bridge_width'), 0.3],
           [Sym('island_removal_mode'), 0]],
          [Sym('polygon'), [Sym('pts')] + [[Sym('xy'), round(x, 4), round(y, 4)] for x, y in pts]]]
    return z


def keepout(pts, name, layers=('*.Cu',), tracks=False, vias=False, pour=False, fps=True):
    na = lambda b: Sym('allowed' if b else 'not_allowed')
    return [Sym('zone'), [Sym('net'), ''], [Sym('layers')] + list(layers),
            [Sym('uuid'), uid('keepout', name)], [Sym('name'), name], [Sym('hatch'), Sym('edge'), 0.5],
            [Sym('connect_pads'), [Sym('clearance'), 0]], [Sym('min_thickness'), 0.25],
            [Sym('keepout'), [Sym('tracks'), na(tracks)], [Sym('vias'), na(vias)], [Sym('pads'), Sym('allowed')],
             [Sym('copperpour'), na(pour)], [Sym('footprints'), na(fps)]],
            [Sym('placement'), [Sym('enabled'), Sym('no')], [Sym('sheetname'), '']],
            [Sym('fill'), [Sym('thermal_gap'), 0.5], [Sym('thermal_bridge_width'), 0.5]],
            [Sym('polygon'), [Sym('pts')] + [[Sym('xy'), round(x, 4), round(y, 4)] for x, y in pts]]]


def board_poly(inset=0.0):
    return [(OX + inset, OY + inset), (OX + BW - inset, OY + inset), (OX + BW - inset, OY + BH - inset),
            (OX + inset, OY + BH - inset)]


LAYERS = [(0, 'F.Cu', 'signal'), (4, 'In1.Cu', 'power'), (6, 'In2.Cu', 'power'), (2, 'B.Cu', 'signal'),
          (9, 'F.Adhes', 'user', 'F.Adhesive'), (11, 'B.Adhes', 'user', 'B.Adhesive'),
          (13, 'F.Paste', 'user'), (15, 'B.Paste', 'user'), (5, 'F.SilkS', 'user', 'F.Silkscreen'),
          (7, 'B.SilkS', 'user', 'B.Silkscreen'), (1, 'F.Mask', 'user'), (3, 'B.Mask', 'user'),
          (17, 'Dwgs.User', 'user', 'User.Drawings'), (19, 'Cmts.User', 'user', 'User.Comments'),
          (21, 'Eco1.User', 'user', 'User.Eco1'), (23, 'Eco2.User', 'user', 'User.Eco2'),
          (25, 'Edge.Cuts', 'user'), (27, 'Margin', 'user'), (31, 'F.CrtYd', 'user', 'F.Courtyard'),
          (29, 'B.CrtYd', 'user', 'B.Courtyard'), (35, 'F.Fab', 'user'), (33, 'B.Fab', 'user')]


def stackup():
    L = lambda *a: list(a)
    return [Sym('stackup'),
            [Sym('layer'), 'F.SilkS', [Sym('type'), 'Top Silk Screen'], [Sym('color'), 'White']],
            [Sym('layer'), 'F.Paste', [Sym('type'), 'Top Solder Paste']],
            [Sym('layer'), 'F.Mask', [Sym('type'), 'Top Solder Mask'], [Sym('color'), 'Green'], [Sym('thickness'), 0.01]],
            [Sym('layer'), 'F.Cu', [Sym('type'), 'copper'], [Sym('thickness'), 0.035]],
            [Sym('layer'), 'dielectric 1', [Sym('type'), 'prepreg'], [Sym('thickness'), 0.2104], [Sym('material'), 'FR4'],
             [Sym('epsilon_r'), 4.4], [Sym('loss_tangent'), 0.02]],
            [Sym('layer'), 'In1.Cu', [Sym('type'), 'copper'], [Sym('thickness'), 0.0152]],
            [Sym('layer'), 'dielectric 2', [Sym('type'), 'core'], [Sym('thickness'), 1.065], [Sym('material'), 'FR4'],
             [Sym('epsilon_r'), 4.6], [Sym('loss_tangent'), 0.02]],
            [Sym('layer'), 'In2.Cu', [Sym('type'), 'copper'], [Sym('thickness'), 0.0152]],
            [Sym('layer'), 'dielectric 3', [Sym('type'), 'prepreg'], [Sym('thickness'), 0.2104], [Sym('material'), 'FR4'],
             [Sym('epsilon_r'), 4.4], [Sym('loss_tangent'), 0.02]],
            [Sym('layer'), 'B.Cu', [Sym('type'), 'copper'], [Sym('thickness'), 0.035]],
            [Sym('layer'), 'B.Mask', [Sym('type'), 'Bottom Solder Mask'], [Sym('color'), 'Green'], [Sym('thickness'), 0.01]],
            [Sym('layer'), 'B.Paste', [Sym('type'), 'Bottom Solder Paste']],
            [Sym('layer'), 'B.SilkS', [Sym('type'), 'Bottom Silk Screen'], [Sym('color'), 'White']],
            [Sym('copper_finish'), 'ENIG'], [Sym('dielectric_constraints'), Sym('no')]]


def header():
    layers = [Sym('layers')]
    for l in LAYERS:
        e = [l[0], l[1], Sym(l[2] if l[2] != 'power' else 'power')]
        if len(l) > 3:
            e.append(l[3])
        layers.append(e)
    setup = [Sym('setup'), stackup(), [Sym('pad_to_mask_clearance'), 0],
             [Sym('allow_soldermask_bridges_in_footprints'), Sym('no')],
             [Sym('tenting'), [Sym('front'), Sym('yes')], [Sym('back'), Sym('yes')]],
             [Sym('aux_axis_origin'), OX, OY + BH], [Sym('grid_origin'), OX, OY],
             [Sym('pcbplotparams'),
              [Sym('layerselection'), Sym('0x00000000_00000000_55555555_5755f5ff')],
              [Sym('plot_on_all_layers_selection'), Sym('0x00000000_00000000_00000000_00000000')],
              [Sym('disableapertmacros'), Sym('no')], [Sym('usegerberextensions'), Sym('no')],
              [Sym('usegerberattributes'), Sym('yes')], [Sym('usegerberadvancedattributes'), Sym('yes')],
              [Sym('creategerberjobfile'), Sym('yes')], [Sym('svgprecision'), 6], [Sym('plotframeref'), Sym('no')],
              [Sym('mode'), 1], [Sym('useauxorigin'), Sym('yes')], [Sym('outputdirectory'), '../../fab/gerbers/']]]
    return [[Sym('version'), Sym('20260206')], [Sym('generator'), 'pcbnew'], [Sym('generator_version'), '10.0'],
            [Sym('general'), [Sym('thickness'), 1.6], [Sym('legacy_teardrops'), Sym('no')]],
            [Sym('paper'), 'A4'],
            [Sym('title_block'), [Sym('title'), design.TITLE], [Sym('date'), design.DATE], [Sym('rev'), design.REV],
             [Sym('comment'), 1, '4-layer 1.6 mm, ENIG, PCBWay standard capabilities']],
            layers, setup]


def silk_text(s, x, y, size=0.8, layer='F.SilkS', rot=0, th=0.15, justify=None):
    e = [Sym('effects'), [Sym('font'), [Sym('size'), size, size], [Sym('thickness'), th]]]
    if justify:
        e.append([Sym('justify')] + [Sym(j) for j in justify.split()])
    if layer.startswith('B.'):
        j = find(e, 'justify')
        if j is None:
            e.append([Sym('justify'), Sym('mirror')])
        else:
            j.append(Sym('mirror'))
    return [Sym('gr_text'), s, [Sym('at'), OX + x, OY + y, rot], [Sym('layer'), layer],
            [Sym('uuid'), uid('gtxt', s, x, y, layer)], e]


HDR_LABELS_A = ['VBUS', 'VSYS', 'VBAT', 'GND', '3V3', 'EN', 'RUN', 'GND', 'A0', 'A1', 'A2', 'GND']
HDR_LABELS_B = ['TX0', 'RX0', 'GP2', 'GP3', 'GP4', 'GP5', 'GND', 'SDA', 'SCL', '3V3', 'GND', 'GND']


def silk_labels():
    g = []
    jx, jy = PLACE['J6'][0], PLACE['J6'][1]
    for i, t in enumerate(HDR_LABELS_A):
        g.append(silk_text(t, jx + i * 2.54, jy + 1.75, 0.6, th=0.12))
        g.append(silk_text(t, jx + i * 2.54, jy + 2.45, 0.6, layer='B.SilkS', th=0.12))
    jx, jy = PLACE['J7'][0], PLACE['J7'][1]
    for i, t in enumerate(HDR_LABELS_B):
        g.append(silk_text(t, jx + i * 2.54, jy - 1.75, 0.6, th=0.12))
        g.append(silk_text(t, jx + i * 2.54, jy - 2.45, 0.6, layer='B.SilkS', th=0.12))
    for t, x, y, sz in SILK_TOP:
        g.append(silk_text(t, x, y, sz))
    for t, x, y, sz in SILK_BOTTOM:
        g.append(silk_text(t, x, y, sz, layer='B.SilkS'))
    return g


SILK_TOP = [
    ('BOOT', 12.5, 5.0, 0.7), ('RESET', 17.6, 5.0, 0.7),
    ('USB-C 5V', 4.0, 15.2, 0.7),
    ('-', 10.8, 24.9, 1.0), ('+', 10.8, 27.1, 1.0), ('LiPo', 4.5, 32.0, 0.7),
    ('CHG', 8.7, 20.2, 0.6),
    ('SWD', 51.0, 4.4, 0.7), ('D G C', 55.5, 7.1, 0.6),
    ('RGB', 57.2, 7.9, 0.6), ('GP25', 51.4, 7.9, 0.6),
    ('QWIIC', 74.0, 32.6, 0.7),
]
SILK_BOTTOM = [
    ('RP2350 Wireless Dev Board', 40.0, 12.0, 1.2),
    ('Rev ' + design.REV + '  ' + design.DATE, 40.0, 14.5, 0.8),
    ('RP2350A | 16MB flash | 8MB PSRAM | ESP32-C6 Wi-Fi 6/BLE 5', 40.0, 17.0, 0.7),
    ('LiPo: JST-PH pin1 = GND, pin2 = +  (CHECK POLARITY)', 40.0, 19.0, 0.7),
    ('WayWayWay', 40.0, 23.0, 0.8),
]


def board_graphics():
    g = rounded_rect(OX, OY, OX + BW, OY + BH, CORNER_R)
    g += silk_labels()
    # antenna keepout: everything right of the module's antenna start, top strip
    ant_x = PLACE['U7'][0] + 5.4
    g.append(keepout([(OX + ant_x, OY - 1), (OX + BW + 1, OY - 1), (OX + BW + 1, OY + PLACE['U7'][1] + 8.6),
                      (OX + ant_x, OY + PLACE['U7'][1] + 8.6)], 'ANTENNA_KEEPOUT_BOARD'))
    return g


def write_board(items, extra):
    out = [Sym('kicad_pcb')] + header() + items + extra
    open(PCB_PATH, 'w').write(dumps(out) + '\n')


def main(route_file=None):
    comps, placed, fps, rpi = build()
    copper, dropped = copy_rpi_copper(rpi, None)
    zones = []
    bp = board_poly(0.0)
    zones.append(zone('GND', 'In1.Cu', bp, 0, 'GND_In1', clearance=0.2))
    zones.append(zone('+3V3', 'In2.Cu', bp, 0, '3V3_In2', clearance=0.2))
    zones.append(zone('GND', 'F.Cu', bp, 0, 'GND_F', clearance=0.2))
    zones.append(zone('GND', 'B.Cu', bp, 0, 'GND_B', clearance=0.2))
    extra = board_graphics() + zones + copper + preroute_items()
    if route_file and os.path.exists(route_file):
        extra += parse('(x ' + open(route_file).read() + ')')[1:]
    write_board(fps, extra)
    fixed = [find(e, 'uuid')[1] for e in copper + preroute_items() if e[0] in ('segment', 'via')]
    json.dump(fixed, open(os.path.join(HERE, 'fixed_uuids.json'), 'w'))
    json.dump({k: v for k, v in placed.items()}, open(os.path.join(HERE, 'placement.json'), 'w'), indent=1)
    print('board written:', len(fps), 'footprints,', len(copper), 'copied RPi items,', dropped, 'clipped RPi segments')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
