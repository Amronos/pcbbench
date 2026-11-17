# RP2350 dev board

A 28 × 78.54 mm, 4-layer RP2350A board with Wi-Fi/BLE, a LiPo charger and microSD, laid out for PCBWay's
standard PCB and turnkey assembly service. Every fitted part is on the top side.

| Block | Part | Notes |
| --- | --- | --- |
| MCU | RP2350A (U1), 12 MHz crystal | Core supply from the internal switching regulator (L1 3.3 µH) |
| Flash | W25Q128JVSIQ (U2), 16 MB | QSPI CS0, boots from it |
| PSRAM | APS6404L-3SQR-SN (U3), 8 MB | QSPI CS1 on GPIO8 |
| USB | USB-C (J1, GCT USB4105), 5.1 kΩ CC pull-downs, USBLC6-2 ESD | USB 2.0 full speed, power and data |
| Charger | BQ24074 (U5) with power path | 445 mA charge current, 500 mA input limit |
| Battery | JST PH 2-pin (J2), reverse-polarity P-FET (Q1) | Single-cell LiPo |
| Battery monitor | 470 k/470 k divider on GPIO28 (ADC2), switched by Q2 | `VBAT = 2 × ADC` |
| 3.3 V | TPS63001 buck-boost (U6) | Runs from the cell or USB; 3V3_EN on the header turns it off |
| Wireless | Raspberry Pi RM2 module (U7, CYW43439) | Wi-Fi 4 and Bluetooth 5.2, same wiring as the Pico 2 W |
| microSD | Molex 104031-0811 (J3) | 4-bit SD on GPIO10-15, card detect on GPIO9 |
| Qwiic / STEMMA QT | JST SH 4-pin (J4) | I²C0 on GPIO4 (SDA) and GPIO5 (SCL), 2.2 kΩ pull-ups |
| RGB LED | WS2812B-2020 (D3) | Data on GPIO22 |
| Buttons | BOOTSEL (SW1), RESET (SW2) | |
| Headers | 2 × 14 pins on 2.54 mm, rows 22.86 mm apart (J5, J6) | Holes only; not fitted. Pin names on the bottom silkscreen |

## Files

| Path | Contents |
| --- | --- |
| `rp2350-devboard.kicad_pro` | KiCad project: schematic (5 sheets) and PCB |
| `BOM.csv` | Bill of materials |
| `fab/` | Gerbers, drill files and job file (`gerbers/`, zipped as `rp2350-devboard-gerbers.zip`), PCBWay BOM and centroid |
| `docs/assembly.md` | Assembly and bring-up instructions |
| `docs/renders/` | 3D renders |
| `lib/` | Project symbols, footprints and 3D models |
| `scripts/` | Generators: `design.py` holds every part and net, the other scripts build the schematic and board, finish it (`teardrops.py`, `label_board.py`) and export `fab/` (`export_fab.py`) |

The schematic, placement and pre-routed copper come from the scripts. Edit the schematic and board in KiCad now.
`build_schematic.py` assigns new UUIDs, which breaks the link to the routed board, and `build_pcb.py` replaces the
routed board.

## Pinout

Left header J5, pin 1 at the top (USB-C is at the bottom):

| Pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J5 | GND | 3V3 | SWCLK | SWDIO | RUN | GP16 | GP17 | GP18 | GP19 | GP20 | GP21 | GP26/A0 | GP27/A1 | GND |
| J6 | GND | VBUS | GND | 3V3 | GP7 | GP6 | GP5/SCL | GP4/SDA | GP3 | GP2 | GP1 | GP0 | GND | 3V3_EN |

Fixed functions:

| GPIO | Function |
| --- | --- |
| 8 | PSRAM CS |
| 9 | microSD card detect (low when a card is in) |
| 10-15 | microSD CLK, CMD, D0, D1, D2, D3 |
| 22 | WS2812B data |
| 23, 24, 25, 29 | RM2 WL_ON, WL_D, WL_CS, WL_CLK (as on the Pico 2 W) |
| 28 | Battery voltage / 2 |

## Design decisions

- **Pico 2 W compatible wireless.** The RM2 uses GPIO23/24/25/29 and the same 470 Ω/10 kΩ data network, and its
  WL_GPIO2 senses VBUS through a 100 k/150 k divider. Stock MicroPython and the Pico SDK `pico2_w` board files
  drive Wi-Fi and BLE unchanged.
- **No WL_GPIO0 LED.** The Pico 2 W's LED hangs off the RM2. Its track would block the left header fan-out, and the
  RGB LED already serves as the user LED, so U7 pin 8 is unconnected. `Pin("LED")` on stock `pico2_w` firmware
  runs without error but lights nothing. Use the WS2812B on GPIO22.
- **Charger in USB500 mode.** EN1 is tied high and EN2 low, so the BQ24074 draws at most 500 mA from any USB port
  without negotiation. ISET = 2 kΩ sets 445 mA fast charge, which suits cells from about 450 mAh up. R10 (ILIM) only
  matters if EN1/EN2 are changed to resistor-programmed mode.
- **Power path.** The BQ24074 OUT pin (VSYS) feeds the TPS63001 from USB when present, else from the cell. The
  buck-boost keeps 3.3 V across the full LiPo range (3.0-4.2 V) and from USB (VSYS = 4.4 V).
- **VSYS not on the header.** VSYS is tied to the cell through the charger's internal BAT-OUT FET, so 5 V fed there
  would charge the cell with no regulation. External 5 V power goes in through VBUS (J6 pin 2), which passes the
  charger's input current limit and over-voltage protection.
- **3V3_EN.** Pulled up to VSYS with 100 kΩ. Grounding J6 pin 14 turns off 3.3 V while the charger keeps working.
- **Battery monitor back-power blocker.** The divider reads VBAT/2, up to 2.1 V. With the 3.3 V rail off, that
  voltage would forward-bias the GPIO28 clamp diode into an unpowered IOVDD. Q2, an N-FET gated by +3V3, connects
  the divider to the pin only while 3.3 V is up. The divider draws 4.5 µA from the cell.
- **2.2 kΩ PSRAM CS pull-up.** At power-on the RP2350 pulls GPIO8 down (36 kΩ minimum). 2.2 kΩ keeps CE# above
  the PSRAM's V_IH so it stays deselected until firmware configures CS1.
- **Reverse-battery P-FET (Q1).** A reversed cell leaves the FET off, so the charger and buck-boost see no
  negative voltage.
- **Headers not fitted.** J5/J6 are holes only, so the board can be soldered down, socketed or fitted with headers
  by the user. J1's four shell tabs are the only plated through-holes that get solder. PCBWay solders them with
  paste-in-hole or by hand.

## Layout

- Stackup: PCBWay standard 1.6 mm 4-layer, 1 oz outer copper, ENIG. F.Cu signals and parts, In1.Cu solid GND
  with no tracks, In2.Cu +3.3 V plane that also carries signals (see the reviewer notes), B.Cu signals with GND
  pour.
- Rules: 0.15 mm track and clearance for signals (PCBWay minimum 0.127 mm), 0.6/0.3 mm vias, USB pair 0.2 mm.
- Power copper: VBUS, VSYS, VBAT, BAT_CONN and the inductor nets run at 0.4 mm and +1V1 at 0.2-0.25 mm. The
  narrowest pieces are 0.15 mm stubs where they enter fine-pitch pins: about 0.7 mm of VBAT at U5's BAT pins and
  the EN1 tie to VSYS. +3V3 reaches the parts through the In2 plane.
- The RM2 sits at the top edge with its antenna past the copper. Its footprint carries the datasheet's RF keepout on
  all copper layers. The datasheet forbids metal only in the antenna keepout, so tracks and vias run under the module
  body.
- The RP2350 regulator follows Raspberry Pi's hardware design guide: VREG_LX runs between the C12 and C13 pads to
  L1. A custom DRC rule allows that one net 0.127 mm clearance, still at PCBWay's minimum.
- Switch-node keepouts on In2.Cu and B.Cu keep signal tracks out of the fields under the buck-boost (tracks and
  vias) and the RP2350 regulator (tracks only, so a GND via can drop the C12/C13 return straight to the plane).
  GND still pours in both.
- Drawn by hand in `scripts/hand_routes.py` and `scripts/build_pcb.py`: the top-left fan-out (SWD, RUN, GP16-27,
  VBAT_SENSE, RGB_DIN and the RM2 lines), USB_D±_MCU from U1 to R3/R4, the VREG_LX loop, and the buck-boost
  BB_L1/BB_L2/VSYS/+3V3 loop. The USB pair was routed as a differential pair and locked before the autoroute.
  The router did the rest, then GND stitching vias and a 3 mm edge fence went in.
- Teardrops on every pad and via. Reference designators are hidden on the silkscreen and shown on F.Fab.

## Reviewer notes

- **DRC.** ERC is clean. DRC has 0 errors, 0 unconnected items and clean schematic parity. One warning remains:
  R7's top silk line touched U3's pin-1 mark and was deleted, so R7 no longer matches its library footprint.
- **Via in pad.** The router put 82 vias in or against SMD pads, such as on the decoupling caps, U1, U2, U3 and J1.
  They are marked filled and capped, so the order needs PCBWay's resin-filled, capped vias, which cost more. Moving
  them beside the pads by hand would allow plain tented vias.
- **In2 is a split plane.** About 410 mm of other nets run on In2.Cu: SD bus, RUN, GP4, QSPI_SCLK (23 mm),
  PSRAM_CS, +1V1, VBUS and others. The +3.3 V copper still connects everywhere, but these traces reference a
  broken plane on one side. That is fine at the default QSPI clock. Check flash and PSRAM signal quality
  before raising the QSPI clock.
- **Routing quality.** The autorouted copper is functional but not tidy. Some routes are long, for example GP0
  runs under U2, and a hand cleanup pass would shorten several.
- **L1 stock.** The Abracon 3.3 µH 0806 inductor had 143 at JLCPCB and 10 at LCSC in November 2026. Any 2016 (0806)
  3.3 µH molded inductor rated ≥ 1 A with DCR ≤ 150 mΩ is a drop-in substitute.
- **Fiducials.** The antenna keepout and the header rows leave no room for fiducials near the top, so the three
  fiducials sit in the lower half of the board. They still form a triangle across the whole width.
- **Hole clearance 0.19 mm.** The board rule is 0.19 mm hole-to-copper because the stock GCT USB4105 footprint
  places its shell tabs that close to the contacts. Confirm it in PCBWay's DFM review.
- **Pico 2 W software differences.** The LED (see above) and the extra parts: PSRAM on GPIO8, microSD on GPIO9-15
  and the WS2812B on GPIO22. The Pico 2 W's GPIO29 ADC VSYS measurement does not exist here: GPIO29 is WL_CLK, and
  the battery reads on GPIO28.
- **Not verified on hardware.** Check charge current, buck-boost ripple and Wi-Fi range on the first boards.
