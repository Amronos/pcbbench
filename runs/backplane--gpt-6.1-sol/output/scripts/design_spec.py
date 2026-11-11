"""Electrical source of truth. Pin keys are manufacturer pad numbers; None = intentional NC."""
COMP=[]
def part(ref,lib,value,mpn,mfr,pins,group,pcbpos,footprint=None,schpos=None,note=''):
 COMP.append(dict(ref=ref,lib=lib,value=value,mpn=mpn,mfr=mfr,pins={str(k):v for k,v in pins.items()},group=group,pcbpos=pcbpos,footprint=footprint,schpos=schpos,note=note))
RFP='Resistor_SMD:R_0603_1608Metric'; CFP='Capacitor_SMD:C_0603_1608Metric'; C4FP='Capacitor_SMD:C_0402_1005Metric'; C8FP='Capacitor_SMD:C_0805_2012Metric'; C12FP='Capacitor_SMD:C_1206_3216Metric'
def r(ref,value,code,a,b,group,pos):part(ref,'Device:R',value,'RC0603FR-07'+code+'L','Yageo',{1:a,2:b},group,pos,RFP)
def cap(ref,value,a,group,pos,kind='100n',b='GND'):
 opts={'100n':('GRM188R71C104KA01D',CFP),'100n0402':('GRM155R71C104KA88D',C4FP),'10u':('GRM21BR61A106KE19L',C8FP),'22u':('GRM31CR61A226KE19L',C12FP),'1u':('GRM188R61C105KA93D',CFP),'4.7u':('GRM21BR61A475KA73L',C8FP),'15p':('GRM1555C1H150JA01D',C4FP),'10p':('GRM1885C1H100JA01D',CFP),'120p':('GRM1885C1H121JA01D',CFP)}
 mpn,fp=opts[kind];part(ref,'Device:C',value,mpn,'Murata',{1:a,2:b},group,pos,fp)
def ind(ref,value,mpn,a,b,group,pos):part(ref,'Device:L',value,mpn,'Murata',{1:a,2:b},group,pos,'Inductor_SMD:L_Murata_DFE201610P')
def sw(ref,net,group,pos):part(ref,'Switch:SW_Push','Pushbutton','PTS810SJM250SMTRLFS','C&K',{1:net,2:'GND'},group,pos,'Button_Switch_SMD:SW_SPST_PTS810')
# RP2350A, externally powered core per datasheet Fig 24.
rppins={1:'3V3',6:'1V1',11:'3V3',20:'3V3',21:'XIN',22:'XOUT_DRV',23:'1V1',24:'SWCLK',25:'SWDIO',26:'RUN',30:'3V3',38:'3V3',39:'1V1',40:'VBAT_ADC',41:'GP27',42:'GP28',43:'GP29',44:'ADC_3V3',45:'3V3',46:'3V3',47:'GND',48:None,49:'3V3',50:'GND',51:'USB_DM_MCU',52:'USB_DP_MCU',53:'3V3',54:'3V3',55:'QSPI_D3',56:'QSPI_CLK',57:'QSPI_D0',58:'QSPI_D2',59:'QSPI_D1',60:'FLASH_CS',61:'GND'}
gp={0:'PSRAM_CS',1:'GP1',2:'I2C_SDA',3:'I2C_SCL',4:'ESP_AT_RX',5:'ESP_AT_TX',6:'ESP_AT_RTS',7:'ESP_AT_CTS',8:'SD_MISO',9:'SD_CS',10:'SD_CLK_DRV',11:'SD_MOSI',12:'GP12',13:'GP13',14:'GP14',15:'GP15',16:'ESP_EN',17:'ESP_BOOT',18:'USB_EN1',19:'CHG_DISABLE',20:'USB_EN2',21:'CHG_N',22:'USB_PGOOD_N',23:'RGB_DATA',24:'SD_DET_N',25:'GP25'}
gppads=[2,3,4,5,7,8,9,10,12,13,14,15,16,17,18,19,27,28,29,31,32,33,34,35,36,37]
for gpio,pad in enumerate(gppads):rppins[pad]=gp[gpio]
part('U1','MCU_RaspberryPi:RP2350A','RP2350A','RP2350A','Raspberry Pi',rppins,'mcu',(137,134,0),schpos=(66.04,76.2),note='Procure A2 or later silicon; do not substitute A1. Externally supplied 1.1V core; firmware sets VREG.HIZ.')
mem={1:'FLASH_CS',2:'QSPI_D1',3:'QSPI_D2',4:'GND',5:'QSPI_D0',6:'QSPI_CLK',7:'QSPI_D3',8:'3V3'}
part('U2','Memory_Flash:W25Q128JVS','16MB QSPI','W25Q128JVSIQ','Winbond',mem,'memory',(137,121,0),schpos=(142.24,35.56))
mem2=dict(mem);mem2[1]='PSRAM_CS'
part('U3','Memory_RAM:APS6404L-3SQRx-SN','8MB PSRAM','APS6404L-3SQR-SN','AP Memory',mem2,'memory',(149,121,0),schpos=(190.5,35.56))
r('R1','10k','10K','FLASH_CS','3V3','memory',(131,122,90));r('R2','10k','10K','PSRAM_CS','3V3','memory',(155,120,90))
cap('C1','100n','3V3','memory',(141,126,0));cap('C2','100n','3V3','memory',(152,126,0))
# Core buck regulator: 0.6*(1+83.5k/100k)=1.101 V.
part('U4','Regulator_Switching:TPS62823DLC','1.1V core buck','TPS62823DLCR','Texas Instruments',{1:'3V3',2:'CORE_FB',3:'GND',4:None,5:'GND',6:'CORE_SW',7:'3V3',8:'CORE_PG'},'core',(146,136,0),schpos=(144.78,83.82))
ind('L1','470nH','DFE201610P-R47M=P2','CORE_SW','1V1','core',(149,133,0))
cap('C3','4.7u','3V3','core',(143,134,90),'4.7u');cap('C4','10u','1V1','core',(151,136,90),'10u')
r('R3','83.5k','83K5','1V1','CORE_FB','core',(147.5,139,0));r('R4','100k','100K','CORE_FB','GND','core',(151,139,0));cap('C5','120p','1V1','core',(147.5,141,0),'120p',b='CORE_FB');r('R5','100k','100K','CORE_PG','3V3','core',(144,139,90))
# Decoupling: one at each package supply group, short to ground plane.
for i,pos in enumerate([(131,131,90),(132,139,90),(136,140,0),(143,131,90),(143,137,90),(133,127,0),(138,128,0),(140,140,0),(134,139,90)]):
 net=['3V3','3V3','3V3','3V3','3V3','3V3','3V3','1V1','1V1'][i]
 cap('C'+str(6+i),'100n',net,'decoupling',pos,'100n0402')
cap('C15','100n','1V1','decoupling',(131,136,90),'100n0402')
cap('C16','4.7u','3V3','decoupling',(139,143,0),'4.7u')
cap('C17','1u','ADC_3V3','decoupling',(144,144,90),'1u');r('R6','200','200R','3V3','ADC_3V3','decoupling',(144,142,0))
# crystal CL=10 pF, 15 pF caps plus stray capacitance, 1k drive damping.
part('Y1','Device:Crystal_GND24','12MHz CL10pF','ABM8-272-T3','Abracon',{1:'XIN',2:'GND',3:'XOUT',4:'GND'},'clock',(128,136,0),'Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',note='12MHz, CL=10pF, ESR <=50 ohms.')
r('R7','1k','1K','XOUT_DRV','XOUT','clock',(129,140,0));cap('C18','15p','XIN','clock',(125,135,90),'15p');cap('C19','15p','XOUT','clock',(125,138,90),'15p')
r('R8','10k','10K','RUN','3V3','controls',(129,127,0));cap('C20','100n','RUN','controls',(127,127,0));sw('SW1','RUN','controls',(124,147,0));r('R9','1k','1K','FLASH_CS','BOOT_SW','controls',(129,122,90));sw('SW2','BOOT_SW','controls',(132,147,0))
# USB-C sink, USB2 data, independently terminated CCs.
part('J1','Connector:USB_C_Receptacle_USB2.0_16P','USB-C','USB4105-GF-A','GCT',{'A1':'GND','A4':'VBUS_RAW','A5':'CC1','A6':'USB_DP','A7':'USB_DM','A8':None,'A9':'VBUS_RAW','A12':'GND','B1':'GND','B4':'VBUS_RAW','B5':'CC2','B6':'USB_DP','B7':'USB_DM','B8':None,'B9':'VBUS_RAW','B12':'GND','SH':'GND'},'usb',(102,143,270),'Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',schpos=(335.28,38.1))
r('R10','5.1k','5K1','CC1','GND','usb',(108,140,0));r('R11','5.1k','5K1','CC2','GND','usb',(108,138,0))
part('U5','Power_Protection:USBLC6-2SC6','USB ESD','USBLC6-2SC6','STMicroelectronics',{1:'USB_DM',2:'GND',3:'USB_DP',4:'USB_DP',5:'VBUS_RAW',6:'USB_DM'},'usb',(110,143,0))
r('R12','27','27R','USB_DM','USB_DM_MCU','usb',(132,129,0));r('R13','27','27R','USB_DP','USB_DP_MCU','usb',(134,129,0))
part('F1','Device:Polyfuse','750mA resettable','MF-MSMF075-2','Bourns',{1:'VBUS_RAW',2:'VBUS'},'usb',(110,134,0),'Fuse:Fuse_1812_4532Metric')
part('D1','Device:D_TVS','5V TVS','SMF5.0A','Littelfuse',{1:'GND',2:'VBUS_RAW'},'usb',(107,134,90),'Diode_SMD:D_SOD-123F')
cap('C21','1u','VBUS','usb',(115,132,90),'1u')
# USB power path charger; 100mA input at reset, 500mA after enumeration; 499mA target charge.
part('U6','Battery_Management:BQ24074RGT','LiPo power-path','BQ24074RGTR','Texas Instruments',{1:'BAT_NTC',2:'VBAT',3:'VBAT',4:'CHG_DISABLE',5:'USB_EN2',6:'USB_EN1',7:'USB_PGOOD_N',8:'GND',9:'CHG_N',10:'VSYS',11:'VSYS',12:'CHG_ILIM',13:'VBUS',14:'CHG_TIMER',15:None,16:'CHG_ISET',17:'GND'},'charger',(115,125,0),schpos=(53.34,213.36),note='External protected 1S 4.2V pack with 10k NTC. ISET=1.78k, nominal499mA. ITERM default10%.')
part('J2','Connector_Generic:Conn_01x03','LiPo + NTC','B3B-PH-K-S(LF)(SN)','JST',{1:'VBAT',2:'GND',3:'BAT_NTC'},'charger',(106,115,0),'Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical')
cap('C22','10u','VBAT','charger',(112,121,90),'10u');cap('C23','10u','VSYS','charger',(119,125,90),'10u');cap('C24','10u','VBUS','charger',(112,128,90),'10u')
r('R14','1.78k','1K78','CHG_ISET','GND','charger',(116,128,0));r('R15','3.24k','3K24','CHG_ILIM','GND','charger',(119,128,0));r('R16','39k','39K','CHG_TIMER','GND','charger',(120,122,90))
r('R17','100k','100K','USB_EN1','GND','charger',(122,129,0));r('R18','100k','100K','USB_EN2','GND','charger',(122,131,0));r('R19','100k','100K','CHG_DISABLE','GND','charger',(121,135,90))
r('R20','10k','10K','USB_PGOOD_N','3V3','charger',(125,131,0));r('R21','10k','10K','CHG_N','3V3','charger',(125,133,0));cap('C25','100n','BAT_NTC','charger',(109,119,0))
# Buck-boost 3.3V rail, input 2.5..4.4V. 1uH + 66uF nominal output.
part('U7','Regulator_Switching:TPS63060','3.3V buck-boost','TPS63060DSCR','Texas Instruments',{1:'BB_L1',2:'VSYS',3:'VSYS',4:'GND',5:'MAIN_PG',6:'BB_VAUX',7:'GND',8:'MAIN_FB',9:'3V3',10:'BB_L2',11:'GND'},'mainpower',(125,119,0),'Package_SON:Texas_S-PWSON-N10',schpos=(147.32,213.36))
ind('L2','1uH','DFE201610P-1R0M=P2','BB_L1','BB_L2','mainpower',(125,116,0))
cap('C26','10u','VSYS','mainpower',(121,118,90),'10u');cap('C27','10u','VSYS','mainpower',(121,115,90),'10u')
for ref,pos in [('C28',(129,115,90)),('C29',(132,115,90)),('C30',(135,115,90))]:cap(ref,'22u','3V3','mainpower',pos,'22u')
cap('C31','100n','BB_VAUX','mainpower',(129,120,90));r('R22','560k','560K','3V3','MAIN_FB','mainpower',(129,118,0));r('R23','100k','100K','MAIN_FB','GND','mainpower',(132,118,0));cap('C32','10p','MAIN_FB','mainpower',(132,120,0),'10p');r('R24','100k','100K','MAIN_PG','3V3','mainpower',(135,119,90))
# battery ADC divider, 2:1; 21uA at4.2V and RC filtering.
r('R25','100k','100K','VBAT','VBAT_ADC','batteryadc',(145,147,0));r('R26','100k','100K','VBAT_ADC','GND','batteryadc',(148,147,0));cap('C33','100n','VBAT_ADC','batteryadc',(151,147,0))
# ESP-AT UART1, 4-wire flow control. UART0 separately exposed for programming.
esppins={1:'3V3',2:'ESP_EN',3:'ESP_AT_RTS',4:'ESP_AT_CTS',5:'ESP_AT_RX',6:'ESP_AT_TX',7:'ESP_STRAP8',8:'ESP_BOOT',9:'GND',10:None,11:'ESP_PROG_RX',12:'ESP_PROG_TX',13:None,14:None,15:None,16:'ESP_STRAP2',17:None,18:None,19:'GND'}
part('U8','RF_Module:ESP32-C3-WROOM-02','Wi-Fi + BLE','ESP32-C3-WROOM-02-N4','Espressif Systems',esppins,'radio',(171,108,0),schpos=(251.46,43.18),note='4MB module. Antenna projects beyond PCB north edge. Load ESP32-C3-WROOM-02 ESP-AT binary on UART0; command UART1 is GPIO6/7/5/4.')
cap('C34','22u','3V3','radio',(157,105,90),'22u');cap('C35','100n','3V3','radio',(159,104,90))
r('R27','10k','10K','ESP_EN','GND','radio',(159,108,0));cap('C36','100n','ESP_EN','radio',(159,110,0))
r('R28','10k','10K','ESP_BOOT','3V3','radio',(157,113,0));r('R29','10k','10K','ESP_STRAP8','3V3','radio',(157,115,0));r('R30','10k','10K','ESP_STRAP2','3V3','radio',(180,103,0));sw('SW3','ESP_BOOT','radio',(155,151,0))
part('J3','Connector_Generic:Conn_01x06','ESP UART0','SSQ-106-03-G-S','Samtec',{1:'GND',2:'3V3',3:'ESP_PROG_TX',4:'ESP_PROG_RX',5:'ESP_EN',6:'ESP_BOOT'},'radio',(181,119,0),'Connector_PinSocket_2.54mm:PinSocket_1x06_P2.54mm_Vertical')
# microSD: SPI1 24MHz maximum initial qualification target, idle pullups.
part('J4','Connector:Micro_SD_Card_Det_Hirose_DM3AT','microSD SPI','DM3AT-SF-PEJM5','Hirose',{1:'SD_DAT2',2:'SD_CS',3:'SD_MOSI',4:'3V3',5:'SD_CLK',6:'GND',7:'SD_MISO',8:'SD_DAT1',9:'SD_DET_N',10:'GND','SH':'GND'},'sd',(173,149,90),'Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5',schpos=(243.84,119.38))
for i,net,pos in [(31,'SD_CS',(164,142,0)),(32,'SD_MOSI',(164,144,0)),(33,'SD_MISO',(164,146,0)),(34,'SD_DAT1',(161,142,0)),(35,'SD_DAT2',(161,144,0)),(36,'SD_DET_N',(161,146,0))]:r('R'+str(i),'47k','47K',net,'3V3','sd',pos)
r('R37','33','33R','SD_CLK_DRV','SD_CLK','sd',(143,130,0));cap('C37','10u','3V3','sd',(164,139,90),'10u');cap('C38','100n','3V3','sd',(166,139,90))
# Qwiic/STEMMA QT pin1 ground,2 3V3,3 SDA,4 SCL.
part('J5','Connector_Generic:Conn_01x04','Qwiic / STEMMA QT','SM04B-SRSS-TB(LF)(SN)','JST',{1:'GND',2:'3V3',3:'I2C_SDA',4:'I2C_SCL'},'qwiic',(110,158,270),'Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal')
r('R38','4.7k','4K7','I2C_SDA','3V3','qwiic',(118,156,0));r('R39','4.7k','4K7','I2C_SCL','3V3','qwiic',(118,158,0));cap('C39','100n','3V3','qwiic',(115,154,0))
# RGB LED with dedicated boost and AHCT buffer, correct on battery and USB.
part('U9','Regulator_Switching:MCP1640x-xCHY','5V LED boost','MCP1640T-I/CHY','Microchip',{1:'LED_SW',2:'GND',3:'3V3',4:'LED_FB',5:'LED_5V',6:'3V3'},'rgb',(151,157,0),schpos=(327.66,215.9))
ind('L3','2.2uH','DFE201610P-2R2M=P2','3V3','LED_SW','rgb',(151,154,0));cap('C40','4.7u','3V3','rgb',(147,155,90),'4.7u');cap('C41','10u','LED_5V','rgb',(155,157,90),'10u');r('R40','976k','976K','LED_5V','LED_FB','rgb',(152,160,0));r('R41','309k','309K','LED_FB','GND','rgb',(156,160,0))
part('U10','74xGxx:74AHCT1G125','LED level buffer','SN74AHCT1G125DBVR','Texas Instruments',{1:'GND',2:'RGB_DATA',3:'GND',4:'RGB_5V_DATA',5:'LED_5V'},'rgb',(144,157,0),'Package_TO_SOT_SMD:SOT-23-5')
cap('C42','100n','LED_5V','rgb',(141,157,90));r('R42','330','330R','RGB_5V_DATA','RGB_DIN','rgb',(144,160,0));r('R43','100k','100K','RGB_DATA','GND','rgb',(141,160,0))
part('D2','LED:SK6812MINI','Addressable RGB','SK6812MINI','OPSCO Optoelectronics',{1:None,2:'GND',3:'RGB_DIN',4:'LED_5V'},'rgb',(137,154,0),note='5V supply, GRB data at800kHz; recommended brightness/current cap in firmware.')
cap('C43','100n','LED_5V','rgb',(137,158,0))
# Fully installed GPIO sockets and keyed debug header.
part('J6','Connector_Generic:Conn_01x12','GPIO socket A','SSQ-112-03-G-S','Samtec',{1:'3V3',2:'GND',3:'GP1',4:'I2C_SDA',5:'I2C_SCL',6:'GP12',7:'GP13',8:'GP14',9:'GP15',10:'GP25',11:'GND',12:'RUN'},'expansion',(116,166,90),'Connector_PinSocket_2.54mm:PinSocket_1x12_P2.54mm_Vertical')
part('J7','Connector_Generic:Conn_01x12','GPIO socket B','SSQ-112-03-G-S','Samtec',{1:'3V3',2:'GND',3:'GP27',4:'GP28',5:'GP29',6:'VBAT_ADC',7:'CHG_N',8:'USB_PGOOD_N',9:'USB_EN1',10:'USB_EN2',11:'CHG_DISABLE',12:'GND'},'expansion',(151,166,90),'Connector_PinSocket_2.54mm:PinSocket_1x12_P2.54mm_Vertical')
part('J8','Connector_Generic:Conn_02x05_Odd_Even','SWD','FTSH-105-01-L-D-K','Samtec',{1:'3V3',2:'SWDIO',3:'GND',4:'SWCLK',5:'GND',6:None,7:None,8:None,9:'GND',10:'RUN'},'debug',(116,146,0),'Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical')
# microSD held off until firmware grants the USB power budget.
for c in COMP:
 if c['ref']=='U1':c['pins']['3']='SD_PWR_EN'
 if c['ref']=='J6':c['pins']['3']='SD_PWR_EN'
 if c['group']=='sd':
  c['pins']={k:('SD_3V3' if v=='3V3' else v) for k,v in c['pins'].items()}
part('U11','Power_Management:TPS22919DCK','SD power switch','TPS22919DCKR','Texas Instruments',{1:'3V3',2:'GND',3:'SD_PWR_EN',4:None,5:'SD_QOD',6:'SD_3V3'},'sd',(159,138,0),schpos=(281.94,134.62))
r('R44','100k','100K','SD_PWR_EN','GND','sd',(156,139,0));r('R45','100','100R','SD_QOD','SD_3V3','sd',(158,141,0));cap('C44','100n','3V3','sd',(159,135,0))
