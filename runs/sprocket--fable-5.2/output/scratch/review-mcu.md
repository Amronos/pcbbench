# MCU core review: RP2350A dev board

Source: `scratch/rp2350-devboard.net`, cross-checked against the RP2350 datasheet (RP-008373-DS-3), "Hardware design with RP2350" (`scratch/ds/hw.txt`), Winbond W25Q128JV rev I, AP Memory APS6404L-3SQR v2.3 and Abracon ABM8-272-T3 drawing 456603.

No must-fix findings. Four should-fix items and five notes.

## Findings

| # | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| 1 | Should fix | PSRAM chip-select pull-up R19 (10 kΩ) is too weak against the RP2350 reset pull-down on GPIO8. | `/PSRAM_CS`: R19.2, U1.12, U3.1. GPIO8 reset state is pull-down, RPD 36 to 113 kΩ at 3.3 V (DS table 1683). The divider gives CE# = 2.58 V worst case, 3.03 V best case. APS6404L needs VIH ≥ VDD − 0.4 V = 2.9 V (DC table) and CE# within 200 mV of VDD during power-up (section 7). 10 kΩ misses the 200 mV rule at every pull-down value and misses VIH at the low end. | Change R19 to 2.2 kΩ (worst case drop 0.19 V). Firmware should also disable the GPIO8 pad pull-down before using XIP_CS1. Raspberry Pi's reference also uses 10 kΩ, so this is a margin issue, not a known failure. |
| 2 | Should fix | PSRAM decoupling is below the datasheet value. | U3.8 has C23 = 100 nF only. APS6404L section 14.3 asks for a low-ESR 1 µF at VDD, with 100 nF optional. | Change C23 to 1 µF 0402, or add 1 µF next to it. |
| 3 | Should fix | L1, Y1 and U1 carry no manufacturer part number. | L1 value "3.3 µH", Y1 value "12 MHz", U1 value "RP2350A", no MPN fields in the schematic. The regulator is only validated with the polarised Abracon AOTA-B201610S3R3-101-T, and the 15 pF / 1 kΩ crystal network is only valid for the 10 pF ABM8-272-T3. | Add MPN fields: `AOTA-B201610S3R3-101-T`, `ABM8-272-T3`, and the A4 stepping order code for U1 (`RP2350A0A4`, confirm with the distributor). |
| 4 | Should fix | GP26 and GP27 on header J6 are not fault tolerant and not 5 V tolerant, with VBUS and +BATT on the same header. | J6.5 = `/GP26_A0` (U1.40), J6.4 = `/GP27_A1` (U1.41). DS table 1674 lists GPIO26 to 29 on QFN-60 as "Digital IO / Analogue" (standard pad). Abs max is IOVDD + 0.5 V (table 1680), so 0.5 V when 3V3 is off. Driving them with 3V3 off back-powers the 3V3 rail through the pad ESD diode. J6.1 = VBUS, J6.2 = +BATT, J6.3 = GND. | Mark A0/A1 on silkscreen and in the docs as "3.3 V max, do not drive when 3V3 is off". If the board must survive careless use, add 1 kΩ series resistors on these two pins. |
| 5 | Note | The battery divider feeds GPIO28 while 3V3 is off. | `+BATT` → R13 100 kΩ → `/VBAT_SENSE` (U1.42, C30 100 nF) → R14 100 kΩ → GND. With a battery fitted and the LDO disabled through `/EN` (J7.2), IOVDD = 0 V and the pin clamps about one diode drop above the rail. Current is limited to 4.2 V / 100 kΩ = 42 µA. This sits right at the IOVDD + 0.5 V abs max and drains about 21 to 42 µA permanently. Powered, the pin sees 2.1 V max, below IOVDD as section 12.4.3 requires. | Acceptable as is because of the 100 kΩ current limit. For strict compliance and zero standby drain, switch the divider top with a P-FET enabled from 3V3. |
| 6 | Note | QSPI_SS has no external pull-up and no footprint for one. | `/QSPI_SS`: R17.1, U1.60, U2.1 only. W25Q128JV requires /CS to track VCC at power-up (section 6.1). The pad has an internal pull-up after reset (table 1675). The reference design keeps a DNF 10 kΩ (R1) for other flash parts. | Optional: add a DNF 10 kΩ 0402 to 3V3 near U2. Not needed for W25Q128JV per Raspberry Pi. |
| 7 | Note | ADC_AVDD is tied straight to +3V3 with 100 nF. | U1.44 on `+3V3`, C19 100 nF. DS section 6.2 allows sharing IOVDD and asks for 100 nF. ADC noise will follow the 3V3 rail, which also feeds the RM2 radio and the WS2812. | Fine for battery monitoring. If A0/A1 accuracy matters, add a ferrite or 10 Ω plus 1 µF filter on pin 44. |
| 8 | Note | E9 status. | E9 affects stepping A2 only, fixed in A3 (DS appendix C.2.1, D.5.1). A4 has no hardware change versus A3, only bootrom changes (C.3.1). No circuit on this board relies on an internal pull-down: PSRAM_CS, SD_CMD/DAT, I2C and RUN have external pull-ups, WL_ON is driven and the CYW43439 has its own 200 kΩ pull-down. | Order A4 parts. If A2 parts are ever fitted, VBAT_SENSE needs the pad input disabled (`adc_gpio_init`), because its 50 kΩ source at about 2 V sits in the leakage region, and header users need external pull-downs of 8.2 kΩ or less. |
| 9 | Note | Fault-tolerant header GPIOs have a 3.63 V limit when unpowered. | GP0 to GP7, GP16 to GP22 and RUN are FT pads: 5.5 V max with IOVDD at 3.3 V, 3.63 V max with IOVDD at 0 V (table 1680). GP4/GP5 also back-feed 3V3 through R22/R23 (2.2 kΩ) if driven while off. | Document "5 V signals only while 3V3 is on". No circuit change. |

Not covered: the regulator PCB layout. The board has no routed tracks yet, and Raspberry Pi states the layout must copy Pico 2 (DS section 6.3.8). J4's physical pin order against a Debug Probe cable is covered in `scratch/jst-polarity.md`, not here.

## Checked and found correct

- U1 pinout: all 60 pins plus pad 61 match DS figure 152 and tables 1674 to 1679. No pin is unconnected.
- U2 W25Q128JVPIQ WSON-8: 1 /CS, 2 IO1, 3 IO2, 4 GND, 5 IO0, 6 CLK, 7 IO3, 8 VCC, pad 9 to GND. Matches Winbond section 3.2/3.3.
- U3 APS6404L SOP-8: 1 CE#, 2 SIO1, 3 SIO2, 4 VSS, 5 SIO0, 6 SCLK, 7 SIO3, 8 VDD. Matches. IO0 to IO3 pair correctly between U1, U2 and U3 (SD0 57, SD1 59, SD2 58, SD3 55).
- GPIO8 is a valid XIP_CS1n pin on RP2350A (function F9 on GPIO0, 8, 19, 47).
- Regulator: VREG_VIN (49) on 3V3 with C6 4.7 µF, VREG_LX (48) to L1.2, L1.1 (dot) to +1V1 with C7 4.7 µF, VREG_FB (50) on +1V1, VREG_PGND (47) to GND, VREG_AVDD (46) through R15 33 Ω with C8 4.7 µF. Values and inductor polarity match DS figure 22 and the design guide figure 4.
- Decoupling: 100 nF per IOVDD pin (C9 to C14), per DVDD pin (C15 to C17), C18 shared by QSPI_IOVDD and USB_OTP_VDD as in the reference, C19 on ADC_AVDD, C22 on U2.
- Crystal: Y1 pins 1 and 3 active, 2 and 4 to GND. XIN (21) direct, XOUT (22) through R16 1 kΩ with C21 on the crystal side. Load = 15 pF / 2 + about 3 pF stray = 10.5 pF against CL = 10 pF. Same values as the reference.
- RUN (26): R18 10 kΩ pull-up, SW2 to GND, also on J7.3.
- BOOT: SW1 pulls QSPI_SS to GND through R17 1 kΩ, same as reference R6. Against the 32 to 86 kΩ internal pull-up this gives about 0.1 V, and the flash can still be driven with the button held.
- Flash IO2/IO3: the IQ variant has QE = 1 fixed, so /WP and /HOLD are disabled. The QSPI_SD2 and SD3 pads also default to pull-up.
- USB: connector D+ → R3 27 Ω → USB_DP (52), D− → R4 27 Ω → USB_DM (51).
- SWD J4: 1 SWCLK, 2 GND, 3 SWDIO, the Raspberry Pi debug connector order. Both pads have internal pull-ups.
- Supplies: all 3.3 V pins share one rail, so there is no sequencing or partial-power case inside U1. DVDD only comes from the on-chip regulator.
- Headers: J6 = 1 VBUS, 2 +BATT, 3 GND, 4 GP27, 5 GP26, 6 GP22, 7 GP21, 8 GP20, 9 GP19, 10 GP18, 11 GP17, 12 GP16. J7 = 1 3V3, 2 EN, 3 RUN, 4 GND, 5 GP0, 6 GP1, 7 GP2, 8 GP3, 9 GP4 (SDA), 10 GP5 (SCL), 11 GP6, 12 GP7.
