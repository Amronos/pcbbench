"""Circuit source of truth: parts, values, footprints, sourcing and pin-to-net wiring.

gen_schematic.py draws the KiCad schematic from this file. Positions are schematic mm on A3 sheets.
"""

R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"

# value -> (manufacturer, MPN, description) for generic passives
PASSIVES = {
    "100 nF": ("Samsung Electro-Mechanics", "CL05B104KO5NNNC", "100 nF 16 V X7R 0402"),
    "4.7 µF": ("Samsung Electro-Mechanics", "CL05A475KP5NRNC", "4.7 µF 10 V X5R 0402"),
    "10 µF": ("Samsung Electro-Mechanics", "CL10A106KP8NNNC", "10 µF 10 V X5R 0603"),
    "4.7 µF 16 V": ("Samsung Electro-Mechanics", "CL10A475KO8NNNC", "4.7 µF 16 V X5R 0603"),
    "15 pF": ("Murata", "GRM1555C1H150JA01D", "15 pF 50 V C0G 0402"),
    "27 Ω": ("YAGEO", "RC0402FR-0727RL", "27 Ω 1% 0402"),
    "33 Ω": ("YAGEO", "RC0402FR-0733RL", "33 Ω 1% 0402"),
    "470 Ω": ("YAGEO", "RC0402FR-07470RL", "470 Ω 1% 0402"),
    "1 kΩ": ("YAGEO", "RC0402FR-071KL", "1 kΩ 1% 0402"),
    "1.6 kΩ": ("YAGEO", "RC0402FR-071K6L", "1.6 kΩ 1% 0402"),
    "2.7 kΩ": ("YAGEO", "RC0402FR-072K7L", "2.7 kΩ 1% 0402"),
    "4.7 kΩ": ("YAGEO", "RC0402FR-074K7L", "4.7 kΩ 1% 0402"),
    "5.1 kΩ": ("YAGEO", "RC0402FR-075K1L", "5.1 kΩ 1% 0402"),
    "10 kΩ": ("YAGEO", "RC0402FR-0710KL", "10 kΩ 1% 0402"),
    "68 kΩ": ("YAGEO", "RC0402FR-0768KL", "68 kΩ 1% 0402"),
    "100 kΩ": ("YAGEO", "RC0402FR-07100KL", "100 kΩ 1% 0402"),
}

PASSIVE_DATASHEETS = {
    "Samsung Electro-Mechanics": "https://product.samsungsem.com/mlcc/basic-search.do",
    "Murata": "https://www.murata.com/en-us/products/productdetail?partno=GRM1555C1H150JA01D",
    "YAGEO": "https://www.yageo.com/upload/media/product/products/datasheet/rchip/PYu-RC_Group_51_RoHS_L_12.pdf",
}

SHEETS = {}

# MPN -> distributor part numbers and approved alternates, written as hidden symbol fields.
# Only numbers seen on the distributor's own page (parts research, July 2026).
_DIST = [
    ("CL05B104KO5NNNC", "C1525", "1276-1001-1-ND"),
    ("CL05A475KP5NRNC", "C368809", None),
    ("CL10A106KP8NNNC", "C19702", "1276-1192-1-ND"),
    ("CL10A475KO8NNNC", "C19666", None),
    ("GRM1555C1H150JA01D", "C76950", "490-5888-1-ND"),
    ("RC0402FR-0727RL", "C138021", "YAG3086CT-ND"),
    ("RC0402FR-0733RL", "C138002", None),
    ("RC0402FR-07470RL", "C114877", None),
    ("RC0402FR-071KL", "C106235", "311-1.00KLRCT-ND"),
    ("RC0402FR-071K6L", "C185451", "YAG3045CT-ND"),
    ("RC0402FR-072K7L", "C138017", None),
    ("RC0402FR-074K7L", "C105871", None),
    ("RC0402FR-075K1L", "C105872", None),
    ("RC0402FR-0710KL", "C60490", None),
    ("RC0402FR-0768KL", "C137947", None),
    ("RC0402FR-07100KL", "C60491", None),
    ("SC1509-A4", "C42411118", "2648-SC1509-A4CT-ND"),
    ("W25Q128JVSIQ", "C97521", None),
    ("APS6404L-3SQR-SN", "C5333729", None),
    ("RMC20452T", "C49451547", "2648-SC1169CT-ND"),
    ("BQ24074RGTR", "C54313", None),
    ("TLV75733PDBVR", "C485517", "296-50414-1-ND"),
    ("USBLC6-2SC6", "C7519", None),
    ("WS2812C-2020-V6", "C55109522", None),
    ("ABM8-272-T3", "C20625731", None),
    ("AOTA-B201610S3R3-101-T", "C42411119", None),
    ("USB4105-GF-A", "C3020560", None),
    ("1040310811", "C585350", None),
    ("SM04B-SRSS-TB(LF)(SN)", "C160404", "455-1804-1-ND"),
    ("S2B-PH-SM4-TB(LF)(SN)", "C295747", "455-1749-1-ND"),
    ("PTS810SJM250SMTRLFS", "C116501", "CKN10502CT-ND"),
    ("LTST-C191KRKT", "C125099", "160-1447-1-ND"),
]
DISTRIBUTORS = {mpn: {k: v for k, v in (("LCSC Part #", lcsc), ("Digikey Part #", dk)) if v}
                for mpn, lcsc, dk in _DIST}
DISTRIBUTORS["PTS810SJM250SMTRLFS"]["Mouser Part #"] = "611-PTS810SJM250SMTR"
ALTERNATES = {
    "APS6404L-3SQR-SN": "APS6404L-3SQN-SN (LCSC C3028887)",
    "AOTA-B201610S3R3-101-T": "any 3.3 µH 2016 inductor, Isat >= 2.4 A, DCR <= 150 mΩ",
    "RC0402FR-0727RL": "UNI-ROYAL 0402WGF270JTCE (LCSC C25100)",
    "RC0402FR-071K6L": "UNI-ROYAL 0402WGF1601TCE (LCSC C4908)",
    "SC1509-A4": "SC1509(13)-A4 (13 in reel). A2 stepping SC1509 also works",
}
for mpn, alt in ALTERNATES.items():
    DISTRIBUTORS[mpn]["Alternate"] = alt


def part(sheet, ref, lib, value, fp, x, y, nets, rot=0, mfr=None, mpn=None, datasheet=None,
         desc=None, dnp=False, in_bom=True):
    """nets maps a pin number (or '@NAME' for every pin with that name) to a net; 'NC' = no connect."""
    if value in PASSIVES and mpn is None:
        mfr, mpn, desc = PASSIVES[value]
        datasheet = PASSIVE_DATASHEETS[mfr]
    SHEETS.setdefault(sheet, []).append(dict(
        ref=ref, lib=lib, value=value.replace(" 16 V", ""), fp=fp, x=x, y=y, rot=rot, nets=nets,
        mfr=mfr, mpn=mpn, datasheet=datasheet, desc=desc, dnp=dnp, in_bom=in_bom))


def R(sheet, ref, value, x, y, n1, n2, rot=0):
    part(sheet, ref, "Device:R", value, R0402, x, y, {"1": n1, "2": n2}, rot=rot)


def C(sheet, ref, value, x, y, n1, n2="GND", rot=0):
    fp = C0603 if value in ("10 µF", "4.7 µF 16 V") else C0402
    part(sheet, ref, "Device:C", value, fp, x, y, {"1": n1, "2": n2}, rot=rot)


# ---------------------------------------------------------------- power
S = "power"
part(S, "J1", "Connector:USB_C_Receptacle_USB2.0_16P", "USB-C",
     "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", 45.72, 93.98,
     {"@VBUS": "VBUS", "@GND": "GND", "@SHIELD": "GND", "A5": "CC1", "B5": "CC2",
      "A6": "USB_DP", "B6": "USB_DP", "A7": "USB_DM", "B7": "USB_DM", "A8": "NC", "B8": "NC"},
     mfr="GCT", mpn="USB4105-GF-A", datasheet="https://gct.co/files/drawings/usb4105.pdf",
     desc="USB 2.0 Type-C receptacle, 16 pin, top mount")
R(S, "R1", "5.1 kΩ", 88.9, 124.46, "CC1", "GND")
R(S, "R2", "5.1 kΩ", 96.52, 124.46, "CC2", "GND")
part(S, "U7", "Power_Protection:USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     121.92, 147.32, {"1": "USB_DP", "6": "USB_DP", "3": "USB_DM", "4": "USB_DM", "2": "GND", "5": "VBUS"},
     mfr="STMicroelectronics", mpn="USBLC6-2SC6",
     datasheet="https://www.st.com/resource/en/datasheet/usblc6-2.pdf", desc="USB 2.0 ESD protection")

part(S, "U5", "Battery_Management:BQ24074RGT", "BQ24074RGTR",
     "Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm_ThermalVias", 200.66, 88.9,
     {"13": "VBUS", "10": "VSYS", "11": "VSYS", "2": "VBAT", "3": "VBAT", "1": "BQ_TS",
      "16": "BQ_ISET", "12": "BQ_ILIM", "6": "VSYS", "5": "GND", "4": "GND", "14": "NC",
      "15": "NC", "7": "NC", "9": "CHG_N", "8": "GND", "17": "GND"},
     mfr="Texas Instruments", mpn="BQ24074RGTR", datasheet="https://www.ti.com/lit/ds/symlink/bq24074.pdf",
     desc="1.5 A single-cell Li-ion charger with power path, USB500 mode")
C(S, "C1", "4.7 µF 16 V", 152.4, 83.82, "VBUS")
C(S, "C2", "10 µF", 251.46, 78.74, "VSYS")
C(S, "C3", "10 µF", 259.08, 104.14, "VBAT")
R(S, "R3", "10 kΩ", 165.1, 127.0, "BQ_TS", "GND")
R(S, "R4", "2.7 kΩ", 172.72, 127.0, "BQ_ISET", "GND")
R(S, "R5", "1.6 kΩ", 180.34, 127.0, "BQ_ILIM", "GND")
part(S, "J4", "Connector_Generic_MountingPin:Conn_01x02_MountingPin", "LiPo",
     "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal", 297.18, 101.6,
     {"1": "GND", "2": "VBAT", "MP": "NC"},
     mfr="JST", mpn="S2B-PH-SM4-TB(LF)(SN)", datasheet="https://www.jst-mfg.com/product/pdf/eng/ePH.pdf",
     desc="JST PH 2-pin 2.0 mm SMD right-angle battery connector, pin 1 = GND, pin 2 = + (Adafruit/SparkFun)")

# ~CHG only sinks while USB is present, so an anode on VBUS leaks nothing from the battery
part(S, "D2", "Device:LED", "red", "LED_SMD:LED_0603_1608Metric", 271.78, 147.32,
     {"1": "CHG_LED_K", "2": "VBUS"}, rot=90,
     mfr="Lite-On", mpn="LTST-C191KRKT",
     datasheet="https://optoelectronics.liteon.com/upload/download/DS22-2000-109/LTST-C191KRKT.pdf",
     desc="Red LED 0603, charge status")
R(S, "R6", "1 kΩ", 271.78, 167.64, "CHG_LED_K", "CHG_N")

# 3.3 V LDO
part(S, "U6", "Regulator_Linear:TLV75733PDBV", "TLV75733PDBVR", "Package_TO_SOT_SMD:SOT-23-5",
     91.44, 218.44, {"1": "VSYS", "3": "3V3_EN", "2": "GND", "5": "+3V3", "4": "NC"},
     mfr="Texas Instruments", mpn="TLV75733PDBVR", datasheet="https://www.ti.com/lit/ds/symlink/tlv757p.pdf",
     desc="3.3 V 1 A LDO with active discharge")
C(S, "C4", "10 µF", 50.8, 223.52, "VSYS")
R(S, "R9", "100 kΩ", 38.1, 223.52, "VSYS", "3V3_EN")
C(S, "C5", "10 µF", 132.08, 223.52, "+3V3")
C(S, "C6", "100 nF", 142.24, 223.52, "+3V3")

# battery and VBUS sensing
R(S, "R10", "100 kΩ", 205.74, 213.36, "VBAT", "VBAT_SENSE")
R(S, "R11", "100 kΩ", 205.74, 236.22, "VBAT_SENSE", "GND")
C(S, "C7", "100 nF", 223.52, 236.22, "VBAT_SENSE")
R(S, "R12", "68 kΩ", 180.34, 213.36, "VBUS", "VBUS_SENSE")
R(S, "R13", "100 kΩ", 180.34, 236.22, "VBUS_SENSE", "GND")

# ---------------------------------------------------------------- mcu
S = "mcu"
U1 = {"@IOVDD": "+3V3", "@DVDD": "+1V1", "46": "VREG_AVDD", "47": "GND", "48": "VREG_LX", "49": "+3V3",
      "50": "+1V1", "44": "+3V3", "53": "+3V3", "54": "+3V3", "61": "GND",
      "21": "XIN", "22": "XOUT", "24": "SWCLK", "25": "SWDIO", "26": "RUN",
      "51": "USB_DM_MCU", "52": "USB_DP_MCU",
      "55": "QSPI_SD3", "56": "QSPI_SCLK", "57": "QSPI_SD0", "58": "QSPI_SD2", "59": "QSPI_SD1", "60": "QSPI_SS"}
GPIO = {0: "GPIO0", 1: "GPIO1", 2: "GPIO2", 3: "GPIO3", 4: "I2C_SDA", 5: "I2C_SCL", 6: "GPIO6",
        7: "GPIO7", 8: "PSRAM_CS", 9: "SD_DET", 10: "SD_CLK", 11: "SD_CMD", 12: "SD_D0", 13: "SD_D1",
        14: "SD_D2", 15: "SD_D3", 16: "GPIO16", 17: "GPIO17", 18: "GPIO18", 19: "GPIO19", 20: "GPIO20",
        21: "GPIO21", 22: "LED_DIN", 23: "WL_ON", 24: "WL_D", 25: "WL_CS", 26: "GPIO26", 27: "GPIO27",
        28: "VBAT_SENSE", 29: "WL_CLK"}
GPIO_PIN = {0: 2, 1: 3, 2: 4, 3: 5, 4: 7, 5: 8, 6: 9, 7: 10, 8: 12, 9: 13, 10: 14, 11: 15, 12: 16, 13: 17,
            14: 18, 15: 19, 16: 27, 17: 28, 18: 29, 19: 31, 20: 32, 21: 33, 22: 34, 23: 35, 24: 36, 25: 37,
            26: 40, 27: 41, 28: 42, 29: 43}
for g, n in GPIO.items():
    U1[str(GPIO_PIN[g])] = n
part(S, "U1", "MCU_RaspberryPi:RP2350A", "RP2350A", "Package_DFN_QFN:QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm",
     190.5, 144.78, U1, mfr="Raspberry Pi", mpn="SC1509-A4",
     datasheet="https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf",
     desc="RP2350A dual Cortex-M33/Hazard3 MCU, QFN-60, no internal flash")
for i in range(8):
    C(S, f"C{10 + i}", "100 nF", 40.64 + 10.16 * i, 58.42, "+3V3")
C(S, "C18", "10 µF", 121.92, 58.42, "+3V3")
for i in range(3):
    C(S, f"C{19 + i}", "100 nF", 40.64 + 10.16 * i, 99.06, "+1V1")
# core regulator, per the RP2350 hardware design guide
C(S, "C22", "4.7 µF", 76.2, 99.06, "+3V3")
part(S, "L1", "Device:L", "3.3 µH", "Inductor_SMD:L_Abracon_AOTA-B201610S", 91.44, 99.06,
     {"1": "VREG_LX", "2": "+1V1"}, mfr="Abracon", mpn="AOTA-B201610S3R3-101-T",
     datasheet="https://abracon.com/Magnetics/power/AOTA-B201610S.pdf",
     desc="3.3 µH 2016 power inductor with polarity mark (RP2350 core regulator)")
C(S, "C23", "4.7 µF", 104.14, 99.06, "+1V1")
R(S, "R20", "33 Ω", 116.84, 99.06, "+3V3", "VREG_AVDD")
C(S, "C24", "4.7 µF", 129.54, 99.06, "VREG_AVDD")
# second VOUT cap at DVDD pin 23, away from LX (RP2350 datasheet 6.3.8.1)
C(S, "C29", "4.7 µF", 144.78, 99.06, "+1V1")
# crystal
part(S, "Y1", "Device:Crystal_GND24", "12 MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
     71.12, 175.26, {"1": "XIN", "3": "XTAL_O", "2": "GND", "4": "GND"},
     mfr="Abracon", mpn="ABM8-272-T3", datasheet="https://abracon.com/Resonators/ABM8-272-T3.pdf",
     desc="12 MHz crystal, 10 pF, 30 ppm, 3.2x2.5 mm")
C(S, "C25", "15 pF", 58.42, 193.04, "XIN")
C(S, "C26", "15 pF", 83.82, 193.04, "XTAL_O")
R(S, "R21", "1 kΩ", 101.6, 175.26, "XTAL_O", "XOUT", rot=90)
# USB series termination close to RP2350
R(S, "R22", "27 Ω", 66.04, 228.6, "USB_DP", "USB_DP_MCU", rot=90)
R(S, "R23", "27 Ω", 66.04, 243.84, "USB_DM", "USB_DM_MCU", rot=90)
# flash + PSRAM on the QSPI bus
part(S, "U2", "Memory_Flash:W25Q128JVS", "W25Q128JVSIQ", "Package_SO:SOIC-8_5.3x5.3mm_P1.27mm",
     325.12, 96.52, {"1": "QSPI_SS", "2": "QSPI_SD1", "3": "QSPI_SD2", "4": "GND", "5": "QSPI_SD0",
                     "6": "QSPI_SCLK", "7": "QSPI_SD3", "8": "+3V3"},
     mfr="Winbond", mpn="W25Q128JVSIQ",
     datasheet="https://www.winbond.com/hq/support/documentation/levelOne.jsp?__locale=en&DocNo=DA00-W25Q128JV",
     desc="128 Mbit QSPI NOR flash")
C(S, "C27", "100 nF", 360.68, 81.28, "+3V3")
part(S, "U3", "Memory_RAM:APS6404L-3SQRx-SN", "APS6404L-3SQR-SN", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     325.12, 160.02, {"1": "PSRAM_CS", "2": "QSPI_SD1", "3": "QSPI_SD2", "4": "GND", "5": "QSPI_SD0",
                      "6": "QSPI_SCLK", "7": "QSPI_SD3", "8": "+3V3"},
     mfr="AP Memory", mpn="APS6404L-3SQR-SN",
     datasheet="https://www.apmemory.com/wp-content/uploads/APM_PSRAM_QSPI_APS6404L-3SQR-v2.3-PKG.pdf",
     desc="64 Mbit QSPI PSRAM, 3.3 V")
C(S, "C28", "100 nF", 360.68, 142.24, "+3V3")
R(S, "R24", "2.7 kΩ", 287.02, 144.78, "+3V3", "PSRAM_CS")
# BOOTSEL and RUN buttons
R(S, "R25", "1 kΩ", 287.02, 228.6, "QSPI_SS", "BOOT_SW", rot=90)
part(S, "SW1", "Switch:SW_Push", "BOOTSEL", "Button_Switch_SMD:SW_SPST_PTS810", 314.96, 228.6,
     {"1": "BOOT_SW", "2": "GND"}, mfr="C&K", mpn="PTS810SJM250SMTRLFS",
     datasheet="https://www.ckswitches.com/media/1476/pts810.pdf", desc="SMD tactile switch 4.2x3.2 mm")
part(S, "SW2", "Switch:SW_Push", "RESET", "Button_Switch_SMD:SW_SPST_PTS810", 314.96, 251.46,
     {"1": "RUN", "2": "GND"}, mfr="C&K", mpn="PTS810SJM250SMTRLFS",
     datasheet="https://www.ckswitches.com/media/1476/pts810.pdf", desc="SMD tactile switch 4.2x3.2 mm")

# ---------------------------------------------------------------- wireless
S = "wireless"
part(S, "U4", "rp2350_dev:RMC20452T", "RMC20452T", "RF_Module:RMC20452T", 177.8, 132.08,
     {"3": "WL_CLK", "5": "WL_D", "6": "WL_DOUT", "9": "WL_CS", "10": "WL_IRQ", "12": "WL_ON",
      "13": "WL_ON", "8": "NC", "18": "NC", "17": "VBUS_SENSE", "2": "NC", "19": "NC", "20": "NC",
      "16": "VSYS", "14": "+3V3", "@GND": "GND"},
     mfr="Raspberry Pi", mpn="RMC20452T", datasheet="https://datasheets.raspberrypi.com/rm2/rm2-datasheet.pdf",
     desc="Raspberry Pi Radio Module 2: CYW43439 Wi-Fi 4 + Bluetooth 5.2")
R(S, "R30", "470 Ω", 127.0, 129.54, "WL_D", "WL_DOUT", rot=90)
R(S, "R31", "10 kΩ", 127.0, 134.62, "WL_D", "WL_IRQ", rot=90)
C(S, "C30", "10 µF", 223.52, 93.98, "VSYS")
C(S, "C31", "100 nF", 233.68, 93.98, "VSYS")
C(S, "C32", "100 nF", 243.84, 93.98, "+3V3")

# ---------------------------------------------------------------- io
S = "io"
part(S, "J2", "Connector:Micro_SD_Card_Det2", "microSD", "Connector_Card:microSD_HC_Molex_104031-0811",
     101.6, 132.08, {"1": "SD_D2", "2": "SD_D3", "3": "SD_CMD", "4": "+3V3", "5": "SD_CLK", "6": "GND",
                     "7": "SD_D0", "8": "SD_D1", "9": "SD_DET", "10": "GND", "SH": "GND"},
     mfr="Molex", mpn="1040310811", datasheet="https://www.molex.com/pdm_docs/sd/1040310811_sd.pdf",
     desc="microSD push-pull socket with card detect")
for i, (net, x) in enumerate([("SD_D2", 30.48), ("SD_D3", 38.1), ("SD_CMD", 45.72), ("SD_D0", 53.34),
                              ("SD_D1", 60.96), ("SD_DET", 68.58)]):
    R(S, f"R{40 + i}", "10 kΩ", x, 66.04, "+3V3", net)
C(S, "C40", "10 µF", 40.64, 190.5, "+3V3")
C(S, "C41", "100 nF", 50.8, 190.5, "+3V3")

part(S, "J3", "Connector_Generic_MountingPin:Conn_01x04_MountingPin", "Qwiic",
     "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal", 236.22, 81.28,
     {"1": "GND", "2": "+3V3", "3": "I2C_SDA", "4": "I2C_SCL", "MP": "NC"},
     mfr="JST", mpn="SM04B-SRSS-TB(LF)(SN)", datasheet="https://www.jst-mfg.com/product/pdf/eng/eSH.pdf",
     desc="Qwiic / STEMMA QT 4-pin JST SH 1.0 mm right-angle")
R(S, "R46", "4.7 kΩ", 193.04, 66.04, "+3V3", "I2C_SDA")
R(S, "R47", "4.7 kΩ", 203.2, 66.04, "+3V3", "I2C_SCL")

part(S, "D1", "LED:WS2812B-2020", "WS2812C-2020-V6", "LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm",
     218.44, 162.56, {"4": "+3V3", "2": "GND", "3": "LED_DIN", "1": "NC"},
     mfr="Worldsemi", mpn="WS2812C-2020-V6", datasheet="https://www.world-semi.com/products/ws2812c-2020-v6.html",
     desc="Addressable RGB LED 2020, VDD 3.3-5.3 V")
C(S, "C42", "100 nF", 193.04, 162.56, "+3V3")

HDR = "Connector_PinHeader_2.54mm:PinHeader_1x15_P2.54mm_Vertical"
# Header order follows the RP2350 pin sides at their board position, to keep the escape routes short
LEFT = ["GND", "GPIO26", "GPIO27", "+3V3", "GND", "GPIO0", "GPIO1", "GPIO2", "GPIO3", "I2C_SDA", "I2C_SCL",
        "GPIO6", "GPIO7", "3V3_EN", "GND"]
RIGHT = ["GND", "GPIO21", "GPIO20", "GPIO19", "GPIO18", "GPIO17", "GPIO16", "SWDIO", "SWCLK", "RUN",
         "+3V3", "VBAT", "VSYS", "VBUS", "GND"]
part(S, "J5", "Connector_Generic:Conn_01x15", "Header L", HDR, 312.42, 134.62,
     {str(i + 1): n for i, n in enumerate(LEFT)}, in_bom=False, dnp=True,
     desc="0.1 in header pads, left edge (not populated)")
part(S, "J6", "Connector_Generic:Conn_01x15", "Header R", HDR, 368.3, 134.62,
     {str(i + 1): n for i, n in enumerate(RIGHT)}, in_bom=False, dnp=True,
     desc="0.1 in header pads, right edge (not populated)")
for i, x in enumerate([304.8, 320.04, 335.28]):
    part(S, f"FID{i + 1}", "Mechanical:Fiducial", "Fiducial", "Fiducial:Fiducial_1mm_Mask2mm", x, 238.76, {},
         in_bom=False, desc="Assembly fiducial")

SHEET_TITLES = {
    "power": "Power: USB-C, LiPo charger with power path, 3.3 V LDO, sensing",
    "mcu": "RP2350A, core regulator, crystal, QSPI flash + PSRAM, buttons",
    "wireless": "Wi-Fi / Bluetooth LE: Raspberry Pi RM2 (CYW43439)",
    "io": "microSD, Qwiic, RGB LED, 0.1 in headers",
}

NOTES = {
    "power": [
        "USB-C sink: 5.1 kΩ Rd on CC1/CC2. BQ24074 EN1 = VSYS, EN2 = GND: USB500 input current limit.",
        "Charge current = 890 AΩ / R4 = 330 mA. TS has a fixed 10 kΩ (no NTC). Default safety timers, 10 % termination.",
        "VSYS = BQ24074 OUT: 4.4 V regulated from USB, VBAT on battery. Pull 3V3_EN low to switch 3.3 V off.",
        "VBAT_SENSE = VBAT / 2 to GPIO28 (ADC2). VBUS_SENSE = 0.595 x VBUS to RM2 WL_GPIO2, as on Pico W.",
        "Charge LED runs from VBUS. Header VSYS and +3V3 are outputs only: VSYS connects straight to the cell.",
    ],
    "mcu": [
        "Core regulator, crystal, BOOTSEL and USB parts follow Raspberry Pi 'Hardware design with RP2350'.",
        "PSRAM chip select on GPIO8 (XIP_CS1n, as Adafruit Feather RP2350) with a 2.7 kΩ pull-up against the reset pull-down.",
        "GPIO0/1 stay free for the default UART0 of pico2_w builds.",
    ],
    "wireless": [
        "Pins match Pico 2 W: GPIO23 WL_ON, GPIO24 data/IRQ, GPIO25 CS, GPIO29 CLK, so the pico2_w CYW43 driver works.",
        "RM2 VIN on VSYS (3.0-4.4 V) keeps TX peaks off the LDO, as Pico W does. WL_GPIO2 reads VBUS.",
    ],
    "io": [
        "microSD wired for SPI1 (CLK GPIO10, MOSI/CMD GPIO11, MISO/D0 GPIO12, CS/D3 GPIO15) and 4-bit PIO SDIO (D0-D3 = GPIO12-15).",
        "Qwiic on I2C0: SDA GPIO4, SCL GPIO5 (Pico SDK defaults). RGB LED data on GPIO22. Header pads are not populated.",
    ],
}
