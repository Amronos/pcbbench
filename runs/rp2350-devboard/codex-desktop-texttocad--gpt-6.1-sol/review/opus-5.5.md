# opus-5.5's review

## Final message

I wrote [review.json](review.json) with 7 findings. Two are major and five are minor. I found no fatal faults.

The two major problems are both power traces too thin for the 1.5 A you set for the charger output and battery path:

| Area | Severity | Refs / net | Problem |
|---|---|---|---|
| routing | major | J2→U4, `VBAT` | The battery path is a 0.15 mm trace. About 9 mm of it runs on In1.Cu, which is only 17.5 µm (0.5 oz) copper. It goes through 3 vias and only widens to 0.3 mm at U4's BAT pads. |
| routing | major | U4→U5, `VSYS` | The charger output to the buck-boost input is a 0.3 mm trace, about 15 mm long, with single 0.3 mm-drill vias. By IPC-2221 that's roughly a 25 °C rise at 1.5 A. About 0.5 mm is needed for 10 °C. |
| layout | minor | U2, U3 | The flash is 9.7 mm and the PSRAM 11.9 mm from the QSPI pins. The PSRAM is wired after the flash, so QSPI_IO1 and QSPI_IO2 run 27–28 mm. |
| routing | minor | `QSPI_IO1`, `QSPI_IO0` | IO1 has 4 vias, two of them for a pointless 1.6 mm hop onto F.Cu. IO0 has 3 vias. |
| routing | minor | `USB_D+`, `USB_D-` | The two lines aren't routed as a pair. D- uses 4 vias. D+ detours around U8 and ends up 4.3 mm longer. |
| routing | minor | `SD_MOSI`, `SD_CS` | Each changes layer 5 times. SD_CLK covers the same distance with 2. |
| layout | minor | SW5 | The power switch is a side-actuated part (C&K datasheet), but its actuator ends 4.2 mm inside the board edge instead of reaching it. |

**Upgrade:** I upgraded all six schematics in place from format 20250114 to 20261106 (10.99). The board was already in the connector's format, so `kicad-cli pcb upgrade` left it unchanged. ERC and DRC both report 0 violations after the upgrade.

**What passed:**
- **Placement:** the parts listed in your brief are where they should be:
  - The antenna hangs off the top edge with nothing in front of it.
  - USB-C, the LiPo connector, Qwiic and microSD all open toward their edges.
  - The crystal is about 5 mm from XIN/XOUT, with short traces.
  - The charger and regulator sit together near the power input.
- **Fatal faults:** two subagents checked every part's pin mapping and footprint against its datasheet. All pads match the stock KiCad footprints. Board nets match the schematic. The custom TPS63070 footprint matches TI's land pattern. The feedback dividers give 3.30 V and 1.10 V. The ESP32 boot pins, UART crossover, SD-in-SPI and Qwiic pinouts are all correct.

**Left out:**
- Tactile buttons away from the edge, since they're pressed from above.
- VBUS at 0.3 mm, since its input current limit is set to about 0.5 A.

I deleted my scratch files and the `board.kicad_prl` that `kicad-cli` created. The folder now holds only the upgraded design and `review.json`.

## Subagent: You are helping review an RP2350 development board KiCad project in /home/ubuntu/review (files: board.kicad_pcb, *.kicad_sch, libraries/Atlas.pretty footprints, libraries/Atlas.kicad_sym, bom.csv). The board is already upgraded; DO NOT modify any project file. Write scratch files only under /home/ubuntu/review/scratch/. Read and write only in /home/ubuntu/review, the KiCad connector and its libraries ($SPROCKET_KICAD_LIBRARIES). Read datasheets on the web as needed. Nobody will answer questions.

I found no fatal faults in the power section. I checked every in-scope part against both the board/schematic files and the datasheets, and none of them stops the board from working or damages a part. The report is in `/home/ubuntu/review/scratch/other_power.md`.

Three part roles in the brief are wrong. The netlist shows:
- R5/R6 are not the buck-boost feedback divider. R5 (3.57k) sets the BQ24074 charge current (ISET) and R6 (3.24k) sets its input current limit (ILIM).
- R42/R43 are not a battery divider. R42 (312k, +3V3→MAIN_FB) and R43 (100k, MAIN_FB→GND) set the TPS63070 output.
- The battery divider is R10/R11 (470k/470k), buffered by U9. The VBUS divider is R12/R13 (1M/330k).

**How I checked**
- **Nets:** the schematic netlist matches the PCB pad nets. The only exceptions are the unconnected J2/J4 mounting pads.
- **Footprints:** every Atlas footprint that has a stock KiCad equivalent has the same pads as stock. The footprints placed on the board match the library, and no part is mirrored.
- **Copper:** each power net is one connected piece of copper, GND included.

**Checked and OK**

| Part | Result | Evidence |
|---|---|---|
| U5 TPS63070, custom footprint | Pad numbers and positions match the TI RNM0015A land pattern (datasheet p.39). | Pins 1–4 run down the left side, 5–8 along the bottom, 9–11 are the long bars on the right, 12–15 along the top. Positions match the drawing, including the bridged 7/8 and 12/13 pads. The board rotates the part 180°, which puts pin 1 at (18.15, 31.75). |
| U5 pin nets | Match the datasheet pin table (§6). | PS/SYNC and EN go to PWR_EN. PG goes to MAIN_PG with a 10k pull-up. VAUX has 100 nF. FB2 and VSEL are on GND, which the datasheet allows when unused. VOUT is +3V3, VIN is VSYS, L1/L2 go to the inductor. |
| U5 output | 3.3 V | 0.8 V × (1 + 312k/100k) = 3.296 V. The 1k series resistor on EN and PS/SYNC follows §8.4. The 1.0 µH inductor is within the allowed range. |
| U4 BQ24074 | All 16 pins plus the exposed pad match Fig. 7-2 / Table 7-1. | CE is on GND, so charging is on. EN1/EN2 go to GPIO16/17 with 100k pull-downs. TMR and ITERM are open, which gives the default timers and 10 % termination. |
| U4 resistors | Within the datasheet ranges (§8.3). | Charge current 890/3.57k = 249 mA. Input limit ≈ 0.47–0.50 A. VSYS stays at or below 4.5 V. |
| J1, R1/R2, F1 | OK | VBUS and GND pins are correct. Each CC pin has its own 5.1k to GND, so the board only gets 5 V. F1 sits between the connector and the rest of VBUS. |
| U8 USBLC6-2SC6 | Pinout matches the ST datasheet (DS4260). | Pin 1 D+, 2 GND, 3 D−, 5 VBUS after the fuse. Pins 4/6 are the internal duplicates of 3/1 and are left open. |
| U7 TLV75801P | SOT-23-5 pinout matches Fig. 4-2. | IN=+3V3, GND, EN=MAIN_PG, FB=CORE_FB, OUT=+1V1. |
| U7 divider | 1.10 V | R34 is the top resistor (+1V1→FB) and R35 the bottom (FB→GND). 0.55 V × (1 + 10k/10k) = 1.10 V, below the RP2350 core maximum of 1.21 V. |
| RP2350 core supply | Wired as the datasheet's external-supply circuit (p.410, Fig. 24). | VREG_FB is on GND and VREG_LX is open. The internal regulator's inputs are on 3V3. U7 is enabled by the 3V3 power-good, so the core comes up after the I/O supply. |
| U9 TLV9001IDBVR | Pinout matches Fig. 6-1. | Unity-gain buffer of VBAT/2 (at most 2.1 V), powered from 3V3, so the ADC0 pin stays at or below 3.3 V. With 3V3 off, input current is about 9 µA, far below the 10 mA limit. |
| VBUS_ADC (ADC1) | Stays below the ADC limit. | 5 V gives 1.24 V at the pin. With the power switch off and USB connected, the pin can only feed about 5 µA into the unpowered chip, which isn't a damage case. |
| U10 TPS22919 | Pinout matches the datasheet. | It switches VSYS to the WS2812 LED supply. All its pins stay at or below 4.5 V, under the 6 V maximum. |
| SW5 JS102011SAQN | Can't short VSYS to GND. | It only drives the 3V3 regulator and LED switch enables through 1k. It is a non-shorting type ("N" suffix), so VSYS and GND are never bridged when it moves. It does not disconnect the battery. |
| J2 JST PH 3-pin | Footprint numbering is correct. | Pin 1 VBAT, 2 GND, 3 NTC. There is no standard pin order for 3-pin battery packs with a thermistor, so I can't call this a fault. |
| U6 ESP32-C3 | Power pins OK. | Pin 1 is on +3V3 with 22 µF and 10 µF, pins 9 and 19 are GND. |
| Capacitor voltage ratings | All exceed their rail voltage. | |

**Not fatal, worth knowing**
- At power-up the charger limits USB input to 100 mA, because the pull-downs hold EN1/EN2 low. Firmware has to drive GPIO16/17 to raise the limit.
- The battery pack's wire order must match J2's pin order (VBAT, GND, NTC).

My scripts, the downloaded datasheets and page renders are in `scratch/`, next to the report.

## Subagent: You are helping review an RP2350 development board KiCad project in /home/ubuntu/review (files: board.kicad_pcb, *.kicad_sch, libraries/Atlas.pretty footprints, libraries/Atlas.kicad_sym, bom.csv). The board is already upgraded; DO NOT modify any project file. Write scratch files only under /home/ubuntu/review/scratch/. Read and write only in /home/ubuntu/review, the KiCad connector and its libraries ($SPROCKET_KICAD_LIBRARIES). Read datasheets on the web as needed. Nobody will answer questions.

I found no fatal faults in the digital/IO section. Every in-scope pin, net, footprint and boot pin matches the datasheets. The report is in `scratch/other_digital.md`; its content follows.

**How it was checked**
- **Footprints:** all 34 footprints in `libraries/Atlas.pretty` have the same pads as the stock KiCad 10 versions: numbers, positions, sizes and rotations. The board's footprints match those library files. Everything is on F.Cu at `scale 1 1`, so nothing is mirrored.
- **Nets:** the board's pad nets match the schematic netlist on all 432 pads. The only exceptions are the J2 and J4 mounting pads, which have no net in either file.
- **Fitting:** no part is marked DNP. Only test points, mounting holes and power flags are left out of the BOM.

**Checked and OK**

| Part | Checked against | Result |
|---|---|---|
| U1 RP2350A pins | Datasheet Tables 1674–1679, Fig. 2 | All GPIOs on the right pins. IOVDD (1, 11, 20, 30, 38, 45), USB_OTP_VDD (53) and QSPI_IOVDD (54) on +3V3. DVDD (6, 23, 39) on +1V1. ADC_AVDD (44) through FB1. Pad 61 on GND. XIN to Y1.1, XOUT through R17 1k to Y1.3. SWCLK 24, SWDIO 25, RUN 26 with a 10k pull-up. |
| U1 package | Datasheet top view | Pad 1 at (27.20, 45.45) and pad 60 at (26.55, 44.80) are side by side at one corner. Pads number counter-clockwise. Pad 61 is the 3.4 mm "reduced ePad" the datasheet shows. |
| U1 core regulator pins with U7 | §6.3.7, Fig. 24 (p. 409) | VREG_AVDD and VREG_VIN on +3V3, PGND on GND, LX unconnected, FB on GND. This is exactly Fig. 24. U7's R34/R35 (10k/10k, 0.55 V feedback) gives 1.1 V. |
| USB | Table 1678 | Pin 52 → R3 27Ω → J1 A6/B6 (D+). Pin 51 → R4 27Ω → J1 A7/B7 (D−). |
| U2 W25Q32JV / U3 APS6404L | W25Q32JV §3.3, APS6404L pin table | All four data lines go to the same pins on both chips (SD0→pin 5, SD1→2, SD2→3, SD3→7). Clock goes through R16 33Ω to pin 6. QSPI_SS → U2.1 and GPIO0 → U3.1, each with a 10k pull-up. Pins number counter-clockwise. Package sizes are right (SS 208 mil, SN 150 mil). |
| PSRAM CS on GPIO0 | RP2350 Table 3 | GPIO0 function F9 is the second memory chip select (QMI CS1n). |
| U6 ESP32-C3-WROOM-02 | Module datasheet Table 3-1, §3.1 | All 19 pads match. Pads 1–9 run down the left side, 10–18 up the right. |
| U6 boot pins | Table 4-3 | IO9, IO8 and IO2 each have a 10k pull-up to 3.3 V, so it boots from flash. GP19 can pull IO9 low through 1k for download mode. |
| U6 EN | "Do not leave EN floating" | EN has a 10k pull-down, and GP18 drives it high through 1k (about 3.0 V; the high threshold is 2.475 V). The schematic note says the pull-down is intentional. |
| UART to the ESP32 | RP2350 Table 3; ESP-AT C3 default pins | GP20 is UART1 TX → ESP IO6 (RX). ESP IO7 (TX) → GP21, UART1 RX. ESP IO4 (RTS) → GP22, UART1 CTS. GP23, UART1 RTS → ESP IO5 (CTS). Every line is crossed correctly. |
| J3 microSD | Hirose pinout; RP2350 SPI1 | CS → GP13 (CSn), MOSI → GP11 (TX), VDD on pin 4, CLK → GP10 (SCK), GND on pin 6, MISO → GP12 (RX). All card lines have 47k pull-ups. Card detect: pin 9 → GP15 with a 10k pull-up, pin 10 to GND. |
| J4 Qwiic | Qwiic pin order; RP2350 I2C0 | Pins are GND, 3.3 V, SDA (GP4), SCL (GP5), with 4.7k pull-ups. |
| D1 WS2812B-2020-V6 | V6 datasheet | Pin 1 DOUT, 2 GND, 3 DIN (from GP14 through 330Ω), 4 power from VSYS through U10. Its input threshold is 0.55 × VDD, so 2.9 V even at 5.3 V, which 3.3 V logic clears. |
| Y1 crystal | ABM8 pinout | Pins 1 and 3 go to the RP2350 crystal pins, 2 and 4 to GND. |
| J6 SWD header | Cortex 10-pin pinout | 3.3 V, SWDIO, GND, SWCLK, GND, NC×3, GND, RUN, all on the right pins. |
| J5, J7 | Wrong nets or shorted rails | None found. |
| SW1–SW4 | TL3342 drawing P010632 | Pads with the same number are the pairs joined inside the switch, so it only closes between pads 1 and 2. SW1 RUN, SW2 BOOT (through 1k to QSPI_SS), SW3 ESP boot and SW4 ESP enable each switch to GND. None shorts a power rail. |

**Not fatal, but firmware has to handle them**
- The ESP32-C3 stays off until RP2350 firmware drives GP18 high.
- The RP2350's internal regulator still starts with FB on GND and LX unconnected. Firmware should turn it off (set VREG.HIZ = 1) to save about 400 µA. The datasheet calls leaving it on "a safe mode of operation".

The helper scripts I wrote and the downloaded datasheets are also in `scratch/`.
