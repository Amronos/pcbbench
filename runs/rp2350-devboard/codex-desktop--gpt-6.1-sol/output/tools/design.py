from pathlib import Path
from collections import defaultdict
from copy import deepcopy
import csv
import json
import math
import uuid
import sexpdata as sx
from shapely.geometry import box, LineString, Point
from shapely.ops import polygonize, unary_union
from shapely.affinity import rotate as rotate_shape, translate as translate_shape

ROOT = Path(__file__).resolve().parent.parent
KICAD = Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport')
NAME = 'Aster2350'
S = sx.Symbol
COMPONENTS = []
SYMBOLS = {}
LIB_CACHE = {}
NETS = {}
BOARD_ITEMS = []
BOARD_UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'aster2350.board'))
ROOT_UUID = str(uuid.uuid5(uuid.NAMESPACE_DNS, 'aster2350.root'))
SHEET_UUIDS = {name: str(uuid.uuid5(uuid.NAMESPACE_DNS, 'aster2350.' + name)) for name in ['processor', 'power', 'interfaces']}


def uid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, 'aster2350.' + name))


def node(name, *values):
    return [S(name), *values]


def tags(data, name):
    return [item for item in data if isinstance(item, list) and item and str(item[0]) == name]


def tag(data, name, default=None):
    return next(iter(tags(data, name)), default)


def replace(data, name, value):
    data[:] = [item for item in data if not (isinstance(item, list) and item and str(item[0]) == name)]
    data.append(value)


def emit(data):
    return sx.dumps(data)


def save(path, data):
    Path(path).write_text(emit(data) + '\n')


def effect(size=1.0, hide=False):
    return node('effects', node('font', node('size', size, size), node('thickness', 0.12)), *([node('hide', S('yes'))] if hide else []))


def load_symbol(lib, name):
    if lib not in LIB_CACHE:
        LIB_CACHE[lib] = sx.loads((KICAD / 'symbols' / (lib + '.kicad_sym')).read_text())
    original = deepcopy(next(symbol for symbol in tags(LIB_CACHE[lib], 'symbol') if symbol[1] == name))
    parent = tag(original, 'extends')
    if parent:
        base = load_symbol(lib, parent[1])
        original = [item for item in original if not (isinstance(item, list) and str(item[0]) == 'extends')]
        original.extend(deepcopy(tags(base, 'symbol')))
        for setting in ['pin_names', 'pin_numbers', 'in_bom', 'on_board']:
            if not tag(original, setting) and tag(base, setting):
                original.append(deepcopy(tag(base, setting)))
    for sub in tags(original, 'symbol'):
        sub[1] = name + '_' + sub[1].rsplit('_', 2)[1] + '_' + sub[1].rsplit('_', 2)[2]
    original[1] = name
    return original


def generic_symbol(name, pin_defs):
    body = node('symbol', name + '_1_1', node('rectangle', node('start', -7.62, 10.16), node('end', 7.62, -10.16), node('stroke', node('width', 0.254), node('type', S('default'))), node('fill', node('type', S('background')))))
    left = pin_defs[:(len(pin_defs) + 1) // 2]
    right = pin_defs[(len(pin_defs) + 1) // 2:]
    for side, pins in [(0, left), (180, right)]:
        for index, (number, label, kind) in enumerate(pins):
            body.append(node('pin', S(kind), S('line'), node('at', -10.16 if side == 0 else 10.16, 7.62 - index * 2.54, side), node('length', 2.54), node('name', label, effect(0.9)), node('number', str(number), effect(0.9))))
    return node('symbol', name, node('pin_names', node('offset', 0.508)), node('in_bom', S('yes')), node('on_board', S('yes')), node('property', 'Reference', 'U', node('at', 0, 12.7, 0), effect()), node('property', 'Value', name, node('at', 0, -12.7, 0), effect()), body)


def add(ref, value, symbol, footprint, pins, position, mpn, manufacturer, sheet, description='', orientation=0):
    if ':' in symbol:
        lib, symbol_name = symbol.split(':')
        if symbol_name not in SYMBOLS:
            SYMBOLS[symbol_name] = load_symbol(lib, symbol_name)
    else:
        symbol_name = symbol
    component = dict(ref=ref, value=value, symbol=symbol_name, footprint=footprint, pins={str(key): val for key, val in pins.items()}, x=position[0], y=position[1], rotation=orientation, mpn=mpn, manufacturer=manufacturer, sheet=sheet, description=description, uuid=uid(ref), sch_pos=None)
    COMPONENTS.append(component)
    return component


def resistor(ref, value, first, second, position, sheet='power', orientation=0):
    code = {'0': '0000', '33': '3300', '27': '2700', '330': '3300', '1k': '1001', '2.2k': '2201', '3.3k': '3301', '4.7k': '4701', '5.1k': '5101', '6.8k': '6801', '10k': '1002', '100k': '1003', '49.9k': '4992', '562k': '5623', '536k': '5363', '3.57k': '3571', '3.24k': '3241', '1.00k': '1001'}[value]
    if value == '330':
        code = '3300'
    package = '0402'
    return add(ref, value, 'Device:R_Small', f'Resistor_SMD:R_{package}_1005Metric', {1: first, 2: second}, position, 'RC0402FR-07' + {'0000':'0RL', '3300':('330RL' if value == '330' else '33RL'), '2700':'27RL', '1001':'1KL', '2201':'2K2L', '3301':'3K3L', '4701':'4K7L', '5101':'5K1L', '6801':'6K8L', '1002':'10KL', '1003':'100KL', '4992':'49K9L', '5623':'562KL', '5363':'536KL', '3571':'3K57L', '3241':'3K24L'}[code], 'Yageo', sheet, '1%, 0402, 62.5 mW; zero-ohm link only where specified', orientation)


def capacitor(ref, value, first, second, position, sheet='power', orientation=0):
    options = {
        '100n': ('Capacitor_SMD:C_0402_1005Metric', 'GRM155R71C104KA88D', '100 nF, 16 V, X7R, 10%, 0402'),
        '1u': ('Capacitor_SMD:C_0603_1608Metric', 'GRM188R71C105KA12D', '1 uF, 16 V, X7R, 10%, 0603'),
        '4.7u': ('Capacitor_SMD:C_0603_1608Metric', 'GRM188R61A475KE15D', '4.7 uF, 10 V, X5R, 10%, 0603'),
        '10u': ('Capacitor_SMD:C_0805_2012Metric', 'GRM21BR61C106KE15L', '10 uF, 16 V, X5R, 10%, 0805'),
        '22u': ('Capacitor_SMD:C_0805_2012Metric', 'GRM21BR61A226ME44L', '22 uF, 10 V, X5R, 20%, 0805'),
        '47u': ('Capacitor_SMD:C_1206_3216Metric', 'GRM31CR61A476ME15L', '47 uF, 10 V, X5R, 20%, 1206'),
        '15p': ('Capacitor_SMD:C_0402_1005Metric', 'GRM1555C1H150JA01D', '15 pF, 50 V, C0G, 5%, 0402'),
        '10p': ('Capacitor_SMD:C_0402_1005Metric', 'GRM1555C1H100JA01D', '10 pF, 50 V, C0G, 5%, 0402'),
    }
    footprint, mpn, description = options[value]
    return add(ref, value, 'Device:C_Small', footprint, {1: first, 2: second}, position, mpn, 'Murata', sheet, description, orientation)


def populate():
    SYMBOLS['APS6404L_3SQR'] = generic_symbol('APS6404L_3SQR', [(1, '~{CE}', 'input'), (2, 'SO/SIO1', 'bidirectional'), (3, 'SIO2', 'bidirectional'), (4, 'VSS', 'power_in'), (5, 'SI/SIO0', 'bidirectional'), (6, 'SCLK', 'input'), (7, 'SIO3', 'bidirectional'), (8, 'VDD', 'power_in')])
    SYMBOLS['TLV61046A'] = generic_symbol('TLV61046A', [(6, 'VIN', 'power_in'), (4, 'EN', 'input'), (2, 'GND', 'power_in'), (1, 'SW', 'passive'), (5, 'VOUT', 'power_out'), (3, 'FB', 'input')])
    rp_pins = {1:'+3V3', 2:'PSRAM_CS', 3:'GPIO1', 4:'GPIO2', 5:'GPIO3', 6:'+1V1', 7:'RADIO_RX', 8:'RADIO_TX', 9:'RADIO_RTS', 10:'RADIO_CTS', 11:'+3V3', 12:'GPIO8', 13:'GPIO9', 14:'SD_SCK_SRC', 15:'SD_MOSI', 16:'SD_MISO', 17:'SD_CS', 18:'SD_DETECT', 19:'GPIO15', 20:'+3V3', 21:'XIN', 22:'XOUT', 23:'+1V1', 24:'SWCLK', 25:'SWDIO', 26:'RUN', 27:'RGB_DATA', 28:'RGB_ENABLE', 29:'GPIO18', 30:'+3V3', 31:'GPIO19', 32:'I2C_SDA', 33:'I2C_SCL', 34:'RADIO_POWER', 35:'USB_500MA', 36:'VBUS_DETECT', 37:'CHARGE_N', 38:'+3V3', 39:'+1V1', 40:'GPIO26_ADC0', 41:'GPIO27_ADC1', 42:'GPIO28_ADC2', 43:'BAT_ADC', 44:'+3V3_ADC', 45:'+3V3', 46:'+3V3', 47:'GND', 48:None, 49:'+3V3', 50:'GND', 51:'USB_DM_MCU', 52:'USB_DP_MCU', 53:'+3V3', 54:'+3V3', 55:'QSPI_D3', 56:'QSPI_CLK_SRC', 57:'QSPI_D0', 58:'QSPI_D2', 59:'QSPI_D1', 60:'FLASH_CS', 61:'GND'}
    add('U1', 'RP2350A', 'MCU_RaspberryPi:RP2350A', 'Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm', rp_pins, (130,137), 'RP2350A', 'Raspberry Pi', 'processor', 'QFN60, external 1.1 V core supply; VREG_FB grounded, LX deliberately open')
    memory_pins = {1:'FLASH_CS', 2:'QSPI_D1', 3:'QSPI_D2', 4:'GND', 5:'QSPI_D0', 6:'QSPI_CLK', 7:'QSPI_D3', 8:'+3V3'}
    add('U2', 'W25Q128JVSIQ', 'Memory_Flash:W25Q128JVS', 'Package_SO:SOIC-8_5.3x5.3mm_P1.27mm', memory_pins, (132,125), 'W25Q128JVSIQ', 'Winbond', 'processor', '16 MiB QSPI NOR, 3 V, 208 mil SOIC8')
    add('U3', 'APS6404L-3SQR-SN', 'APS6404L_3SQR', 'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm', {**memory_pins, '1':'PSRAM_CS'}, (120,125), 'APS6404L-3SQR-SN', 'AP Memory', 'processor', '8 MiB 3.3 V QSPI PSRAM, 150 mil SOP8; NOT a 1.8 V variant')
    add('Y1', '12MHz', 'Device:Crystal_GND24_Small', 'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm', {1:'XIN', 2:'GND', 3:'XTAL_OUT', 4:'GND'}, (123,142), 'ABM8-272-T3', 'Abracon', 'processor', '12 MHz, CL=10 pF, ESR<=50 ohm, reference-design crystal')
    resistor('R1', '1k', 'XOUT', 'XTAL_OUT', (126,142), 'processor', 90)
    capacitor('C1','15p','XIN','GND',(121.4,144.3),'processor')
    capacitor('C2','15p','XTAL_OUT','GND',(124.6,144.3),'processor')
    resistor('R2','33','QSPI_CLK_SRC','QSPI_CLK',(129.3,131.8),'processor',90)
    resistor('R3','4.7k','+3V3','FLASH_CS',(135.7,130),'processor')
    resistor('R4','4.7k','+3V3','PSRAM_CS',(116.2,129),'processor')
    resistor('R5','4.7k','+3V3','QSPI_D2',(138.2,127),'processor')
    resistor('R6','4.7k','+3V3','QSPI_D3',(138.2,124.5),'processor')
    capacitor('C3','100n','+3V3','GND',(136.5,122.5),'processor',90)
    capacitor('C4','100n','+3V3','GND',(124.2,122.5),'processor',90)
    capacitor('C5','1u','+3V3','GND',(120,121),'processor',90)
    for index, position in enumerate([(125,133.8),(124.9,136),(129,142),(135,138.4),(135,134.9),(134.2,131.6),(131.1,131.6)], 6):
        capacitor('C'+str(index),'100n','+3V3','GND',position,'processor',90 if index in [8,11,12] else 0)
    capacitor('C13','100n','+1V1','GND',(124.9,137.6),'processor')
    capacitor('C14','4.7u','+1V1','GND',(127,142.7),'processor',90)
    capacitor('C15','100n','+1V1','GND',(135,137.1),'processor')
    capacitor('C16','1u','+3V3','GND',(133,131),'processor',90)
    resistor('R7','33','+3V3','+3V3_ADC',(136,131.1),'processor',90)
    capacitor('C17','100n','+3V3_ADC','GND',(135.3,132.5),'processor')
    add('U4','TLV75801PDRVR','Regulator_Linear:TLV75801PDRV','Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm',{1:'+1V1',2:'CORE_FB',3:'GND',4:'+3V3',5:None,6:'+3V3',7:'GND'},(137,140.8),'TLV75801PDRVR','Texas Instruments','processor','500 mA adjustable LDO, 0.55 V reference, 1.100 V nominal core; WSON thermal pad grounded')
    resistor('R8','10k','+1V1','CORE_FB',(137.5,143),'processor',90)
    resistor('R9','10k','CORE_FB','GND',(139.4,143),'processor')
    capacitor('C18','1u','+3V3','GND',(135,141.3),'processor')
    capacitor('C19','4.7u','+1V1','GND',(139.1,140.8),'processor')
    resistor('R10','10k','+3V3','RUN',(133.8,143.2),'processor')
    capacitor('C20','100n','RUN','GND',(135,145),'processor')
    add('SW1','BOOTSEL','Switch:SW_Push','Button_Switch_SMD:SW_SPST_TL3342',{1:'BOOT_GND',2:'GND'},(129,149),'TL3342F160QG','E-Switch','processor','Hold while applying power or RESET for ROM USB mass-storage boot')
    resistor('R11','1k','FLASH_CS','BOOT_GND',(129,146),'processor',90)
    add('SW2','RESET','Switch:SW_Push','Button_Switch_SMD:SW_SPST_TL3342',{1:'RUN',2:'GND'},(140,149),'TL3342F160QG','E-Switch','processor','RP2350 reset button')
    add('J1','USB-C','Connector:USB_C_Receptacle_USB2.0_16P','Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',{**{pin:'GND' for pin in ['A1','A12','B1','B12','SH']},**{pin:'USB_VBUS' for pin in ['A4','A9','B4','B9']},'A5':'CC1','B5':'CC2','A6':'USB_DP','B6':'USB_DP','A7':'USB_DM','B7':'USB_DM','A8':None,'B8':None},(112,163),'USB4105-GF-A','GCT','power','USB 2.0 device, both plug orientations; plated shell slots')
    resistor('R12','5.1k','CC1','GND',(108.8,157.5))
    resistor('R13','5.1k','CC2','GND',(115.2,157.5))
    add('U5','USBLC6-2SC6','Power_Protection:USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6',{1:'USB_DP',2:'GND',3:'USB_DM',4:'USB_DM',5:'USB_VBUS',6:'USB_DP'},(113,153.4),'USBLC6-2SC6','STMicroelectronics','power','USB low-capacitance ESD array; pin-pairs are the same net')
    resistor('R14','27','USB_DP','USB_DP_MCU',(130.7,130),'processor',90)
    resistor('R15','27','USB_DM','USB_DM_MCU',(131.1,128.3),'processor',90)
    capacitor('C21','100n','USB_VBUS','GND',(115.6,153.6))
    add('F1','500mA PTC','Device:Polyfuse_Small','Fuse:Fuse_1812_4532Metric',{1:'USB_VBUS',2:'VBUS'},(106.3,154.5),'MF-MSMF050-2','Bourns','power','500 mA hold resettable fuse, 15 V max, 1812',orientation=90)
    add('U6','BQ24074RGTR','Battery_Management:BQ24074RGT','Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm',{1:'BAT_NTC',2:'BAT',3:'BAT',4:'GND',5:'GND',6:'USB_500MA',7:'POWER_GOOD_N',8:'GND',9:'CHARGE_N',10:'VSYS',11:'VSYS',12:'CHG_ILIM',13:'VBUS',14:'CHG_TMR',15:'CHG_ITERM',16:'CHG_ISET',17:'GND'},(109,147),'BQ24074RGTR','Texas Instruments','power','4.2 V single-cell LiPo charger; OUT=4.4 V USB power path, 250 mA maximum charging')
    capacitor('C22','1u','VBUS','GND',(109,151))
    capacitor('C23','10u','VSYS','GND',(112.3,147))
    capacitor('C24','4.7u','BAT','GND',(105.5,146))
    resistor('R16','3.57k','CHG_ISET','GND',(109,143.4))
    resistor('R17','3.24k','CHG_ILIM','GND',(112.3,144))
    resistor('R18','49.9k','CHG_TMR','GND',(107.5,143.4))
    resistor('R19','3.3k','CHG_ITERM','GND',(106,143.4))
    resistor('R20','100k','USB_500MA','GND',(113.6,145))
    resistor('R21','3.3k','+3V3','CHARGE_N',(116,146))
    resistor('R22','3.3k','+3V3','POWER_GOOD_N',(116,148))
    add('J2','LiPo + NTC','Connector_Generic:Conn_01x03','Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical',{1:'BAT',2:'BAT_NTC',3:'GND'},(107,138),'B3B-PH-K-S(LF)(SN)','JST','power','Protected 1S 4.2 V LiPo, >=500 mAh, 10 kohm 3435 K pack thermistor; pin 1=BAT+, 2=NTC, 3=GND')
    capacitor('C25','100n','BAT_NTC','GND',(109,141.3))
    add('U7','TPS63060DSCR','Regulator_Switching:TPS63060','Package_SON:Texas_S-PWSON-N10',{1:'BUCK_L1',2:'VSYS',3:'VSYS',4:'GND',5:None,6:'BUCK_VAUX',7:'GND',8:'BUCK_FB',9:'+3V3',10:'BUCK_L2',11:'GND'},(114,132),'TPS63060DSCR','Texas Instruments','power','2.25 A switch buck-boost, 3.310 V nominal output; PS/SYNC low enables power-save')
    add('L1','1.5uH','Device:L_Small','Inductor_SMD:L_Coilcraft_XxL4020',{1:'BUCK_L1',2:'BUCK_L2'},(109,132),'XFL4020-152MEC','Coilcraft','power','1.5 uH, 20%, shielded, Isat=4.4 A, DCR=14.4 milliohm',orientation=90)
    capacitor('C26','10u','VSYS','GND',(113.7,128.8))
    capacitor('C27','10u','VSYS','GND',(111,127.8))
    capacitor('C28','22u','+3V3','GND',(113.7,135.3))
    capacitor('C29','22u','+3V3','GND',(116.3,135.3))
    capacitor('C30','100n','BUCK_VAUX','GND',(116.5,130.5))
    resistor('R23','562k','+3V3','BUCK_FB',(117,132.1))
    resistor('R24','100k','BUCK_FB','GND',(118.8,132.1))
    capacitor('C31','10p','BUCK_FB','GND',(118.8,134))
    add('U8','TLV9001IDCKR','Amplifier_Operational:TLV9001IDCK','Package_TO_SOT_SMD:SOT-353_SC-70-5',{1:'BAT_DIV',2:'GND',3:'BAT_BUFFER',4:'BAT_BUFFER',5:'+3V3'},(146,138),'TLV9001IDCKR','Texas Instruments','power','RRIO voltage follower prevents RP2350 GPIO leakage loading battery divider')
    resistor('R25','100k','BAT','BAT_DIV',(143,136))
    resistor('R26','100k','BAT_DIV','GND',(143,138))
    capacitor('C32','100n','BAT_DIV','GND',(143,140))
    capacitor('C33','100n','+3V3','GND',(147.7,137.3))
    resistor('R27','1k','BAT_BUFFER','BAT_ADC',(145.7,140.5),orientation=90)
    capacitor('C34','100n','BAT_ADC','GND',(145.7,142))
    resistor('R28','5.1k','VBUS','VBUS_DETECT',(118.4,150.1))
    resistor('R29','6.8k','VBUS_DETECT','GND',(118.4,152))
    capacitor('C35','100n','VBUS_DETECT','GND',(120.2,151))
    add('U9','ESP32-C3-WROOM-02-N4','RF_Module:ESP32-C3-WROOM-02','RF_Module:ESP32-C3-WROOM-02',{1:'+3V3_RF',2:'ESP_EN',3:'RADIO_CTS',4:'RADIO_RTS',5:None,6:None,7:'ESP_STRAP8',8:'ESP_BOOT',9:'GND',10:None,11:'RADIO_RX',12:'RADIO_TX',13:None,14:None,15:None,16:'ESP_STRAP2',17:None,18:None,19:'GND'},(165,118.1),'ESP32-C3-WROOM-02-N4','Espressif','interfaces','2.4 GHz Wi-Fi b/g/n + Bluetooth LE 5, 4 MiB flash, PCB antenna; factory firmware must be programmed')
    add('U10','TPS22919DCKR','Power_Management:TPS22919DCK','Package_TO_SOT_SMD:SOT-363_SC-70-6',{1:'+3V3',2:'GND',3:'RADIO_POWER',4:None,5:'+3V3_RF',6:'+3V3_RF'},(149.5,112.5),'TPS22919DCKR','Texas Instruments','interfaces','1.5 A load switch, quick-output-discharge tied to switched rail; off by default')
    resistor('R30','100k','RADIO_POWER','GND',(147,112.5),'interfaces')
    resistor('R31','10k','+3V3_RF','ESP_EN',(154,112),'interfaces')
    capacitor('C36','100n','ESP_EN','GND',(154,113.8),'interfaces')
    capacitor('C37','1u','+3V3','GND',(149.5,115),'interfaces',90)
    capacitor('C38','47u','+3V3_RF','GND',(152,109),'interfaces',90)
    capacitor('C39','100n','+3V3_RF','GND',(154,110),'interfaces')
    resistor('R32','10k','+3V3_RF','ESP_STRAP8',(152.5,119.9),'interfaces')
    resistor('R33','10k','+3V3_RF','ESP_BOOT',(152.5,121.7),'interfaces')
    resistor('R34','10k','+3V3_RF','ESP_STRAP2',(176,114.8),'interfaces')
    add('SW3','ESP BOOT','Switch:SW_Push','Button_Switch_SMD:SW_SPST_TL3342',{1:'ESP_BOOT',2:'GND'},(153,127),'TL3342F160QG','E-Switch','interfaces','Hold low through radio power-on to flash the ESP32-C3 ROM UART bootloader')
    add('J3','microSD','Connector:Micro_SD_Card_Det2','Connector_Card:microSD_HC_Molex_104031-0811',{1:'SD_DAT2',2:'SD_CS',3:'SD_MOSI',4:'+3V3',5:'SD_SCK',6:'GND',7:'SD_MISO',8:'SD_DAT1',9:'SD_DETECT',10:'GND','SH':'GND'},(173,140),'104031-0811','Molex','interfaces','Push-pull microSD socket with card detect; SPI mode, 3.3 V only',orientation=90)
    for reference, net_name, position in [('R35','SD_CS',(163.6,142)),('R36','SD_MISO',(163.6,136)),('R37','SD_MOSI',(163.6,140)),('R38','SD_DAT1',(163.6,134)),('R39','SD_DAT2',(163.6,144))]:
        resistor(reference,'10k','+3V3',net_name,position,'interfaces')
    resistor('R40','3.3k','+3V3','SD_DETECT',(173,148),'interfaces',90)
    resistor('R41','33','SD_SCK_SRC','SD_SCK',(140,135),'interfaces',90)
    capacitor('C40','10u','+3V3','GND',(163.5,138),'interfaces')
    capacitor('C41','100n','+3V3','GND',(166,139.8),'interfaces')
    add('J4','Qwiic / STEMMA QT','Connector_Generic:Conn_01x04','Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical',{1:'GND',2:'+3V3',3:'I2C_SDA',4:'I2C_SCL','MP':'GND'},(170,158),'BM04B-SRSS-TB(LF)(SN)','JST','interfaces','1.0 mm JST SH; GND,3V3,SDA,SCL; 3.3 V peripherals, 100 mA total external budget')
    resistor('R42','2.2k','+3V3','I2C_SDA',(165.5,157),'interfaces')
    resistor('R43','2.2k','+3V3','I2C_SCL',(165.5,159),'interfaces')
    capacitor('C42','100n','+3V3','GND',(166.3,161),'interfaces')
    add('U11','TLV61046ADBVR','TLV61046A','Package_TO_SOT_SMD:SOT-23-6',{1:'RGB_SW',2:'GND',3:'RGB_FB',4:'RGB_ENABLE',5:'+5V_RGB',6:'+3V3'},(148.3,153),'TLV61046ADBVR','Texas Instruments','interfaces','Dedicated switched 5.06 V RGB boost rail; off by default')
    add('L2','10uH','Device:L_Small','Inductor_SMD:L_Coilcraft_LPS3010',{1:'+3V3',2:'RGB_SW'},(144,153),'LPS3010-103MLC','Coilcraft','interfaces','10 uH, 20%, shielded, >1 A saturation current',orientation=90)
    resistor('R44','536k','+5V_RGB','RGB_FB',(148.7,150.7),'interfaces',90)
    resistor('R45','100k','RGB_FB','GND',(150.5,150.7),'interfaces')
    resistor('R46','100k','RGB_ENABLE','GND',(151,154.1),'interfaces')
    capacitor('C43','4.7u','+3V3','GND',(144,150.3),'interfaces',90)
    capacitor('C44','4.7u','+5V_RGB','GND',(148.5,156),'interfaces',90)
    add('U12','SN74AHCT1G125DBVR','74xGxx:74AHCT1G125','Package_TO_SOT_SMD:SOT-23-5',{1:'GND',2:'RGB_DATA',3:'GND',4:'RGB_DOUT_BUF',5:'+5V_RGB'},(155,153),'SN74AHCT1G125DBVR','Texas Instruments','interfaces','5 V buffer, TTL input accepts RP2350 3.3 V; active-low output enable grounded')
    resistor('R47','100k','RGB_DATA','GND',(155,150.5),'interfaces',90)
    resistor('R48','330','RGB_DOUT_BUF','RGB_DIN',(157.2,154.4),'interfaces',90)
    capacitor('C45','100n','+5V_RGB','GND',(153,153.2),'interfaces')
    add('D1','WS2812B-2020','LED:WS2812B-2020','LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm',{1:None,2:'GND',3:'RGB_DIN',4:'+5V_RGB'},(160,153),'WS2812B-2020','Worldsemi','interfaces','Addressable RGB LED, 800 kbit/s, 5 V supply, GRB; observe pin-1 orientation')
    capacitor('C46','100n','+5V_RGB','GND',(161.8,153),'interfaces')
    add('J5','SWD','Connector_Generic:Conn_01x03','Connector_JST:JST_SH_BM03B-SRSS-TB_1x03-1MP_P1.00mm_Vertical',{1:'SWCLK',2:'GND',3:'SWDIO','MP':'GND'},(152,144),'BM03B-SRSS-TB(LF)(SN)','JST','interfaces','Raspberry Pi Debug Probe pinout: SWCLK,GND,SWDIO; target is self-powered')
    left_pins = {1:'+3V3',2:'GND',3:'GPIO1',4:'GPIO2',5:'GPIO3',6:'GPIO8',7:'GPIO9',8:'GPIO15'}
    right_pins = {1:'GND',2:'GPIO18',3:'GPIO19',4:'GPIO26_ADC0',5:'GPIO27_ADC1',6:'GPIO28_ADC2',7:'RUN',8:'+3V3'}
    add('J6','GPIO A','Connector_Generic:Conn_01x08','Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical',left_pins,(102.8,117),'61300811121','Wurth Elektronik','interfaces','Factory installed 1x8 2.54 mm male header; 3.3 V logic only')
    add('J7','GPIO B','Connector_Generic:Conn_01x08','Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical',right_pins,(133,159),'61300811121','Wurth Elektronik','interfaces','Factory installed 1x8 2.54 mm male header; ADC0/1/2 available',orientation=90)
    for index,(net_name,position) in enumerate([('GND',(120,156)),('VSYS',(116,141)),('+3V3',(122,148)),('+1V1',(137,146)),('BAT',(105,142)),('BAT_ADC',(148,141)),('RADIO_RX',(176,126)),('RADIO_TX',(176,128)),('ESP_EN',(149,119)),('POWER_GOOD_N',(119,146)),('USB_500MA',(121,152)),('RUN',(143,147)),('RGB_ENABLE',(153,157))],1):
        add('TP'+str(index),net_name,'Connector:TestPoint','TestPoint:TestPoint_Pad_D1.0mm',{1:net_name},position,'','', 'interfaces','Bare test pad; not a purchased or assembled component')
    for index,(position,net_name) in enumerate([((104.8,152),'USB_VBUS'),((104,148),'VBUS'),((141,132),'+3V3_ADC'),((120,159),'GND')],1):
        component = add('#FLG'+str(index),'PWR_FLAG','power:PWR_FLAG','',{1:net_name},position,'','','power','ERC supply declaration')
        component['virtual'] = True
    for reference, ground_pin in [('J4', '1'), ('J5', '2')]:
        connector = next(component for component in COMPONENTS if component['ref'] == reference)
        original_name = connector['symbol']
        local_name = original_name + ('_QT' if reference == 'J4' else '_SWD')
        symbol = deepcopy(SYMBOLS[original_name])
        symbol[1] = local_name
        for unit in tags(symbol, 'symbol'):
            unit[1] = local_name + '_' + unit[1].rsplit('_', 2)[1] + '_' + unit[1].rsplit('_', 2)[2]
        SYMBOLS[local_name] = symbol
        connector['symbol'] = local_name
        for unit in tags(symbol, 'symbol'):
            ground = next((pin for pin in tags(unit, 'pin') if tag(pin, 'number')[1] == ground_pin), None)
            if ground is not None:
                mounting_pin = deepcopy(ground)
                replace(mounting_pin, 'number', node('number', 'MP', effect(1.27)))
                replace(mounting_pin, 'name', node('name', 'Shield', effect(1.27)))
                mounting_pin.append(node('hide', S('yes')))
                unit.append(mounting_pin)
                connector['pins']['MP'] = 'GND'


def pins_of(component):
    pins = {}
    for sub in tags(SYMBOLS[component['symbol']], 'symbol'):
        for pin in tags(sub, 'pin'):
            pins[tag(pin,'number')[1]] = pin
    return pins


def render_component(component, position, sheet_path):
    xcoord, ycoord = [round(round((value*scale+offset) / 1.27) * 1.27, 4) for value,scale,offset in zip(position,[0.6,0.48],[5,10])]
    if component['ref'] == 'D1':
        xcoord, ycoord = 355.6, 110.49
    if component['ref'] == 'U1':
        xcoord, ycoord = 58.42, 83.82
    component['sch_pos'] = (xcoord, ycoord)
    placed = node('symbol', node('lib_id','Aster:'+component['symbol']), node('at', xcoord, ycoord, 0), node('unit',1), node('in_bom', S('no') if component.get('virtual') or component['ref'].startswith('TP') else S('yes')), node('on_board', S('no') if component.get('virtual') else S('yes')), node('dnp',S('no')), node('uuid',component['uuid']))
    library_pins = pins_of(component)
    highest = max([tag(pin,'at')[2] for pin in library_pins.values()] or [5])
    properties = [('Reference', component['ref']), ('Value', component['value']), ('Footprint', component.get('fp_id','')), ('Datasheet', ''), ('Manufacturer',component['manufacturer']), ('MPN',component['mpn']),('Description',component['description'])]
    for index,(label,value) in enumerate(properties):
        property_x, property_y = xcoord, ycoord-highest-4-index*1.8
        if index < 2 and component['ref'].startswith(('R','C','L')):
            property_x, property_y = xcoord+5.08, ycoord-1.27+index*2.54
        placed.append(node('property',label,value,node('at',property_x,property_y,0),effect(1.1,index>=2)))
    placed.append(node('instances', node('project', NAME, node('path', sheet_path, node('reference',component['ref']),node('unit',1)))))
    graphics=[placed]
    processed=set()
    for number,pin in library_pins.items():
        placed.append(node('pin',number,node('uuid',uid(component['ref']+'.pin.'+number))))
        at=tag(pin,'at'); xpin=round(xcoord+at[1],4); ypin=round(ycoord-at[2],4); angle=at[3]
        net_name=component['pins'].get(number)
        if net_name is None:
            graphics.append(node('no_connect',node('at',xpin,ypin),node('uuid',uid(component['ref']+'.nc.'+number))))
            continue
        if (xpin,ypin,net_name) in processed:
            continue
        processed.add((xpin,ypin,net_name))
        distance=3.81
        xend=round(xpin-distance*math.cos(math.radians(angle)),4)
        yend=round(ypin+distance*math.sin(math.radians(angle)),4)
        graphics.append(node('wire',node('pts',node('xy',xpin,ypin),node('xy',xend,yend)),node('stroke',node('width',0),node('type',S('default'))),node('uuid',uid(component['ref']+'.wire.'+number))))
        graphics.append(node('global_label',net_name,node('shape',S('bidirectional')),node('at',xend,yend,angle),effect(1.0),node('uuid',uid(component['ref']+'.label.'+number)),node('property','Intersheetrefs','${INTERSHEET_REFS}',node('at',xend,yend,angle),effect(1.0,True))))
    return graphics


def generate_schematic():
    titles = {'processor':'Processor, QSPI memories and external core supply', 'power':'USB-C, LiPo power path and voltage monitoring', 'interfaces':'Wi-Fi / BLE, microSD, I2C, RGB and development connectors'}
    for sheet in SHEET_UUIDS:
        components=[component for component in COMPONENTS if component['sheet']==sheet]
        sheet_path='/'+ROOT_UUID+'/'+SHEET_UUIDS[sheet]
        data=node('kicad_sch',node('version',20250114),node('generator',S('eeschema')),node('uuid',uid('file.'+sheet)),node('paper','A3'),node('title_block',node('title',NAME+' - '+titles[sheet]),node('date','2026-11-09'),node('rev','A'),node('company','Autonomous engineering prototype')))
        lib=node('lib_symbols')
        for symbol_name in sorted({component['symbol'] for component in components}):
            symbol=deepcopy(SYMBOLS[symbol_name]);symbol[1]='Aster:'+symbol_name;lib.append(symbol)
        data.append(lib)
        major=[component for component in components if component['ref'].startswith(('U','J')) and not component['ref'].startswith('TP')]
        minor=[component for component in components if component not in major]
        if sheet=='processor':
            main=next(component for component in major if component['ref']=='U1')
            main['sch_pos']=(90,110);data.extend(render_component(main,main['sch_pos'],sheet_path));major.remove(main)
            for index,component in enumerate(major):
                component['sch_pos']=(220+index%2*130,60+index//2*90);data.extend(render_component(component,component['sch_pos'],sheet_path))
            for index,component in enumerate(minor):
                component['sch_pos']=(55+index%8*64,300+index//8*33);data.extend(render_component(component,component['sch_pos'],sheet_path))
        else:
            for index,component in enumerate(major):
                component['sch_pos']=(65+index%4*130,60+index//4*90);data.extend(render_component(component,component['sch_pos'],sheet_path))
            for index,component in enumerate(minor):
                component['sch_pos']=(45+index%9*60,300+index//9*29);data.extend(render_component(component,component['sch_pos'],sheet_path))
        notes={'processor':'EXTERNAL DVDD: 1.1 V from U4. VREG_VIN and VREG_AVDD remain powered; VREG_FB=GND; LX=NC.\nFirmware must set VREG.HIZ. PSRAM uses QMI CS1n on GPIO0. BOOTSEL only shorts flash CS through 1k.', 'power':'USB device only: CC1/CC2=5.1k to GND. EN2=0; EN1=GPIO23, default 100mA, 500mA after USB configuration.\nBattery J2: 1=BAT+, 2=10k NTC, 3=GND. External protected 1S pack >=500mAh. No NTC means no charging.\nBQ24074: ICHG=890/3570=249mA; ITERM=0.030*3300/3570=27.7mA in USB500 mode; timer nominally 6.65h.', 'interfaces':'GPIO4/5 = UART1 TX/RX; GPIO6/7 = UART1 CTS/RTS. ESP IO4=CTS and IO5=RTS require custom firmware pin configuration.\nRadio power GPIO22 and RGB enable GPIO17 default OFF. Before radio power-off, set all four UART pins high impedance.\nI2C0 GPIO20/21. microSD SPI1 GPIO10/11/12/13 + detect GPIO14. All headers and connectors are installed by PCBWay.'}
        note_effect = effect(1.1)
        note_effect.append(node('justify',S('left'),S('top')))
        data.append(node('text',notes[sheet],node('at',14,257,0),note_effect,node('uuid',uid('notes.'+sheet))))
        save(ROOT/(sheet+'.kicad_sch'),data)
    root=node('kicad_sch',node('version',20250114),node('generator',S('eeschema')),node('uuid',ROOT_UUID),node('paper','A4'),node('title_block',node('title',NAME+' development board'),node('date','2026-11-09'),node('rev','A'),node('company','RP2350A / 16 MiB flash / 8 MiB PSRAM')))
    root.append(node('lib_symbols'))
    for index,sheet in enumerate(SHEET_UUIDS):
        xcoord=25+index*85;ycoord=70
        root.append(node('sheet',node('at',xcoord,ycoord),node('size',70,35),node('stroke',node('width',0.254),node('type',S('default'))),node('fill',node('color',0,0,0,0)),node('uuid',SHEET_UUIDS[sheet]),node('property','Sheetname',sheet.title(),node('at',xcoord,ycoord-2,0),effect(1.27)),node('property','Sheetfile',sheet+'.kicad_sch',node('at',xcoord,ycoord+37,0),effect(1.27)),node('instances',node('project',NAME,node('path','/'+ROOT_UUID,node('page',str(index+2)))))))
    root.append(node('text','ASTER2350  |  REV A\n80 x 65 mm, 4-layer development board\nUSB-C device + LiPo power path + Wi-Fi and Bluetooth LE\nAll parts populated; top-side SMT plus factory-soldered THT headers and battery connector.\n\nNet labels are global across the three subsystem sheets.\nRead README.md and fab/ASSEMBLY.md before ordering.\nPrototype: no physical hardware validation or regulatory certification performed.',node('at',25,125,0),effect(1.8),node('uuid',uid('root.notes'))))
    root.append(node('sheet_instances',node('path','/',node('page','1'))))
    for text in tags(root, 'text'):
        tag(text, 'effects').append(node('justify',S('left'),S('top')))
    save(ROOT/(NAME+'.kicad_sch'),root)
    library=node('kicad_symbol_lib',node('version',20250114),node('generator',S('kicad_symbol_editor')))
    library.extend(deepcopy(list(SYMBOLS.values())))
    save(ROOT/'libraries/Aster.kicad_sym',library)
    (ROOT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Aster") (type "KiCad") (uri "${KIPRJMOD}/libraries/Aster.kicad_sym") (options "") (descr "Vendored KiCad symbols and verified custom ICs")))\n')


def generate_footprints():
    folder=ROOT/'libraries/Aster.pretty';folder.mkdir(exist_ok=True)
    for component in COMPONENTS:
        if not component['footprint']:
            continue
        lib,name=component['footprint'].split(':');fname=lib+'__'+name
        component['fp_id']='Aster:'+fname
        destination=folder/(fname+'.kicad_mod')
        if destination.exists():
            continue
        footprint=sx.loads((KICAD/'footprints'/(lib+'.pretty')/(name+'.kicad_mod')).read_text())
        footprint[1]=fname
        footprint[:]=[item for item in footprint if not (isinstance(item,list) and str(item[0])=='model')]
        if name=='ESP32-C3-WROOM-02':
            footprint[:]=[item for item in footprint if not (isinstance(item,list) and str(item[0])=='pad' and item[1]=='19' and str(item[2])=='thru_hole')]
        if name=='Texas_S-PWSON-N10':
            footprint[:]=[item for item in footprint if not (isinstance(item,list) and str(item[0])=='pad' and item[1]=='11')]
            footprint.append(node('pad','11',S('smd'),S('rect'),node('at',0,0),node('size',1.7,2.15),node('layers','F.Cu','F.Mask')))
            for xcoord in [-0.45,0.45]:
                for ycoord in [-0.7,0,0.7]:
                    footprint.append(node('pad','',S('smd'),S('rect'),node('at',xcoord,ycoord),node('size',0.65,0.55),node('layers','F.Paste')))
        save(destination,footprint)
    (ROOT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Aster") (type "KiCad") (uri "${KIPRJMOD}/libraries/Aster.pretty") (options "") (descr "Project-local footprints; no external libraries needed")))\n')


def legalize_placement():
    overrides={'J1':(112,162.6,0),'U5':(113,153.8,270),'R14':(130.4,131.8,270),'R15':(131.6,131.8,270),'J2':(109,139,0),'U7':(112.8,132,0),'L1':(112.8,127.5,0),'C26':(108.9,131.5,180),'C27':(108.9,129.2,180),'C28':(117.2,131.5,0),'C29':(117.2,135.2,0),'C30':(115.5,134,0),'C18':(140.5,140.15,0),'C19':(134.9,140.15,180),'C38':(153.1,116.3,0),'C39':(154.2,114.8,0),'SW3':(151.5,127.8,0)}
    footprints={}
    for component in COMPONENTS:
        if component['ref'] in overrides:
            component['x'],component['y'],component['rotation']=overrides[component['ref']]
        if component.get('fp_id'):
            footprints[component['ref']]=sx.loads((ROOT/'libraries/Aster.pretty'/(component['fp_id'].split(':')[1]+'.kicad_mod')).read_text())
    fixed_order=['J1','U5','R14','R15','U9','J3','J6','J7','J2','J4','J5','U1','U2','U3','U4','U6','U7','L1','U8','U10','U11','U12','L2','SW1','SW2','SW3','Y1','F1','D1']
    ordered=sorted([component for component in COMPONENTS if component.get('fp_id')],key=lambda component:(fixed_order.index(component['ref']) if component['ref'] in fixed_order else 100+(int(component['ref'][1:]) if component['ref'].startswith('C') else 100 if component['ref'].startswith('R') else 200)))
    occupied=[box(xcoord-2.7,ycoord-2.7,xcoord+2.7,ycoord+2.7) for xcoord,ycoord in [(104,104),(144,104),(104,161),(176,161)]]
    occupied.extend([box(xcoord-1.15,ycoord-1.15,xcoord+1.15,ycoord+1.15) for xcoord,ycoord in [(103,108),(124,160),(177,151)]])
    antenna=box(151,100,179,111)
    usb_corridor=LineString([(113.15,151.5),(115.65,149),(120.2,149),(120.2,130),(130.8,130),(130.8,130.9)]).buffer(0.5,join_style=2)
    for component in ordered:
        footprint=footprints[component['ref']]
        points=[]
        courtyard_lines=[]
        courtyard_shapes=[]
        rotation=math.radians(component['rotation'])
        for graphic in footprint:
            if not isinstance(graphic,list) or str(graphic[0]) not in ['fp_line','fp_rect','fp_circle','fp_poly'] or tag(graphic,'layer',[None,''])[1]!='F.CrtYd':
                continue
            for point_name in ['start','end','center']:
                point=tag(graphic,point_name)
                if point:
                    points.append(point[1:3])
            if str(graphic[0])=='fp_line':
                courtyard_lines.append(LineString([tag(graphic,'start')[1:3],tag(graphic,'end')[1:3]]))
            elif str(graphic[0])=='fp_rect':
                first=tag(graphic,'start')[1:3];second=tag(graphic,'end')[1:3]
                courtyard_shapes.append(box(min(first[0],second[0]),min(first[1],second[1]),max(first[0],second[0]),max(first[1],second[1])))
            elif str(graphic[0])=='fp_circle':
                centre=tag(graphic,'center')[1:3];endpoint=tag(graphic,'end')[1:3]
                courtyard_shapes.append(Point(*centre).buffer(math.dist(centre,endpoint)))
            polygon=tag(graphic,'pts')
            if polygon:
                points.extend(point[1:3] for point in polygon[1:])
        if not points:
            points=[[-0.7,-0.7],[0.7,0.7]]
        rotated=[(point[0]*math.cos(rotation)+point[1]*math.sin(rotation),-point[0]*math.sin(rotation)+point[1]*math.cos(rotation)) for point in points]
        xlow=min(point[0] for point in rotated);xhigh=max(point[0] for point in rotated);ylow=min(point[1] for point in rotated);yhigh=max(point[1] for point in rotated)
        courtyard_shapes.extend(list(polygonize(courtyard_lines)))
        local_shape=rotate_shape(unary_union(courtyard_shapes),-component['rotation'],origin=(0,0)) if courtyard_shapes else box(xlow,ylow,xhigh,yhigh)
        desired=(component['x'],component['y'])
        candidates=[(0,0)]
        for index in range(1,56):
            radius=index*0.2
            candidates.extend((radius*math.cos(index2*math.pi/12),radius*math.sin(index2*math.pi/12)) for index2 in range(24))
        chosen=None
        for dx,dy in candidates:
            xcoord=round(desired[0]+dx,3);ycoord=round(desired[1]+dy,3)
            shape=translate_shape(local_shape,xcoord,ycoord).buffer(0.06)
            if component['ref'] not in ['J1','U9','J3'] and (shape.bounds[0]<100.6 or shape.bounds[1]<100.6 or shape.bounds[2]>179.4 or shape.bounds[3]>164.4):
                continue
            if component['ref']!='U9' and shape.intersects(antenna):
                continue
            if component['ref'] not in ['J1','U5','R14','R15'] and shape.intersects(usb_corridor):
                continue
            if any(shape.intersects(other) for other in occupied):
                continue
            chosen=(xcoord,ycoord,shape);break
        if chosen is None:
            raise ValueError('No legal placement for '+component['ref'])
        component['x'],component['y']=chosen[:2];occupied.append(chosen[2])
        if abs(chosen[0]-desired[0])+abs(chosen[1]-desired[1])>0.01:
            print(f'Placed {component["ref"]} at {chosen[:2]} (desired {desired})')


def physical_pads(component):
    for index,pad in enumerate(tags(component['pcb_fp'],'pad')):
        layer=tag(pad,'layers')
        if not any('Cu' in str(value) for value in layer[1:]):
            continue
        xcoord,ycoord=tag(pad,'at')[1:3]
        rotation=math.radians(component['rotation'])
        yield dict(id=str(index),number=pad[1],net=component['pins'].get(pad[1]),x=component['x']+xcoord*math.cos(rotation)+ycoord*math.sin(rotation),y=component['y']-xcoord*math.sin(rotation)+ycoord*math.cos(rotation),pad=pad)


def pad_position(reference,number):
    component=next(component for component in COMPONENTS if component['ref']==reference)
    entries=[entry for entry in physical_pads(component) if entry['number']==str(number)]
    entry=max(entries,key=lambda entry:tag(entry['pad'],'size')[1]*tag(entry['pad'],'size')[2])
    return (round(entry['x'],6),round(entry['y'],6))


def track_path(net_name,points,width=0.15,layer='F.Cu'):
    for index,(start,end) in enumerate(zip(points,points[1:])):
        if math.dist(start,end)<0.000001:
            continue
        BOARD_ITEMS.append(node('segment',node('start',*start),node('end',*end),node('width',width),node('layer',layer),node('net',NETS[net_name]),node('uuid',uid('route.'+net_name+str(start)+str(end)+layer))))


def via_at(net_name,position):
    BOARD_ITEMS.append(node('via',node('at',*position),node('size',0.6),node('drill',0.3),node('layers','F.Cu','B.Cu'),node('net',NETS[net_name]),node('uuid',uid('via.'+net_name+str(position)))))


def critical_routing():
    dp_conn=pad_position('J1','B6');dm_conn=pad_position('J1','A7')
    dp_esd_in=pad_position('U5','6');dp_esd_out=pad_position('U5','1')
    dm_esd_in=pad_position('U5','4');dm_esd_out=pad_position('U5','3')
    track_path('USB_DP',[dp_conn,(dp_conn[0],157.0),(dp_esd_in[0],156.0),dp_esd_in,dp_esd_out])
    track_path('USB_DM',[dm_conn,(dm_conn[0],156.7),(dm_esd_in[0],156.3),dm_esd_in,dm_esd_out])
    other_dm=pad_position('J1','B7');other_dp=pad_position('J1','A6')
    track_path('USB_DM',[other_dm,(other_dm[0],159.75),(dm_conn[0],159.75),dm_conn])
    first_via=(other_dp[0],157.3);second_via=(dp_conn[0],157.3)
    track_path('USB_DP',[other_dp,first_via]);via_at('USB_DP',first_via);via_at('USB_DP',second_via)
    track_path('USB_DP',[first_via,second_via],layer='B.Cu')
    dp_res=pad_position('R14','1');dm_res=pad_position('R15','1');midpoint=(dp_res[0]+dm_res[0])/2
    centre=LineString([(113.15,151.5),(115.65,149),(120.2,149),(120.2,130),(midpoint,130),(midpoint,130.8)])
    for net_name,side,esd,resistor in [('USB_DP','left',dp_esd_out,dp_res),('USB_DM','right',dm_esd_out,dm_res)]:
        path=[tuple(round(value,6) for value in point) for point in centre.parallel_offset(0.15,side,join_style=2).coords]
        if math.dist(path[0],esd)>math.dist(path[-1],esd):
            path.reverse()
        track_path(net_name,[esd,(esd[0],151.4),*path,resistor])
    track_path('USB_DP_MCU',[pad_position('U1','52'),pad_position('R14','2')])
    track_path('USB_DM_MCU',[pad_position('U1','51'),(130.8,132.85),(131.34,132.31),pad_position('R15','2')])
    first=pad_position('U7','1');coil=pad_position('L1','1')
    track_path('BUCK_L1',[first,(110.7,131)],0.2)
    track_path('BUCK_L1',[(110.7,131),(110.7,129.4),(coil[0],129.4-(coil[0]-110.7)),coil],0.4)
    first=pad_position('U7','10');coil=pad_position('L1','2')
    track_path('BUCK_L2',[first,(115,131)],0.2)
    track_path('BUCK_L2',[(115,131),(115,129.4),(coil[0],129.4-(115-coil[0])),coil],0.4)
    cap=pad_position('C26','1');cap2=pad_position('C27','1')
    track_path('VSYS',[pad_position('U7','2'),(110,131.5)],0.2)
    track_path('VSYS',[(110,131.5),cap],0.5)
    track_path('VSYS',[cap,(cap2[0],cap[1]-(cap[0]-cap2[0])),cap2],0.5)
    track_path('VSYS',[pad_position('U7','3'),(110.4,132),(109.5,133.05)],0.15)
    track_path('VSYS',[cap,(cap[0],132.7),(109.5,133.05)],0.5)
    via_at('VSYS',(109.5,133.05))
    out=pad_position('U7','9');cap=pad_position('C28','1')
    track_path('+3V3',[out,(115.4,131.5)],0.2)
    track_path('+3V3',[(115.4,131.5),cap],0.5)
    cap=pad_position('C23','1')
    track_path('VSYS',[pad_position('U6','10'),(111.15,147.25),(111.35,147.25)],0.15)
    track_path('VSYS',[pad_position('U6','11'),(111.15,146.75),(111.15,147.25)],0.15)
    track_path('VSYS',[(111.35,147.25),cap],0.5)
    track_path('VSYS',[(111.35,147.25),(111.7,147.6),(111.7,148.9),(111.4,149.2)],0.5)
    via_at('VSYS',(111.4,149.2))


def copper_zone(net_name,layer,points,priority=0):
    return node('zone',node('net',NETS[net_name]),node('net_name',net_name),node('layer',layer),node('uuid',uid('plane.'+net_name+layer)),node('hatch',S('edge'),0.5),node('priority',priority),node('connect_pads',node('clearance',0.15)),node('min_thickness',0.15),node('fill',S('yes'),node('thermal_gap',0.2),node('thermal_bridge_width',0.2),node('island_removal_mode',0)),node('polygon',node('pts',*[node('xy',*point) for point in points])))


def regenerate_uuids(data, prefix):
    for index,item in enumerate(data):
        if isinstance(item,list):
            if str(item[0])=='uuid':
                item[1]=uid(prefix+'.'+str(index))
            else:
                regenerate_uuids(item,prefix+'.'+str(index))


def board_text(value, position, layer='F.SilkS', size=0.8, angle=0):
    text_effects=effect(size)
    if layer.startswith('B.'):
        text_effects.append(node('justify',S('mirror')))
    return node('gr_text',value,node('at',*position,angle),node('layer',layer),node('uuid',uid('text.'+value+str(position))),text_effects)


def generate_board():
    all_nets=sorted({net_name for component in COMPONENTS for net_name in component['pins'].values() if net_name is not None})
    NETS.update({name:index+1 for index,name in enumerate(all_nets)})
    board=node('kicad_pcb',node('version',20241229),node('generator',S('pcbnew')),node('general',node('thickness',1.6)),node('paper','A4'),node('title_block',node('title',NAME),node('date','2026-11-09'),node('rev','A')))
    board.append(node('layers',*[node(str(number),name,S(kind)) for number,name,kind in [(0,'F.Cu','signal'),(1,'In1.Cu','power'),(2,'In2.Cu','signal'),(31,'B.Cu','signal'),(32,'B.Adhes','user'),(33,'F.Adhes','user'),(34,'B.Paste','user'),(35,'F.Paste','user'),(36,'B.SilkS','user'),(37,'F.SilkS','user'),(38,'B.Mask','user'),(39,'F.Mask','user'),(40,'Dwgs.User','user'),(41,'Cmts.User','user'),(44,'Edge.Cuts','user'),(46,'B.CrtYd','user'),(47,'F.CrtYd','user'),(48,'B.Fab','user'),(49,'F.Fab','user')]]))
    for row in board[-1][1:]:
        row[0]=int(str(row[0]))
    setup=node('setup',node('pad_to_mask_clearance',0.03),node('solder_mask_min_width',0.08),node('aux_axis_origin',100,165),node('grid_origin',100,165))
    stack=node('stackup',node('layer','F.SilkS',node('type','Top Silk Screen')),node('layer','F.Paste',node('type','Top Solder Paste')),node('layer','F.Mask',node('type','Top Solder Mask'),node('thickness',0.01)))
    for name,kind,thickness in [('F.Cu','copper',0.035),('dielectric 1','prepreg',0.1),('In1.Cu','copper',0.035),('dielectric 2','core',1.24),('In2.Cu','copper',0.035),('dielectric 3','prepreg',0.1),('B.Cu','copper',0.035)]:
        layer=node('layer',name,node('type',kind),node('thickness',thickness))
        if kind!='copper':
            layer.extend([node('material','FR4'),node('epsilon_r',4.2),node('loss_tangent',0.02)])
        stack.append(layer)
    stack.extend([node('layer','B.Mask',node('type','Bottom Solder Mask'),node('thickness',0.01)),node('layer','B.Paste',node('type','Bottom Solder Paste')),node('layer','B.SilkS',node('type','Bottom Silk Screen')),node('copper_finish','ENIG'),node('dielectric_constraints',S('yes'))])
    setup.append(stack);board.append(setup)
    board.extend(node('net',index,name) for name,index in NETS.items())
    for component in COMPONENTS:
        if not component.get('fp_id'):
            continue
        footprint=deepcopy(sx.loads((ROOT/'libraries/Aster.pretty'/(component['fp_id'].split(':')[1]+'.kicad_mod')).read_text()))
        footprint[1]=component['fp_id']
        footprint[:]=[item for item in footprint if not (isinstance(item,list) and str(item[0]) in ['version','generator'])]
        replace(footprint,'at',node('at',component['x'],component['y'],component['rotation']))
        replace(footprint,'uuid',node('uuid',uid('footprint.'+component['ref'])))
        footprint.append(node('path','/'+ROOT_UUID+'/'+SHEET_UUIDS[component['sheet']]+'/'+component['uuid']))
        footprint.append(node('sheetname',component['sheet'].title()))
        footprint.append(node('sheetfile',component['sheet']+'.kicad_sch'))
        for prop in tags(footprint,'property'):
            if prop[1]=='Reference':
                prop[2]=component['ref'];replace(prop,'effects',effect(0.7));replace(prop,'layer',node('layer','F.Fab'))
            elif prop[1]=='Value':
                prop[2]=component['value'];replace(prop,'effects',effect(0.7));replace(prop,'layer',node('layer','F.Fab'))
        for label,value in [('MPN',component['mpn']),('Manufacturer',component['manufacturer'])]:
            footprint.append(node('property',label,value,node('at',0,0,0),node('layer','F.Fab'),effect(0.7,True)))
        for pad in tags(footprint,'pad'):
            net_name=component['pins'].get(pad[1])
            if net_name:
                pad.append(node('net',NETS[net_name],net_name))
            if pad[1] in pins_of(component):
                pin=pins_of(component)[pad[1]]
                pad.append(node('pinfunction',tag(pin,'name')[1]))
                pad.append(node('pintype',str(pin[1])))
        regenerate_uuids(footprint,component['ref'])
        component['pcb_fp']=footprint
        board.append(footprint)
    for start,end in [((100,100),(180,100)),((180,100),(180,165)),((180,165),(100,165)),((100,165),(100,100))]:
        board.append(node('gr_line',node('start',*start),node('end',*end),node('stroke',node('width',0.05),node('type',S('default'))),node('layer','Edge.Cuts'),node('uuid',uid('outline.'+str(start)))))
    for index,(xcoord,ycoord) in enumerate([(104,104),(144,104),(104,161),(176,161)],1):
        footprint=node('footprint','Aster:MountingHole',node('layer','F.Cu'),node('at',xcoord,ycoord),node('uuid',uid('mount.'+str(index))),node('attr',S('board_only'),S('exclude_from_pos_files'),S('exclude_from_bom')),node('pad','',S('np_thru_hole'),S('circle'),node('at',0,0),node('size',2.7,2.7),node('drill',2.7),node('layers','*.Cu','*.Mask')))
        board.append(footprint)
    for index,(xcoord,ycoord) in enumerate([(103,108),(124,160),(177,151)],1):
        footprint=node('footprint','Aster:Fiducial',node('layer','F.Cu'),node('at',xcoord,ycoord),node('uuid',uid('fid.'+str(index))),node('attr',S('board_only'),S('exclude_from_pos_files'),S('exclude_from_bom')),node('pad','',S('smd'),S('circle'),node('at',0,0),node('size',1,1),node('layers','F.Cu','F.Mask'),node('solder_mask_margin',0.5)))
        board.append(footprint)
    board.extend([board_text('ASTER2350  REV A',(130,110),size=1.3),board_text('USB',(112,164),size=0.9),board_text('LiPo 1S + NTC',(110,139.7),size=0.8),board_text('+ N -',(109,140.7),size=0.9),board_text('BOOT',(129,152),size=0.7),board_text('RESET',(139,152),size=0.7),board_text('ESP BOOT',(153,130),size=0.7),board_text('QWIIC / QT',(170,155.3),size=0.7),board_text('3V3 ONLY',(169,162.3),size=0.7),board_text('SWD',(152,146.7),size=0.7),board_text('microSD SPI',(170,150.2),size=0.7),board_text('ANTENNA - NO METAL',(165,101.3),size=0.8),board_text('ASTER2350 | 4L | REV A',(140,115),'B.SilkS',1.4),board_text('1S 4.2V LiPo + 10k NTC ONLY\nGPIO: 3.3V logic; not 5V tolerant\nUSB-C DEVICE / 500mA after enumeration',(137,121),'B.SilkS',1.0)])
    critical_routing()
    board.extend(BOARD_ITEMS)
    perimeter=[(100.35,100.35),(150.7,100.35),(150.7,111.4),(179.65,111.4),(179.65,164.65),(100.35,164.65)]
    board.append(copper_zone('GND','In1.Cu',perimeter))
    board.append(copper_zone('+3V3','In2.Cu',perimeter))
    board.append(copper_zone('GND','F.Cu',perimeter))
    board.append(copper_zone('VSYS','B.Cu',[(104.5,126.8),(118.6,126.8),(118.6,154.2),(104.5,154.2)],1))
    save(ROOT/(NAME+'.kicad_pcb'),board)
    config={'board': {'design_settings': {'rules': {'min_clearance':0.1,'min_track_width':0.1,'min_via_diameter':0.6,'min_through_hole_diameter':0.3,'min_via_annular_width':0.15,'min_hole_clearance':0.15,'min_copper_edge_clearance':0.3,'min_silk_clearance':0.1,'min_text_height':0.6,'min_text_thickness':0.1,'solder_mask_to_copper_clearance':0.0},'rule_severities':{'silk_overlap':'warning','silk_over_copper':'warning','lib_footprint_mismatch':'ignore','lib_footprint_issues':'ignore'}},'layer_presets':[]},'net_settings':{'classes':[{'name':'Default','clearance':0.1,'track_width':0.15,'via_diameter':0.6,'via_drill':0.3,'diff_pair_width':0.17,'diff_pair_gap':0.15,'diff_pair_via_gap':0.25}]},'meta':{'filename':NAME+'.kicad_pro','version':1},'text_variables':{'REVISION':'A'}}
    (ROOT/(NAME+'.kicad_pro')).write_text(json.dumps(config,indent=2)+'\n')
    (ROOT/'design-data.json').write_text(json.dumps([{key:value for key,value in component.items() if key!='pcb_fp'} for component in COMPONENTS],indent=2)+'\n')


def generate_dsn():
    layers=['F.Cu','In1.Cu','In2.Cu','B.Cu']
    data=node('pcb',NAME,node('parser',node('host_cad','KiCad'),node('host_version','10.0')),node('resolution',S('um'),10),node('unit',S('um')))
    structure=node('structure')
    for index,layer in enumerate(layers):
        structure.append(node('layer',layer,node('type',S('signal')),node('property',node('index',index))))
    structure.append(node('boundary',node('path',S('pcb'),0,100000,-100000,180000,-100000,180000,-165000,100000,-165000,100000,-100000)))
    structure.append(node('plane','GND',node('polygon','In1.Cu',0,100350,-100350,150850,-100350,150850,-111000,179650,-111000,179650,-164650,100350,-164650)))
    structure.append(node('plane','+3V3',node('polygon','In2.Cu',0,100350,-100350,150700,-100350,150700,-111400,179650,-111400,179650,-164650,100350,-164650)))
    structure.append(node('via','Via_600_300'))
    structure.append(node('rule',node('width',150),node('clearance',120)))
    structure.append(node('keepout','antenna',node('rect',S('signal'),151000,-111000,179000,-100000)))
    placement=node('placement');library=node('library');network=node('network');net_pins=defaultdict(list)
    for component in COMPONENTS:
        if not component.get('pcb_fp'):
            continue
        reference=component['ref'];image=node('image',reference)
        placement.append(node('component',reference,node('place',reference,0,0,S('front'),0)))
        seen=set()
        for entry in physical_pads(component):
            pad=entry['pad'];size=tag(pad,'size')[1:3];net_name=entry['net']
            if not pad[1]:
                if str(pad[2])=='np_thru_hole':
                    image.append(node('keepout','hole'+entry['id'],node('circle',S('signal'),max(size)*1000,entry['x']*1000,-entry['y']*1000)))
                continue
            at_key=(round(entry['x'],5),round(entry['y'],5),net_name,round(size[0],5),round(size[1],5))
            if at_key in seen:
                continue
            seen.add(at_key)
            pin_name=pad[1]+'_'+entry['id'];stack_name=reference+'_'+pin_name
            image.append(node('pin',stack_name,pin_name,round(entry['x']*1000),round(-entry['y']*1000)))
            padstack=node('padstack',stack_name)
            pad_angle=(tag(pad,'at')[3] if len(tag(pad,'at'))>3 else 0)+component['rotation']
            if round(pad_angle)%180==90:
                size=size[::-1]
            pad_layers=tag(pad,'layers')[1:]
            for layer in (layers if '*.Cu' in pad_layers else [value for value in pad_layers if value in layers]):
                if str(pad[3])=='circle':
                    shape=node('circle',layer,round(size[0]*1000))
                else:
                    shape=node('rect',layer,-size[0]*500,-size[1]*500,size[0]*500,size[1]*500)
                padstack.append(node('shape',shape))
            padstack.append(node('attach',S('off')));library.append(padstack)
            if net_name:
                net_pins[net_name].append(S(reference+'-'+pin_name))
        library.append(image)
    for index,(xcoord,ycoord) in enumerate([(104,104),(144,104),(104,161),(176,161)]):
        structure.append(node('keepout','M'+str(index),node('circle',S('signal'),3300,xcoord*1000,-ycoord*1000)))
    for index,(xcoord,ycoord) in enumerate([(103,108),(124,160),(177,151)]):
        structure.append(node('keepout','FID'+str(index),node('circle','F.Cu',2000,xcoord*1000,-ycoord*1000)))
    via=node('padstack','Via_600_300')
    for layer in layers:
        via.append(node('shape',node('circle',layer,600)))
    via.append(node('attach',S('off')));library.append(via)
    for net_name,pin_list in net_pins.items():
        network.append(node('net',net_name,node('pins',*pin_list)))
    network.append(node('class','default',*net_pins.keys(),node('circuit',node('use_via','Via_600_300')),node('rule',node('width',150),node('clearance',120))))
    wiring=node('wiring')
    net_by_code={code:name for name,code in NETS.items()}
    for item in BOARD_ITEMS:
        net_name=net_by_code[tag(item,'net')[1]]
        if str(item[0])=='segment':
            start=tag(item,'start')[1:3];end=tag(item,'end')[1:3]
            wiring.append(node('wire',node('path',tag(item,'layer')[1],tag(item,'width')[1]*1000,round(start[0]*1000),round(-start[1]*1000),round(end[0]*1000),round(-end[1]*1000)),node('net',net_name),node('type',S('protect'))))
        elif str(item[0])=='via':
            position=tag(item,'at')[1:3]
            wiring.append(node('via','Via_600_300',round(position[0]*1000),round(-position[1]*1000),node('net',net_name),node('type',S('protect'))))
    data.extend([structure,placement,library,network,wiring])
    text=emit(data).replace('(string_quote \\")','(string_quote ")')
    (ROOT/'tools/unrouted.dsn').write_text(text+'\n')


def main():
    populate()
    for sub in tags(SYMBOLS['TPS22919DCK'],'symbol'):
        for pin in tags(sub,'pin'):
            if tag(pin,'number')[1]=='5':
                pin[1]=S('passive')
    generate_footprints()
    legalize_placement()
    generate_schematic()
    generate_board()
    generate_dsn()
    print(f'Generated {len(COMPONENTS)} symbols, {len(NETS)} nets, {len(SYMBOLS)} local symbols')


if __name__=='__main__':
    main()
