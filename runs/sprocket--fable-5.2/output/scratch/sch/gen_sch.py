"""Generates rp2350-devboard.kicad_sch. Coordinates are in 2.54 mm grid units."""
import json, sys, os
from schlib import Sch, POWER

OUTPATH = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = json.load(open(os.path.join(HERE, 'parts.json')))
# sourcing data (manufacturer, MPN, distributor numbers, datasheet) from the two sourcing passes
for f in ('parts-A.json', 'parts-B.json'):
    for key, src in json.load(open(os.path.join(HERE, '..', f))).items():
        PARTS[key].update({k: v for k, v in src.items() if k not in ('desc', 'notes')})
G = 2.54
s = Sch(OUTPATH)


def g(v):
    return round(v * G, 3)


def P(key, lib, ref, x, y, o=0, value=None, **kw):
    p = PARTS[key]
    fields = {k: p.get(k, '') for k in ('Manufacturer', 'MPN', 'Digikey Part #', 'Mouser Part #', 'LCSC Part #')}
    return s.place(lib, ref, g(x), g(y), o, value or p['value'], p['fp'], fields, ds=p.get('ds'), **kw)


def N(ref, mapping, L=1, side=False):
    s.nets(ref, mapping, L * G, side)


def W(*pts):
    s.wire(*[(g(x), g(y)) for x, y in pts])


def J(x, y):
    s.junction(g(x), g(y))


def NA(net, x, y, d, L=1):
    s.net_at(net, g(x), g(y), d, L * G)


def pin(ref, p):
    x, y = s.pin(ref, p)
    return round(x / G, 3), round(y / G, 3)


VT = dict(refpos=(2.3, -1.27), valpos=(2.3, 1.27))       # vertical two-pin part: texts to the right
HT = dict(refpos=(0, -2.3, 'c'), valpos=(0, 2.3, 'c'))   # horizontal: ref above, value below
HA = dict(refpos=(-3.2, -2.3, 'c'), valpos=(2.6, -2.3, 'c'))
CA = dict(refpos=(-3.2, -3.4, 'c'), valpos=(2.6, -3.4, 'c'))
CB = dict(refpos=(-3.2, 3.4, 'c'), valpos=(2.6, 3.4, 'c'))  # horizontal: both above
HB = dict(refpos=(-3.2, 2.3, 'c'), valpos=(2.6, 2.3, 'c'))    # horizontal: both below


def Rv(key, ref, x, y, top, bot, **kw):
    P(key, 'Device:R', ref, x, y, 0, **{**VT, **kw})
    N(ref, {k: v for k, v in (('1', top), ('2', bot)) if v}, 0.5)


def Cv(key, ref, x, y, top, bot, **kw):
    P(key, 'Device:C', ref, x, y, 0, **{**VT, **kw})
    N(ref, {k: v for k, v in (('1', top), ('2', bot)) if v}, 0.5)


def Rh(key, ref, x, y, left=None, right=None, t=HT, sym='Device:R'):
    P(key, sym, ref, x, y, 90, **t)
    if left:
        N(ref, {'1': left})
    if right:
        N(ref, {'2': right})


def block(title, x1, y1, x2, y2):
    s.box(g(x1), g(y1), g(x2), g(y2))
    s.text(title, g(x1 + 0.6), g(y1 + 1.6), 2.0, True)


# ---------------------------------------------------------------- USB-C
block('USB-C, ESD protection', 4, 6, 46, 50)
P('usbc', 'Connector:USB_C_Receptacle_USB2.0_16P', 'J1', 14, 27)
N('J1', {'A4': 'VBUS', 'A1': 'GND', 'SH': 'GND', 'A8': None, 'B8': None})
W((20, 23), (24.5, 23))
P('r5k1', 'Device:R', 'R1', 26, 23, 90, **HA)
W((20, 24), (24.5, 24))
P('r5k1', 'Device:R', 'R2', 26, 24, 90, **HB)
s.label('CC1', g(21), g(23), (1, 0))
s.label('CC2', g(21), g(24), (1, 0))
W((27.5, 23), (30, 23), (30, 24), (30, 25))
W((27.5, 24), (30, 24))
J(30, 24)
s.power('GND', g(30), g(25))
W((20, 26), (22, 26), (22, 27), (20, 27))                      # D- A7/B7
NA('USB_CONN_DN', 22, 26, (1, 0))
W((20, 28), (22, 28), (22, 29), (20, 29))                      # D+ A6/B6
NA('USB_CONN_DP', 22, 28, (1, 0))
P('usblc6', 'Power_Protection:USBLC6-2SC6', 'U6', 16, 44, refpos=(5, -9), valpos=(5, -6.5))
N('U6', {'1': 'USB_CONN_DP', '3': 'USB_CONN_DN', '6': 'USB_CONN_DP', '4': 'USB_CONN_DN', '5': 'VBUS', '2': 'GND'})
Rh('r27', 'R3', 36, 42, 'USB_CONN_DP', 'USB_DP')
Rh('r27', 'R4', 36, 46, 'USB_CONN_DN', 'USB_DM')
Cv('c10u25', 'C1', 29, 14, 'VBUS', 'GND')
s.flag(g(39), g(12.5))
W((39, 12.5), (43, 12.5))
s.power('VBUS', g(43), g(12.5))
s.flag(g(39), g(17))
W((39, 17), (43, 17))
s.power('GND', g(43), g(17))

# ---------------------------------------------------------------- charger
block('LiPo charger with power path (500 mA USB limit, 494 mA charge)', 48, 6, 102, 50)
P('bq24074', 'Battery_Management:BQ24074RGT', 'U4', 68, 22, refpos=(3, -17), valpos=(3, -14.5))
N('U4', {'IN': 'VBUS', 'VSS': 'GND', '~{CE}': 'GND', 'EN2': 'GND', 'ITERM': None, 'TMR': None,
         '~{PGOOD}': '~{PGOOD}', '~{CHG}': '~{CHG}', 'BAT': 'VBAT'}, 2)
N('U4', {'EN1': 'CHG_EN1'}, 5)
# ILIM / ISET resistors
W((63, 25), (58, 25), (58, 26.5))
Rv('r1k5', 'R5', 58, 28, None, 'GND', refpos=(-2.3, -1.27, 'r'), valpos=(-2.3, 1.27, 'r'))
W((63, 26), (62, 26), (62, 27.5))
Rv('r1k8', 'R6', 62, 29, None, 'GND')
# EN1 divider from VBUS
Rv('r100k', 'R8', 52, 11.5, 'VBUS', None)
Rv('r100k', 'R9', 52, 17.5, None, 'GND')
W((52, 13), (52, 14.5))
W((52, 14.5), (52, 16))
NA('CHG_EN1', 52, 14.5, (1, 0))
J(52, 14.5)
# OUT -> VSYS with output capacitor
W((73, 18), (82, 18))
W((82, 18), (85, 18))
s.label('VSYS', g(85), g(18), (1, 0))
Cv('c10u25', 'C2', 82, 19.5, None, 'GND')
# TS
W((73, 23), (75, 23))
Rh('r10k', 'R7', 76.5, 23, None, 'GND', t=HA)
# status LEDs
for i, (rr, dd, net, key) in enumerate((('R10', 'D2', '~{PGOOD}', 'led_g'), ('R11', 'D3', '~{CHG}', 'led_a'))):
    x = 84 + 9 * i
    Rv('r2k2', rr, x, 30, None, None)
    NA('VSYS', x, 28.5, (0, -1))
    P(key, 'Device:LED', dd, x, 33, 90, refpos=(5.5, -1.27, 'c'), valpos=(5.5, 1.27, 'c'))
    NA(net, x, 34.5, (0, 1))
# battery connector, capacitor, sense divider
P('jst_ph', 'Connector_Generic_MountingPin:Conn_01x02_MountingPin', 'J2', 96, 12, refpos=(0, -7.5, 'c'), valpos=(0, -5, 'c'))
N('J2', {'1': PARTS['jst_ph']['pin1'], '2': PARTS['jst_ph']['pin2']}, 2, side=True)
N('J2', {'MP': 'GND'})
Cv('c10u25', 'C3', 82, 12, 'VBAT', 'GND')
Rv('r100k', 'R13', 56, 39, 'VBAT', None)
Rv('r100k', 'R14', 56, 44, None, 'GND')
W((56, 40.5), (56, 41.5))
W((56, 41.5), (56, 42.5))
W((56, 41.5), (62, 41.5))
W((62, 41.5), (66, 41.5))
s.label('VBAT_SENSE', g(66), g(41.5), (1, 0))
J(56, 41.5)
J(62, 41.5)
W((62, 41.5), (62, 42.5))
Cv('c100n', 'C30', 62, 44, None, 'GND')
s.text('VBAT_SENSE = VBAT / 2 on GPIO28 (ADC2)', g(50), g(49), 1.27)

# ---------------------------------------------------------------- 3V3 LDO
block('3.3 V regulator', 104, 6, 136, 30)
P('ldo', 'Regulator_Linear:TLV75733PDBV', 'U5', 119, 16, refpos=(-7, -9), valpos=(-7, -6.5))
N('U5', {'GND': 'GND', 'NC': None})
assert pin('U5', 'IN') == (116, 15) and pin('U5', 'OUT') == (122, 15)
W((116, 15), (112, 15))
W((112, 15), (109, 15))
s.label('VSYS', g(109), g(15), (-1, 0))
Cv('c1u', 'C4', 112, 16.5, None, 'GND', refpos=(-2.3, -0.5, 'r'), valpos=(-2.3, 2, 'r'))
J(112, 15)
W((116, 16), (115, 16), (115, 21))
s.label('EN', g(115), g(21), (0, 1))
W((122, 15), (126, 15))
W((126, 15), (130, 15))
s.power('+3V3', g(130), g(15))
Cv('c10u25', 'C5', 126, 16.5, None, 'GND')
J(126, 15)
Rh('r100k', 'R12', 124, 26, 'VSYS', 'EN')

# ---------------------------------------------------------------- MCU
block('RP2350A, core regulator, crystal, decoupling', 4, 52, 58, 113)
P('rp2350', 'MCU_RaspberryPi:RP2350A', 'U1', 38, 80, refpos=(8, -47.5), valpos=(8, 47.5))
gp = {0: 'GP0', 1: 'GP1', 2: 'GP2', 3: 'GP3', 4: 'GP4_SDA', 5: 'GP5_SCL', 6: 'GP6', 7: 'GP7', 8: 'PSRAM_CS',
      9: 'RGB_DIN', 10: 'SD_CLK', 11: 'SD_CMD', 12: 'SD_DAT0', 13: 'SD_DAT1', 14: 'SD_DAT2', 15: 'SD_DAT3',
      16: 'GP16', 17: 'GP17', 18: 'GP18', 19: 'GP19', 20: 'GP20', 21: 'GP21', 22: 'GP22', 23: 'WL_ON',
      24: 'WL_D', 25: 'WL_CS', 26: 'GP26_A0', 27: 'GP27_A1', 28: 'VBAT_SENSE', 29: 'WL_CLK'}
names = {n: (f'GPIO{n}' if n < 26 else f'GPIO{n}/ADC{n - 26}') for n in gp}
N('U1', {names[n]: net for n, net in gp.items()})
N('U1', {'RUN': 'RUN', 'USB_DM': 'USB_DM', 'USB_DP': 'USB_DP', '~{QSPI_SS}': 'QSPI_SS', 'QSPI_SCLK': 'QSPI_SCLK',
         'QSPI_SD0': 'QSPI_SD0', 'QSPI_SD1': 'QSPI_SD1', 'QSPI_SD2': 'QSPI_SD2', 'QSPI_SD3': 'QSPI_SD3',
         'SWCLK': 'SWCLK', 'SWDIO': 'SWDIO'})
# 3V3 pins
for x in (33, 34, 36, 37, 39):
    W((x, 62), (x, 60))
W((33, 60), (34, 60))
W((34, 60), (36, 60))
W((36, 60), (37, 60))
W((37, 60), (39, 60))
for x in (34, 37):
    J(x, 60)
s.power('+3V3', g(36), g(60))
# 1V1 pins
W((41, 62), (41, 60), (43, 60))
W((43, 62), (43, 60))
W((43, 60), (45, 60))
J(43, 60)
s.power('+1V1', g(45), g(60))
# switching regulator
W((40, 62), (40, 58.5))
s.label('VREG_LX', g(40), g(58.5), (0, -1))
P('ind', 'Device:L', 'L1', 15, 56.5, 90, **HT)
N('L1', {'2': 'VREG_LX'})
W((13.5, 56.5), (11, 56.5))
W((11, 56.5), (6.5, 56.5))
s.power('+1V1', g(11), g(56.5))
s.flag(g(6.5), g(56.5))
Cv('c4u7', 'C7', 8, 64.5, '+1V1', 'GND')
Cv('c4u7', 'C6', 13, 64.5, '+3V3', 'GND')
s.text('L1 dot (pin 1) to +1V1', g(6.5), g(60), 1.0)
P('r33', 'Device:R', 'R15', 20.5, 60, 90, **HB)
N('R15', {'1': '+3V3'}, 0.5)
W((22, 60), (25, 60))
W((25, 60), (28, 60))
W((28, 60), (31, 60), (31, 62))
Cv('c4u7', 'C8', 25, 61.5, None, 'GND')
J(25, 60)
s.flag(g(28), g(60))
# ground
W((37, 98), (37, 99), (38, 99))
W((38, 98), (38, 99))
s.power('GND', g(38), g(99))
# crystal
W((28, 86), (14, 86))
W((14, 86), (14, 86.5))
P('xtal', 'Device:Crystal_GND24', 'Y1', 14, 88, 270, refpos=(5.5, -1.27, 'l'), valpos=(5.5, 1.27, 'l'))
W((14, 89.5), (14, 90))
W((14, 90), (22, 90))
P('r1k', 'Device:R', 'R16', 23.5, 90, 90, **HB)
W((25, 90), (28, 90))
N('Y1', {'2': 'GND'})
W((14, 86), (11, 86))
P('c15p', 'Device:C', 'C20', 9.5, 86, 90, **CA)
N('C20', {'1': 'GND'})
J(14, 86)
W((14, 90), (11, 90))
P('c15p', 'Device:C', 'C21', 9.5, 90, 90, **CB)
N('C21', {'1': 'GND'}, 2)
J(14, 90)
# decoupling
for i, ref in enumerate(['C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C18', 'C19']):
    Cv('c100n', ref, 8 + 6 * i, 106, '+3V3', 'GND')
s.text('IOVDD x6 (C9 to C14)', g(7), g(112), 1.0)
s.text('QSPI_IOVDD + USB_OTP_VDD', g(40), g(112), 1.0)
s.text('ADC_AVDD', g(51.5), g(112.7), 1.0)
for i, ref in enumerate(['C15', 'C16', 'C17']):
    Cv('c100n', ref, 7 + 4.5 * i, 73, '+1V1', 'GND')
s.text('DVDD x3', g(6), g(78.7), 1.0)

# ---------------------------------------------------------------- memories and buttons
block('16 MB QSPI flash, 8 MB QSPI PSRAM, BOOT and RESET', 60, 52, 102, 84)
P('flash', 'Memory_Flash:W25Q128JVP', 'U2', 72, 64, refpos=(5, 15), valpos=(5, 17.5))
N('U2', {'~{CS}': 'QSPI_SS', 'CLK': 'QSPI_SCLK', 'DI/IO_{0}': 'QSPI_SD0', 'DO/IO_{1}': 'QSPI_SD1',
         '~{WP}/IO_{2}': 'QSPI_SD2', '~{HOLD}/~{RESET}/IO_{3}': 'QSPI_SD3', 'VCC': '+3V3'})
W((72, 69), (72, 70))
W((73, 69), (73, 70), (72, 70))
s.power('GND', g(72), g(70))
Cv('c100n', 'C22', 78, 58, '+3V3', 'GND')
P('psram', 'Memory_RAM:APS6404L-3SQRx-SN', 'U3', 91, 64, refpos=(3, 15), valpos=(3, 17.5))
N('U3', {'~{CE}': 'PSRAM_CS', 'SCLK': 'QSPI_SCLK', 'SI/SIO0': 'QSPI_SD0', 'SO/SIO1': 'QSPI_SD1', 'SIO2': 'QSPI_SD2',
         'SIO3': 'QSPI_SD3', 'VDD': '+3V3', 'VSS': 'GND'})
Cv('c1u', 'C23', 97, 58, '+3V3', 'GND')
Rh('r1k', 'R17', 69, 76, 'QSPI_SS', None)
W((70.5, 76), (73, 76))
P('sw', 'Switch:SW_Push', 'SW1', 75, 76, value='BOOT', refpos=(0, -5.8, 'c'), valpos=(0, 3, 'c'))
N('SW1', {'2': 'GND'})
Rh('r2k2', 'R19', 92, 76, '+3V3', 'PSRAM_CS')
P('sw', 'Switch:SW_Push', 'SW2', 75, 81, value='RESET', refpos=(0, -5.8, 'c'), valpos=(0, 3, 'c'))
N('SW2', {'1': 'RUN', '2': 'GND'})
Rh('r10k', 'R18', 92, 81, '+3V3', 'RUN')

# ---------------------------------------------------------------- radio
block('Wi-Fi 4 + Bluetooth 5.2 (Pico 2 W pinout)', 104, 32, 136, 84)
P('rm2', 'devboard:RM2', 'U7', 122, 56, refpos=(7, -15), valpos=(9.5, 15))
N('U7', {'WL_ON': 'WL_ON', 'BT_ON': 'WL_ON', 'CS': 'WL_CS', 'SCLK': 'WL_CLK', 'DI': 'WL_D', 'DO': 'WL_DO',
         'nIRQ': 'WL_IRQ', 'GPIO0': 'WL_GPIO0', 'GPIO1': None, 'GPIO2': None})
W((121, 50), (121, 49), (122, 49))
W((123, 50), (123, 49), (122, 49))
s.power('+3V3', g(122), g(49))
for x in (119.5, 120.5, 121.5, 122.5, 123.5, 124.5):
    W((x, 62), (x, 63))
for a, b in zip((119.5, 120.5, 121.5, 122.5, 123.5), (120.5, 121.5, 122.5, 123.5, 124.5)):
    W((a, 63), (b, 63))
W((122.5, 63), (122.5, 63.5))
s.power('GND', g(122.5), g(63.5))
Rh('r470', 'R20', 113, 68, 'WL_D', 'WL_DO')
Rh('r10k', 'R21', 113, 72, 'WL_D', 'WL_IRQ')
Rh('r470', 'R29', 113, 77, 'WL_GPIO0', None)
W((114.5, 77), (117.5, 77))
P('led_g', 'Device:LED', 'D4', 119, 77, 180, refpos=(0, -2.5, 'c'), valpos=(0, 2.7, 'c'))
N('D4', {'K': 'GND'})
s.text('User LED on WL_GPIO0', g(109), g(81.5), 1.0)
Cv('c4u7', 'C24', 107, 40, '+3V3', 'GND')
Cv('c100n', 'C25', 112, 40, '+3V3', 'GND')
Cv('c100n', 'C26', 131, 40, '+3V3', 'GND')

# ---------------------------------------------------------------- microSD
block('microSD (SPI1 or 4-bit SDIO)', 60, 86, 102, 113)
P('usd', 'Connector:Micro_SD_Card_Det_Hirose_DM3AT', 'J5', 88, 97, refpos=(-8, -15), valpos=(0, 19.5))
N('J5', {'DAT2': 'SD_DAT2', 'DAT3/CD': 'SD_DAT3', 'CMD': 'SD_CMD', 'CLK': 'SD_CLK', 'DAT0': 'SD_DAT0', 'DAT1': 'SD_DAT1',
         'DET_A': None, 'DET_B': None, 'SHIELD': 'GND'})
N('J5', {'VDD': '+3V3', 'VSS': 'GND'}, 8)
for i, (ref, net) in enumerate((('R24', 'SD_CMD'), ('R25', 'SD_DAT0'), ('R26', 'SD_DAT1'), ('R27', 'SD_DAT2'), ('R28', 'SD_DAT3'))):
    y = 104 + 2 * i
    Rh('r10k', ref, 66, y, None, net, t=dict(refpos=(0, -2.0, 'c'), valpos=(0, 2, 'c'), hide_value=True))
    W((64.5, y), (63, y))
    if i:
        W((63, y - 2), (63, y))
        if i < 4:
            J(63, y)
s.power('+3V3', g(63), g(104))
s.text('5x 10 kΩ', g(60.5), g(102), 1.0)
Cv('c10u04', 'C27', 80, 108.5, '+3V3', 'GND')
Cv('c100n', 'C28', 86, 108.5, '+3V3', 'GND')

# ---------------------------------------------------------------- RGB LED
block('Addressable RGB LED', 104, 86, 136, 101)
P('rgb', PARTS['rgb']['sym'], 'D1', 114, 94.5, refpos=(4, -8.5), valpos=(4, 8.5))
N('D1', {'DIN': 'RGB_DIN', 'DOUT': None, 'VDD': '+3V3', 'VSS': 'GND'})
Cv('c100n', 'C29', 127, 94.5, '+3V3', 'GND')

# ---------------------------------------------------------------- connectors
block('Headers, Qwiic, debug', 138, 6, 161, 99)
P('hdr', 'Connector_Generic:Conn_01x12', 'J6', 152, 16, refpos=(0, -16), valpos=(0, 18.5), hide_value=True)
N('J6', dict((str(i + 1), n) for i, n in enumerate(
    [None, 'VSYS', None, 'GP27_A1', 'GP26_A0', 'GP22', 'GP21', 'GP20', 'GP19', 'GP18', 'GP17', 'GP16']) if n), side=True)
N('J6', {'1': 'VBUS'}, 3, side=True)
N('J6', {'3': 'GND'}, 5, side=True)
P('hdr', 'Connector_Generic:Conn_01x12', 'J7', 152, 32, refpos=(0, -16), valpos=(0, 18.5), hide_value=True)
N('J7', dict((str(i + 1), n) for i, n in enumerate(
    [None, 'EN', 'RUN', None, 'GP0', 'GP1', 'GP2', 'GP3', 'GP4_SDA', 'GP5_SCL', 'GP6', 'GP7']) if n), side=True)
N('J7', {'1': '+3V3'}, 3, side=True)
N('J7', {'4': 'GND'}, 5, side=True)
P('jst_sh4', 'Connector_Generic_MountingPin:Conn_01x04_MountingPin', 'J3', 153, 54, refpos=(0, -7.5), valpos=(0, -5))
N('J3', {'1': 'GND', '3': 'GP4_SDA', '4': 'GP5_SCL'}, side=True)
N('J3', {'2': '+3V3'}, 5, side=True)
N('J3', {'MP': 'GND'})
Rh('r2k2', 'R22', 147, 64, '+3V3', 'GP4_SDA')
Rh('r2k2', 'R23', 147, 68, '+3V3', 'GP5_SCL')
P('jst_sh3', 'Connector_Generic_MountingPin:Conn_01x03_MountingPin', 'J4', 153, 78, refpos=(0, -7.5), valpos=(0, -5.2))
N('J4', {'1': 'SWCLK_C', '3': 'SWDIO_C'}, side=True)
N('J4', {'2': 'GND'}, 5, side=True)
N('J4', {'MP': 'GND'})
s.text('Raspberry Pi 3-pin debug', g(141), g(84.5), 1.0)
Rh('r100', 'R30', 148, 88, 'SWCLK', 'SWCLK_C')
Rh('r100', 'R31', 148, 92, 'SWDIO', 'SWDIO_C')
for i in range(3):
    P('fid', 'Mechanical:Fiducial', f'FID{i + 1}', 143 + 6 * i, 97, refpos=(-3.6, 0, 'c'), hide_value=True)

tb = s.s.get_title_block()
tb.title = 'RP2350 Wi-Fi dev board'
tb.revision = 'A'
tb.date = '2026-11-10'
tb.company = 'Open hardware, built for PCBWay turnkey assembly'
s.s.set_title_block(tb)
s.save()
print('saved', len(s.parts), 'parts')
