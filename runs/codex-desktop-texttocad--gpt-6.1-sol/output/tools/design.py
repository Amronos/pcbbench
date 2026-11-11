from pathlib import Path
from library_tools import flatten_symbol, child, pin_description

ROOT = Path(__file__).resolve().parents[1]
NAME = 'Atlas2350'
PARTS = []


def add(ref, library, symbol, value, mpn, manufacturer, nets, board, sheet, schematic,
        footprint=None, description=''):
    template = flatten_symbol(library, symbol)
    footprint = footprint or next(item[2] for item in template
                                   if isinstance(item, list) and str(item[0]) == 'property'
                                   and item[1] == 'Footprint')
    pin_numbers = {pin['number'] for pin in pin_description(template)}
    nets = {str(number): net for number, net in nets.items()}
    if pin_numbers != set(nets):
        raise ValueError(f'{ref}: missing {pin_numbers - set(nets)}, extra {set(nets) - pin_numbers}')
    PARTS.append(dict(ref=ref, library=library, symbol=symbol, value=value, mpn=mpn,
                      manufacturer=manufacturer, nets=nets, board=board, sheet=sheet,
                      schematic=schematic, footprint=footprint, description=description))


def resistor(ref, value, mpn, first, second, board, sheet, schematic, size='0402'):
    add(ref, 'Device', 'R', value, mpn, 'Yageo', {1: first, 2: second}, board, sheet,
        schematic, f'Resistor_SMD:R_{size}_{"1005" if size == "0402" else "1608"}Metric')


def capacitor(ref, value, mpn, first, second, board, sheet, schematic, size='0402'):
    add(ref, 'Device', 'C', value, mpn, 'Murata', {1: first, 2: second}, board, sheet,
        schematic, f'Capacitor_SMD:C_{size}_{dict(zip(["0402", "0603", "0805", "1206"], ["1005", "1608", "2012", "3216"]))[size]}Metric')


gpio = {
    0: 'PSRAM_CS', 1: 'GPIO1', 2: 'GPIO2', 3: 'GPIO3', 4: 'I2C_SDA', 5: 'I2C_SCL',
    6: 'GPIO6', 7: 'GPIO7', 8: 'GPIO8', 9: 'GPIO9', 10: 'SD_CLK', 11: 'SD_MOSI',
    12: 'SD_MISO', 13: 'SD_CS', 14: 'RGB_DATA', 15: 'SD_DETECT', 16: 'USB_500_EN',
    17: 'USB_SUSPEND_EN', 18: 'ESP_EN_CTRL', 19: 'ESP_BOOT_CTRL', 20: 'WIFI_TX', 21: 'WIFI_RX',
    22: 'WIFI_CTS', 23: 'WIFI_RTS', 24: 'CHARGE_N', 25: 'POWERGOOD_N',
    26: 'BAT_ADC', 27: 'VBUS_ADC', 28: 'GPIO28_ADC2', 29: 'GPIO29_ADC3'
}
rp_nets = {1: '+3V3', 6: '+1V1', 11: '+3V3', 20: '+3V3', 21: 'XIN',
           22: 'XOUT', 23: '+1V1', 24: 'SWCLK', 25: 'SWDIO', 26: 'RUN',
           30: '+3V3', 38: '+3V3', 39: '+1V1', 44: 'ADC_AVDD', 45: '+3V3',
           46: '+3V3', 47: 'GND', 48: None, 49: '+3V3', 50: 'GND',
           51: 'USB_PHY_D-', 52: 'USB_PHY_D+', 53: '+3V3', 54: '+3V3',
           55: 'QSPI_IO3', 56: 'QSPI_CLK_SRC', 57: 'QSPI_IO0',
           58: 'QSPI_IO2', 59: 'QSPI_IO1', 60: 'FLASH_CS', 61: 'GND'}
for pin in pin_description(flatten_symbol('MCU_RaspberryPi', 'RP2350A')):
    if pin['name'].startswith('GPIO'):
        rp_nets[int(pin['number'])] = gpio[int(pin['name'][4:].split('/')[0])]
add('U1', 'MCU_RaspberryPi', 'RP2350A', 'RP2350A', 'RP2350A', 'Raspberry Pi',
    rp_nets, (30, 42, 90), 'MCU', (100, 103, 0),
    'Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm',
    'Dual Cortex-M33 / Hazard3, 520KB SRAM, 150MHz; external 1.1V core supply')

memory_nets = {1: 'FLASH_CS', 2: 'QSPI_IO1', 3: 'QSPI_IO2', 4: 'GND',
               5: 'QSPI_IO0', 6: 'QSPI_CLK', 7: 'QSPI_IO3', 8: '+3V3'}
add('U2', 'Memory_Flash', 'W25Q32JVSS', 'W25Q32JVSSIQ', 'W25Q32JVSSIQ', 'Winbond',
    memory_nets, (20, 52, 90), 'Memory', (70, 70, 0),
    description='32Mbit / 4MiB QSPI NOR flash')
add('U3', 'Memory_RAM', 'APS6404L-3SQRx-SN', 'APS6404L-3SQR-SN', 'APS6404L-3SQR-SN',
    'AP Memory', {**memory_nets, 1: 'PSRAM_CS'}, (29, 56, 90), 'Memory', (160, 70, 0),
    description='64Mbit / 8MiB 3.3V QSPI PSRAM, SOP-8 narrow body')

add('U4', 'Battery_Management', 'BQ24074RGT', 'BQ24074RGTR', 'BQ24074RGTR',
    'Texas Instruments', {1: 'BAT_TS', 2: 'VBAT', 3: 'VBAT', 4: 'GND', 5: 'USB_SUSPEND_EN',
                         6: 'USB_500_EN', 7: 'POWERGOOD_N', 8: 'GND', 9: 'CHARGE_N',
                         10: 'VSYS', 11: 'VSYS', 12: 'CHG_ILIM', 13: 'VBUS',
                         14: None, 15: None, 16: 'CHG_ISET', 17: 'GND'},
    (13, 19, 0), 'Power', (70, 72, 0),
    description='4.2V single-cell charger, USB100/500 modes and dynamic power path')
add('U5', 'Custom', 'TPS63070RNM', 'TPS63070RNMR', 'TPS63070RNMR',
    'Texas Instruments', {1: 'PWR_EN', 2: 'MAIN_PG', 3: 'MAIN_VAUX', 4: 'GND',
                         5: 'MAIN_FB', 6: 'GND', 7: '+3V3', 8: '+3V3',
                         9: 'BUCK_L2', 10: 'GND', 11: 'BUCK_L1', 12: 'VSYS',
                         13: 'VSYS', 14: 'PWR_EN', 15: 'GND'},
    (15, 29, 0), 'Power', (170, 72, 0),
    description='2A-class adjustable buck-boost set3.296V; 2.8V to4.5V system input')
add('U7', 'Regulator_Linear', 'TLV75801PDBV', 'TLV75801PDBVR', 'TLV75801PDBVR',
    'Texas Instruments', {1: '+3V3', 2: 'GND', 3: 'MAIN_PG', 4: 'CORE_FB', 5: '+1V1'},
    (28, 31, 0), 'MCU', (240, 55, 0),
    description='500mA adjustable LDO, 1.1V core rail, 10k/10k feedback')

esp_nets = {1: '+3V3', 2: 'ESP_EN', 3: 'WIFI_CTS', 4: 'WIFI_RTS', 5: 'WIFI_TX', 6: 'WIFI_RX',
            7: 'ESP_STRAP8', 8: 'ESP_BOOT', 9: 'GND', 10: None, 11: 'ESP_PROG_RX',
            12: 'ESP_PROG_TX', 13: None, 14: None, 15: None, 16: 'ESP_STRAP2',
            17: None, 18: None, 19: 'GND'}
add('U6', 'RF_Module', 'ESP32-C3-WROOM-02', 'ESP32-C3-WROOM-02-N4',
    'ESP32-C3-WROOM-02-N4', 'Espressif Systems', esp_nets, (65, 7, 0),
    'Wireless', (90, 90, 0), description='4MB flash Wi-Fi 802.11b/g/n and BLE5 UART coprocessor')

usb_nets = {'A1': 'GND', 'A4': 'VBUS_RAW', 'A5': 'USB_CC1', 'A6': 'USB_D+',
            'A7': 'USB_D-', 'A8': None, 'A9': 'VBUS_RAW', 'A12': 'GND',
            'B1': 'GND', 'B4': 'VBUS_RAW', 'B5': 'USB_CC2', 'B6': 'USB_D+',
            'B7': 'USB_D-', 'B8': None, 'B9': 'VBUS_RAW', 'B12': 'GND', 'SH': 'GND'}
add('J1', 'Connector', 'USB_C_Receptacle_USB2.0_16P', 'USB-C', 'USB4105-GF-A', 'GCT',
    usb_nets, (3, 40, 270), 'Interfaces', (65, 80, 0),
    'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',
    'USB2.0 device / 5V sink; both CC pins 5.1k Rd; through-hole shell stakes')
add('J2', 'Connector_Generic', 'Conn_01x03', 'LiPo + NTC',
    'S3B-PH-SM4-TB(LF)(SN)', 'JST', {1: 'VBAT', 2: 'GND', 3: 'BAT_TS'},
    (4, 15, 270), 'Power', (32, 72, 0),
    'Connector_JST:JST_PH_S3B-PH-SM4-TB_1x03-1MP_P2.00mm_Horizontal',
    'External protected 1S LiPo with 10k NTC; custom 3-pin polarity; battery not supplied')
add('J3', 'Connector', 'Micro_SD_Card_Det_Hirose_DM3AT', 'microSD SPI',
    'DM3AT-SF-PEJM5', 'Hirose', {1: 'SD_DAT2', 2: 'SD_CS', 3: 'SD_MOSI',
                              4: '+3V3', 5: 'SD_CLK', 6: 'GND', 7: 'SD_MISO',
                              8: 'SD_DAT1', 9: 'SD_DETECT', 10: 'GND', 'SH': 'GND'},
    (68, 62, 0), 'Interfaces', (220, 82, 0),
    'Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5',
    'Push-push microSD socket, SPI mode, card detect, no card supplied')
add('J4', 'Connector_Generic', 'Conn_01x04', 'Qwiic / STEMMA QT',
    'SM04B-SRSS-TB(LF)(SN)', 'JST', {1: 'GND', 2: '+3V3', 3: 'I2C_SDA', 4: 'I2C_SCL'},
    (76, 38, 90), 'Interfaces', (295, 62, 0),
    'Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal',
    '3.3V I2C, pin1 GND, pin2 VCC, pin3 SDA, pin4 SCL')
header_nets = {1: '+3V3', 2: 'GND', 3: 'GPIO1', 4: 'GPIO2', 5: 'GPIO3', 6: 'GPIO6',
               7: 'GPIO7', 8: 'GPIO8', 9: 'GPIO9', 10: 'CHARGE_N', 11: 'POWERGOOD_N',
               12: 'RGB_DATA', 13: 'GPIO28_ADC2', 14: 'GPIO29_ADC3', 15: 'I2C_SDA',
               16: 'I2C_SCL', 17: 'RUN', 18: 'GND', 19: 'VBUS', 20: 'VSYS'}
add('J5', 'Connector_Generic', 'Conn_02x10_Odd_Even', 'GPIO expansion',
    'TSW-110-07-G-D', 'Samtec', header_nets, (48, 49, 0), 'MCU', (240, 165, 0),
    'Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical',
    'Through-hole 2x10 male header, PCBWay must fit and solder')
add('J6', 'Connector_Generic', 'Conn_02x05_Odd_Even', 'Cortex SWD',
    'FTSH-105-01-L-D', 'Samtec', {1: '+3V3', 2: 'SWDIO', 3: 'GND', 4: 'SWCLK',
                                5: 'GND', 6: None, 7: None, 8: None, 9: 'GND', 10: 'RUN'},
    (42, 28, 0), 'MCU', (315, 168, 0),
    'Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical',
    '10-pin Cortex SWD through-hole header; no SWO; pin7 remains physically present')
add('J7', 'Connector_Generic', 'Conn_01x06', 'ESP programming',
    'TSW-106-07-G-S', 'Samtec', {1: 'GND', 2: '+3V3', 3: 'ESP_PROG_TX',
                              4: 'ESP_PROG_RX', 5: 'ESP_BOOT', 6: 'ESP_EN'},
    (57, 24, 90), 'Wireless', (220, 76, 0),
    'Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical',
    '3.3V UART0 flashing header; never connect a 5V UART')

add('U8', 'Power_Protection', 'USBLC6-2SC6', 'USBLC6-2SC6', 'USBLC6-2SC6',
    'STMicroelectronics', {1: 'USB_D+', 2: 'GND', 3: 'USB_D-',
                          4: None, 5: 'VBUS', 6: None},
    (10, 40, 90), 'Interfaces', (118, 83, 0),
    'Package_TO_SOT_SMD:SOT-23-6', 'Low capacitance USB ESD shunt; unused internally-common I/O4/6 pads left externally NC')
add('D1', 'LED', 'WS2812B-2020', 'WS2812B-2020-V6', 'WS2812B-2020-V6', 'Worldsemi',
    {1: None, 2: 'GND', 3: 'RGB_DIN', 4: 'LED_VDD'}, (74, 26, 0), 'Interfaces', (294, 140, 0),
    'LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm',
    'V6 only, 3.3-5.5V and VIH=0.55VDD; switched VSYS, blank below battery about3.6V under load')
add('U10', 'Power_Management', 'TPS22919DCK', 'TPS22919DCKR', 'TPS22919DCKR',
    'Texas Instruments', {1: 'VSYS', 2: 'GND', 3: 'PWR_EN', 4: None,
                         5: 'LED_VDD', 6: 'LED_VDD'},
    (77, 23, 0), 'Interfaces', (285, 180, 0),
    description='1.6-5.5V LED load switch; ON=PWR_EN, QOD tied OUT; LED off with SW5')

add('F1', 'Device', 'Polyfuse', '500mA hold', 'MF-MSMF050-2', 'Bourns',
    {1: 'VBUS_RAW', 2: 'VBUS'}, (8, 34, 0), 'Interfaces', (72, 35, 90),
    'Fuse:Fuse_1812_4532Metric', 'Resettable input fuse, 0.5A hold / 1A trip')
add('L1', 'Device', 'L', '1.0uH', 'XAL4020-102MEC', 'Coilcraft',
    {1: 'BUCK_L1', 2: 'BUCK_L2'}, (11, 29, 90), 'Power', (166, 42, 90),
    'Inductor_SMD:L_Coilcraft_XAL4020-XXX', 'Shielded power inductor; 1uH with >=22uF effective output capacitance')
add('FB1', 'Device', 'FerriteBead', '600R @ 100MHz', 'BLM15AG601SN1D', 'Murata',
    {1: '+3V3', 2: 'ADC_AVDD'}, (34, 35, 0), 'MCU', (177, 108, 90),
    'Inductor_SMD:L_0402_1005Metric', 'ADC analog supply bead, 300mA')
add('Y1', 'Device', 'Crystal_GND24', '12MHz / 10pF', 'ABM8-272-T3', 'Abracon',
    {1: 'XIN', 2: 'GND', 3: 'XTAL_OUT', 4: 'GND'}, (39, 43, 0), 'MCU', (60, 177, 0),
    'Crystal:Crystal_SMD_Abracon_ABM8G-4Pin_3.2x2.5mm',
    'Raspberry Pi recommended 12MHz crystal, 10pF CL, <=50ohm ESR')

for ref, value, mpn, first, second, board, sheet, schematic in [
    ('R1', '5.1k 1%', 'RC0402FR-075K1L', 'USB_CC1', 'GND', (8, 45, 0), 'Interfaces', (44, 143, 0)),
    ('R2', '5.1k 1%', 'RC0402FR-075K1L', 'USB_CC2', 'GND', (8, 48, 0), 'Interfaces', (67, 143, 0)),
    ('R3', '27R 1%', 'RC0402FR-0727RL', 'USB_D+', 'USB_PHY_D+', (25, 41.8, 0), 'Interfaces', (155, 70, 90)),
    ('R4', '27R 1%', 'RC0402FR-0727RL', 'USB_D-', 'USB_PHY_D-', (25, 40.7, 0), 'Interfaces', (155, 96, 90)),
    ('R5', '3.57k 1%', 'RC0402FR-073K57L', 'CHG_ISET', 'GND', (10, 21, 90), 'Power', (46, 132, 0)),
    ('R6', '3.24k 1%', 'RC0402FR-073K24L', 'CHG_ILIM', 'GND', (13, 23, 0), 'Power', (72, 132, 0)),
    ('R7', '100k 1%', 'RC0402FR-07100KL', 'USB_500_EN', 'GND', (17, 17, 0), 'Power', (98, 132, 0)),
    ('R8', '10k 1%', 'RC0402FR-0710KL', 'CHARGE_N', '+3V3', (17, 21, 90), 'Power', (124, 132, 0)),
    ('R9', '10k 1%', 'RC0402FR-0710KL', 'POWERGOOD_N', '+3V3', (17, 23, 90), 'Power', (150, 132, 0)),
    ('R10', '470k 1%', 'RC0402FR-07470KL', 'VBAT', 'BAT_SENSE', (36, 34, 90), 'Power', (255, 67, 0)),
    ('R11', '470k 1%', 'RC0402FR-07470KL', 'BAT_SENSE', 'GND', (38, 34, 90), 'Power', (255, 93, 0)),
    ('R12', '1M 1%', 'RC0402FR-071ML', 'VBUS', 'VBUS_ADC', (38, 36, 90), 'Power', (298, 67, 0)),
    ('R13', '330k 1%', 'RC0402FR-07330KL', 'VBUS_ADC', 'GND', (40, 36, 90), 'Power', (298, 93, 0)),
    ('R14', '10k 1%', 'RC0402FR-0710KL', 'FLASH_CS', '+3V3', (20, 47, 0), 'Memory', (48, 122, 0)),
    ('R15', '10k 1%', 'RC0402FR-0710KL', 'PSRAM_CS', '+3V3', (29, 51, 0), 'Memory', (144, 122, 0)),
    ('R16', '33R 1%', 'RC0402FR-0733RL', 'QSPI_CLK_SRC', 'QSPI_CLK', (25, 44.5, 0), 'Memory', (106, 48, 90)),
    ('R17', '1k 1%', 'RC0402FR-071KL', 'XOUT', 'XTAL_OUT', (35.5, 43, 90), 'MCU', (58, 203, 90)),
    ('R18', '10k 1%', 'RC0402FR-0710KL', 'RUN', '+3V3', (37, 48, 90), 'MCU', (150, 171, 0)),
    ('R19', '1k 1%', 'RC0402FR-071KL', 'BOOT_SWITCH', 'FLASH_CS', (34, 62, 90), 'Memory', (240, 68, 90)),
    ('R20', '10k 1%', 'RC0402FR-0710KL', 'ESP_EN', 'GND', (54, 8, 90), 'Wireless', (170, 120, 0)),
    ('R21', '10k 1%', 'RC0402FR-0710KL', 'ESP_BOOT', '+3V3', (54, 12, 90), 'Wireless', (210, 120, 0)),
    ('R22', '1k 1%', 'RC0402FR-071KL', 'ESP_EN_CTRL', 'ESP_EN', (53, 16, 90), 'Wireless', (170, 63, 90)),
    ('R23', '1k 1%', 'RC0402FR-071KL', 'ESP_BOOT_CTRL', 'ESP_BOOT', (54, 18, 90), 'Wireless', (170, 87, 90)),
    ('R24', '4.7k 1%', 'RC0402FR-074K7L', 'I2C_SDA', '+3V3', (70, 36, 90), 'Interfaces', (267, 92, 0)),
    ('R25', '4.7k 1%', 'RC0402FR-074K7L', 'I2C_SCL', '+3V3', (70, 40, 90), 'Interfaces', (305, 92, 0)),
    ('R26', '47k 1%', 'RC0402FR-0747KL', 'SD_CS', '+3V3', (58, 57, 90), 'Interfaces', (189, 144, 0)),
    ('R27', '47k 1%', 'RC0402FR-0747KL', 'SD_MOSI', '+3V3', (58, 60, 90), 'Interfaces', (213, 144, 0)),
    ('R28', '47k 1%', 'RC0402FR-0747KL', 'SD_MISO', '+3V3', (58, 63, 90), 'Interfaces', (237, 144, 0)),
    ('R29', '47k 1%', 'RC0402FR-0747KL', 'SD_DAT1', '+3V3', (63, 53, 0), 'Interfaces', (189, 181, 0)),
    ('R30', '47k 1%', 'RC0402FR-0747KL', 'SD_DAT2', '+3V3', (66, 53, 0), 'Interfaces', (213, 181, 0)),
    ('R31', '10k 1%', 'RC0402FR-0710KL', 'SD_DETECT', '+3V3', (72, 52, 0), 'Interfaces', (237, 181, 0)),
    ('R32', '330R 1%', 'RC0402FR-07330RL', 'RGB_DATA', 'RGB_DIN', (70, 26, 0), 'Interfaces', (267, 140, 90)),
    ('R33', '100k 1%', 'RC0402FR-07100KL', 'RGB_DIN', 'GND', (72, 29, 90), 'Interfaces', (315, 180, 0)),
    ('R36', '10k 1%', 'RC0402FR-0710KL', 'ESP_STRAP8', '+3V3', (54, 14, 90), 'Wireless', (252, 120, 0)),
    ('R37', '10k 1%', 'RC0402FR-0710KL', 'ESP_STRAP2', '+3V3', (77, 3, 90), 'Wireless', (294, 120, 0)),
    ('R38', '100R 1%', 'RC0402FR-07100RL', 'BAT_BUF', 'BAT_ADC', (39, 17, 0), 'Power', (326, 83, 90)),
    ('R39', '1k 1%', 'RC0402FR-071KL', 'PWR_SWITCH', 'PWR_EN', (15, 38, 0), 'Power', (175, 150, 90)),
    ('R40', '10k 1%', 'RC0402FR-0710KL', 'MAIN_PG', '+3V3', (22, 31, 90), 'Power', (345, 151, 0)),
    ('R41', '100k 1%', 'RC0402FR-07100KL', 'USB_SUSPEND_EN', 'GND', (21, 14, 0), 'Power', (124, 95, 0)),
    ('R42', '312k 0.1%', 'RT0402BRD07312KL', '+3V3', 'MAIN_FB', (20, 35, 90), 'Power', (250, 154, 0)),
    ('R43', '100k 0.1%', 'RT0402BRD07100KL', 'MAIN_FB', 'GND', (22, 35, 90), 'Power', (280, 154, 0)),
]:
    resistor(ref, value, mpn, first, second, board, sheet, schematic)
for ref, first, second, board, schematic in [
    ('R34', '+1V1', 'CORE_FB', (30, 28, 90), (240, 113, 0)),
    ('R35', 'CORE_FB', 'GND', (30, 26, 90), (270, 113, 0))
]:
    resistor(ref, '10k 0.1%', 'RT0402BRD0710KL', first, second, board, 'MCU', schematic)

cap100 = 'GRM155R71C104KA88D'
cap1u = 'GRM155R61A105KE15D'
cap47u = 'GRM188R60J475KE19D'
cap10u = 'GRM21BR61A106KE19L'
cap22u = 'GRM21BR60J226ME39L'
for ref, first, board, sheet, schematic in [
    ('C1', '+3V3', (29, 47, 0), 'MCU', (170, 38, 0)),
    ('C2', '+3V3', (33, 47, 0), 'MCU', (196, 38, 0)),
    ('C3', '+3V3', (35, 46, 90), 'MCU', (222, 38, 0)),
    ('C4', '+3V3', (35, 40, 90), 'MCU', (248, 38, 0)),
    ('C5', '+3V3', (33, 37, 0), 'MCU', (274, 38, 0)),
    ('C6', '+3V3', (31, 37, 0), 'MCU', (300, 38, 0)),
    ('C7', '+3V3', (25, 38, 90), 'MCU', (170, 75, 0)),
    ('C8', '+3V3', (25, 46, 90), 'MCU', (196, 75, 0)),
    ('C9', '+3V3', (25, 36, 90), 'MCU', (222, 75, 0)),
    ('C10', 'ADC_AVDD', (36, 37, 90), 'MCU', (170, 133, 0)),
    ('C11', '+1V1', (31, 47, 0), 'MCU', (275, 75, 0)),
    ('C12', '+1V1', (35, 37, 0), 'MCU', (301, 75, 0)),
    ('C13', '+1V1', (35, 44, 90), 'MCU', (325, 75, 0)),
    ('C14', '+3V3', (16, 52, 90), 'Memory', (74, 122, 0)),
    ('C15', '+3V3', (25, 56, 90), 'Memory', (171, 122, 0)),
    ('C16', 'VBUS', (15, 15, 90), 'Power', (40, 188, 0)),
    ('C17', 'VSYS', (18, 29, 90), 'Power', (171, 170, 0)),
    ('C18', 'BAT_TS', (8, 17, 0), 'Power', (203, 133, 0)),
    ('C19', 'BAT_SENSE', (40, 34, 90), 'Power', (255, 132, 0)),
    ('C20', 'VBUS_ADC', (42, 36, 90), 'Power', (298, 132, 0)),
    ('C21', 'ESP_EN', (51, 8, 90), 'Wireless', (170, 158, 0)),
    ('C22', '+3V3', (53, 4, 90), 'Wireless', (35, 155, 0)),
    ('C23', '+3V3', (68, 51, 0), 'Interfaces', (259, 219, 0)),
    ('C24', 'LED_VDD', (74, 30, 90), 'Interfaces', (294, 219, 0)),
    ('C40', '+3V3', (33, 16, 90), 'Power', (340, 125, 0)),
    ('C42', 'MAIN_VAUX', (16, 33.8, 0), 'Power', (310, 154, 0)),
]:
    capacitor(ref, '100nF 16V X7R', cap100, first, 'GND', board, sheet, schematic)
for ref, value, mpn, first, board, sheet, schematic, size in [
    ('C25', '4.7uF 6.3V X5R', cap47u, '+3V3', (27, 36, 90), 'MCU', (326, 38, 0), '0603'),
    ('C26', '2.2uF 10V X5R', 'GRM188R61A225KE15D', '+3V3', (25, 31, 90), 'MCU', (200, 55, 0), '0603'),
    ('C27', '2.2uF 10V X5R', 'GRM188R61A225KE15D', '+1V1', (31, 31, 90), 'MCU', (279, 55, 0), '0603'),
    ('C28', '10uF 10V X5R', cap10u, 'VBAT', (9, 18, 90), 'Power', (74, 188, 0), '0805'),
    ('C29', '4.7uF 10V X5R', 'GRM21BR61A475KA73L', 'VBUS', (13, 15, 90), 'Power', (107, 188, 0), '0805'),
    ('C30', '10uF 10V X5R', cap10u, 'VSYS', (18, 19, 90), 'Power', (139, 188, 0), '0805'),
    ('C31', '10uF 10V X5R', cap10u, 'VSYS', (15, 25, 90), 'Power', (174, 188, 0), '0805'),
    ('C32', '22uF 16V X5R', 'GRM31CR61C226KE15L', '+3V3', (19, 29, 90), 'Power', (205, 188, 0), '1206'),
    ('C33', '22uF 16V X5R', 'GRM31CR61C226KE15L', '+3V3', (19, 32, 90), 'Power', (237, 188, 0), '1206'),
    ('C34', '22uF 6.3V X5R', cap22u, '+3V3', (52, 2, 90), 'Wireless', (63, 155, 0), '0805'),
    ('C35', '10uF 10V X5R', cap10u, '+3V3', (70, 49, 0), 'Interfaces', (224, 219, 0), '0805'),
    ('C36', '1uF 10V X5R', cap1u, 'LED_VDD', (76, 30, 90), 'Interfaces', (326, 219, 0), '0402'),
    ('C45', '1uF 10V X5R', cap1u, 'VSYS', (77, 20, 90), 'Interfaces', (258, 180, 0), '0402'),
    ('C37', '1uF 10V X5R', cap1u, 'ADC_AVDD', (38, 37, 90), 'MCU', (196, 133, 0), '0402'),
    ('C43', '1uF 10V X5R', cap1u, '+3V3', (33, 56, 90), 'Memory', (196, 122, 0), '0402'),
    ('C44', '10uF 10V X5R', cap10u, '+3V3', (54, 2, 270), 'Wireless', (90, 155, 0), '0805'),
]:
    capacitor(ref, value, mpn, first, 'GND', board, sheet, schematic, size)
capacitor('C41', '1nF 50V C0G', 'GRM1555C1H102JA01D', 'BAT_ADC', 'GND',
          (41, 17, 0), 'Power', (368, 125, 0))
add('U9', 'Custom', 'TLV9001IDBV', 'TLV9001IDBVR', 'TLV9001IDBVR',
    'Texas Instruments', {1: 'BAT_BUF', 2: 'GND', 3: 'BAT_SENSE', 4: 'BAT_BUF', 5: '+3V3'},
    (35, 16, 0), 'Power', (295, 118, 0), 'Package_TO_SOT_SMD:SOT-23-5',
    'RRIO unity-gain buffer for high-impedance battery divider; 100ohm ADC isolation')
for ref, net, board, schematic in [
    ('C38', 'XIN', (39, 46, 0), (39, 224, 0)),
    ('C39', 'XTAL_OUT', (39, 40, 0), (83, 224, 0)),
]:
    capacitor(ref, '15pF 50V C0G', 'GRM1555C1H150JA01D', net, 'GND', board, 'MCU', schematic)

for ref, net, board, sheet, schematic in [
    ('SW1', 'RUN', (40, 55, 0), 'MCU', (149, 208, 0)),
    ('SW2', 'BOOT_SWITCH', (40, 63, 0), 'Memory', (245, 107, 0)),
    ('SW3', 'ESP_BOOT', (64, 31, 0), 'Wireless', (220, 158, 0)),
    ('SW4', 'ESP_EN', (57, 31, 0), 'Wireless', (265, 158, 0)),
]:
    add(ref, 'Switch', 'SW_Push', 'RESET' if ref in {'SW1', 'SW4'} else 'BOOT',
        'TL3342F160QG', 'E-Switch', {1: net, 2: 'GND'}, board, sheet, schematic,
        'Button_Switch_SMD:SW_SPST_TL3342', 'SMT normally-open tactile switch')
add('SW5', 'Switch', 'SW_SPDT', 'POWER', 'JS102011SAQN', 'C&K',
    {1: 'VSYS', 2: 'PWR_SWITCH', 3: 'GND'}, (8, 63, 270), 'Power', (175, 112, 0),
    'Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN',
    'Logic-level power switch; charger remains active when system is off')

for index, position in enumerate([(4, 4, 0), (4, 71, 0), (76, 71, 0)], 1):
    add(f'H{index}', 'Mechanical', 'MountingHole', 'M2.5 NPTH', '', '', {}, position,
        'Interfaces', (40 + index * 28, 235, 0),
        'MountingHole:MountingHole_2.7mm_M2.5', 'Mechanical hole, no fitted hardware')

for index, (net, position) in enumerate([
    ('GND', (22, 20, 0)), ('VBUS', (22, 23, 0)), ('VBAT', (22, 16, 0)),
    ('VSYS', (22, 26, 0)), ('+3V3', (23, 29, 0)), ('+1V1', (33, 29, 0)),
    ('RUN', (44, 55, 0)), ('ESP_PROG_RX', (74, 17, 0)),
    ('ESP_PROG_TX', (74, 20, 0)), ('BAT_TS', (8, 21, 0))
], 1):
    add(f'TP{index}', 'Connector', 'TestPoint', net, '', '', {1: net}, position,
        'Power' if index < 7 or index == 10 else 'Wireless' if index in {8, 9} else 'MCU',
        (270 if index == 10 else 35 + (index % 6) * 38, 250, 0), 'TestPoint:TestPoint_Pad_D1.0mm',
        'Bare ENIG probe target; no assembled component')

if __name__ == '__main__':
    import json
    print(f'{len(PARTS)} footprints; {len({net for part in PARTS for net in part["nets"].values() if net})} nets')
    (ROOT / 'design.json').write_text(json.dumps(PARTS, indent=2) + '\n')
