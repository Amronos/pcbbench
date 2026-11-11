"""Single source of truth for the RP2350 dev board: components, nets, BOM data.

Every component lists: reference, symbol lib id, footprint, value, sheet,
pin->net map, and BOM attributes (MPN, manufacturer, LCSC code).
Pins may be given by number or by (unique or repeated) pin name.
A net of None means "intentionally not connected" (gets a no-connect flag).
"""
import kilib

PROJECT = 'rp2350-dev'
TITLE = 'RP2350 Wireless Dev Board'
REV = 'A'
DATE = '2026-11-09'

SHEETS = [
    # (sheet id, title, file)
    ('power', 'Power', 'power.kicad_sch', 'Power: USB-C, Li-Po charger / power-path, 3V3'),
    ('mcu', 'MCU', 'mcu.kicad_sch', 'RP2350A core, QSPI flash, PSRAM'),
    ('wireless', 'Wireless', 'wireless.kicad_sch', 'ESP32-C6 Wi-Fi 6 / BLE 5 co-processor'),
    ('io', 'IO', 'io.kicad_sch', 'microSD, Qwiic, RGB LED, headers'),
]

POWER_NETS = {
    # net name -> power symbol lib id used in the schematic
    'GND': 'power:GND',
    '+3V3': 'power:+3V3',
    '+1V1': 'power:+1V1',
    'VBUS': 'power:VBUS',
    'VSYS': 'power:VCC',     # value overridden to VSYS
    'VBAT': 'power:+BATT',   # value overridden to VBAT
}

COMPONENTS = []

# Common BOM data for jellybean parts --------------------------------------
R0402 = {
    '0R': ('0402WGF0000TCE', 'C17168'), '27R': ('0402WGF270JTCE', 'C25100'),
    '33R': ('0402WGF330JTCE', 'C25105'), '1k': ('0402WGF1001TCE', 'C11702'),
    '1.5k': ('0402WGF1501TCE', 'C25867'), '2k': ('0402WGF2001TCE', 'C4109'),
    '4.7k': ('0402WGF4701TCE', 'C25900'), '5.1k': ('0402WGF5101TCE', 'C25905'),
    '10k': ('0402WGF1002TCE', 'C25744'), '100k': ('0402WGF1003TCE', 'C25741'),
    '200k': ('0402WGF2003TCE', 'C25764'),
}
CAPS = {
    # value: (footprint, MPN, manufacturer, LCSC, description)
    '100n': ('C_0402', 'CL05B104KO5NNNC', 'Samsung Electro-Mechanics', 'C1525', '100nF 16V X7R 0402'),
    '15p': ('C_0402', '0402CG150J500NT', 'FH (Fenghua)', 'C1548', '15pF 50V C0G 0402'),
    '1u': ('C_0402', 'CL05A105KA5NQNC', 'Samsung Electro-Mechanics', 'C52923', '1uF 25V X5R 0402'),
    '4.7u': ('C_0402', 'CL05A475MP5NRNC', 'Samsung Electro-Mechanics', 'C23733', '4.7uF 10V X5R 0402'),
    '4.7u/25V': ('C_0603', 'CL10A475KA8NQNC', 'Samsung Electro-Mechanics', 'C69335', '4.7uF 25V X5R 0603'),
    '10u': ('C_0603', 'CL10A106MA8NRNC', 'Samsung Electro-Mechanics', 'C96446', '10uF 25V X5R 0603'),
}
FP_STD = {
    'R_0402': 'Resistor_SMD:R_0402_1005Metric',
    'C_0402': 'Capacitor_SMD:C_0402_1005Metric',
    'C_0603': 'Capacitor_SMD:C_0603_1608Metric',
}
# Footprints copied verbatim from the Raspberry Pi RP2350A minimal design
FP_RPI = {
    'R_0402': 'RP2350_Dev:R_0402_RPi',
    'C_0402': 'RP2350_Dev:C_0402_RPi',
    'C_0402_W': 'RP2350_Dev:C_0402_RPi_Wide',
}


def part(ref, sym, fp, value, sheet, pins, mpn='', mfr='', lcsc='', desc='', rpi=None,
         dnp=False, in_bom=True, fields=None):
    COMPONENTS.append(dict(ref=ref, sym=sym, fp=fp, value=value, sheet=sheet, pins=pins,
                           mpn=mpn, mfr=mfr, lcsc=lcsc, desc=desc, rpi=rpi, dnp=dnp,
                           in_bom=in_bom, fields=fields or {}))


def R(ref, value, a, b, sheet, rpi=None, desc=None):
    mpn, lcsc = R0402[value]
    fp = FP_RPI['R_0402'] if rpi else FP_STD['R_0402']
    part(ref, 'Device:R', fp, value, sheet, {'1': a, '2': b}, mpn=mpn,
         mfr='UNI-ROYAL', lcsc=lcsc, desc=desc or ('Resistor %s 1%% 0402' % value), rpi=rpi)
    COMPONENTS[-1]['bomdesc'] = 'Thick-film resistor %s 1%% 62.5mW 0402' % value


def C(ref, value, a, b, sheet, rpi=None, wide=False):
    fpk, mpn, mfr, lcsc, desc = CAPS[value]
    if rpi:
        fp = FP_RPI['C_0402_W'] if wide else FP_RPI['C_0402']
        if fpk != 'C_0402':
            raise ValueError('RPi block caps are 0402')
    else:
        fp = FP_STD[fpk]
    part(ref, 'Device:C', fp, value.split('/')[0], sheet, {'1': a, '2': b}, mpn=mpn, mfr=mfr,
         lcsc=lcsc, desc=desc, rpi=rpi)


# =========================================================================
# Sheet: power
# =========================================================================
S = 'power'
part('J1', 'Connector:USB_C_Receptacle_USB2.0_16P',
     'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal', 'USB4105-GF-A', S,
     {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'A4': 'VBUS', 'A9': 'VBUS',
      'B4': 'VBUS', 'B9': 'VBUS', 'A5': 'CC1', 'B5': 'CC2', 'A6': 'USB_DP', 'B6': 'USB_DP',
      'A7': 'USB_DM', 'B7': 'USB_DM', 'A8': None, 'B8': None, 'SH': 'GND'},
     mpn='USB4105-GF-A', mfr='GCT', lcsc='C3020560', desc='USB Type-C receptacle, USB 2.0, 16P, SMD + THT shell')
R('R1', '5.1k', 'CC1', 'GND', S, desc='USB-C CC1 sink pull-down (Rd) 5.1k 1% 0402')
R('R2', '5.1k', 'CC2', 'GND', S, desc='USB-C CC2 sink pull-down (Rd) 5.1k 1% 0402')
part('U1', 'Power_Protection:USBLC6-2SC6', 'Package_TO_SOT_SMD:SOT-23-6', 'USBLC6-2SC6', S,
     {'1': 'USB_DP', '6': 'USB_DP', '3': 'USB_DM', '4': 'USB_DM', '2': 'GND', '5': 'VBUS'},
     mpn='USBLC6-2SC6', mfr='STMicroelectronics', lcsc='C7519', desc='USB 2.0 ESD protection, SOT-23-6')

# Li-Po charger with dynamic power-path (BQ24074)
part('U2', 'Battery_Management:BQ24074RGT', 'Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm',
     'BQ24074RGTR', S,
     {'IN': 'VBUS', 'OUT': 'VSYS', 'BAT': 'VBAT', 'VSS': 'GND', '17': 'GND', 'TS': 'BQ_TS',
      '~{CE}': 'GND', 'EN1': 'GND', 'EN2': 'VSYS', '~{PGOOD}': 'PGOOD_N', '~{CHG}': 'CHG_N',
      'ILIM': 'BQ_ILIM', 'ISET': 'BQ_ISET', 'TMR': None, 'ITERM': None},
     mpn='BQ24074RGTR', mfr='Texas Instruments', lcsc='C54313',
     desc='1.5A single-cell Li-ion charger with DPPM power-path, VQFN-16')
C('C1', '4.7u/25V', 'VBUS', 'GND', S)          # charger IN bypass (1-10uF)
C('C2', '10u', 'VSYS', 'GND', S)               # charger OUT (4.7-47uF)
C('C3', '10u', 'VBAT', 'GND', S)               # battery pin bypass
R('R3', '10k', 'BQ_TS', 'GND', S, desc='TS fixed 10k (no pack NTC) 1% 0402')
R('R4', '1.5k', 'BQ_ILIM', 'GND', S, desc='ILIM: 1550/1.5k = 1.03A input limit, 1% 0402')
R('R5', '2k', 'BQ_ISET', 'GND', S, desc='ISET: 890/2k = 445mA fast charge, 1% 0402')
R('R6', '100k', '+3V3', 'PGOOD_N', S, desc='PGOOD pull-up 100k 1% 0402')
R('R7', '100k', '+3V3', 'CHG_N', S, desc='CHG pull-up 100k 1% 0402')
R('R8', '1k', '+3V3', 'LED_CHG_A', S, desc='Charge LED resistor 1k 1% 0402')
part('D1', 'Device:LED', 'LED_SMD:LED_0603_1608Metric', 'RED', S, {'1': 'CHG_N', '2': 'LED_CHG_A'},
     mpn='KT-0603R', mfr='Hubei KENTO Elec', lcsc='C2286', desc='LED red 0603 (charging)')
part('J2', 'Connector_Generic_MountingPin:Conn_01x02_MountingPin',
     'Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal', 'BATT', S,
     {'1': 'GND', '2': 'VBAT', 'MP': 'GND'},
     mpn='S2B-PH-SM4-TB(LF)(SN)', mfr='JST', lcsc='C295747',
     desc='JST PH 2-pin right-angle SMD, Li-Po battery (pin1 = GND, pin2 = +)')
# Battery voltage monitor: VBAT/3 into ADC3 (GPIO29), same ratio as Pico 2 VSYS sense
R('R9', '200k', 'VBAT', 'VBAT_SENSE', S, desc='VBAT divider top 200k 1% 0402')
R('R10', '100k', 'VBAT_SENSE', 'GND', S, desc='VBAT divider bottom 100k 1% 0402')
C('C4', '100n', 'VBAT_SENSE', 'GND', S)
# 3.3V LDO
part('U3', 'Regulator_Linear:TLV75733PDBV', 'Package_TO_SOT_SMD:SOT-23-5', 'TLV75733PDBVR', S,
     {'IN': 'VSYS', 'GND': 'GND', 'EN': 'LDO_EN', 'NC': None, 'OUT': '+3V3'},
     mpn='TLV75733PDBVR', mfr='Texas Instruments', lcsc='C485517', desc='1A 3.3V LDO, SOT-23-5')
R('R11', '100k', 'VSYS', 'LDO_EN', S, desc='LDO enable pull-up 100k 1% 0402')
C('C5', '10u', 'VSYS', 'GND', S)
C('C6', '10u', '+3V3', 'GND', S)
C('C7', '10u', '+3V3', 'GND', S)

# =========================================================================
# Sheet: mcu  (RP2350A core = Raspberry Pi "RP2350A minimal" reference)
# =========================================================================
S = 'mcu'
GP = {i: None for i in range(30)}
GP.update({
    0: 'GPIO0', 1: 'GPIO1', 2: 'GPIO2', 3: 'GPIO3', 4: 'GPIO4', 5: 'GPIO5',
    6: 'PGOOD_N', 7: 'CHG_N', 8: 'PSRAM_CS', 9: 'SD_DET',
    10: 'SD_CLK', 11: 'SD_CMD', 12: 'SD_D0', 13: 'SD_D1', 14: 'SD_D2', 15: 'SD_D3',
    16: 'I2C_SDA', 17: 'I2C_SCL', 18: 'ESP_EN', 19: 'ESP_BOOT',
    20: 'ESP_RXD', 21: 'ESP_TXD', 22: 'ESP_RTS', 23: 'ESP_CTS',
    24: 'NEOPIXEL', 25: 'LED_USER', 26: 'GPIO26_A0', 27: 'GPIO27_A1', 28: 'GPIO28_A2',
    29: 'VBAT_SENSE',
})
u1pins = {'IOVDD': '+3V3', 'DVDD': '+1V1', 'ADC_AVDD': '+3V3', 'VREG_AVDD': 'VREG_AVDD',
          'VREG_PGND': 'GND', 'VREG_LX': 'VREG_LX', 'VREG_VIN': '+3V3', 'VREG_FB': '+1V1',
          'USB_OTP_VDD': '+3V3', 'QSPI_IOVDD': '+3V3', 'GND': 'GND',
          'XIN': 'XIN', 'XOUT': 'XOUT', 'SWCLK': 'SWCLK', 'SWDIO': 'SWDIO', 'RUN': 'RUN',
          'USB_DM': 'USB_DM_MCU', 'USB_DP': 'USB_DP_MCU',
          'QSPI_SD0': 'QSPI_SD0', 'QSPI_SD1': 'QSPI_SD1', 'QSPI_SD2': 'QSPI_SD2',
          'QSPI_SD3': 'QSPI_SD3', 'QSPI_SCLK': 'QSPI_SCLK', '~{QSPI_SS}': 'QSPI_SS'}
for i in range(30):
    nm = 'GPIO%d' % i if i < 26 else 'GPIO%d/ADC%d' % (i, i - 26)
    u1pins[nm] = GP[i]
part('U4', 'MCU_RaspberryPi:RP2350A', 'RP2350_Dev:RP2350A_QFN60_RPi', 'RP2350A', S, u1pins,
     mpn='RP2350A', mfr='Raspberry Pi', lcsc='C42411118',
     desc='RP2350A dual Cortex-M33/Hazard3 MCU, QFN-60 7x7', rpi='U1')
# Internal switching regulator: exact RPi reference parts
part('L1', 'Device:L', 'RP2350_Dev:L_Abracon_AOTA-B201610', '3.3uH', S, {'1': '+1V1', '2': 'VREG_LX'},
     mpn='AOTA-B201610S3R3-101-T', mfr='Abracon', lcsc='C42411119',
     desc='3.3uH 2016 polarity-marked inductor (RP2350 VREG, orientation critical)', rpi='L1')
C('C8', '4.7u', '+3V3', 'GND', S, rpi='C6', wide=True)       # VREG_VIN
C('C9', '4.7u', '+1V1', 'GND', S, rpi='C7', wide=True)       # VREG output
C('C10', '4.7u', 'VREG_AVDD', 'GND', S, rpi='C9')            # VREG_AVDD filter cap
R('R12', '33R', '+3V3', 'VREG_AVDD', S, rpi='R3', desc='VREG_AVDD RC filter 33R 1% 0402')
# Decoupling (positions as RPi reference)
C('C11', '100n', '+1V1', 'GND', S, rpi='C8')
C('C12', '100n', '+1V1', 'GND', S, rpi='C10')
C('C13', '100n', '+1V1', 'GND', S, rpi='C11')
C('C14', '100n', '+3V3', 'GND', S, rpi='C12')
C('C15', '100n', '+3V3', 'GND', S, rpi='C13')
C('C16', '100n', '+3V3', 'GND', S, rpi='C14')
C('C17', '100n', '+3V3', 'GND', S, rpi='C15')
C('C18', '100n', '+3V3', 'GND', S, rpi='C16')
C('C19', '100n', '+3V3', 'GND', S, rpi='C17')
C('C20', '100n', '+3V3', 'GND', S, rpi='C18')
C('C21', '10u', '+3V3', 'GND', S)                            # bulk near core
# USB series resistors
R('R13', '27R', 'USB_DP', 'USB_DP_MCU', S, rpi='R7', desc='USB D+ series 27R 1% 0402')
R('R14', '27R', 'USB_DM', 'USB_DM_MCU', S, rpi='R8', desc='USB D- series 27R 1% 0402')
# Crystal
part('Y1', 'Device:Crystal_GND24', 'RP2350_Dev:Crystal_3225_RPi', '12MHz', S,
     {'1': 'XIN', '3': 'XOSC_R', '2': 'GND', '4': 'GND'},
     mpn='ABM8-272-T3', mfr='Abracon', lcsc='C20625731', desc='12MHz crystal 10pF 3.2x2.5 (RPi recommended)', rpi='X1')
C('C22', '15p', 'XIN', 'GND', S, rpi='C3')
C('C23', '15p', 'XOSC_R', 'GND', S, rpi='C4')
R('R15', '1k', 'XOUT', 'XOSC_R', S, rpi='R2', desc='Crystal drive-limit 1k 1% 0402')
# QSPI flash
part('U5', 'Memory_Flash:W25Q128JVS', 'RP2350_Dev:SOIC-8_5.3mm_RPi', 'W25Q128JVSIQ', S,
     {'1': 'FLASH_SS', '2': 'QSPI_SD1', '3': 'QSPI_SD2', '4': 'GND', '5': 'QSPI_SD0',
      '6': 'QSPI_SCLK', '7': 'QSPI_SD3', '8': '+3V3'},
     mpn='W25Q128JVSIQ', mfr='Winbond', lcsc='C97521', desc='128Mbit (16MB) QSPI NOR flash, SOIC-8 208mil', rpi='U3')
C('C24', '100n', '+3V3', 'GND', S, rpi='C2')
R('R16', '10k', '+3V3', 'FLASH_SS', S, rpi='R1', desc='Flash CS pull-up 10k 1% 0402')
R('R17', '0R', 'QSPI_SS', 'FLASH_SS', S, rpi='R10', desc='Flash CS link 0R 0402 (RPi reference option)')
R('R18', '1k', 'QSPI_SS', 'USB_BOOT', S, rpi='R6', desc='BOOTSEL 1k 1% 0402')
# PSRAM (XIP CS1 = GPIO8)
part('U6', 'Memory_RAM:APS6404L-3SQRx-SN', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', 'APS6404L-3SQR-SN', S,
     {'1': 'PSRAM_CS', '2': 'QSPI_SD1', '3': 'QSPI_SD2', '4': 'GND', '5': 'QSPI_SD0',
      '6': 'QSPI_SCLK', '7': 'QSPI_SD3', '8': '+3V3'},
     mpn='APS6404L-3SQR-SN', mfr='AP Memory', lcsc='C5333729', desc='64Mbit (8MB) QSPI PSRAM 3.3V, SOP-8')
C('C25', '100n', '+3V3', 'GND', S)
R('R19', '10k', '+3V3', 'PSRAM_CS', S, desc='PSRAM CS pull-up 10k 1% 0402')
# Buttons
part('SW1', 'Switch:SW_Push', 'Button_Switch_SMD:SW_SPST_PTS810', 'BOOT', S, {'1': 'USB_BOOT', '2': 'GND'},
     mpn='PTS810 SJM 250 SMTR LFS', mfr='C&K', lcsc='C116501', desc='Tactile switch 4.2x3.2mm SMD (BOOTSEL)')
part('SW2', 'Switch:SW_Push', 'Button_Switch_SMD:SW_SPST_PTS810', 'RESET', S, {'1': 'RUN', '2': 'RUN_SW'},
     mpn='PTS810 SJM 250 SMTR LFS', mfr='C&K', lcsc='C116501', desc='Tactile switch 4.2x3.2mm SMD (RESET)')
R('R20', '1k', 'RUN_SW', 'GND', S, desc='RESET button series 1k 1% 0402 (RPi reference)')
# SWD debug connector (Raspberry Pi 3-pin debug connector standard)
part('J3', 'Connector_Generic_MountingPin:Conn_01x03_MountingPin',
     'Connector_JST:JST_SH_SM03B-SRSS-TB_1x03-1MP_P1.00mm_Horizontal', 'SWD', S,
     {'1': 'SWCLK', '2': 'GND', '3': 'SWDIO', 'MP': 'GND'},
     mpn='SM03B-SRSS-TB(LF)(SN)', mfr='JST', lcsc='C160403',
     desc='JST SH 3-pin, Raspberry Pi Debug Connector pinout (SWCLK/GND/SWDIO)')

# =========================================================================
# Sheet: wireless (ESP32-C6-MINI-1 as Wi-Fi 6 / BLE 5 co-processor)
# =========================================================================
S = 'wireless'
esp = {'GND': 'GND', '3V3': '+3V3', 'EN': 'ESP_EN', 'IO9': 'ESP_BOOT', 'IO8': 'ESP_IO8',
       'RXD0': 'ESP_RXD', 'TXD0': 'ESP_TXD', 'IO6': 'ESP_RTS', 'IO7': 'ESP_CTS',
       'IO12': 'ESP_USB_DM', 'IO13': 'ESP_USB_DP',
       'IO0': None, 'IO1': None, 'IO2': None, 'IO3': None, 'IO4': None, 'IO5': None,
       'IO14': None, 'IO15': None, 'IO18': None, 'IO19': None, 'IO20': None, 'IO21': None,
       'IO22': None, 'IO23': None, 'NC': None}
part('U7', 'RF_Module:ESP32-C6-MINI-1', 'RP2350_Dev:ESP32-C6-MINI-1_BoardEdge', 'ESP32-C6-MINI-1-N4', S, esp,
     mpn='ESP32-C6-MINI-1-N4', mfr='Espressif', lcsc='C5736265',
     desc='Wi-Fi 6 / BLE 5 / 802.15.4 module, PCB antenna, 4MB flash')
C('C26', '10u', '+3V3', 'GND', S)
C('C27', '100n', '+3V3', 'GND', S)
R('R21', '10k', '+3V3', 'ESP_EN', S, desc='ESP EN pull-up 10k 1% 0402')
C('C28', '1u', 'ESP_EN', 'GND', S)
R('R22', '10k', '+3V3', 'ESP_BOOT', S, desc='ESP GPIO9 strap pull-up 10k 1% 0402')
R('R23', '10k', '+3V3', 'ESP_IO8', S, desc='ESP GPIO8 strap pull-up 10k 1% 0402')
part('TP1', 'Connector:TestPoint', 'TestPoint:TestPoint_Pad_D1.0mm', 'ESP_D-', S, {'1': 'ESP_USB_DM'},
     in_bom=False, desc='Test pad: ESP32-C6 USB D-')
part('TP2', 'Connector:TestPoint', 'TestPoint:TestPoint_Pad_D1.0mm', 'ESP_D+', S, {'1': 'ESP_USB_DP'},
     in_bom=False, desc='Test pad: ESP32-C6 USB D+')

# =========================================================================
# Sheet: io
# =========================================================================
S = 'io'
part('J4', 'Connector:Micro_SD_Card_Det_Hirose_DM3AT', 'Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5',
     'DM3AT-SF-PEJM5', S,
     {'DAT2': 'SD_D2', 'DAT3/CD': 'SD_D3', 'CMD': 'SD_CMD', 'VDD': '+3V3', 'CLK': 'SD_CLK',
      'VSS': 'GND', 'DAT0': 'SD_D0', 'DAT1': 'SD_D1', 'DET_B': 'GND', 'DET_A': 'SD_DET', 'SH': 'GND'},
     mpn='DM3AT-SF-PEJM5', mfr='Hirose', lcsc='C114218', desc='microSD push-push socket with card detect')
R('R24', '10k', '+3V3', 'SD_CMD', S, desc='SD CMD pull-up 10k 1% 0402')
R('R25', '10k', '+3V3', 'SD_D0', S, desc='SD DAT0 pull-up 10k 1% 0402')
R('R26', '10k', '+3V3', 'SD_D1', S, desc='SD DAT1 pull-up 10k 1% 0402')
R('R27', '10k', '+3V3', 'SD_D2', S, desc='SD DAT2 pull-up 10k 1% 0402')
R('R28', '10k', '+3V3', 'SD_D3', S, desc='SD DAT3 pull-up 10k 1% 0402')
R('R29', '10k', '+3V3', 'SD_DET', S, desc='SD card-detect pull-up 10k 1% 0402')
C('C29', '10u', '+3V3', 'GND', S)
C('C30', '100n', '+3V3', 'GND', S)
# Qwiic / STEMMA QT
part('J5', 'Connector_Generic_MountingPin:Conn_01x04_MountingPin',
     'Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal', 'QWIIC', S,
     {'1': 'GND', '2': '+3V3', '3': 'I2C_SDA', '4': 'I2C_SCL', 'MP': 'GND'},
     mpn='SM04B-SRSS-TB(LF)(SN)', mfr='JST', lcsc='C160404', desc='JST SH 4-pin (Qwiic / STEMMA QT)')
R('R30', '4.7k', '+3V3', 'I2C_SDA', S, desc='I2C SDA pull-up 4.7k 1% 0402')
R('R31', '4.7k', '+3V3', 'I2C_SCL', S, desc='I2C SCL pull-up 4.7k 1% 0402')
# Addressable RGB LED
part('D2', 'LED:WS2812B-2020', 'LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm', 'WS2812B-2020', S,
     {'VDD': '+3V3', 'VSS': 'GND', 'DIN': 'NEOPIXEL', 'DOUT': None},
     mpn='WS2812B-2020-V6', mfr='Worldsemi', lcsc='C52917434', desc='Addressable RGB LED 2.0x2.0mm')
C('C31', '100n', '+3V3', 'GND', S)
# User LED
R('R32', '1k', 'LED_USER', 'LED_USER_A', S, desc='User LED resistor 1k 1% 0402')
part('D3', 'Device:LED', 'LED_SMD:LED_0603_1608Metric', 'YELLOW', S, {'1': 'GND', '2': 'LED_USER_A'},
     mpn='NCD0603Y2', mfr='Foshan NationStar', lcsc='C89811', desc='LED yellow 0603 (user, GPIO25)')
# Pin headers (2.54mm, mounted on the bottom side so the board plugs into a breadboard)
HDR_A = ['VBUS', 'VSYS', 'VBAT', 'GND', '+3V3', 'LDO_EN', 'RUN', 'GND', 'GPIO26_A0', 'GPIO27_A1',
         'GPIO28_A2', 'GND']
HDR_B = ['GPIO0', 'GPIO1', 'GPIO2', 'GPIO3', 'GPIO4', 'GPIO5', 'GND', 'I2C_SDA', 'I2C_SCL', '+3V3',
         'GND', 'GND']
part('J6', 'Connector_Generic:Conn_01x12', 'Connector_PinHeader_2.54mm:PinHeader_1x12_P2.54mm_Vertical',
     'PWR/ADC', S, {str(i + 1): n for i, n in enumerate(HDR_A)},
     mpn='PZ254V-11-12P', mfr='XFCN', lcsc='C2840012', desc='1x12 2.54mm male header, THT (fit on bottom side)')
part('J7', 'Connector_Generic:Conn_01x12', 'Connector_PinHeader_2.54mm:PinHeader_1x12_P2.54mm_Vertical',
     'GPIO', S, {str(i + 1): n for i, n in enumerate(HDR_B)},
     mpn='PZ254V-11-12P', mfr='XFCN', lcsc='C2840012', desc='1x12 2.54mm male header, THT (fit on bottom side)')
# Fiducials and mounting holes (not in BOM)
for i in range(3):
    part('FID%d' % (i + 1), 'Mechanical:Fiducial', 'Fiducial:Fiducial_1mm_Mask2mm', 'Fiducial', S, {},
         in_bom=False, desc='Assembly fiducial')


# -------------------------------------------------------------------------
def resolve():
    """Resolve name-keyed pin maps into number-keyed ones; verify completeness."""
    for c in COMPONENTS:
        pins = kilib.symbol_pins(c['sym'])
        bynum = {}
        for k, net in c['pins'].items():
            matched = [p for p in pins if p['number'] == k]
            if not matched:
                matched = [p for p in pins if p['name'] == k]
            if not matched:
                raise KeyError('%s: pin %r not found' % (c['ref'], k))
            for p in matched:
                bynum[p['number']] = net
        missing = sorted(set(p['number'] for p in pins) - set(bynum))
        if missing:
            raise KeyError('%s: unassigned pins %s' % (c['ref'], missing))
        c['pinnets'] = bynum
        c['pinlist'] = pins
    return COMPONENTS


def nets():
    out = {}
    for c in resolve():
        for num, n in c['pinnets'].items():
            if n:
                out.setdefault(n, []).append((c['ref'], num))
    return out


if __name__ == '__main__':
    ns = nets()
    for n in sorted(ns):
        print('%-14s %s' % (n, ' '.join('%s.%s' % x for x in ns[n])))
    singles = [n for n in ns if len(ns[n]) < 2]
    print('single-pin nets:', singles)
    print(len(COMPONENTS), 'components')
