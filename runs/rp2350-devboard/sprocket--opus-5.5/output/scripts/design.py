"""Single source of truth for the RP2350 dev board: parts, values, sourcing and pin-to-net maps."""

NC = "NC"

YAGEO_DS = "https://www.yageo.com/upload/media/product/productsearch/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf"


def samsung_ds(mpn):
    return f"https://weblib.samsungsem.com/mlcc/mlcc-ec-data-sheet.do?partNumber={mpn[:-1]}"


RESISTORS = {  # value: (MPN, LCSC)
    "27 Ω": ("RC0402FR-0727RL", "C138021"),
    "33 Ω": ("RC0402FR-0733RL", "C138002"),
    "100 Ω": ("RC0402FR-07100RL", "C106232"),
    "470 Ω": ("RC0402FR-07470RL", "C114877"),
    "1 kΩ": ("RC0402FR-071KL", "C106235"),
    "1.74 kΩ": ("RC0402FR-071K74L", "C163482"),
    "2 kΩ": ("RC0402FR-072KL", "C60488"),
    "2.2 kΩ": ("RC0402FR-072K2L", "C114762"),
    "5.1 kΩ": ("RC0402FR-075K1L", "C105872"),
    "10 kΩ": ("RC0402FR-0710KL", "C60490"),
    "100 kΩ": ("RC0402FR-07100KL", "C60491"),
    "150 kΩ": ("RC0402FR-07150KL", "C93947"),
    "470 kΩ": ("RC0402FR-07470KL", "C137976"),
}

CAPACITORS = {  # value: (MPN, LCSC, footprint)
    "15 pF": ("CL05C150JB5NNNC", "C86285", "Capacitor_SMD:C_0402_1005Metric"),
    "100 nF": ("CL05B104KO5NNNC", "C1525", "Capacitor_SMD:C_0402_1005Metric"),
    "4.7 µF": ("CL05A475MP5NRNC", "C23733", "Capacitor_SMD:C_0402_1005Metric"),
    "4.7 µF 25 V": ("CL21A475KAQNNNE", "C1779", "Capacitor_SMD:C_0805_2012Metric"),
    "10 µF": ("CL10A106KP8NNNC", "C19702", "Capacitor_SMD:C_0603_1608Metric"),
    "22 µF": ("CL21A226MAQNNNE", "C45783", "Capacitor_SMD:C_0805_2012Metric"),
}

SHEETS = ["MCU", "Memory", "USB & Power", "Wireless", "IO"]
SHEET_FILES = {"MCU": "mcu", "Memory": "memory", "USB & Power": "power", "Wireless": "wireless", "IO": "io"}

POWER_SYMBOLS = {"GND": "power:GND", "+3V3": "power:+3V3", "+1V1": "power:+1V1", "VBUS": "power:VBUS"}

parts = []
_sheet = None


def sheet(name):
    global _sheet
    _sheet = name


def part(ref, lib, value, fp, nets, mfr="", mpn="", lcsc="", ds="", **kw):
    p = dict(ref=ref, lib=lib, value=value, fp=fp, nets=nets, mfr=mfr, mpn=mpn, lcsc=lcsc,
             ds=ds, sheet=_sheet, unpopulated=False)
    p.update(kw)
    parts.append(p)
    return p


def R(ref, value, a, b):
    mpn, lcsc = RESISTORS[value]
    return part(ref, "Device:R", value, "Resistor_SMD:R_0402_1005Metric", {"1": a, "2": b},
                "YAGEO", mpn, lcsc, YAGEO_DS)


def C(ref, value, a, b="GND"):
    mpn, lcsc, fp = CAPACITORS[value]
    return part(ref, "Device:C", value.replace(" 25 V", "/25 V"), fp, {"1": a, "2": b},
                "Samsung Electro-Mechanics", mpn, lcsc, samsung_ds(mpn))


def BUTTON(ref, value, a, b):
    return part(ref, "Switch:SW_Push", value, "Button_Switch_SMD:SW_SPST_PTS810", {"1": a, "2": b},
                "C&K", "PTS810SJM250SMTRLFS", "C116501", "https://www.ckswitches.com/media/1476/pts810.pdf")


# ---------------------------------------------------------------- MCU
sheet("MCU")
gpio = {
    0: "GP0", 1: "GP1", 2: "GP2", 3: "GP3", 4: "GP4_SDA", 5: "GP5_SCL", 6: "GP6", 7: "GP7",
    8: "PSRAM_CS", 9: "SD_DET", 10: "SD_CLK", 11: "SD_CMD", 12: "SD_D0", 13: "SD_D1", 14: "SD_D2", 15: "SD_D3",
    16: "GP16", 17: "GP17", 18: "GP18", 19: "GP19", 20: "GP20", 21: "GP21", 22: "RGB_DIN",
    23: "WL_ON", 24: "WL_D", 25: "WL_CS", 26: "GP26_A0", 27: "GP27_A1", 28: "VBAT_SENSE", 29: "WL_CLK",
}
gpio_pins = [2, 3, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 27, 28, 29, 31, 32, 33, 34, 35, 36, 37, 40, 41, 42, 43]
u1 = {str(pin): gpio[i] for i, pin in enumerate(gpio_pins)}
u1.update({p: "+3V3" for p in ["1", "11", "20", "30", "38", "45", "44", "49", "53", "54"]})
u1.update({p: "+1V1" for p in ["6", "23", "39", "50"]})
u1.update({
    "46": "VREG_AVDD", "47": "GND", "48": "VREG_LX", "51": "USB_DM_MCU", "52": "USB_DP_MCU",
    "55": "QSPI_SD3", "56": "QSPI_SCLK", "57": "QSPI_SD0", "58": "QSPI_SD2", "59": "QSPI_SD1", "60": "QSPI_SS",
    "61": "GND", "21": "XIN", "22": "XOUT", "24": "SWCLK", "25": "SWDIO", "26": "RUN",
})
part("U1", "MCU_RaspberryPi:RP2350A", "RP2350A", "rp2350-devboard:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm_ThermalVias",
     u1, "Raspberry Pi", "RP2350A", "C42411118", "https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf")
for i, n in enumerate(range(1, 7)):
    C(f"C{n}", "100 nF", "+3V3")          # IOVDD pins 1, 11, 20, 30, 38, 45
for n in range(7, 10):
    C(f"C{n}", "100 nF", "+1V1")          # DVDD pins 6, 23, 39
C("C10", "100 nF", "+3V3")                # USB_OTP_VDD + QSPI_IOVDD
C("C11", "100 nF", "+3V3")                # ADC_AVDD
C("C12", "4.7 µF", "+3V3")                # VREG_VIN
C("C13", "4.7 µF", "+1V1")                # core regulator output
R("R1", "33 Ω", "+3V3", "VREG_AVDD")
C("C14", "4.7 µF", "VREG_AVDD")
# pad 1 carries the polarity dot; Raspberry Pi puts the dot on the VREG_FB/DVDD side
part("L1", "Device:L", "3.3 µH", "rp2350-devboard:L_Abracon_AOTA-B201610S3R3-101-T", {"1": "+1V1", "2": "VREG_LX"},
     "Abracon", "AOTA-B201610S3R3-101-T", "C42411119", "https://abracon.com/Magnetics/power/AOTA-B201610S.pdf")
part("Y1", "Device:Crystal_GND24", "12 MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
     {"1": "XIN", "2": "GND", "3": "XOUT_X", "4": "GND"},
     "Abracon", "ABM8-272-T3", "C20625731", "https://abracon.com/datasheets/ABM8-272-T3.pdf")
R("R2", "1 kΩ", "XOUT", "XOUT_X")
C("C15", "15 pF", "XIN")
C("C16", "15 pF", "XOUT_X")
R("R3", "27 Ω", "USB_DP_MCU", "USB_DP")
R("R4", "27 Ω", "USB_DM_MCU", "USB_DM")
R("R5", "1 kΩ", "QSPI_SS", "BOOTSEL_SW")
BUTTON("SW1", "BOOTSEL", "BOOTSEL_SW", "GND")
R("R6", "10 kΩ", "+3V3", "RUN")
BUTTON("SW2", "RESET", "RUN", "GND")

# ---------------------------------------------------------------- Memory
sheet("Memory")
qspi = {"2": "QSPI_SD1", "3": "QSPI_SD2", "4": "GND", "5": "QSPI_SD0", "6": "QSPI_SCLK", "7": "QSPI_SD3", "8": "+3V3"}
part("U2", "Memory_Flash:W25Q128JVS", "W25Q128JVSIQ", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
     {"1": "QSPI_SS", **qspi}, "Winbond", "W25Q128JVSIQ", "C97521",
     "https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf")
C("C17", "100 nF", "+3V3")
part("U3", "Memory_RAM:APS6404L-3SQRx-SN", "APS6404L-3SQR-SN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     {"1": "PSRAM_CS", **qspi}, "AP Memory", "APS6404L-3SQR-SN", "C5333729",
     "https://www.apmemory.com/wp-content/uploads/APM_PSRAM_QSPI_APS6404L-3SQR-v2.3-PKG.pdf")
C("C18", "100 nF", "+3V3")
R("R7", "2.2 kΩ", "+3V3", "PSRAM_CS")  # must beat the RP2350 power-on pull-down (36 kΩ min) to keep CE# within V_IH

# ---------------------------------------------------------------- USB & Power
sheet("USB & Power")
part("J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C", "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
     {"A1": "GND", "A12": "GND", "B1": "GND", "B12": "GND", "A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS",
      "A5": "CC1", "B5": "CC2", "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM",
      "A8": NC, "B8": NC, "SH": "GND"},
     "GCT", "USB4105-GF-A", "C3020560", "https://gct.co/files/drawings/usb4105.pdf")
R("R8", "5.1 kΩ", "CC1", "GND")
R("R9", "5.1 kΩ", "CC2", "GND")
part("U4", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM", "2": "GND", "5": "VBUS"},
     "STMicroelectronics", "USBLC6-2SC6", "C7519", "https://www.st.com/resource/en/datasheet/usblc6-2.pdf")
part("U5", "Battery_Management:BQ24074RGT", "BQ24074RGTR", "rp2350-devboard:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm_ThermalVias",
     # EN2=0, EN1=1 selects USB500: 500 mA input limit with VIN-DPM, safe on any USB port
     {"13": "VBUS", "10": "VSYS", "11": "VSYS", "2": "VBAT", "3": "VBAT", "1": "CHG_TS", "4": "GND", "5": "GND",
      "6": "VSYS", "7": NC, "8": "GND", "17": "GND", "9": "CHG_N", "12": "CHG_ILIM", "14": NC, "15": NC, "16": "CHG_ISET"},
     "Texas Instruments", "BQ24074RGTR", "C54313", "https://www.ti.com/lit/ds/symlink/bq24074.pdf")
C("C19", "4.7 µF 25 V", "VBUS")
C("C20", "10 µF", "VSYS")
C("C21", "10 µF", "VBAT")
R("R10", "1.74 kΩ", "CHG_ILIM", "GND")
R("R11", "2 kΩ", "CHG_ISET", "GND")
R("R12", "10 kΩ", "CHG_TS", "GND")
R("R13", "1 kΩ", "VSYS", "CHG_LED")
part("D1", "Device:LED", "LED orange", "LED_SMD:LED_0603_1608Metric", {"1": "CHG_N", "2": "CHG_LED"},
     "Lite-On", "LTST-C191KFKT", "C160478",
     "https://optoelectronics.liteon.com/upload/download/DS22-2000-224/LTST-C191KFKT.pdf")
part("Q1", "Transistor_FET:Q_PMOS_GSD", "DMG2305UX", "Package_TO_SOT_SMD:SOT-23-3",
     {"1": "GND", "2": "VBAT", "3": "BAT_CONN"},
     "Diodes Incorporated", "DMG2305UX-7", "C150470", "https://www.diodes.com/assets/Datasheets/DMG2305UX.pdf")
part("J2", "Connector_Generic_MountingPin:Conn_01x02_MountingPin", "LiPo", "rp2350-devboard:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
     {"1": "GND", "2": "BAT_CONN", "MP": NC},
     "JST", "S2B-PH-SM4-TB(LF)(SN)", "C295747", "https://www.jst-mfg.com/product/pdf/eng/ePH.pdf")
R("R14", "470 kΩ", "VBAT", "VBAT_DIV")
R("R15", "470 kΩ", "VBAT_DIV", "GND")
# blocks VBAT/2 from back-powering the ADC pin's diode to IOVDD while +3V3 is off (as on the Pico 2 W)
part("Q2", "Transistor_FET:DMG1012T", "DMG1012T", "Package_TO_SOT_SMD:SOT-523",
     {"1": "+3V3", "2": "VBAT_SENSE", "3": "VBAT_DIV"},
     "Diodes Incorporated", "DMG1012T-7", "C20512", "https://www.diodes.com/assets/Datasheets/ds31783.pdf")
C("C22", "100 nF", "VBAT_SENSE")
part("U6", "Regulator_Switching:TPS63001", "TPS63001DRCR", "rp2350-devboard:Texas_DRC0010J_ThermalVias",
     {"5": "VSYS", "8": "BB_VINA", "6": "3V3_EN", "7": "PS_SYNC", "4": "BB_L1", "2": "BB_L2", "1": "+3V3",
      "10": "+3V3", "3": "GND", "9": "GND", "11": "GND"},
     "Texas Instruments", "TPS63001DRCR", "C28060", "https://www.ti.com/lit/ds/symlink/tps63001.pdf")
C("C23", "10 µF", "VSYS")
R("R16", "100 Ω", "VSYS", "BB_VINA")
C("C24", "100 nF", "BB_VINA")
R("R17", "100 kΩ", "VSYS", "3V3_EN")
R("R18", "100 kΩ", "PS_SYNC", "GND")
part("L2", "Device:L", "2.2 µH", "rp2350-devboard:L_Murata_DFE252012F", {"1": "BB_L1", "2": "BB_L2"},
     "Murata", "DFE252012F-2R2M=P2", "C576403",
     "https://www.murata.com/en-us/api/pdfdownloadapi?cate=luInductorforPowerCircuits&partno=DFE252012F-2R2M%23")
C("C25", "22 µF", "+3V3")
C("C26", "22 µF", "+3V3")

# ---------------------------------------------------------------- Wireless
sheet("Wireless")
part("U7", "rp2350-devboard:RMC20452T", "RM2", "rp2350-devboard:RMC20452T",
     # WL_GPIO0 (pin 8) drives the Pico W's LED; this board has no LED there, as its route would block the header fan-out
     {"1": "GND", "2": NC, "3": "WL_CLK", "4": "GND", "5": "WL_D", "6": "WL_D_470R", "7": "GND", "8": NC,
      "9": "WL_CS", "10": "WL_IRQ", "11": "GND", "12": "WL_ON", "13": "WL_ON", "14": "+3V3", "15": "GND",
      "16": "+3V3", "17": "WL_VBUS_DET", "18": "PS_SYNC", "19": NC, "20": NC, "21": "GND"},
     "Raspberry Pi", "RMC20452T", "C49451547", "https://datasheets.raspberrypi.com/rm2/rm2-datasheet.pdf")
R("R19", "470 Ω", "WL_D", "WL_D_470R")
R("R20", "10 kΩ", "WL_D", "WL_IRQ")
C("C27", "10 µF", "+3V3")
C("C28", "100 nF", "+3V3")
C("C29", "100 nF", "+3V3")
R("R22", "100 kΩ", "VBUS", "WL_VBUS_DET")
R("R23", "150 kΩ", "WL_VBUS_DET", "GND")

# ---------------------------------------------------------------- IO
sheet("IO")
part("J3", "Connector:Micro_SD_Card_Det2", "microSD", "rp2350-devboard:microSD_HC_Molex_104031-0811",
     {"1": "SD_D2", "2": "SD_D3", "3": "SD_CMD", "4": "+3V3", "5": "SD_CLK", "6": "GND", "7": "SD_D0", "8": "SD_D1",
      "9": "SD_DET", "10": "GND", "SH": "GND"},
     "Molex", "1040310811", "C585350",
     "https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/104/104031/1040310811_sd.pdf")
for ref, net in [("R24", "SD_CMD"), ("R25", "SD_D0"), ("R26", "SD_D1"), ("R27", "SD_D2"), ("R28", "SD_D3")]:
    R(ref, "10 kΩ", "+3V3", net)
R("R29", "100 kΩ", "+3V3", "SD_DET")
C("C30", "10 µF", "+3V3")
C("C31", "100 nF", "+3V3")
part("J4", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", "Qwiic", "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
     {"1": "GND", "2": "+3V3", "3": "GP4_SDA", "4": "GP5_SCL", "MP": NC},
     "JST", "SM04B-SRSS-TB(LF)(SN)", "C160404", "https://www.jst-mfg.com/product/pdf/eng/eSH.pdf")
R("R30", "2.2 kΩ", "+3V3", "GP4_SDA")
R("R31", "2.2 kΩ", "+3V3", "GP5_SCL")
part("D3", "LED:WS2812B-2020", "WS2812B-2020", "rp2350-devboard:LED_WS2812B-2020_PLCC4_2.0x2.0mm",
     {"4": "+3V3", "2": "GND", "3": "RGB_DIN", "1": NC},
     "Worldsemi", "WS2812B-2020-V6", "C52917434", "https://www.lcsc.com/datasheet/C52917434.pdf")
C("C32", "100 nF", "+3V3")

# Ordered like the RP2350 pins around the package, so header traces fan out without crossing. The top pins of
# both headers sit beside the RM2 and carry only power; 3V3_EN sits at the bottom, next to the buck-boost.
# VSYS is not brought out: it is tied to the cell through the charger's BAT-OUT FET, so 5 V fed there would
# charge the LiPo with no regulation.
HEADER_LEFT = ["GND", "+3V3", "SWCLK", "SWDIO", "RUN", "GP16", "GP17", "GP18", "GP19", "GP20", "GP21", "GP26_A0",
               "GP27_A1", "GND"]
HEADER_RIGHT = ["GND", "VBUS", "GND", "+3V3", "GP7", "GP6", "GP5_SCL", "GP4_SDA", "GP3", "GP2", "GP1", "GP0", "GND",
                "3V3_EN"]
for ref, nets in [("J5", HEADER_LEFT), ("J6", HEADER_RIGHT)]:
    part(ref, "Connector_Generic:Conn_01x14", "Header 1x14 (not fitted)", "Connector_PinHeader_2.54mm:PinHeader_1x14_P2.54mm_Vertical",
         {str(i + 1): n for i, n in enumerate(nets)}, unpopulated=True)
sheet(None)
for i in range(1, 4):
    part(f"FID{i}", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", {}, unpopulated=True)


def sheets_of_net():
    out = {}
    for p in parts:
        for n in p["nets"].values():
            out.setdefault(n, set()).add(p["sheet"])
    return out
