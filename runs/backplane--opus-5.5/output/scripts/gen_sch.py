"""Generate the hierarchical KiCad schematic from design.py.

Connectivity is expressed with global labels / power symbols on short wire stubs
at every pin, so the schematic is generated deterministically from the netlist.
"""
import os, math, uuid
from sexp import dumps, Sym, find, findall
import kilib, design

HERE = os.path.dirname(os.path.abspath(__file__))
BOARD_DIR = os.path.join(HERE, '..', 'boards', design.PROJECT)
NS = uuid.UUID('6f1c1e0a-2b8e-4c7e-9a51-7d0c2e3b4a10')
G = 1.27  # grid


def uid(*parts):
    return str(uuid.uuid5(NS, '/'.join(str(p) for p in parts)))


ROOT_UUID = uid('root')
SHEET_UUID = {s[0]: uid('sheet', s[0]) for s in design.SHEETS}


def snap(v):
    return round(v / G) * G


def font(size=1.27):
    return [Sym('effects'), [Sym('font'), [Sym('size'), size, size]]]


def font_j(j, size=1.27, hide=False):
    e = [Sym('effects'), [Sym('font'), [Sym('size'), size, size]]]
    if j:
        e.append([Sym('justify')] + [Sym(x) for x in j.split()])
    if hide:
        e.append([Sym('hide'), Sym('yes')])
    return e


def rot(px, py, r):
    a = math.radians(r)
    return px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)


def pin_screen(X, Y, r, p):
    """Return (x, y, outward_angle_deg) of a pin's connection point on screen."""
    dx, dy = rot(p['x'], p['y'], r)
    out = (p['angle'] + 180 + r) % 360
    return X + dx, Y - dy, out


def dirv(a):
    a = math.radians(a)
    return round(math.cos(a), 6), round(-math.sin(a), 6)


def sym_body_bbox(libid):
    s = kilib.load_symbol(libid)
    xs, ys = [], []

    def walk(n):
        for e in n:
            if not isinstance(e, list) or not e:
                continue
            k = e[0]
            if k == 'rectangle':
                for kk in ('start', 'end'):
                    p = find(e, kk)
                    xs.append(float(p[1])); ys.append(float(p[2]))
            elif k in ('polyline', 'bezier'):
                for p in find(e, 'pts')[1:]:
                    xs.append(float(p[1])); ys.append(float(p[2]))
            elif k == 'circle':
                c = find(e, 'center'); rr = float(find(e, 'radius')[1])
                xs.extend([float(c[1]) - rr, float(c[1]) + rr]); ys.extend([float(c[2]) - rr, float(c[2]) + rr])
            elif k == 'arc':
                for kk in ('start', 'mid', 'end'):
                    p = find(e, kk)
                    xs.append(float(p[1])); ys.append(float(p[2]))
            elif k == 'pin':
                at = find(e, 'at'); L = float(find(e, 'length')[1]); a = math.radians(float(at[3]))
                xs.extend([float(at[1]), float(at[1]) + L * math.cos(a)])
                ys.extend([float(at[2]), float(at[2]) + L * math.sin(a)])
            elif k == 'symbol':
                walk(e)
    walk(s)
    if not xs:
        return -1.27, -1.27, 1.27, 1.27
    # lib y-up -> screen y-down
    return min(xs), -max(ys), max(xs), -min(ys)


POWER_BODY_ANGLE = {}  # libid -> body direction in lib frame


def power_body_angle(libid):
    if libid not in POWER_BODY_ANGLE:
        p = kilib.symbol_pins(libid)[0]
        x0, y0, x1, y1 = sym_body_bbox(libid)
        # body is above (screen y negative) for +V, below for GND
        POWER_BODY_ANGLE[libid] = 90 if (y0 + y1) / 2 < 0 else 270
    return POWER_BODY_ANGLE[libid]


def label_len(text):
    return 1.27 * 0.75 * len(text) + 2.5


class Sheet:
    def __init__(self, sid, title, fname, root=False):
        self.sid, self.title, self.fname = sid, title, fname
        self.items = []
        self.libs = {}
        self.pwr_n = 0
        self.root = root

    def need_lib(self, libid):
        if libid not in self.libs:
            self.libs[libid] = kilib.lib_symbol_for_sch(libid)

    def path(self):
        return '/' + ROOT_UUID + ('' if self.root else '/' + SHEET_UUID[self.sid])

    def symbol(self, libid, ref, value, X, Y, r=0, fp='', fields=None, in_bom=True, on_board=True,
               dnp=False, hide_ref=False, hide_val=False, ref_at=None, val_at=None, key=None, desc=''):
        self.need_lib(libid)
        u = uid('sym', key or ref)
        pins = kilib.symbol_pins(libid)
        props = []
        rx, ry = ref_at or (X, Y - 2.54)
        vx, vy = val_at or (X, Y + 2.54)
        props.append([Sym('property'), 'Reference', ref, [Sym('at'), rx, ry, 0], font_j('left', hide=hide_ref)])
        props.append([Sym('property'), 'Value', value, [Sym('at'), vx, vy, 0], font_j('left', hide=hide_val)])
        props.append([Sym('property'), 'Footprint', fp, [Sym('at'), X, Y, 0], font_j(None, hide=True)])
        ds = kilib.symbol_prop(libid, 'Datasheet') or ''
        props.append([Sym('property'), 'Datasheet', ds if ds != '~' else '', [Sym('at'), X, Y, 0], font_j(None, hide=True)])
        props.append([Sym('property'), 'Description', desc or (kilib.symbol_prop(libid, 'Description') or ''),
                      [Sym('at'), X, Y, 0], font_j(None, hide=True)])
        for k, v in (fields or {}).items():
            props.append([Sym('property'), k, v, [Sym('at'), X, Y, 0], font_j(None, hide=True)])
        node = [Sym('symbol'), [Sym('lib_id'), libid], [Sym('at'), X, Y, r], [Sym('unit'), 1],
                [Sym('exclude_from_sim'), Sym('no')], [Sym('in_bom'), Sym('yes' if in_bom else 'no')],
                [Sym('on_board'), Sym('yes' if on_board else 'no')], [Sym('dnp'), Sym('yes' if dnp else 'no')],
                [Sym('uuid'), u]] + props
        seen = set()
        for p in pins:
            if p['number'] in seen:
                continue
            seen.add(p['number'])
            node.append([Sym('pin'), p['number'], [Sym('uuid'), uid('pin', key or ref, p['number'])]])
        node.append([Sym('instances'), [Sym('project'), design.PROJECT,
                                        [Sym('path'), self.path(), [Sym('reference'), ref], [Sym('unit'), 1]]]])
        self.items.append(node)
        return u

    def wire(self, x0, y0, x1, y1):
        self.items.append([Sym('wire'), [Sym('pts'), [Sym('xy'), x0, y0], [Sym('xy'), x1, y1]],
                           [Sym('stroke'), [Sym('width'), 0], [Sym('type'), Sym('default')]],
                           [Sym('uuid'), uid('w', self.sid, x0, y0, x1, y1)]])

    def glabel(self, text, x, y, ang, shape='passive'):
        j = {0: 'left', 180: 'right', 90: 'left', 270: 'right'}[int(ang) % 360]
        self.items.append([Sym('global_label'), text, [Sym('shape'), Sym(shape)], [Sym('at'), x, y, ang],
                           [Sym('fields_autoplaced'), Sym('yes')], font_j(j),
                           [Sym('uuid'), uid('gl', self.sid, text, x, y)],
                           [Sym('property'), 'Intersheetrefs', '${INTERSHEET_REFS}', [Sym('at'), x, y, 0],
                            font_j(j, hide=True)]])

    def noconn(self, x, y):
        self.items.append([Sym('no_connect'), [Sym('at'), x, y], [Sym('uuid'), uid('nc', self.sid, x, y)]])

    def power(self, net, x, y, out_ang):
        libid = design.POWER_NETS[net]
        body = power_body_angle(libid)
        r = (out_ang - body) % 360
        self.pwr_n += 1
        ref = '#PWR_%s_%03d' % (self.sid.upper(), self.pwr_n)
        # value text placed beyond the symbol
        dx, dy = dirv(out_ang)
        tx, ty = x + dx * 3.8, y + dy * 3.8
        self.symbol(libid, ref, net, x, y, r, hide_ref=True, ref_at=(x, y), val_at=(tx, ty), key=ref)

    def pwrflag(self, net, x, y):
        self.pwr_n += 1
        ref = '#FLG_%s_%03d' % (self.sid.upper(), self.pwr_n)
        self.symbol('power:PWR_FLAG', ref, 'PWR_FLAG', x, y, 0, hide_ref=True, ref_at=(x, y),
                    val_at=(x + 1.27, y - 3.2), key=ref)

    def text(self, s, x, y, size=1.27):
        self.items.append([Sym('text'), s, [Sym('exclude_from_sim'), Sym('no')], [Sym('at'), x, y, 0],
                           [Sym('effects'), [Sym('font'), [Sym('size'), size, size]], [Sym('justify'), Sym('left'), Sym('top')]],
                           [Sym('uuid'), uid('txt', self.sid, s[:40], x, y)]])

    def sheet_symbol(self, sid, title, fname, x, y, w, h, page):
        u = SHEET_UUID[sid]
        self.items.append([Sym('sheet'), [Sym('at'), x, y], [Sym('size'), w, h],
                           [Sym('exclude_from_sim'), Sym('no')], [Sym('in_bom'), Sym('yes')], [Sym('on_board'), Sym('yes')],
                           [Sym('dnp'), Sym('no')], [Sym('fields_autoplaced'), Sym('yes')],
                           [Sym('stroke'), [Sym('width'), 0.1524], [Sym('type'), Sym('solid')]],
                           [Sym('fill'), [Sym('color'), 0, 0, 0, 0.0]],
                           [Sym('uuid'), u],
                           [Sym('property'), 'Sheetname', title, [Sym('at'), x, y - 0.7, 0], font_j('left bottom')],
                           [Sym('property'), 'Sheetfile', fname, [Sym('at'), x, y + h + 0.6, 0], font_j('left top')],
                           [Sym('instances'), [Sym('project'), design.PROJECT,
                                               [Sym('path'), '/' + ROOT_UUID, [Sym('page'), str(page)]]]]])

    def write(self, paper, page_title, comments=()):
        tb = [Sym('title_block'), [Sym('title'), design.TITLE + ' - ' + page_title], [Sym('date'), design.DATE],
              [Sym('rev'), design.REV], [Sym('company'), 'Generated by scripts/gen_sch.py']]
        for i, c in enumerate(comments):
            tb.append([Sym('comment'), i + 1, c])
        out = [Sym('kicad_sch'), [Sym('version'), Sym('20260306')], [Sym('generator'), 'eeschema'],
               [Sym('generator_version'), '10.0'], [Sym('uuid'), ROOT_UUID if self.root else uid('file', self.sid)],
               [Sym('paper'), paper], tb,
               [Sym('lib_symbols')] + [self.libs[k] for k in sorted(self.libs)]]
        out += self.items
        if self.root:
            out.append([Sym('sheet_instances'), [Sym('path'), '/', [Sym('page'), '1']]])
        out.append([Sym('embedded_fonts'), Sym('no')])
        with open(os.path.join(BOARD_DIR, self.fname), 'w') as f:
            f.write(dumps(out) + '\n')


STUB = 2.54


def comp_extent(c):
    """Bounding box (relative to symbol origin, screen coords) including stubs + labels."""
    x0, y0, x1, y1 = sym_body_bbox(c['sym'])
    for p in c['pinlist']:
        px, py, out = pin_screen(0, 0, 0, p)
        net = c['pinnets'][p['number']]
        dx, dy = dirv(out)
        if net is None:
            L = 1.0
        elif net in design.POWER_NETS:
            L = 4.5 + 0.9 * len(net)
        else:
            L = STUB + label_len(net)
        ex, ey = px + dx * L, py + dy * L
        # labels are ~2.5mm tall perpendicular to their direction
        x0 = min(x0, ex - (1.5 if dy else 0)); x1 = max(x1, ex + (1.5 if dy else 0))
        y0 = min(y0, ey - (1.5 if dx else 0)); y1 = max(y1, ey + (1.5 if dx else 0))
    return x0 - 1.5, y0 - 4.0, x1 + 1.5, y1 + 4.0


def place_component(sh, c, X, Y):
    fields = {'MPN': c['mpn'], 'Manufacturer': c['mfr'], 'LCSC': c['lcsc']}
    fields.update(c['fields'])
    bx0, by0, bx1, by1 = sym_body_bbox(c['sym'])
    is_ic = (bx1 - bx0) > 8
    if is_ic:
        ref_at = (X + bx0, Y + by0 - 1.5)
        val_at = (X + bx0, Y + by1 + 2.0)
    else:
        ref_at = (X + bx1 + 1.0, Y - 1.0)
        val_at = (X + bx1 + 1.0, Y + 1.5)
    sh.symbol(c['sym'], c['ref'], c['value'], X, Y, 0, fp=c['fp'], fields=fields,
              in_bom=c['in_bom'], dnp=c['dnp'], ref_at=ref_at, val_at=val_at, desc=c['desc'])
    done = set()
    for p in c['pinlist']:
        px, py, out = pin_screen(X, Y, 0, p)
        key = (round(px, 3), round(py, 3))
        if key in done:
            continue  # stacked pins share one connection point
        done.add(key)
        net = c['pinnets'][p['number']]
        if p['type'] == 'no_connect' and net is None:
            continue
        if net is None:
            sh.noconn(px, py)
            continue
        dx, dy = dirv(out)
        if net in design.POWER_NETS and dy == 0:
            ex, ey = px + dx * STUB, py + dy * STUB
            sh.wire(px, py, ex, ey)
            sh.glabel(net, ex, ey, out)
        elif net in design.POWER_NETS:
            lvl = int(round(px / 2.54)) % 3 if (is_ic and dy != 0) else 0
            if lvl:
                ex, ey = px + dx * 3.81 * lvl, py + dy * 3.81 * lvl
                sh.wire(px, py, ex, ey)
                sh.power(net, ex, ey, out)
            else:
                sh.power(net, px, py, out)
        else:
            ex, ey = px + dx * STUB, py + dy * STUB
            sh.wire(px, py, ex, ey)
            sh.glabel(net, ex, ey, out)


PAPERS = [('A3', 420, 297), ('A2', 594, 420), ('A1', 841, 594)]


def layout_sheet(sh, comps, flags, notes):
    exts = [(c, comp_extent(c)) for c in comps]
    for paper, W, H in PAPERS:
        xL, xR, yT, yB = 15, W - 15, 20, H - 45
        positions = []
        x, y, rowh = xL, yT, 0
        ok = True
        for c, (x0, y0, x1, y1) in exts:
            w, h = x1 - x0, y1 - y0
            if x + w > xR:
                x, y, rowh = xL, y + rowh + 2, 0
            if y + h > yB:
                ok = False
                break
            positions.append((c, snap(x - x0), snap(y - y0)))
            x += w + 2
            rowh = max(rowh, h)
        if ok:
            break
    for c, X, Y in positions:
        place_component(sh, c, X, Y)
    # power flags along the bottom-left
    fx = snap(20)
    fy = snap(H - 35)
    for net in flags:
        if net in design.POWER_NETS:
            ey = fy + 2.54 if net == 'GND' else fy - 2.54
            sh.wire(fx, fy, fx, ey)
            sh.power(net, fx, ey, 270 if net == 'GND' else 90)
            sh.pwrflag(net, fx, fy)
        else:
            sh.wire(fx, fy, fx, fy + 2.54)
            sh.glabel(net, fx, fy + 2.54, 270)
            sh.pwrflag(net, fx, fy)
        fx += snap(15)
    ty = H - 75
    tx = 110
    for n in notes:
        sh.text(n, tx, ty)
        tx += 150
    return paper


SHEET_NOTES = {
    'power': [
        "USB-C sink: 5.1k Rd on CC1/CC2 (default USB power).\n"
        "BQ24074 power-path: OUT (VSYS) is fed from VBUS when present,\n"
        "battery supplements via DPPM. EN2=1/EN1=0 -> ILIM resistor mode,\n"
        "R4 1.5k -> 1.03 A input limit. R5 2k -> 445 mA charge current.\n"
        "TMR open = default safety timers, ITERM open = 10% termination.\n"
        "TS: 10k fixed resistor (packs without NTC).",
        "VBAT sense: VBAT/3 on GPIO29 (ADC3), same scaling as Pico 2.\n"
        "Divider draws ~14 uA from the cell.\n"
        "3V3: TLV75733P 1 A LDO from VSYS; EN on header (pull low = off).\n"
        "Battery: JST-PH 2 pin, pin 1 = GND, pin 2 = +VBAT (Adafruit/SparkFun\n"
        "polarity). CHECK YOUR CELL'S POLARITY BEFORE CONNECTING.",
    ],
    'mcu': [
        "RP2350A core copied from Raspberry Pi 'RP2350A Minimal' R4 reference\n"
        "(MIT licence): regulator (L1 polarity-marked AOTA-B201610, C8/C9/C10,\n"
        "R12 33R), crystal (ABM8-272-T3, 15p, 1k), decoupling, flash, BOOTSEL.\n"
        "Schematic refs differ; PCB placement/routing of this block is the RPi\n"
        "layout rotated 90 deg.",
        "PSRAM (APS6404L, 8 MB) on XIP_CS1 = GPIO8 (same as Adafruit Feather\n"
        "RP2350 so existing board configs work). Flash 16 MB on QSPI_SS.\n"
        "BOOT button doubles as a user button (read via QSPI_SS).\n"
        "SWD on JST-SH 3 pin (Raspberry Pi Debug Probe pinout).",
    ],
    'wireless': [
        "ESP32-C6-MINI-1 runs ESP-AT or ESP-Hosted firmware as a Wi-Fi 6 / BLE 5\n"
        "co-processor. Link: RP2350 UART1 (GPIO20 TX, 21 RX, 22 CTS, 23 RTS)\n"
        "<-> ESP UART0 (RXD0/TXD0) + IO6 (RTS) / IO7 (CTS).\n"
        "GPIO18 = ESP_EN (drive low to reset), GPIO19 = ESP IO9 strap\n"
        "(low at reset = ROM download mode) -> RP2350 can re-flash the ESP\n"
        "over the same UART (esp-serial-flasher). IO8 pulled up (required\n"
        "for download mode). ESP native USB on test pads TP1/TP2.",
    ],
    'io': [
        "microSD wired for 4-bit SDIO via PIO (CLK GPIO10, CMD GPIO11,\n"
        "D0-D3 GPIO12-15 consecutive) and also usable in SPI mode\n"
        "(SPI1: SCK=10, MOSI=11, MISO=12, CS=15). Card detect GPIO9 (low = card).\n"
        "Qwiic/STEMMA QT on I2C0 GPIO16/17 with 4.7k pull-ups.\n"
        "WS2812B-2020 on GPIO24 (powered from 3V3). User LED GPIO25.",
        "Headers are 2.54 mm, fitted on the bottom side (breadboard use).\n"
        "J6: VBUS VSYS VBAT GND 3V3 EN RUN GND A0 A1 A2 GND\n"
        "J7: GP0(TX) GP1(RX) GP2 GP3 GP4 GP5 GND SDA SCL 3V3 GND GND",
    ],
}
FLAGS = {'power': ['GND', 'VBUS'], 'mcu': ['+1V1', 'VREG_AVDD'], 'wireless': [], 'io': []}


def main():
    comps = design.resolve()
    pages = []
    for i, (sid, title, fname, ptitle) in enumerate(design.SHEETS):
        sh = Sheet(sid, title, fname)
        cs = [c for c in comps if c['sheet'] == sid]
        paper = layout_sheet(sh, cs, FLAGS[sid], SHEET_NOTES[sid])
        sh.write(paper, ptitle)
        pages.append((sid, title, fname))
        print(sid, paper, len(cs), 'components')
    root = Sheet('root', 'Top', design.PROJECT + '.kicad_sch', root=True)
    x, y = 30, 40
    for i, (sid, title, fname) in enumerate(pages):
        root.sheet_symbol(sid, title, fname, x + (i % 2) * 110, y + (i // 2) * 45, 80, 25, i + 2)
    root.text(
        "RP2350 Wireless Dev Board - block overview\n\n"
        "USB-C (5V) -> BQ24074 charger/power-path -> VSYS -> TLV75733P LDO -> 3V3\n"
        "1-cell Li-Po on JST-PH (charged at 445 mA, VBAT/3 monitored on GPIO29)\n"
        "RP2350A + 16 MB QSPI flash + 8 MB QSPI PSRAM (GPIO8 = XIP_CS1)\n"
        "ESP32-C6-MINI-1 (Wi-Fi 6 / BLE 5) on UART1 with RTS/CTS flow control\n"
        "microSD (SDIO 4-bit / SPI), Qwiic I2C0, WS2812B-2020 RGB LED, user LED\n",
        30, 140, 1.6)
    root.text(
        "GPIO map\n"
        "GP0/GP1  UART0 TX/RX (header)\n"
        "GP2-GP5  header\n"
        "GP6      ~PGOOD (USB power present, low)\n"
        "GP7      ~CHG (charging, low)\n"
        "GP8      PSRAM CS (XIP_CS1)\n"
        "GP9      microSD card detect\n"
        "GP10-15  microSD CLK, CMD, D0-D3\n",
        30, 185, 1.6)
    root.text(
        "\n"
        "GP16/17  I2C0 SDA/SCL (Qwiic + header)\n"
        "GP18     ESP32-C6 EN\n"
        "GP19     ESP32-C6 IO9 (boot strap)\n"
        "GP20-23  UART1 TX/RX/CTS/RTS to ESP32-C6\n"
        "GP24     WS2812B data, GP25 user LED\n"
        "GP26-28  ADC0-2 (header)\n"
        "GP29     VBAT/3 (ADC3)\n",
        140, 185, 1.6)
    root.write('A3', 'Top level')
    print('root written')


if __name__ == '__main__':
    main()
