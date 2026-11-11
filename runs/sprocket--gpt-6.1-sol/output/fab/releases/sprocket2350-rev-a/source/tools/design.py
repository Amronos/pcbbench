from dataclasses import dataclass

@dataclass
class Part:
    ref: str
    symbol: str
    value: str
    footprint: str
    manufacturer: str
    mpn: str
    datasheet: str
    nets: dict
    xy: tuple
    angle: float = 0
    block: str = ''
    schematic_xy: tuple = (0,0)

parts=[]
def add(ref,symbol,value,footprint,manufacturer,mpn,datasheet,nets,xy,angle=0,block=''):
    p=Part(ref,symbol,value,footprint,manufacturer,mpn,datasheet,{str(k):v for k,v in nets.items()},xy,angle,block)
    parts.append(p)
    return p

def r(ref,value,n1,n2,xy,angle=0,block=''):
    codes={'100 kΩ':'100K','10 kΩ':'10K','5.1 kΩ':'5K1','3.3 kΩ':'3K3','1 kΩ':'1K','1.8 kΩ':'1K8','27 Ω':'27R','33 Ω':'33R','100 Ω':'100R','330 Ω':'330R','8.66 kΩ':'8K66','8.87 kΩ':'8K87','68.1 kΩ':'68K1','3.48 kΩ':'3K48','2.94 kΩ':'2K94','2 kΩ':'2K','220 kΩ':'220K','330 kΩ':'330K'}
    return add(ref,'Device:R',value,'Resistor_SMD:R_0603_1608Metric','Yageo',f'RC0603FR-07{codes[value]}L','https://www.yageo.com/en/Product/category/resistor/General_Purpose/nbe',{'1':n1,'2':n2},xy,angle,block)

def c(ref,value,n1,xy,angle=0,block=''):
    data={
        '100 nF':('C_0603_1608Metric','GRM188R71C104KA01D'),
        '1 µF':('C_0603_1608Metric','GRM188R71C105KA12D'),
        '4.7 µF':('C_0805_2012Metric','GRM21BR71A475KA73L'),
        '10 µF':('C_0805_2012Metric','GRM21BC71E106ME11L'),
        '22 µF':('C_1206_3216Metric','GRM31CR61A226KE19L'),
        '15 pF':('C_0603_1608Metric','GRM1885C1H150JA01D'),
    }
    fp,mpn=data[value]
    return add(ref,'Device:C',value,'Capacitor_SMD:'+fp,'Murata',mpn,'https://www.murata.com/en-us/products/capacitor/mlcc',{'1':n1,'2':'GND'},xy,angle,block)

rp={1:'+3V3',11:'+3V3',20:'+3V3',30:'+3V3',38:'+3V3',45:'+3V3',6:'CORE_1V1',23:'CORE_1V1',39:'CORE_1V1',46:'VREG_AVDD',47:'GND',48:'VREG_LX',49:'+3V3',50:'CORE_1V1',53:'+3V3',54:'+3V3',44:'+3V3',61:'GND',21:'XIN',22:'XOUT',24:'SWCLK',25:'SWDIO',26:'RUN',51:'USB_M_MCU',52:'USB_P_MCU',55:'QSPI_D3',56:'QSPI_CLK',57:'QSPI_D0',58:'QSPI_D2',59:'QSPI_D1',60:'FLASH_CS'}
gp={0:'PSRAM_CS',1:'GPIO1',2:'I2C_SDA',3:'I2C_SCL',4:'SD_MISO',5:'SD_CS',6:'SD_CLK',7:'SD_MOSI',8:'SD_DETECT',9:'RGB_DATA',10:'USB_500_EN',11:'CHARGE_DISABLE',12:'UART_TX',13:'UART_RX',14:'UART_CTS',15:'UART_RTS',16:'RADIO_CTRL',17:'GPIO17',18:'GPIO18',19:'GPIO19',20:'GPIO20',21:'GPIO21',22:'GPIO22',23:'GPIO23',24:'GPIO24',25:'GPIO25',26:'BAT_ADC',27:'ADC1',28:'ADC2',29:'ADC3'}
gp_pins=[2,3,4,5,7,8,9,10,12,13,14,15,16,17,18,19,27,28,29,31,32,33,34,35,36,37,40,41,42,43]
rp.update({p:gp[i] for i,p in enumerate(gp_pins)})
add('U1','MCU_RaspberryPi:RP2350A','RP2350A','Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm','Raspberry Pi','RP2350A','https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf',rp,(55,53),block='MCU')
mem={1:'FLASH_CS',2:'QSPI_D1',3:'QSPI_D2',4:'GND',5:'QSPI_D0',6:'QSPI_CLK',7:'QSPI_D3',8:'+3V3'}
add('U2','Board:W25Q128JVS','16 MB flash','Package_SO:SOIC-8_5.3x5.3mm_P1.27mm','Winbond','W25Q128JVSIQ','https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf',mem,(49,37),block='Memory')
add('U3','Memory_RAM:APS6404L-3SQRx-SN','8 MB PSRAM','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm','AP Memory','APS6404L-3SQR-SN','https://www.apmemory.com/cn/downloadFiles/032411212009597427',dict(mem,**{'1':'PSRAM_CS'}),(63,37),block='Memory')
c('C1','100 nF','+3V3',(44,35),90,'Memory');c('C2','100 nF','+3V3',(67,35),90,'Memory')
r('R1','10 kΩ','+3V3','FLASH_CS',(44,38),90,'Memory');r('R2','1.8 kΩ','+3V3','PSRAM_CS',(67,39),90,'Memory')
r('R3','1 kΩ','FLASH_CS','BOOT_SWITCH',(45,45),0,'MCU')
add('SW1','Switch:SW_Push','BOOT','Button_Switch_SMD:SW_SPST_TL3342','E-Switch','TL3342F160QG','https://www.e-switch.com/product/tl3342-series-subminiature-smt-tactile-switch/',{1:'BOOT_SWITCH',2:'GND'},(41,48),block='MCU')
add('SW2','Switch:SW_Push','RESET','Button_Switch_SMD:SW_SPST_TL3342','E-Switch','TL3342F160QG','https://www.e-switch.com/product/tl3342-series-subminiature-smt-tactile-switch/',{1:'RUN',2:'GND'},(41,57),block='MCU')
r('R4','10 kΩ','+3V3','RUN',(46,59),90,'MCU')
add('Y1','Device:Crystal_GND24','12 MHz','Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm','Abracon','ABM8-272-T3','https://abracon.com/Resonators/ABM8.pdf',{1:'XIN',2:'GND',3:'XTAL_OUT',4:'GND'},(44,64),block='MCU')
r('R5','1 kΩ','XOUT','XTAL_OUT',(47.5,62.5),90,'MCU');c('C3','15 pF','XIN',(41,62),90,'MCU');c('C4','15 pF','XTAL_OUT',(44.5,67),0,'MCU')
add('L1','Device:L','3.3 µH','Inductor_SMD:L_Abracon_AOTA-B201610S','Abracon','AOTA-B201610S3R3-101-T','https://abracon.com/Magnetics/power/AOTA-B201610S.pdf',{1:'VREG_LX',2:'CORE_1V1'},(58.5,47),90,'MCU')
r('R6','33 Ω','+3V3','VREG_AVDD',(62,46),90,'MCU')
c('C5','4.7 µF','VREG_AVDD',(64.5,44),0,'MCU')
c('C6','4.7 µF','+3V3',(56.2,47.2),90,'MCU')
c('C7','4.7 µF','CORE_1V1',(58.5,44.3),90,'MCU')
c('C8','4.7 µF','CORE_1V1',(53,61),90,'MCU')
for ref,xy,ang,net in [
    ('C9',(49.5,49.5),180,'+3V3'),('C10',(49.5,54.5),180,'+3V3'),('C11',(53,58.5),270,'+3V3'),('C12',(59,58.5),270,'+3V3'),('C13',(60.5,53.5),0,'+3V3'),('C14',(60.5,49.5),0,'+3V3'),
    ('C15',(54,48),90,'+3V3'),('C16',(52,48),90,'+3V3'),('C17',(63,49.5),0,'+3V3'),
    ('C18',(49.5,52),180,'CORE_1V1'),('C19',(56,58.5),270,'CORE_1V1'),('C20',(63,53.5),0,'CORE_1V1')]:
    c(ref,'100 nF',net,xy,ang,'MCU')

usb={'A1':'GND','A12':'GND','B1':'GND','B12':'GND','SH':'GND','A4':'VBUS','A9':'VBUS','B4':'VBUS','B9':'VBUS','A5':'CC1','B5':'CC2','A6':'USB_P','B6':'USB_P','A7':'USB_M','B7':'USB_M','A8':None,'B8':None}
add('J1','Connector:USB_C_Receptacle_USB2.0_16P','USB-C','Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal','GCT','USB4105-GF-A','https://gct.co/connector/usb4105',usb,(37,23.5),180,'USB')
r('R7','5.1 kΩ','CC1','GND',(34,30),0,'USB');r('R8','5.1 kΩ','CC2','GND',(40,30),0,'USB')
r('R9','27 Ω','USB_P','USB_P_MCU',(51,44.8),90,'USB');r('R10','27 Ω','USB_M','USB_M_MCU',(49,44.8),90,'USB')
add('U4','Power_Protection:USBLC6-2SC6','USB ESD','Package_TO_SOT_SMD:SOT-23-6','STMicroelectronics','USBLC6-2SC6','https://www.st.com/resource/en/datasheet/usblc6-2.pdf',{1:'USB_M',2:'GND',3:'USB_P',4:'USB_P',5:'VBUS',6:'USB_M'},(38,34),block='USB')

add('U5','Battery_Management:BQ24074RGT','Power-path charger','Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm','Texas Instruments','BQ24074RGTR','https://www.ti.com/lit/ds/symlink/bq24074.pdf',{1:'BAT_TS',2:'BAT',3:'BAT',4:'CHARGE_DISABLE',5:'GND',6:'USB_500_EN',7:'USB_PGOOD_N',8:'GND',9:'CHG_N',10:'SYS',11:'SYS',12:'CHG_ILIM',13:'VBUS',14:'CHG_TMR',15:None,16:'CHG_ISET',17:'GND'},(28.5,42),block='Power')
add('U6','Regulator_Switching:TPS63001','3.3 V buck-boost','Package_SON:Texas_DRC0010J','Texas Instruments','TPS63001DRCR','https://www.ti.com/lit/ds/symlink/tps63001.pdf',{1:'+3V3',2:'BUCK_L2',3:'GND',4:'BUCK_L1',5:'SYS',6:'SYS',7:'GND',8:'BUCK_VINA',9:'GND',10:'+3V3',11:'GND'},(29,57),block='Power')
add('L2','Device:L','2.2 µH','Inductor_SMD:L_Coilcraft_XxL4020','Coilcraft','XFL4020-222MEC','https://www.coilcraft.com/getmedia/50632d43-da1b-4cdb-8ab4-3029cab51df3/xfl4020.pdf',{1:'BUCK_L1',2:'BUCK_L2'},(29,52),90,'Power')
c('C21','1 µF','VBUS',(28.5,38.5),90,'Power');c('C22','10 µF','BAT',(24,44),90,'Power');c('C23','10 µF','SYS',(32,44),90,'Power')
c('C24','10 µF','SYS',(25,56),90,'Power');c('C25','100 nF','BUCK_VINA',(25,59),90,'Power')
r('R36','100 Ω','SYS','BUCK_VINA',(25,61.5),90,'Power')
c('C26','22 µF','+3V3',(34,55),90,'Power');c('C27','22 µF','+3V3',(34,59),90,'Power')
r('R11','8.66 kΩ','CHG_ISET','GND',(24.5,40),90,'Power')
r('R12','3.48 kΩ','CHG_ILIM','GND',(24,48),0,'Power')
r('R13','10 kΩ','BAT_TS','GND',(33,40),90,'Power')
r('R14','68.1 kΩ','CHG_TMR','GND',(31.5,36.5),90,'Power')
r('R16','10 kΩ','USB_500_EN','GND',(35,47.5),0,'Power')
r('R17','10 kΩ','+3V3','CHARGE_DISABLE',(36,43),90,'Power')
r('R18','10 kΩ','+3V3','USB_PGOOD_N',(32,49.5),90,'Power')
r('R19','10 kΩ','+3V3','CHG_N',(36,50.5),90,'Power')
add('J2','Connector_Generic:Conn_01x02','LiPo','Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal','JST','S2B-PH-SM4-TB(LF)(SN)','https://www.jst-mfg.com/product/pdf/eng/ePH.pdf',{1:'GND',2:'BAT'},(26,29),180,'Power')
r('R20','3.3 kΩ','+3V3','GAUGE_SDA',(38,63),0,'Power');r('R21','3.3 kΩ','+3V3','GAUGE_SCL',(38,65),0,'Power');c('C28','100 nF','BAT',(35,67.2),270,'Power')
add('U8','Board:MAX17048G','Battery voltage / SOC','Package_DFN_QFN:TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm','Analog Devices / Maxim','MAX17048G+T10','https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf',{1:'GND',2:'BAT',3:'BAT',4:'GND',5:None,6:'GND',7:'GAUGE_SCL',8:'GAUGE_SDA',9:'GND'},(35,64),block='Power')

add('U7','RF_Module:ESP32-C3-WROOM-02','Wi-Fi + BLE','RF_Module:ESP32-C3-WROOM-02','Espressif Systems','ESP32-C3-WROOM-02-N4','https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf',{1:'+3V3',2:'RADIO_EN',3:'UART_CTS',4:'UART_RTS',5:'UART_TX',6:'UART_RX',7:'RADIO_IO8',8:'RADIO_BOOT',9:'GND',10:None,11:'PROG_RX',12:'PROG_TX',13:None,14:None,15:None,16:'RADIO_IO2',17:None,18:None,19:'GND'},(87,27),block='Radio')
r('R22','100 kΩ','RADIO_EN','GND',(74,31),0,'Radio');c('C29','1 µF','RADIO_EN',(74,34),0,'Radio')
r('R35','1 kΩ','RADIO_CTRL','RADIO_EN',(71,31),0,'Radio')
r('R23','10 kΩ','+3V3','RADIO_IO8',(77,36),90,'Radio');r('R24','10 kΩ','+3V3','RADIO_BOOT',(80,37),0,'Radio');r('R25','10 kΩ','+3V3','RADIO_IO2',(75,38.5),90,'Radio')
c('C30','10 µF','+3V3',(74,27),90,'Radio');c('C31','100 nF','+3V3',(76,29),90,'Radio');c('C32','22 µF','+3V3',(91,37),90,'Radio')
add('SW3','Switch:SW_Push','RADIO BOOT','Button_Switch_SMD:SW_SPST_TL3342','E-Switch','TL3342F160QG','https://www.e-switch.com/product/tl3342-series-subminiature-smt-tactile-switch/',{1:'RADIO_BOOT',2:'GND'},(85,43),block='Radio')
add('J3','Connector_Generic:Conn_01x04','Radio UART','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical','Samtec','TSW-104-07-G-S','https://www.samtec.com/products/tsw',{1:'GND',2:'PROG_TX',3:'PROG_RX',4:'RADIO_EN'},(96,38),block='Radio')

add('J4','Connector:Micro_SD_Card_Det_Hirose_DM3AT','microSD','Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5','Hirose','DM3AT-SF-PEJM5','https://www.hirose.com/en/product/document?clcode=CL0609-0031-0-00&documenttype=2&lang=en',{1:'SD_DAT2',2:'SD_CS',3:'SD_MOSI',4:'+3V3',5:'SD_CLK',6:'GND',7:'SD_MISO',8:'SD_DAT1',9:'SD_DETECT',10:'GND','SH':'GND'},(84,79),block='Peripherals')
for ref,net,xy in [('R26','SD_CS',(73,62)),('R27','SD_MOSI',(75,62)),('R28','SD_MISO',(77,62)),('R29','SD_DAT1',(79,62)),('R30','SD_DAT2',(81,62)),('R31','SD_DETECT',(72,65))]:
    r(ref,'10 kΩ','+3V3',net,xy,90,'Peripherals')
c('C33','10 µF','+3V3',(71,70),90,'Peripherals');c('C34','100 nF','+3V3',(71,73),90,'Peripherals')
add('J5','Connector_Generic:Conn_01x04','Qwiic / STEMMA QT','Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical','JST','BM04B-SRSS-TB(LF)(SN)','https://www.jst-mfg.com/product/pdf/eng/eSH.pdf',{1:'GND',2:'+3V3',3:'I2C_SDA',4:'I2C_SCL'},(68,80),block='Peripherals')
r('R32','5.1 kΩ','+3V3','I2C_SDA',(64,73),90,'Peripherals');r('R33','5.1 kΩ','+3V3','I2C_SCL',(64,76),90,'Peripherals')
add('D1','LED:WS2812B','RGB V6','LED_SMD:LED_WS2812B_PLCC4_5.0x5.0mm_P3.2mm','Worldsemi','WS2812B-V6','https://www.tme.eu/Document/88f56341f2c21fd586036db245cb26cf/WS2812B-V6_V1.4_EN.pdf',{1:'+3V3',2:None,3:'GND',4:'RGB_DIN'},(68,57),block='Peripherals')
r('R34','330 Ω','RGB_DATA','RGB_DIN',(64,59),90,'Peripherals');c('C35','100 nF','+3V3',(67,62),90,'Peripherals')
headers=['+3V3','GND','GPIO1','RADIO_BOOT','CHG_N','GPIO17','GPIO18','GPIO19','GPIO20','GPIO21','GPIO22','GPIO23','GPIO24','GPIO25','ADC1','ADC2','ADC3','RUN','+3V3','GND']
add('J6','Connector_Generic:Conn_02x10_Odd_Even','GPIO','Connector_PinHeader_2.54mm:PinHeader_2x10_P2.54mm_Vertical','Samtec','TSW-110-07-G-D','https://www.samtec.com/products/tsw',dict(enumerate(headers,1)),(34,78),90,'Peripherals')
add('J7','Connector_Generic:Conn_01x04','SWD','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical','Samtec','TSW-104-07-G-S','https://www.samtec.com/products/tsw',{1:'+3V3',2:'SWDIO',3:'GND',4:'SWCLK'},(47,70),90,'MCU')

for ref,net,xy in [('TP1','VBUS',(22,33)),('TP2','SYS',(22,62)),('TP3','+3V3',(32,64)),('TP4','GND',(29,67)),('TP5','BAT',(22,30)),('TP6','CHG_N',(36,53)),('TP7','USB_PGOOD_N',(32,52)),('TP8','CORE_1V1',(57,62))]:
    add(ref,'Connector:TestPoint',net,'TestPoint:TestPoint_Pad_D1.0mm','PCB copper','COPPER-TESTPOINT','',{1:net},xy,block='Test')

for ref,xy in [('H1',(23,81.5)),('H2',(96.5,81.5)),('H3',(58,23.5))]:
    add(ref,'Mechanical:MountingHole','M2.5','MountingHole:MountingHole_2.7mm_M2.5','PCB hole','NPTH-2.7MM','',{},xy,block='Mechanical')
for ref,xy in [('FID1',(22.5,24)),('FID2',(95,56)),('FID3',(61,80))]:
    add(ref,'Mechanical:Fiducial','Fiducial','Fiducial:Fiducial_1mm_Mask2mm','PCB copper','COPPER-FIDUCIAL','',{},xy,block='Mechanical')

usb_names={'USB_M':'USB_D_N','USB_P':'USB_D_P','USB_M_MCU':'MCU_USB_N','USB_P_MCU':'MCU_USB_P'}
for part in parts:
    part.nets={pin:usb_names.get(net,net) for pin,net in part.nets.items()}

placement_updates={
    'R3':(43,41.5),'R4':(47,59),'C1':(43,35),'R1':(43,38),'C2':(68,35),'R2':(68,39),
    'C9':(49.2,49.5),'C10':(49.2,54.5),'C18':(49.2,52),
    'C11':(53,58.8),'C12':(59,58.8),'C19':(56,58.8),
    'C13':(60.8,53.5),'C14':(60.8,49.5),'C17':(64,49.5),'C20':(64,53.5),
    'C15':(54,47.2),'C16':(52,47.2),'C6':(56.2,47),'C7':(58.5,43.8),'C8':(54.5,63),
    'C21':(28.5,38.2),'C26':(29,53.4),'C27':(35.5,54.2),'C24':(28,61.2),'C25':(33,58),'R36':(33,61.4),
    'TP1':(22,35),'TP5':(23,33.5),'TP6':(38,38),'TP7':(34,35),
    'FID1':(47,23.5),'C33':(71,70),'C34':(71,73.5),'J4':(84,76),
    'R32':(64,72.2),'R33':(64,75.5),'R34':(63,59),'R20':(39,62.5),'R21':(39,66),'R36':(32,61),
    'C30':(75.5,23.4),'C31':(73,23.4),'R9':(52,44),'R10':(54,44),'TP5':(22,68.5),
    'L2':(24.1,56.8),'R18':(27,47.5),'R19':(29.5,47.5),
}
for part in parts:
    if part.ref in placement_updates:part.xy=placement_updates[part.ref]
    if part.ref in ['C30','C31','C22','C23','C24']:part.angle=270
    if part.ref in ['C25','C26']:part.angle=0
    if part.ref in ['R20','R21']:part.angle=90
    if part.ref in ['R9','R10','R5']:part.angle=270
    if part.ref=='L1':
        part.nets={'1':'CORE_1V1','2':'VREG_LX'};part.angle=270
    if part.ref in ['L1','U7','J4','D1']:
        part.footprint='Board:'+part.footprint.split(':',1)[1]
    if part.ref=='C28':part.xy=(35,67.2);part.angle=270
    if part.ref=='U1':part.nets.update({'32':'GAUGE_SDA','33':'GAUGE_SCL','40':'ADC0'})
    if part.ref=='J6':part.nets.update({'5':'ADC0','9':'GAUGE_SDA','10':'GAUGE_SCL'})
    if part.ref=='C20':
        part.footprint='Capacitor_SMD:C_0201_0603Metric'
        part.mpn='GRM033Z71C104KE14D'
        part.datasheet='https://pim.murata.com/asset/pim4/ceramicCapacitorSMD/GRM033Z71C104KE14-01A-EN_PDF_CERAMICCAPACITORSMD'
    if part.ref=='C6':
        part.value='22 µF'
        part.footprint='Capacitor_SMD:C_0603_1608Metric'
        part.mpn='GRM188R61A226ME15D'
        part.datasheet='https://www.farnell.com/datasheets/2047978.pdf'
