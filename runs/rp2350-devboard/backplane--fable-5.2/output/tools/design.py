"""Single source of truth for the RP2350 dev board: parts, nets, placement.
Schematic and PCB are generated from this by build_sch.py / build_pcb.py."""
NAME = 'rp2350-devboard'
W, H = 76.2, 22.86          # board size (mm)
OX, OY = 100.0, 80.0        # board origin on the KiCad page
HX0, HPITCH = 36.0, 2.54    # header pin 1 x, pitch
MX, MY = 47.5, 11.43        # MCU centre
RX, RY = W - 8.25, 11.43    # RM2 centre

PWR = {'GND', '+3V3', '+1V1', 'VBUS', 'VBAT', 'VSYS'}
P = []   # parts


def part(ref, lib, value, fp, nets, pos, sch, mpn='', mfr='', lcsc='', desc='', bom=True, layer='F', extra=None):
    P.append(dict(ref=ref, lib=lib, value=value, fp=fp, nets=nets, pos=pos, sch=sch, mpn=mpn, mfr=mfr,
                  lcsc=lcsc, desc=desc, bom=bom, layer=layer, extra=extra or {}))

R0402 = 'Resistor_SMD:R_0402_1005Metric'
C0402 = 'Capacitor_SMD:C_0402_1005Metric'
C0603 = 'Capacitor_SMD:C_0603_1608Metric'
RES = {  # value -> (mpn, lcsc)
    '5.1k': ('RC0402FR-075K1L', ''), '27R': ('RC0402FR-0727RL', ''),
    '10k': ('RC0402FR-0710KL', ''), '1.5k': ('RC0402FR-071K5L', ''),
    '3.0k': ('RC0402FR-073KL', ''), '100k': ('RC0402FR-07100KL', ''),
    '150k': ('RC0402FR-07150KL', ''), '2.2k': ('RC0402FR-072K2L', ''),
    '200k': ('RC0402FR-07200KL', ''), '33R': ('RC0402FR-0733RL', ''),
    '1k': ('RC0402FR-071KL', ''), '47k': ('RC0402FR-0747KL', ''),
    '470R': ('RC0402FR-07470RL', ''),
}
CAP = {
    '100nF': (C0402, 'CL05B104KO5NNNC', '', '100nF 16V X7R 0402'),
    '4.7uF': (C0402, 'CL05A475MP5NRNC', '', '4.7uF 10V X5R 0402'),
    '1uF': (C0402, 'CL05A105KA5NQNC', '', '1uF 25V X5R 0402'),
    '15pF': (C0402, 'CL05C150JB5NNNC', '', '15pF 50V C0G 0402'),
    '10uF': (C0603, 'CL10A106MA8NRNC', '', '10uF 25V X5R 0603'),
    '4.7uF/25V': (C0603, 'CL10A475KA8NQNC', '', '4.7uF 25V X5R 0603'),
}


def R(ref, value, a, b, pos, sch):
    mpn, lcsc = RES[value]
    part(ref, 'Device:R', value, R0402, {'1': a, '2': b}, pos, sch, mpn, 'Yageo', lcsc,
         'Resistor %s 1%% 0402' % value)


def C(ref, value, a, b, pos, sch):
    fp, mpn, lcsc, d = CAP[value]
    part(ref, 'Device:C', value.split('/')[0], fp, {'1': a, '2': b}, pos, sch, mpn, 'Samsung', lcsc, 'Capacitor ' + d)

# ---------------------------------------------------------------- USB-C + ESD
part('J1', 'Connector:USB_C_Receptacle_USB2.0_16P', 'USB-C', 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',
     {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND', 'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS',
      'B9': 'VBUS', 'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP', 'A7': 'USB_DM', 'B7': 'USB_DM',
      'A8': None, 'B8': None},
     (3.0, 6.2, 270), (40, 60), 'TYPE-C-31-M-12', 'Korean Hroparts Elec', 'C165948',
     'USB Type-C receptacle, USB 2.0, 16 pin, SMD mid-mount shell THT')
R('R1', '5.1k', 'CC1', 'GND', (8.95, 3.6, 270), (75, 45, 'h'))
R('R2', '5.1k', 'CC2', 'GND', (8.95, 8.9, 270), (75, 52.5, 'h'))
part('U6', 'Power_Protection:USBLC6-2SC6', 'USBLC6-2SC6', 'Package_TO_SOT_SMD:SOT-23-6',
     {'1': 'USB_DM', '6': 'USB_DM', '3': 'USB_DP', '4': 'USB_DP', '2': 'GND', '5': 'VBUS'},
     (11.6, 6.2, 0), (100, 62), 'USBLC6-2SC6', 'STMicroelectronics', 'C7519', 'USB ESD protection, SOT-23-6')
R('R3', '27R', 'USB_DP', 'USB_DP_R', (37.0, 11.78, 0), (75, 77.5, 'h'))
R('R4', '27R', 'USB_DM', 'USB_DM_R', (37.0, 10.72, 0), (75, 85, 'h'))

# ---------------------------------------------------------------- charger / power path
part('U4', 'Battery_Management:BQ24074RGT', 'BQ24074RGTR', 'Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm',
     {'1': 'TS', '2': 'VBAT', '3': 'VBAT', '4': 'GND', '5': 'GND', '6': 'VBUS_DET', '7': None, '8': 'GND', '17': 'GND',
      '9': 'CHG_N', '10': 'VSYS', '11': 'VSYS', '12': 'ILIM', '13': 'VBUS', '14': None, '15': None, '16': 'ISET'},
     (17.6, 4.6, 0), (170, 50), 'BQ24074RGTR', 'Texas Instruments', 'C54313',
     '1.5A single-cell Li-ion charger with power path, VQFN-16')
C('C1', '4.7uF/25V', 'VBUS', 'GND', (18.2, 1.3, 0), (140, 40, 'v'))
C('C2', '10uF', 'VSYS', 'GND', (20.7, 4.6, 270), (200, 50, 'v'))
C('C3', '10uF', 'VBAT', 'GND', (14.6, 4.4, 90), (212, 50, 'v'))
R('R5', '10k', 'TS', 'GND', (13.85, 2.3, 180), (200, 65, 'h'))
R('R6', '1.5k', 'ILIM', 'GND', (20.65, 2.2, 0), (140, 72.5, 'h'))
R('R7', '3.0k', 'ISET', 'GND', (15.75, 1.5, 180), (140, 80, 'h'))
R('R8', '100k', 'VBUS', 'VBUS_DET', (16.4, 7.7, 0), (140, 57.5, 'h'))
R('R9', '150k', 'VBUS_DET', 'GND', (18.4, 7.7, 0), (140, 65, 'h'))
R('R10', '2.2k', 'VBUS', 'CHG_A', (22.75, 2.7, 0), (200, 72.5, 'h'))
part('D2', 'Device:LED', 'ORANGE', 'LED_SMD:LED_0603_1608Metric', {'1': 'CHG_N', '2': 'CHG_A'},
     (22.7, 5.0, 90), (200, 80), 'XL-1608UOC-06', 'XINGLIGHT', 'C965800', 'LED orange 0603 (charging)')
part('J2', 'Connector_Generic_MountingPin:Conn_01x02_MountingPin', 'LiPo',
     'Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal', {'1': 'GND', '2': 'VBAT', 'MP': 'GND'},
     (4.9, 17.0, 270), (235, 62), 'S2B-PH-SM4-TB(LF)(SN)', 'JST', 'C295747', 'JST PH 2-pin side-entry SMD, single-cell LiPo')

# ---------------------------------------------------------------- 3V3 LDO, battery sense
part('U5', 'Regulator_Linear:TLV75733PDBV', 'TLV75733PDBVR', 'Package_TO_SOT_SMD:SOT-23-5',
     {'1': 'VSYS', '2': 'GND', '3': 'EN', '4': None, '5': '+3V3'},
     (28.0, 11.2, 0), (278, 45), 'TLV75733PDBVR', 'Texas Instruments', 'C485517', '3.3V 1A LDO, SOT-23-5')
C('C5', '1uF', 'VSYS', 'GND', (25.4, 9.9, 270), (258, 52, 'v'))
C('C4', '10uF', '+3V3', 'GND', (31.1, 11.2, 270), (298, 52, 'v'))
R('R11', '100k', 'VSYS', 'EN', (25.9, 13.6, 0), (262, 68, 'h'))
R('R12', '200k', 'VBAT', 'BAT_SENSE', (30.9, 7.35, 180), (262, 80, 'h'))
R('R13', '200k', 'BAT_SENSE', 'GND', (30.9, 8.29, 0), (287, 80, 'h'))
C('C6', '100nF', 'BAT_SENSE', 'GND', (30.9, 9.23, 0), (306, 82, 'v'))

# ---------------------------------------------------------------- MCU
mcu = {'61': 'GND', '47': 'GND', '44': '+3V3', '53': '+3V3', '54': '+3V3', '49': '+3V3', '46': 'VREG_AVDD',
       '48': 'VREG_LX', '50': '+1V1', '21': 'XIN', '22': 'XOUT', '24': 'SWCLK', '25': 'SWDIO', '26': 'RUN',
       '51': 'USB_DM_R', '52': 'USB_DP_R', '55': 'QSPI_SD3', '56': 'QSPI_SCLK', '57': 'QSPI_SD0', '58': 'QSPI_SD2',
       '59': 'QSPI_SD1', '60': 'QSPI_SS'}
for p in (1, 11, 20, 30, 38, 45): mcu[str(p)] = '+3V3'
for p in (6, 23, 39): mcu[str(p)] = '+1V1'
GPIO = {0: 'PSRAM_CS', 1: 'SD_CD', 2: 'SD_CLK', 3: 'SD_CMD', 4: 'SD_D0', 5: 'SD_D1', 6: 'SD_D2', 7: 'SD_D3',
        8: 'GP8', 9: 'GP9', 10: 'GP10', 11: 'GP11', 12: 'GP12', 13: 'GP13', 14: 'GP14', 15: 'GP15',
        16: 'WL_ON', 17: 'WL_CS', 18: 'WL_D', 19: 'WL_CLK', 20: 'GP20', 21: 'GP21', 22: 'GP22', 23: 'RGB_DIN',
        24: 'SDA', 25: 'SCL', 26: 'GP26_A0', 27: 'GP27_A1', 28: 'GP28_A2', 29: 'BAT_SENSE'}
GPIN = {0: 2, 1: 3, 2: 4, 3: 5, 4: 7, 5: 8, 6: 9, 7: 10, 8: 12, 9: 13, 10: 14, 11: 15, 12: 16, 13: 17, 14: 18, 15: 19,
        16: 27, 17: 28, 18: 29, 19: 31, 20: 32, 21: 33, 22: 34, 23: 35, 24: 36, 25: 37, 26: 40, 27: 41, 28: 42, 29: 43}
for g, n in GPIO.items(): mcu[str(GPIN[g])] = n
part('U1', 'MCU_RaspberryPi:RP2350A', 'RP2350A', 'Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm', mcu,
     (MX, MY, 90), (128, 195), 'RP2350A0A4', 'Raspberry Pi', 'C42411118',
     'Dual Cortex-M33 / RISC-V MCU, QFN-60 (A4 stepping)')
# decoupling: (ref, net, pcb pos)
for i, (ref, val, net, pos) in enumerate([
        ('C7', '100nF', '+3V3', (46.6, 18.2, 0)), ('C8', '100nF', '+3V3', (44.55, 18.2, 180)),
        ('C9', '100nF', '+3V3', (54.4, 15.7, 180)), ('C10', '100nF', '+3V3', (43.75, 4.05, 270)),
        ('C11', '100nF', '+3V3', (52.1, 7.3, 90)), ('C12', '100nF', '+3V3', (44.7, 6.15, 90)),
        ('C13', '100nF', '+3V3', (42.45, 11.63, 180)), ('C15', '100nF', '+3V3', (43.75, 6.0, 90)),
        ('C19', '4.7uF', '+3V3', (42.9, 9.43, 90)), ('C16', '100nF', '+1V1', (44.7, 4.2, 90)),
        ('C17', '100nF', '+1V1', (54.4, 17.7, 180)), ('C18', '100nF', '+1V1', (54.4, 16.7, 180)),
        ('C21', '4.7uF', '+1V1', (41.3, 9.43, 90)), ('C20', '4.7uF', 'VREG_AVDD', (42.45, 7.55, 0))]):
    C(ref, val, net, 'GND', pos, (25 + 11.43 * (i % 8), 125 + 22 * (i // 8), 'v'))
R('R14', '33R', '+3V3', 'VREG_AVDD', (40.55, 7.55, 0), (40, 172.5, 'h'))
part('L1', 'Device:L', '3.3uH', 'Inductor_SMD:L_Murata_DFE201610P', {'1': '+1V1', '2': 'VREG_LX'},
     (39.7, 9.3, 90), (40, 180, 'h'), 'AOTA-B201610S3R3-101-T', 'Abracon', 'C42411119',
     '3.3uH polarised inductor for RP2350 core SMPS, 2016')
part('Y1', 'Device:Crystal_GND24', '12MHz', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',
     {'1': 'XIN', '3': 'XTAL_O', '2': 'GND', '4': 'GND'}, (56.2, 12.55, 90), (40, 218), 'ABM8-272-T3', 'Abracon',
     'C20625731', '12MHz crystal 10pF 3225')
C('C23', '15pF', 'XIN', 'GND', (57.05, 15.6, 270), (25, 230, 'v'))
C('C24', '15pF', 'XTAL_O', 'GND', (54.3, 9.6, 0), (55, 230, 'v'))
R('R15', '1k', 'XOUT', 'XTAL_O', (53.5, 11.2, 90), (40, 202.5, 'h'))
part('SW2', 'Switch:SW_Push', 'RESET', 'Button_Switch_SMD:SW_SPST_B3U-1000P', {'1': 'RUN', '2': 'GND'},
     (35.8, 5.4, 180), (40, 255), 'B3U-1000P', 'Omron', 'C231329', 'Tactile switch 3x2.5mm SMD')
for i, (ref, net, x, y, d) in enumerate((('TP1', 'SWCLK', 51.1, 10.75, '1.0'), ('TP2', 'SWDIO', 53.6, 10.9, '1.0'),
                                        ('TP3', 'GND', 57.58, 5.0, '1.5'))):
    part(ref, 'Connector:TestPoint', net, 'TestPoint:TestPoint_Pad_D%smm' % d, {'1': net}, (x, y, 0),
         (25 + 14 * i, 272), bom=False, layer='B', desc='SWD test pad (bottom side)')

# ---------------------------------------------------------------- QSPI flash + PSRAM
part('U2', 'Memory_Flash:W25Q128JVP', 'W25Q128JVPIQ', 'Package_SON:WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm',
     {'1': 'QSPI_SS', '2': 'QSPI_SD1', '3': 'QSPI_SD2', '4': 'GND', '5': 'QSPI_SD0', '6': 'QSPI_SCLK',
      '7': 'QSPI_SD3', '8': '+3V3', '9': 'GND'},
     (37.1, 15.5, 0), (245, 130), 'W25Q128JVPIQ', 'Winbond', 'C190862', '128Mbit QSPI NOR flash, WSON-8 6x5')
part('U3', 'Memory_RAM:APS6404L-3SQRx-ZR', 'APS6404L-3SQR-ZR', 'Package_SON:Winbond_USON-8-1EP_3x2mm_P0.5mm_EP0.2x1.6mm',
     {'1': 'PSRAM_CS', '2': 'QSPI_SD1', '3': 'QSPI_SD2', '4': 'GND', '5': 'QSPI_SD0', '6': 'QSPI_SCLK',
      '7': 'QSPI_SD3', '8': '+3V3', '9': 'GND'},
     (35.1, 8.3, 0), (245, 175), 'APS6404L-3SQR-ZR', 'AP Memory', 'C3040877', '64Mbit QSPI PSRAM, USON-8 3x2')
C('C25', '100nF', '+3V3', 'GND', (39.0, 12.2, 180), (275, 120, 'v'))
C('C26', '100nF', '+3V3', 'GND', (38.7, 6.9, 90), (275, 165, 'v'))
R('R17', '10k', '+3V3', 'QSPI_SS', (34.7, 12.25, 180), (215, 145, 'h'))
R('R18', '1k', 'QSPI_SS', 'BOOT', (32.8, 12.8, 180), (215, 152.5, 'h'))
R('R19', '10k', '+3V3', 'PSRAM_CS', (45.9, 19.3, 0), (215, 190, 'h'))
part('SW1', 'Switch:SW_Push', 'BOOT', 'Button_Switch_SMD:SW_SPST_B3U-1000P', {'1': 'BOOT', '2': 'GND'},
     (30.6, 18.2, 0), (215, 162), 'B3U-1000P', 'Omron', 'C231329', 'Tactile switch 3x2.5mm SMD')

# ---------------------------------------------------------------- RM2 radio
part('U7', 'rp2350-devboard:RM2', 'RM2', 'RF_Module:RMC20452T',
     {'1': 'GND', '4': 'GND', '7': 'GND', '11': 'GND', '15': 'GND', '21': 'GND', '2': None, '19': None, '20': None,
      '3': 'WL_CLK', '5': 'WL_D', '6': 'WL_DOUT', '8': 'WL_GPIO0', '9': 'WL_CS', '10': 'WL_IRQ', '12': 'WL_ON',
      '13': 'WL_ON', '14': '+3V3', '16': '+3V3', '17': None, '18': None},
     (RX, RY, 270), (368, 55), 'RMC20452T', 'Raspberry Pi', 'C49451547',
     'Raspberry Pi Radio Module 2 (CYW43439), 2.4GHz Wi-Fi 4 + Bluetooth 5.2')
R('R25', '470R', 'WL_DOUT', 'WL_D', (57.9, 4.4, 180), (335, 76, 'h'))
R('R26', '10k', 'WL_D', 'WL_IRQ', (57.9, RY - 1.5, 0), (335, 83.5, 'h'))
R('R27', '1k', 'WL_GPIO0', 'LED_A', (57.9, RY - 4.5, 180), (335, 91, 'h'))
part('D3', 'Device:LED', 'GREEN', 'LED_SMD:LED_0603_1608Metric', {'1': 'GND', '2': 'LED_A'},
     (55.4, 6.4, 0), (372, 91), 'XL-1608SYGC-06', 'XINGLIGHT', 'C965805', 'LED yellow-green 0603, Vf 2.2V (user LED on RM2 GPIO0)')
C('C29', '100nF', '+3V3', 'GND', (56.9, 18.3, 90), (390, 80, 'v'))
C('C30', '10uF', '+3V3', 'GND', (58.2, 18.3, 90), (398, 80, 'v'))
C('C31', '100nF', '+3V3', 'GND', (58.45, 14.6, 90), (406, 80, 'v'))

# ---------------------------------------------------------------- microSD
part('J4', 'Connector:Micro_SD_Card_Det2', 'microSD', 'Connector_Card:microSD_HC_Molex_104031-0811',
     {'1': 'SD_D2', '2': 'SD_D3', '3': 'SD_CMD', '4': '+3V3', '5': 'SD_CLK', '6': 'GND', '7': 'SD_D0', '8': 'SD_D1',
      '9': 'SD_CD', '10': 'GND', 'SH': 'GND'},
     (17.0, 16.4, 180), (372, 150), '104031-0811', 'Molex', 'C585350', 'microSD push-pull socket with card detect')
C('C27', '100nF', '+3V3', 'GND', (24.5, 12.2, 270), (315, 128, 'v'))
C('C28', '10uF', '+3V3', 'GND', (25.6, 19.0, 0), (326, 128, 'v'))
# ---------------------------------------------------------------- Qwiic, RGB, headers
part('J3', 'Connector_Generic_MountingPin:Conn_01x04_MountingPin', 'Qwiic',
     'Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
     {'1': 'GND', '2': '+3V3', '3': 'SDA', '4': 'SCL', 'MP': 'GND'},
     (29.5, 3.1, 180), (272, 222), 'SM04B-SRSS-TB(LF)(SN)', 'JST', 'C160404', 'JST SH 4-pin 1mm side-entry (Qwiic / STEMMA QT)')
R('R28', '2.2k', '+3V3', 'SDA', (29.0, 7.5, 90), (225, 212.5, 'h'))
R('R29', '2.2k', '+3V3', 'SCL', (27.9, 7.5, 90), (225, 220, 'h'))
part('D1', 'LED:WS2812B-2020', 'WS2812B-2020', 'LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm',
     {'1': None, '2': 'GND', '3': 'RGB_DIN', '4': '+3V3'}, (40.2, 4.6, 0), (310, 222), 'WS2812B-2020', 'Worldsemi',
     'C52917434', 'Addressable RGB LED 2020 (V6, 3.3-5.3V supply)')
C('C32', '100nF', '+3V3', 'GND', (42.5, 4.4, 270), (330, 220, 'v'))
TOP = ['VBUS', 'VBAT', 'EN', 'GND', 'GP28_A2', 'GP27_A1', 'GP26_A0', 'SCL', 'SDA', 'GP22', 'GP21', 'GP20']
BOT = ['+3V3', 'GND', 'VSYS', 'GND', 'GP8', 'GP9', 'GP10', 'GP11', 'GP12', 'GP13', 'GP14', 'GP15']
part('J5', 'Connector_Generic:Conn_01x12', 'HDR_TOP', 'Connector_PinHeader_2.54mm:PinHeader_1x12_P2.54mm_Vertical',
     {str(i + 1): n for i, n in enumerate(TOP)}, (HX0, 1.27, 90), (352, 222), bom=False,
     desc='1x12 2.54mm header holes (not populated)')
part('J6', 'Connector_Generic:Conn_01x12', 'HDR_BOT', 'Connector_PinHeader_2.54mm:PinHeader_1x12_P2.54mm_Vertical',
     {str(i + 1): n for i, n in enumerate(BOT)}, (HX0, H - 1.27, 90), (390, 222), bom=False,
     desc='1x12 2.54mm header holes (not populated)')

# schematic-only notes: (x, y, text)
BLOCKS = [
    (15, 25, 120, 95, 'USB-C, ESD, USB series resistors'),
    (125, 25, 245, 95, 'LiPo charger + power path (BQ24074)'),
    (250, 25, 314, 95, '3V3 LDO, battery sense'),
    (318, 25, 410, 95, 'Wi-Fi / BLE (Raspberry Pi RM2)'),
    (15, 100, 195, 280, 'RP2350A, core SMPS, crystal, reset, SWD'),
    (200, 100, 298, 200, 'QSPI flash (XIP CS0) + PSRAM (XIP CS1 = GPIO0), BOOT'),
    (302, 100, 410, 200, 'microSD (SDIO 4-bit / SPI0), pull-ups: RP2350 internal'),
    (200, 204, 410, 248, 'Qwiic / STEMMA QT, RGB LED, headers (J5/J6 not populated)'),
]

# ================================================================ PCB-only data
def mp(n, d=0.0):
    """centre of RP2350 pad n, moved d mm outward (negative = towards the chip centre)"""
    if 46 <= n <= 60: return (round(MX - 3.45 - d, 3), round(MY - 2.8 + 0.4 * (n - 46), 3))
    if 1 <= n <= 15: return (round(MX - 2.8 + 0.4 * (n - 1), 3), round(MY + 3.45 + d, 3))
    if 16 <= n <= 30: return (round(MX + 3.45 + d, 3), round(MY + 2.8 - 0.4 * (n - 16), 3))
    return (round(MX + 2.8 - 0.4 * (n - 31), 3), round(MY - 3.45 - d, 3))
HT = lambda i: (HX0 + HPITCH * i, 1.27)        # top header pad i (0-based)
HB = lambda i: (HX0 + HPITCH * i, H - 1.27)    # bottom header pad
RP = RX - 7.75                                 # x of the RM2 pads facing the MCU
RT = lambda k: (RX + 2.55 - 1.5 * (k - 1), RY - 6.75)   # RM2 top-row pad k (1..7)

MAN_TRACKS = []   # (net, layer, width, points)
MAN_VIAS = []     # (net, x, y)
def T(net, pts, w=0.15, layer='F.Cu'): MAN_TRACKS.append((net, layer, w, [(round(x, 3), round(y, 3)) for x, y in pts]))
def V(net, x, y): MAN_VIAS.append((net, round(x, 3), round(y, 3)))

# ---- RP2350 core regulator: mirrors the Raspberry Pi reference layout (VREG_LX runs between the pads
#      of the VIN and output capacitors to the inductor, PGND returns straight to the VIN capacitor)
T('VREG_LX', [mp(48, -0.2), (40.95, 9.43), (40.35, 8.83), (40.0, 8.6)], 0.18)
T('+3V3', [mp(49, -0.2), (43.2, 9.83), (42.9, 9.91)], 0.2)
T('GND', [mp(47, -0.2), (43.2, 9.03), (42.9, 8.95)], 0.2)
T('GND', [(42.9, 8.95), (42.1, 8.9), (41.3, 8.95)], 0.3); V('GND', 42.1, 8.9)
T('+3V3', [(42.9, 9.91), (42.1, 10.05)], 0.3); V('+3V3', 42.1, 10.05)
T('+1V1', [(41.3, 9.91), (40.3, 10.0), (39.7, 10.025)], 0.3)
T('+1V1', [(39.7, 10.025), (38.35, 10.03), (38.35, 9.25)], 0.4); V('+1V1', 38.35, 10.03); V('+1V1', 38.35, 9.25)
T('VREG_AVDD', [mp(46, -0.2), (43.6, 8.63), (43.3, 8.33), (41.97, 8.33), (41.97, 7.55)])
T('VREG_AVDD', [(41.06, 7.55), (41.97, 7.55)], 0.2)
T('+3V3', [(45.1, 11.63), (44.6, 11.63), (44.4, 11.43), (43.3, 11.43), (43.0, 11.55)], 0.2); V('+3V3', 45.1, 11.63)
T('+3V3', [(44.6, 11.63), (44.4, 11.83), (43.3, 11.83), (43.0, 11.7)], 0.2)
# ---- power pins that drop to the planes inside the pad ring
T('+1V1', [mp(50, -0.2), (45.1, 10.23)], 0.2); V('+1V1', 45.1, 10.23)                       # VREG_FB
T('+1V1', [mp(39, -0.2), (47.1, 8.6), (46.85, 9.05)], 0.2); V('+1V1', 46.85, 9.05)
T('+1V1', [mp(23, -0.2), (49.9, 11.43)], 0.2); V('+1V1', 49.9, 11.43)
T('+1V1', [mp(6, -0.2), (46.7, 13.8)], 0.2); V('+1V1', 46.7, 13.8)
T('+3V3', [mp(38, -0.2), (47.5, 8.6), (47.75, 9.05)], 0.2); V('+3V3', 47.75, 9.05)
T('+3V3', [mp(20, -0.2), (49.9, 12.63)], 0.2); V('+3V3', 49.9, 12.63)
T('+3V3', [mp(11, -0.2), (48.7, 13.8)], 0.2); V('+3V3', 48.7, 13.8)
T('+3V3', [mp(1, -0.2), (44.7, 14.3), (45.0, 13.75)], 0.2); V('+3V3', 45.0, 13.75)
T('+3V3', [mp(45, 0.2), (44.7, 6.63)], 0.2)
T('+3V3', [mp(44, 0.2), (45.1, 7.3), (44.75, 6.95)])
T('+3V3', [(43.75, 6.48), (44.7, 6.63)], 0.2)
T('+3V3', [mp(30, 0.2), (51.65, 8.63), (52.1, 8.18), (52.1, 7.78)], 0.2)
for dx, dy in ((0, 0), (-0.95, -0.95), (0.95, -0.95), (-0.95, 0.95), (0.95, 0.95)): V('GND', MX + dx, MY + dy)
# ---- USB (series resistors next to the regulator, as a tight pair)
T('USB_DM_R', [mp(51, -0.2), (43.55, 10.63), (43.46, 10.72), (37.51, 10.72)])
T('USB_DP_R', [mp(52, -0.2), (38.6, 11.03), (38.0, 11.63), (37.6, 11.78)])
# ---- QSPI: planar bundle down the right-hand side of the flash, CS/IO1/IO2 wrap underneath.
#      Each shared line has a via (tap) from which the PSRAM branch leaves on the bottom layer.
T('QSPI_SD3', [mp(55, -0.2), (40.65, 12.23), (40.45, 12.43), (40.45, 14.665), (40.25, 14.865), (39.8, 14.865)]); V('QSPI_SD3', 40.45, 14.23)
T('QSPI_SCLK', [mp(56, -0.2), (41.45, 12.63), (41.25, 12.83), (41.25, 15.835), (40.95, 16.135), (39.8, 16.135)]); V('QSPI_SCLK', 41.25, 13.4)
T('QSPI_SD0', [mp(57, -0.2), (42.25, 13.03), (42.05, 13.23), (42.05, 16.805), (41.45, 17.405), (39.8, 17.405)]); V('QSPI_SD0', 42.05, 13.9)
T('QSPI_SD2', [mp(58, -0.2), (43.05, 13.43), (42.85, 13.63), (42.85, 18.05), (42.65, 18.25), (34.05, 18.25),
               (33.75, 17.95), (33.75, 16.435), (34.05, 16.135), (34.4, 16.135)]); V('QSPI_SD2', 38.5, 18.25)
T('QSPI_SD1', [mp(59, -0.2), (43.35, 13.83), (43.15, 14.03), (43.15, 18.85), (42.95, 19.05), (33.65, 19.05),
               (33.45, 18.85), (33.45, 15.165), (33.75, 14.865), (34.4, 14.865)]); V('QSPI_SD1', 37.0, 19.05)
T('QSPI_SS', [mp(60, -0.2), (43.55, 14.23), (43.45, 14.33), (43.45, 19.4), (43.25, 19.6), (33.35, 19.6),
              (33.15, 19.4), (33.15, 13.895), (33.45, 13.595), (34.4, 13.595)])
T('QSPI_SS', [(34.4, 13.595), (34.19, 13.0), (34.19, 12.25)]); T('QSPI_SS', [(34.19, 12.25), (33.7, 12.25), (33.31, 12.64)])
# ---- bottom edge: PSRAM_CS / SD escape to vias (continue on B.Cu), GP8..GP11 straight to the header
BL = dict(layer='B.Cu')
SDY = 20.5                                   # via row under the microSD socket
JX = {'SD_D1': 12.455, 'SD_D0': 13.505, 'SD_CLK': 15.705, 'SD_CMD': 17.905, 'SD_D3': 19.005, 'SD_D2': 20.105}
# F.Cu fan below the MCU into a via row; on B.Cu the lines turn into a westbound bus (lanes 0.3 mm apart)
FAN = [('PSRAM_CS', 2, 15.55, 44.0, None), ('SD_CD', 3, 15.6, 44.9, 16.85), ('SD_CMD', 5, 15.6, 45.8, 16.55),
       ('SD_D0', 7, 15.6, 46.7, 16.25), ('SD_D2', 9, 15.6, 47.6, 15.95), ('SD_D3', 10, 15.6, 48.5, 15.65)]
WEST = {  # continuation of each lane on B.Cu (from the east) down to its via
    'SD_CD': [(32.3, 16.85), (31.55, 17.6), (28.9, 17.6), (28.15, 16.85), (22.74, 16.85)],
    'SD_CMD': [(31.0, 16.55), (30.6, 16.95)],
    'SD_D0': [(30.1, 16.25), (29.6, 16.75)],
    'SD_D2': [(29.3, 15.95), (29.0, 16.25), (20.4, 16.25), (20.105, 16.55), (20.105, SDY)],
    'SD_D3': [(28.85, 15.65), (28.55, 15.95), (19.3, 15.95), (19.005, 16.25), (19.005, SDY)],
    'SD_D1': [(28.0, 15.35)],
    'SD_CLK': [(29.0, 15.05), (28.7, 14.75), (27.6, 14.75), (27.3, 15.05), (16.0, 15.05), (15.705, 15.35), (15.705, SDY)],
}
for net, pin, ys, vx, lane in FAN:
    px = mp(pin)[0]
    T(net, [mp(pin, -0.2), (px, ys), (vx, ys + abs(px - vx)), (vx, 17.4)]); V(net, vx, 17.4)
    if lane: T(net, [(vx, 17.4), (vx - (17.4 - lane), lane)] + WEST[net], **BL)
T('SD_CLK', [mp(4, 0.2), (45.9, 14.3), (45.85, 13.8)]); V('SD_CLK', 45.85, 13.8)
T('SD_CLK', [(45.85, 13.8), (45.85, 14.2), (45.0, 15.05)] + WEST['SD_CLK'], **BL)
T('SD_D1', [mp(8, 0.2), (47.5, 14.3), (47.7, 13.9)]); V('SD_D1', 47.7, 13.9)
T('SD_D1', [(47.7, 13.9), (47.7, 14.6), (46.95, 15.35)] + WEST['SD_D1'], **BL)
for n in WEST: V(n, *WEST[n][-1])
# D1, D0 and CMD cross the rest of the bus on F.Cu underneath the card socket
T('SD_D1', [(28.0, 15.35), (27.25, 14.6), (13.3, 14.6), (12.455, 15.45), (12.455, 21.6)])
T('SD_D0', [(29.6, 16.75), (27.0, 16.75), (25.95, 17.8), (16.5, 17.8), (13.505, 20.795), (13.505, 21.6)])
T('SD_CMD', [(30.6, 16.95), (30.0, 17.55), (30.0, 19.0), (29.55, 19.45), (28.6, 19.45), (28.15, 19.9), (18.6, 19.9),
             (17.905, 20.595), (17.905, 21.6)])
T('SD_CD', [(22.74, 16.85), (22.74, 15.7)])
for n in ('SD_CLK', 'SD_D3', 'SD_D2'): T(n, [(JX[n], SDY), (JX[n], 21.6)])
T('GP8', [mp(12, -0.2), (49.1, 17.9), (46.4, 20.6), HB(4)])
T('GP9', [mp(13, -0.2), (49.5, 19.3), (48.9, 19.9), HB(5)])
T('GP10', [mp(14, -0.2), (49.9, 19.0), (51.24, 20.34), HB(6)])
T('GP11', [mp(15, -0.2), (50.3, 17.5), (53.3, 20.5), HB(7)])
# ---- right edge
T('GP12', [mp(16, -0.2), (51.5, 14.23), (51.7, 14.43), (51.7, 18.35), (53.55, 20.2), (55.6, 20.2), HB(8)])
T('GP13', [mp(17, -0.2), (51.75, 13.83), (52.1, 14.2), (52.3, 14.4)]); V('GP13', 52.3, 14.4)
T('GP13', [(52.3, 14.4), (51.7, 15.0), (51.7, 18.1), (52.5, 18.9), (58.46, 18.9), (58.86, 19.3), HB(9)], layer='B.Cu')
T('GP14', [(52.3, 13.6), (53.3, 14.4), (54.0, 15.1), (54.0, 18.2), (54.4, 18.6), (61.0, 18.6), (61.4, 19.0), HB(10)], layer='B.Cu')
T('GP15', [(53.05, 13.15), (53.6, 13.15), (54.6, 14.15), (54.6, 17.9), (55.0, 18.3), (63.54, 18.3), (63.94, 18.7), HB(11)], layer='B.Cu')
T('GP14', [mp(18, -0.2), (51.9, 13.43), (52.1, 13.55), (52.3, 13.6)]); V('GP14', 52.3, 13.6)
T('GP15', [mp(19, -0.2), (52.75, 13.03), (53.05, 13.15)]); V('GP15', 53.05, 13.15)
T('XIN', [mp(21, -0.2), (52.0, 12.23), (52.32, 12.55), (56.2, 12.55), (56.75, 13.1), (57.05, 13.4)])
T('XIN', [(57.05, 13.65), (57.05, 15.12)])
T('XOUT', [mp(22, -0.2), (53.2, 11.83), (53.5, 11.71)])
T('XTAL_O', [(53.5, 10.69), (54.2, 10.69), (54.75, 11.24), (55.35, 11.45)])
T('XTAL_O', [(53.5, 10.69), (53.82, 10.2), (53.82, 9.6)])
T('SWCLK', [mp(24, -0.2), (51.9, 11.03), (52.2, 11.3)]); V('SWCLK', 52.2, 11.3)
T('SWDIO', [mp(25, -0.2), (51.9, 10.63), (52.2, 10.45)]); V('SWDIO', 52.2, 10.45)
T('RUN', [mp(26, 0.2), (50.4, 10.23), (49.9, 10.6)]); V('RUN', 49.9, 10.6)
# RUN crosses the radio lines and the header fan-out on In2 on its way to the reset button
T('RUN', [(49.9, 10.6), (50.5, 10.0), (51.3, 10.0), (51.75, 9.55), (52.2, 9.55), (52.6, 9.15), (52.6, 9.0), (53.6, 8.0), (53.6, 6.2), (53.2, 5.8),
          (47.9, 5.8), (46.0, 3.9), (39.0, 3.9), (38.4, 4.5)], layer='In2.Cu'); V('RUN', 38.4, 4.5)
T('RUN', [(38.4, 4.5), (37.9, 5.0), (37.5, 5.4)])
T('WL_ON', [mp(27, 0.2), (50.3, 9.83), (49.9, 9.7)]); V('WL_ON', 49.9, 9.7)
T('WL_ON', [(49.9, 9.7), (50.45, 9.15), (53.3, 9.15), (55.45, 11.3), (57.5, 11.3), (58.5, 12.3)], layer='B.Cu'); V('WL_ON', 58.5, 12.3)
T('WL_ON', [(58.5, 12.3), (59.0, 12.93), (RP, 12.93), (RP, 14.43)])
# ---- top edge: fan to the top header, radio signals through the channel above the RM2 pads
T('GP28_A2', [mp(42, -0.2), (45.9, 2.6), (46.16, 2.34), HT(4)])
T('GP27_A1', [mp(41, -0.2), (46.3, 5.6), (48.7, 3.2), HT(5)])
T('GP26_A0', [mp(40, -0.2), (46.7, 6.2), (51.0, 1.9), HT(6)])
T('BAT_SENSE', [mp(43, 0.2), (45.5, 8.6), (45.75, 9.05)]); V('BAT_SENSE', 45.75, 9.05)
T('SCL', [mp(37, -0.2), (47.9, 7.3), (53.63, 1.57), HT(7)])
T('SDA', [mp(36, -0.2), (48.3, 7.33), (53.18, 2.45), (55.9, 2.45), HT(8)])
T('RGB_DIN', [mp(35, 0.2), (48.7, 8.6), (48.65, 9.05)]); V('RGB_DIN', 48.65, 9.05)
T('GP22', [mp(34, -0.2), (49.1, 7.3), (53.65, 2.75), (58.3, 2.75), HT(9)])
T('GP21', [mp(33, 0.2), (49.5, 9.05)]); V('GP21', 49.5, 9.05)
T('GP21', [(49.5, 9.05), (49.5, 8.2), (50.6, 7.1), (50.6, 4.9), (51.6, 3.9), (60.0, 3.9), (61.4, 2.5), HT(10)], layer='B.Cu')
# I2C from the header pads back to the Qwiic connector
T('SCL', [HT(7), (53.3, 2.0), (52.85, 2.45), (46.6, 2.45), (45.55, 3.5), (28.45, 3.5), (28.05, 3.9), (28.05, 6.2)], layer='B.Cu'); V('SCL', 28.05, 6.2)
T('SDA', [HT(8), (55.4, 2.2), (54.85, 2.75), (46.9, 2.75), (45.85, 3.8), (29.5, 3.8), (29.1, 4.2), (29.1, 6.2)], layer='B.Cu'); V('SDA', 29.1, 6.2)
T('SCL', [(28.0, 5.1), (28.05, 6.2), (27.9, 6.99)]); T('SDA', [(29.0, 5.1), (29.1, 6.2), (29.0, 6.99)])
T('GP20', [mp(32, -0.2), (49.9, 7.3), (54.15, 3.05), (59.3, 3.05), (59.95, 2.4), (63.2, 2.4), (63.75, 1.85), HT(11)])
c3 = RT(3)
T('WL_CLK', [mp(31, -0.2), (50.3, 7.33), (54.28, 3.35), (59.45, 3.35), (60.1, 2.7), (c3[0] - 0.95, 2.7),
             (c3[0], 3.65), (c3[0], 4.3)])
c5 = RT(5); c6 = RT(6)
T('WL_D', [(57.39, 4.4), (57.39, 3.65), (59.6, 3.65), (60.25, 3.0), (c5[0] - 0.65, 3.0), (c5[0], 3.65), (c5[0], 4.3)])
T('WL_DOUT', [(58.41, 4.4), (59.3, 4.4), (60.4, 3.3), (c6[0] - 0.35, 3.3), (c6[0], 3.65), (c6[0], 4.3)])
# ---- +1V1 distribution on the bottom layer (inductor -> FB -> DVDD pins -> decoupling)
B1 = dict(w=0.4, layer='B.Cu')
T('+1V1', [(38.35, 10.03), (38.35, 9.25), (38.55, 9.45), (41.4, 9.45)], **B1); T('+1V1', [(41.4, 9.45), (42.8, 9.45)], 0.18, 'B.Cu')
T('+1V1', [(42.8, 9.45), (44.32, 9.45), (45.1, 10.23)], **B1)
V('+1V1', 45.35, 4.68); T('+1V1', [(44.7, 4.68), (45.35, 4.68)], 0.25)                 # C16
T('+1V1', [(45.35, 4.68), (46.3, 5.63), (46.3, 8.2), (46.85, 8.75), (46.85, 9.05)], 0.3, 'B.Cu')
T('BAT_SENSE', [(45.75, 9.05), (45.75, 8.75), (45.2, 8.2), (40.6, 8.2), (40.3, 7.9), (40.3, 5.5), (40.0, 5.2), (33.0, 5.2),
                (31.9, 6.3), (31.9, 7.2), (30.81, 8.29), (29.85, 8.29)], layer='B.Cu'); V('BAT_SENSE', 29.85, 8.29)
T('BAT_SENSE', [(30.39, 7.35), (30.39, 9.23)]); T('BAT_SENSE', [(30.39, 8.29), (29.85, 8.29)])
T('+1V1', [(45.1, 10.23), (46.1, 9.75), (46.85, 9.05)], **B1)
T('+1V1', [(46.85, 9.05), (47.1, 9.78), (48.85, 9.78), (49.175, 10.1), (49.175, 10.9), (49.6, 11.43), (49.9, 11.43)], **B1)
T('+1V1', [(47.6, 9.78), (47.6, 10.38), (46.55, 11.43), (47.5, 12.38), (47.5, 13.0), (46.7, 13.8)], **B1)
T('WL_D', [mp(29, -0.2), (52.3, 9.03), (52.6, 8.73), (53.6, 8.73), (53.6, 5.2), (54.3, 4.5), (57.2, 4.5)])
T('WL_CS', [mp(28, -0.2), (52.5, 9.43), (52.9, 9.03), (55.6, 9.03), (56.2, 8.43), (RP - 0.5, 8.43)])
for mx_ in (32.3, 26.7):
    V('GND', mx_, 2.6); T('GND', [(mx_, 1.6), (mx_, 2.6)], 0.3)                                # Qwiic shell tabs
T('GND', [(34.1, 5.4), (34.1, 4.3), (33.3, 3.5), (32.6, 2.8), (32.3, 2.6)], 0.25)                # reset switch
T('RGB_DIN', [(48.65, 9.05), (48.65, 8.3), (47.2, 6.85), (47.2, 4.85), (46.47, 4.12), (42.28, 4.12), (41.8, 4.6), (41.8, 5.75)], layer='B.Cu')
V('RGB_DIN', 41.8, 5.75); T('RGB_DIN', [(41.8, 5.75), (41.3, 5.25), (41.115, 5.15)])
T('USB_DM', [(36.49, 10.72), (34.5, 10.72)]); V('USB_DM', 34.5, 10.72)
T('USB_DP', [(36.49, 11.78), (36.0, 11.3), (33.95, 11.3), (33.6, 10.95), (33.6, 10.45)]); V('USB_DP', 33.6, 10.45)
# ---- small local links
T('GND', [(16.3, 5.35), (17.0, 5.2)], 0.2); T('GND', [(16.85, 5.9), (17.1, 5.3)], 0.2)   # BQ24074 CE, EN2
T('GND', [(18.35, 5.9), (18.1, 5.3)], 0.2); V('GND', 17.6, 4.6)                          # BQ24074 VSS, EP
T('GND', [(34.4, 17.405), (35.1, 17.405), (35.7, 17.0)], 0.25); V('GND', 36.4, 13.9); V('GND', 37.8, 13.9)
T('GND', [(33.675, 9.05), (35.1, 9.05)], 0.2)                                            # PSRAM VSS -> EP
T('+3V3', [(39.8, 13.595), (39.48, 12.9), (39.48, 12.2)], 0.25)                          # flash VCC -> C25
T('+3V3', [(36.525, 7.55), (37.2, 7.3), (38.2, 7.3), (38.7, 7.38)], 0.2)                # PSRAM VDD -> C26
# ---- PSRAM branch of the QSPI bus: vias beside the PSRAM pads, bottom-layer links from the taps
T('QSPI_SD3', [(36.525, 8.05), (37.6, 8.0)]); V('QSPI_SD3', 37.6, 8.0)
T('QSPI_SCLK', [(36.525, 8.55), (37.0, 8.55), (37.35, 8.9), (37.6, 8.9)]); V('QSPI_SCLK', 37.6, 8.9)
T('QSPI_SD0', [(36.525, 9.05), (36.9, 9.05), (37.6, 9.8)]); V('QSPI_SD0', 37.6, 9.8)
T('QSPI_SD1', [(33.675, 8.05), (33.2, 8.05), (32.9, 7.75), (32.65, 7.75)]); V('QSPI_SD1', 32.65, 7.75)
T('QSPI_SD2', [(33.675, 8.55), (32.65, 8.55)]); V('QSPI_SD2', 32.65, 8.55)
T('PSRAM_CS', [(33.675, 7.55), (33.675, 6.8)]); V('PSRAM_CS', 33.675, 6.8)
T('QSPI_SD0', [(42.05, 13.9), (42.05, 11.05), (41.75, 10.75), (37.9, 10.75), (37.6, 10.45), (37.6, 9.8)], **BL)
T('QSPI_SCLK', [(41.25, 13.4), (40.6, 12.75), (40.6, 11.2), (40.45, 11.05), (37.35, 11.05), (37.0, 10.7),
                (37.0, 9.25), (37.35, 8.9), (37.6, 8.9)], **BL)
T('QSPI_SD3', [(40.45, 14.23), (40.05, 13.83), (40.05, 11.75), (39.65, 11.35), (36.9, 11.35), (36.45, 10.9), (36.45, 8.45),
               (36.9, 8.0), (37.6, 8.0)], **BL)
T('+1V1', [(49.9, 11.43), (50.6, 11.43), (51.25, 12.1), (56.6, 12.1), (56.6, 16.0), (56.2, 16.4), (55.66, 16.7), (55.66, 17.7)], 0.3, 'B.Cu')
# the three lines that have to cross the SD bus use short tracks on In2 (cut into the 3V3 plane)
I2 = dict(layer='In2.Cu')
T('QSPI_SD2', [(38.5, 18.25), (37.1, 16.85), (37.1, 11.9), (36.7, 11.5), (33.05, 11.5), (32.65, 11.1), (32.65, 8.55)], **I2)
T('QSPI_SD1', [(37.0, 19.05), (35.6, 17.65), (35.6, 13.3), (35.2, 12.9), (32.4, 12.9), (32.0, 12.5), (32.0, 8.15),
               (32.4, 7.75), (32.65, 7.75)], **I2)
T('PSRAM_CS', [(44.0, 17.4), (43.6, 17.0), (39.25, 17.0), (38.85, 16.6), (38.85, 11.15), (38.45, 10.75), (35.6, 10.75),
               (35.6, 7.2), (35.2, 6.8), (33.675, 6.8)], **I2)

# pads that get a plane via at an explicit position: (ref, pad) -> (x, y)
VIA_HINTS = {
    ('U5', '2'): (28.0, 11.2), ('U5', '5'): (29.95, 10.25), ('U6', '2'): (11.6, 6.2), ('U3', '4'): (34.6, 9.9), ('C25', '1'): (39.48, 12.95), ('C25', '2'): (38.3, 12.95), ('R17', '1'): (35.75, 12.15), ('C26', '2'): (39.5, 6.05), ('C24', '2'): (55.6, 9.6),
    ('U7', '7'): (RX - 6.45, RY - 5.2), ('U7', '4'): (RX - 1.95, RY - 5.2), ('U7', '1'): (RX + 2.55, RY - 5.2),
    ('U7', '15'): (RX - 6.45, RY + 5.2), ('U7', '21'): (RX + 2.55, RY + 5.2), ('U7', '11'): (RX - 6.2, RY),
    ('U7', '14'): (RX - 6.15, RY + 4.15), ('U7', '16'): (RX - 4.95, RY + 5.2),
    ('J3', '1'): (31.0, 6.45), ('J3', '2'): (30.0, 6.45),
    ('J4', '4'): (16.805, 20.5), ('J4', '6'): (14.605, 20.5),
    ('J2', '1'): (8.6, 14.9),
    ('D1', '2'): (39.5, 6.05), ('D1', '4'): (41.9, 2.9),
    ('C12', '2'): (45.3, 5.67), ('C15', '2'): (43.1, 5.0), ('C10', '2'): (43.1, 5.0), ('C32', '2'): (43.1, 5.0), ('C16', '2'): (44.7, 2.94),
    ('C10', '1'): (43.75, 2.79), ('R19', '1'): (45.575, 18.2),
    ('C8', '1'): (45.575, 18.2), ('C7', '1'): (45.575, 18.2), ('C7', '2'): (47.85, 18.2), ('C8', '2'): (44.07, 19.05),
    ('C11', '2'): (52.9, 6.82), ('C13', '2'): (41.2, 11.63), ('C17', '2'): (53.1, 17.7), ('C18', '2'): (53.1, 16.7),
}
NO_AUTO_VIA = {('R13', '2'), ('C6', '2'), ('C16', '1'), ('C13', '1'), ('C19', '1'), ('C19', '2'), ('C21', '1'), ('C21', '2'), ('L1', '1'), ('C12', '1'), ('C32', '1')}
# rectangles (x0, y0, x1, y1) kept free of automatic plane vias (signal escape lanes)
VIA_KEEPOUT = [
    (45.3, 1.0, 62.0, 7.4),      # GPIO fan-out to the top header
    (44.6, 15.4, 52.5, 21.0),    # GPIO fan-out below the MCU
    (51.5, 8.4, 53.2, 15.0),     # right-hand escape
    (40.2, 12.0, 43.6, 19.9),    # QSPI bundle
    (32.9, 13.3, 34.1, 19.9), (33.0, 17.9, 43.6, 19.9),   # QSPI wrap
    (59.0, 2.2, 71.0, 3.6),      # channel above the RM2 pads
    (36.0, 10.3, 43.6, 12.0),    # USB pair
]
SILK = []   # (text, x, y, {options})
for i, n in enumerate(TOP):
    SILK.append((n.replace('_A', '/A').replace('GP', ''), HX0 + HPITCH * i, 4.0, dict(layer='B.SilkS', ang=90, size=0.75)))
for i, n in enumerate(BOT):
    SILK.append((n.replace('+', '').replace('GP', ''), HX0 + HPITCH * i, H - 4.0, dict(layer='B.SilkS', ang=90, size=0.75)))
SILK += [
    ('RP2350 Wi-Fi/BLE dev board', 21.0, 9.8, dict(layer='B.SilkS', size=1.2)),
    ('rev A  2026-11', 21.0, 11.8, dict(layer='B.SilkS', size=0.9)),
    ('numbers = GPIO', 30.0, 2.0, dict(layer='B.SilkS', size=0.7)),
    ('LiPo 3.7V', 5.0, 14.2, dict(layer='B.SilkS', size=0.8)),
    ('+', 9.2, 18.0, dict(layer='B.SilkS', size=1.0)), ('-', 9.2, 16.0, dict(layer='B.SilkS', size=1.0)),
    ('SWCLK', 51.1, 12.9, dict(layer='B.SilkS', size=0.6)), ('SWDIO', 54.0, 9.75, dict(layer='B.SilkS', size=0.6)),
    ('GND', 57.58, 6.4, dict(layer='B.SilkS', size=0.6)),
    ('+', 9.95, 18.0, dict(size=0.9)), ('-', 9.95, 16.0, dict(size=0.9)),
    ('BOOT', 30.6, 16.1, dict(size=0.65)), ('RST', 35.8, 3.5, dict(size=0.65)),
    ('CHG', 22.7, 7.25, dict(size=0.6)), ('LED', 55.4, 5.25, dict(size=0.6)),
    ('L1: polarity dot at pad 1 (+1V1 side, towards the board bottom edge)', 20.0, 26.0, dict(layer='F.Fab', size=0.8, just=['left'])),
    ('All parts on the top side. J5/J6 header holes and TP1-TP3 are not populated.', 20.0, 27.5, dict(layer='F.Fab', size=0.8, just=['left'])),
]
BOM_NOTES = {
    'L1': 'POLARISED: marking dot must sit on pad 1 (+1V1 net), see assembly drawing',
    'U7': 'Castellated module, antenna end overhangs towards the board edge (no copper underneath the antenna)',
    'D1': 'Pin 1 (DOUT) marked on silkscreen', 'J1': 'USB-C receptacle at board edge', 'U1': 'RP2350A0A4 (A4 stepping)',
}


NOTES = [
    (128, 86, 'Charge current 890/R7 = 297 mA. USB input limit 500 mA (EN2=0, EN1=1 while VBUS present).'),
    (128, 90, 'TS tied to 10k (no NTC in a 2-wire pack). Safety timers and 10% termination at defaults (TMR, ITERM open).'),
    (252, 90, 'BAT_SENSE = VBAT/2 on GPIO29 / ADC3'),
    (320, 36, 'gSPI wired like Pico 2 W; pins: ON=GP16 CS=GP17 DATA=GP18 CLK=GP19'),
    (18, 262, 'SWD test pads are on the bottom side'),
    (18, 111, 'Core supply: on-chip SMPS, L1 = AOTA-B201610S3R3-101-T (polarised, dot to +1V1)'),
    (202, 111, 'GPIO0 = XIP_CS1 (PSRAM), pulled up by R19'),
    (304, 196, 'CLK=GP2 CMD=GP3 D0..D3=GP4..GP7 CD=GP1 (switch to GND)'),
    (202, 244, 'I2C0: SDA=GP24 SCL=GP25. RGB LED on GP23, powered from 3V3.'),
]
