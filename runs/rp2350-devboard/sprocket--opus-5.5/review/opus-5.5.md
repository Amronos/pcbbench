# opus-5.5's review

## Final message

I wrote [review.json](review.json) with 7 findings: 4 major and 3 minor. None are fatal, so I filed nothing under `other`.

The upgrade made no changes. `kicad-cli pcb upgrade` and `sch upgrade` reported every file as already in the connector's 10.99 format (board 20261031, schematics 20261106). Running the upgrade created a `board.kicad_prl` settings file, which I deleted, so the design files are byte-for-byte untouched.

| # | Area | Severity | Finding |
|---|---|---|---|
| 1 | routing | major | `QSPI_SD3` from U1 pin 55 to U2 pin 7 is 65.5 mm with 8 vias, against 9.3 mm direct. It loops out to the left edge and back under SW1. |
| 2 | routing | minor | `QSPI_SS` (20.8 mm and 4 vias, against 4.6 mm direct), `QSPI_SD0` to the PSRAM and `PSRAM_CS` all take indirect routes. |
| 3 | routing | major | `SD_CLK` (87 mm) and `SD_D3` (98 mm) run down the far left edge, although the microSD socket is at the bottom right. |
| 4 | routing | major | The battery current from U5's BAT pins passes through a 0.15 mm track at (106.4, 99.1) to (105.8, 99.1), then 0.4 mm on an inner layer. That is too narrow for 1.5 A. |
| 5 | routing | major | USB D+ from J1 contact A6 loops 18 mm under the receptacle before joining B6, which leaves an 18 mm stub in one plug orientation. |
| 6 | routing | minor | The USB pair zigzags through the power stage, and D+ passes 0.23 mm from the switch-node pad of the buck-boost inductor L2. |
| 7 | layout | minor | The charger U5 and the 3.3 V regulator U6 sit about 24 mm from the USB-C connector, so VBUS runs 34 mm with 7 vias. |

**Checked with no findings:**
- **Placement:**
  - The flash, PSRAM and crystal are 4 to 9 mm from their pins. Those traces are short and have no vias.
  - The USB-C, battery, Qwiic and microSD connectors all open off a board edge. The microSD card sticks out 3.45 mm past the bottom edge, which is how Molex draws it.
  - The Wi-Fi module's antenna end is flush with the top edge, and no copper or parts sit in front of it.
- **Copper:** DRC finds no unconnected items, and the copper-hygiene check finds no stubs.
- **Pins and footprints:** three subagents checked these against the manufacturer datasheets and found no fatal faults. This covered:
  - every chip pin mapping, the charger mode straps, and both battery MOSFETs;
  - the pin order of the LED, USB-C, microSD and Qwiic connectors;
  - every custom footprint.

**Left out:**
- SW1 and SW2 sit about 8 mm inside the right edge. They are top-pressed buttons a user can still reach, so I didn't report them.
- `VSYS` leaves the charger's OUT pins on 0.25 mm track for about 1 mm. That is a neck-down at the 0.5 mm-pitch pins, so I didn't report it either.

My working files are in `scratch/` inside this folder: the extracted netlist, pad and track dumps, the path scripts, plots and the subagents' notes. Delete it if you only want `review.json`.

## Subagent: If you spawn subagents, every `spawn_subagent` call must set `model` to opus-5.5 and `reasoning` to high. Put this same rule, word for word, in every subagent's prompt.

I found no fatal, major or minor problems with U7 (RM2). I checked the footprint, every pin net, the host wiring and the antenna placement against the official RM2 datasheet, release 7 dated 20/02/2026: https://datasheets.raspberrypi.com/rm2/rm2-datasheet.pdf

**Confirmed problems**

None.

**Checked and correct**

**1. Footprint vs datasheet Fig. 4 (p.7), Fig. 6 (p.9) and Fig. 7 (p.10)**

The footprint is not mirrored or rotated, and it is on F.Cu.

| Item | Datasheet | `RMC20452T.kicad_mod` / board |
|---|---|---|
| Module body | 14.5 × 16.5 mm | F.Fab ±7.25 × ±8.25 mm, so the absolute body is x 106.75–121.25, y 50.00–66.50 |
| Pads | 21 castellated pads, 1.0 × 2.0 mm, 1.5 mm pitch, 0.5 mm overhang past the body edge | 2.0 × 1.0 mm, 1.5 mm pitch, centres 0.5 mm inside the edge, so 0.5 mm sticks out |
| Side pins 7 and 15 | 1.8 mm from the bottom edge | y = +6.45, which is 1.8 mm from +8.25 |
| Bottom pins 8 and 14 | 2.75 mm from the side edges | x = ±4.5 |
| Numbering (top view) | Pin 1 top-left, counter-clockwise: 1–7 down the left, 8–14 along the bottom, 15–21 up the right | Pads 1–7 at x −6.75 going downward (abs 107.25, y 55.7→64.7); 8–14 at y +7.75 left to right (abs y 66.0, x 109.5→118.5); 15–21 at x +6.75 going upward. Pin 1 is at the top-left (107.25, 55.70) |
| Antenna end | Above pins 1 and 21 | Toward −y |
| RF keepout | 35.5 mm wide, 13.5 mm past the module top, ending 5.0 mm below the module top | Zone ±17.75 × (−21.75…−3.25), all copper layers. Absolute 96.25–131.75 × 36.5–55.0 |

The board file uses the new `(transform (translate 114 58.25))` format, so the keepout coordinates stored inside the footprint are relative. The keepout therefore sits on the part, not off the board.

**2. Pin nets vs Table 2 (p.10), Table 1 in §1.3.2 (p.5) and §2.6 (p.11)**

| Pin | Function | Net | Matches |
|---|---|---|---|
| 1, 4, 7, 11, 15, 21 | GND | GND | ✓ |
| 2, 19, 20 | NC | unconnected | ✓ |
| 3 | gSPI SCLK | WL_CLK → U1.43 GPIO29 | ✓ |
| 5 | gSPI DI | WL_D → U1.36 GPIO24 | ✓ |
| 6 | gSPI DO | R19 470 Ω → WL_D | ✓ (470 Ω per Table 1) |
| 9 | gSPI CS | WL_CS → U1.37 GPIO25 | ✓ |
| 10 | nIRQ | R20 10 kΩ → WL_D | ✓ (10 kΩ per Table 1) |
| 12 / 13 | WL_ON / BT_ON | both on WL_ON → U1.35 GPIO23 | ✓ |
| 14 | VDDIO (3.3 V or 1.8 V) | +3V3 | ✓ |
| 16 | VIN (3.0–4.8 V; RF performance drops below 3.2 V) | +3V3 from the fixed 3.3 V TPS63001 | ✓ within rating |
| 8 | GPIO0 | unconnected | OK, optional |
| 17 | GPIO2 | VBUS divider, R22 100 kΩ / R23 150 kΩ | ✓ VBUS 5.0 V gives 3.0 V and 5.5 V gives 3.3 V, so it stays ≤ VDDIO. 3.3 V ±5% I/O VIH is 2.0 V (Table 4), so detection threshold ≈ 3.3 V |
| 18 | GPIO1 | PS_SYNC to U6 TPS63001 PS/SYNC, with R18 100 kΩ pulldown | ✓ Same use as Pico 2 W (§1.3.3 GPIO expansion: "SMPS power save") |

I also checked the RP2350A QFN-60 pin numbers against the RP2350 datasheet Fig. 2 (§1.2.1.1): pin 35 is GPIO23, 36 is GPIO24, 37 is GPIO25 and 43 is GPIO29. The symbol pin functions in `nets.txt` agree with Table 2 for all 21 pins.

**3. Placement**

- U7 sits at (114.0, 58.25), rotation 0. Its antenna end (body top at y = 50.00) is flush with the top board edge at y = 50, so the antenna points out of the board. The board corner arcs are well outside x 106.75–121.25.
- Nothing is in front of the antenna, because the area past y = 50 is off the board.
- No pad, track, arc or via from any other footprint has y < 57. The nearest parts are:
  - J5 pin 1 at (102.57, 60.16)
  - J6 pin 1 at (125.43, 60.16)
  - R23 at (122.6, 61.4)

  All three sit beside the module body, behind the keepout's lower edge at y = 55.0.
- No copper zone fill on any layer overlaps the RF keepout region. I checked this with shapely intersections of every zone fill against the keepout.

Scratch files, including the datasheet page renders and the U7 area render, are in `/home/ubuntu/review/scratch/sub_wireless/`.

## Subagent: If you spawn subagents, every `spawn_subagent` call must set `model` to opus-5.5 and `reasoning` to high. Put this same rule, word for word, in every subagent's prompt.

I found no fatal fault in any of the nine footprints. Every pad map, pin‑1 location, pitch and connector opening matches the manufacturer drawing.

I compared each library footprint pad by pad with the stock KiCad 10 footprint of the same name. D3, J2, J3, U5 and U6 have identical pads. L1 has the same pads plus a polarity dot. J1 and J4 are the stock footprints. I then checked the footprints against the manufacturer drawings below. Scratch renders and PDFs are in `scratch/sub_fp/`.

**Confirmed problems**

None at minor, major or fatal level.

**Checked and correct**

| Ref | Checked | Evidence |
|---|---|---|
| D3 WS2812B‑2020‑V6 | The pads are 0.7×0.7 mm at ±0.915/±0.55. That matches the 0.7 mm pads, 0.40 mm gap and 1.13 mm inner spacing. Rotating the datasheet top view by 180° gives the footprint order 1 DO top‑left, 2 GND bottom‑left, 3 DI bottom‑right, 4 VDD top‑right. Board pads: 1 (108.515,85.95) unconnected DOUT, 2 (108.515,84.85) GND, 3 (106.685,84.85) RGB_DIN, 4 (106.685,85.95) +3V3. VDD at 3.3 V is within the V6 range of 3.3–5.3 V. | Worldsemi WS2812B‑2020‑V6 datasheet p.2, "PCB Solder Pad" and "Pin Arrangement": https://file.thegioiic.com/upload/documents/1792377585_WS2812B-2020-V6.pdf |
| J2 S2B‑PH‑SM4‑TB | Signal pads are 1.0×3.5 mm at 2.0 mm pitch. The MP pads are 1.5×3.4 mm. The body outline is 7.9 mm wide by 6.0 mm deep, matching B = 7.9 and depth 6. Pin 1 is on the left when you look into the opening, as the drawing shows. The signal pads sit at x=107.95, so the opening faces −x. The front face is at x≈100.7, 0.7 mm inside the left edge. The cable enters from off the board. | JST ePH.pdf p.4, "Side entry type": https://www.jst-mfg.com/product/pdf/eng/ePH.pdf |
| J3 Molex 104031‑0811 | All 14 pads match the "Recommended PCB layout" rotated 180°. Details are below the table. | Molex SD‑104031‑001 sheet 1 (copy at https://www.limpulsion.fr/upload/docs/1040310811.PDF; Molex's own server timed out) |
| J4 SM04B‑SRSS‑TB (stock) | The signal pads sit at x=122.72 and the MP pads at x=126.595. The body front is at x≈127.3, 0.7 mm inside the right edge, so the cable enters from the right edge. The pin order is 1 GND, 2 +3V3, 3 SDA, 4 SCL, which is the Qwiic order. | Stock footprint, after JST eSH.pdf |
| J1 USB4105‑GF‑A (stock) | The footprint's "PCB Edge" line is at local y=+3.675, which lands on board y=128.54, the bottom edge exactly. That fits the drawing: the front slot centre is 2.60 mm from the PCB edge, and the board has 128.54−125.94 = 2.60. The shell front is flush with the edge and the opening faces off the board. The pins carry the right nets: CC1 on A5, CC2 on B5, D+ on A6/B6, D− on A7/B7, VBUS on A4/A9/B4/B9 and GND on A1/A12/B1/B12. | GCT USB4105 drawing, "Recommended PCB Layout": https://gct.co/files/drawings/usb4105.pdf |
| L2 DFE252012F | The pads are 0.8×2.0 mm at ±1.0. That is exactly Murata's pattern of 1.2 mm gap, 2.8 mm overall and 2.0 mm height. | Murata datasheet, "Recommended patterns": https://www.murata.com/~/media/webrenewal/products/inductor/chip/tokoproducts/wirewoundmetalalloychiptype/m_dfe252012f.ashx |
| L1 AOTA‑B201610S3R3‑101‑T | It solders and assembles. The pads are KiCad's stock 0.8×1.6 mm at ±0.75, which is smaller than Abracon's 1.0×1.6 mm pads with a 1.0 mm gap. They still cover the 0.6 mm terminals at 0.4–1.0 mm from centre, so I don't report this. The polarity dot sits at pad 1, which is on +1V1, and pad 2 is on VREG_LX. That matches the RP2350 datasheet Fig. 26, where the orientation indicator is on the V<sub>OUT</sub> end. | Abracon datasheet p.4: https://abracon.com/datasheets/AOTA-B201610S3R3-101-T.pdf; RP2350 datasheet §6.3.8, Figs. 26 and 28 (`scratch/rp2350.pdf` p.412–414) |
| U5 BQ24074 RGT0016C | The pitch is 0.5 mm and pad centres span 2.8 mm. The 0.825×0.25 mm pads are slightly longer than TI's 0.6×0.24 mm. The thermal pad is 1.68 mm with vias at ±0.59, against TI's ±0.58. Pin 1 is top‑left and the numbering runs counter‑clockwise. Every pin carries its datasheet function. | TI SLUS810N Fig. 7‑2, p.7, and RGT0016C land pattern, p.53: https://www.ti.com/lit/ds/symlink/bq24074.pdf |
| U6 TPS63001 DRC0010J | The pads are 0.6×0.24 mm at ±1.4 with 0.5 mm pitch. The exposed pad is 1.65×2.4 mm with tabs out to 3.4 mm, and the vias sit at (0,±0.95) and (±0.575,0). Pin 1 is top‑left, 1–5 run down the left side and 6–10 up the right. Every pin carries its datasheet function, and FB is tied to +3V3 as the fixed‑output version needs. | TI SLVS520C, Pin Configuration p.3 and DRC0010J land pattern p.24: https://www.ti.com/lit/ds/symlink/tps63001.pdf |

**J3 microSD details**

- **Pads:**
  - Pin 1 centre is 3.105 mm from the socket centre, on the detect‑switch side.
  - Pin 8 is the narrow 0.75 mm pad.
  - The ground pads G1–G4 are 1.55, 1.17, 1.9 and 1.9 mm wide.
  - The detect pads are 1.2×1.0 mm, 6.15 and 9.85 mm from the pin row.
- **Pin map:** it matches the drawing's table (T1 DAT2, T2 CD/DAT3, T3 CMD, T4 VDD, T5 CLK, T6 Vss, T7 DAT0, T8 DAT1). The board nets follow it: SD_D2, SD_D3, SD_CMD, +3V3, SD_CLK, GND, SD_D0, SD_D1. Pads 9 and 10 form the detect switch, on SD_DET and GND.
- **Card entry:** the card goes in on the same side as the pin tails. Molex lists "Card Entry Location: Front", and the drawing's card outline sticks out 4.0 mm past the tail side. On the board the tails are at y=127.74, the body front is at y≈127.99 and the bottom edge is at 128.54. So the slot opens off the bottom edge, and an inserted card sticks out about 3.45 mm past the edge.
- **3D model:** the model is rotated 180° compared with the stock footprint. It is a different STEP file, and `renders/top.png` shows its tails over the pad row, so the rotation only lines the model up with the pads.

**Other things checked**

- **Copper near the bottom edge:** J3's pin and shell pads end at y=128.29. That is 0.25 mm from the edge and about 0.30 mm from the corner arc, which meets the project's 0.25 mm `min_copper_edge_clearance`.
- **Battery wiring on J2:** pin 1 is GND and pin 2 is BAT_CONN. The footprint matches the drawing. Whether a given LiPo pack's leads match this order is a battery choice I did not check.

## Subagent: If you spawn subagents, every `spawn_subagent` call must set `model` to opus-5.5 and `reasoning` to high. Put this same rule, word for word, in every subagent's prompt.

I found no confirmed fatal faults in the parts you assigned. Every pin number matched the manufacturer's datasheet, and every strap and power path works. No files were changed.

**Confirmed fatal problems**
None.

**Checked and correct**
- **U5 BQ24074 pins** match TI SLUS810 (https://www.ti.com/lit/ds/symlink/bq24074.pdf), Fig. 7-2 and Table 7-1: 1 TS, 2/3 BAT, 4 CE, 5 EN2, 6 EN1, 7 PGOOD, 8 VSS, 9 CHG, 10/11 OUT, 12 ILIM, 13 IN, 14 TMR, 15 ITERM, 16 ISET, 17 pad to VSS. On the BQ24074, pin 15 is ITERM, not SYSOFF (SYSOFF is only on the '75 and '79).
- **U5 straps:**
  - CE is tied to GND, so charging is enabled.
  - EN2 = 0 and EN1 = 1 (tied to OUT) selects USB500 mode (Table 7-2). Both EN pins are driven, not left floating.
  - TS has a fixed 10 kΩ (R12) to VSS, which the datasheet allows when the battery has no NTC.
  - TMR open gives the default timers. ITERM open gives the default 10% termination.
- **U5 values and limits:**
  - R11 2 kΩ gives about 445 mA charge current (KISET 890 AΩ, allowed 590 Ω to 8.9 kΩ).
  - R10 1.74 kΩ is in the allowed 1.1 to 8 kΩ range.
  - The highest voltage on EN1 is OUT at 4.5 V, under the 7 V abs-max. IN is rated to 28 V.
- **U6 TPS63001 pins** match TI (https://www.ti.com/lit/ds/symlink/tps63001.pdf), Pin Functions table: 1 VOUT, 2 L2, 3 PGND, 4 L1, 5 VIN, 6 EN, 7 PS/SYNC, 8 VINA, 9 GND, 10 FB, 11 pad to PGND.
  - FB is tied to VOUT, as the fixed-output version requires.
  - EN is pulled to VSYS through R17 100k. PS/SYNC is pulled down by R18, so it starts in power-save mode.
  - VINA has the R16 100 Ω / C24 filter. VSYS stays at or below 4.5 V, inside the 5.5 V input limit.
- **Q1 DMG2305UX** (https://www.diodes.com/assets/Datasheets/DMG2305UX.pdf): the SOT-23 pins are 1 G, 2 S, 3 D, matching the nets (gate GND, source VBAT, drain BAT_CONN).
  - With the battery correct, the body diode conducts from drain to source. That gives Vgs of about −VBAT, well past the −0.9 V max threshold, so the FET turns fully on. It then carries current both ways, so the battery can power the board and be charged.
  - With the battery reversed and no USB, the FET stays off. Vgs stays within the ±8 V rating.
- **Q2 DMG1012T** (https://www.diodes.com/assets/Datasheets/DMG1012T.pdf): the SOT-523 pins are 1 G, 2 S, 3 D, matching the nets.
  - The divider point is at most 2.1 V. With the gate at 3.3 V, Vgs is at least 1.2 V, above the 1.0 V max threshold, so the FET passes the voltage to the ADC.
  - When 3V3 is off, the FET is off and its body diode (ADC side to divider) is reverse-biased, so the GPIO28 pin is isolated from the battery.
- **U4 USBLC6-2SC6** (https://www.st.com/resource/en/datasheet/usblc6-2.pdf), functional diagram: 1/6 I/O1 on USB_DP, 3/4 I/O2 on USB_DM, 2 GND, 5 VBUS. All match.
- **U2 W25Q128JV** (Winbond datasheet, §3.3, SOIC 208-mil): 1 /CS, 2 IO1, 3 IO2, 4 GND, 5 IO0, 6 CLK, 7 IO3, 8 VCC. These match the QSPI nets.
- **U3 APS6404L** (https://www.pjrc.com/store/APS6404L_3SQR.pdf, §3.1): 1 CE#, 2 SIO1, 3 SIO2, 4 VSS, 5 SIO0, 6 SCLK, 7 SIO3, 8 VDD. These match. The -3SQR part runs from 2.7 to 3.6 V.
- **GPIO8 as PSRAM chip select:** the RP2350 datasheet GPIO function table lists F9 "QMI CS1n" on GPIO 0, 8, 19 and 47. The FLASH_DEVINFO CS1_GPIO field also allows 0, 8, 19 and 47. R7 pulls the line up.
- **J1 USB-C** uses the standard pin names:
  - CC1 (A5) and CC2 (B5) each have a separate 5.1k pull-down.
  - VBUS is on A4, A9, B4 and B9. GND is on A1, A12, B1 and B12.
  - D+ is on A6 and B6, D− on A7 and B7, so both plug orientations work.
- **J3 microSD** (Molex 104031-0811 drawing): contacts 1 DAT2, 2 CD/DAT3, 3 CMD, 4 VDD, 5 CLK, 6 VSS, 7 DAT0, 8 DAT1 match the nets.
  - The card-detect switch is open with no card and closes when a card is inserted. One side goes to GND (pin 10) and the other to SD_DET, which R29 pulls up to 3V3 (pin 9). That works whichever way the two switch pins are assigned.
  - The SD bus fits PIO SDIO: D0 to D3 sit on consecutive GPIOs 12 to 15, and CLK on GPIO10 is D0−2, the usual offset.
- **D3 WS2812B-2020-V6** (Worldsemi V6 sheet): 1 DOUT, 2 GND, 3 DIN, 4 VDD match the nets. The V6 is rated from 3.3 V.
- **J4 Qwiic:** 1 GND, 2 3V3, 3 SDA (GPIO4), 4 SCL (GPIO5) matches SparkFun's order, with 2.2k pull-ups R30 and R31. GPIO4 and GPIO5 are I2C0 SDA and SCL.
- **Power-on orders:** USB only, battery only and both all reach 3V3 correctly. The BQ24074 blocks current flowing back from BAT or OUT into IN. Pulling 3V3_EN low just turns off the TPS63001 and isolates Q2. Feeding 5 V into J6.2 only reaches IN and the USBLC6, which is fine.

**Non-fatal observations**
- R10 (ILIM) has no effect in this strap: EN2 = 0 and EN1 = 1 means the input is capped at 500 mA. The ILIM resistor only applies when EN2 = 1 and EN1 = 0.
- 5 V fed into J6.2 while a USB host is plugged in pushes current back into the host's VBUS, because there is no diode.
- With USB connected and the battery plugged in backwards, the charger's BAT voltage turns Q1 on. The protection only works when no USB is present.
- The WL_VBUS_DET divider puts about 3.0 V into the RM2's GPIO2 even when the RM2 is unpowered, but the 100k limits the current to about 30 µA or less.
- The R14/R15 divider draws about 4.5 µA from the battery all the time.
- Erratum RP2350-E14: the bootrom's `connect_internal_flash()` sets up the pads for pin 0 rather than GPIO8. The workaround is in firmware: clear GPIO8's pad isolation after that call.
