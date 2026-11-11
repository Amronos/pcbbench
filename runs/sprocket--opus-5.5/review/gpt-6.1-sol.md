# gpt-6.1-sol's review

## Final message

Wrote [review.json](review.json) with exactly the requested keys and types.

Resaved all schematics and the PCB with the connector's KiCad version. No circuit, placement, or routing changes.

Main concerns: USB current headroom, LDO heating, core-regulator placement, and high-speed routing.

## Subagent: Review power-path and thermal read-only in /home/ubuntu/review. Board RP2350 WiFi LiPo USB-C. User asks powerPath true iff USB runs system while charging including no/flat battery, and unplug charged battery maintains 3.3V no reset. Need thermal score 0-10 (9-10 ship,6-8 minor,3-5 serious,0-2 fail). Files upgraded already. scratch/netlist.xml, scratch/drc.json available; BOM is authoritative part list. Use working-with-kicad skill and connector, web datasheets BQ24074 TLV757 etc. Read/write only workspace and connector/libs, scratch for derived outputs. Do not change design. Evaluate wiring, current limits, dropout, transients, copper and vias and worst full-load dissipation; provide evidence and recommendation.

powerPath is **true**, with one load condition. Thermal score: **7/10** (minor issues). I changed no design files. All derived files are in `scratch/powerpath/`, with the full write-up in [REPORT.md](scratch/powerpath/REPORT.md).

**Power path**

| Requirement | Result | Evidence |
|---|---|---|
| USB runs the system while charging | Yes | The BQ24074 holds OUT at a fixed 4.3/4.4/4.5 V (min/typ/max), separate from BAT. Its power-path control cuts charge current first, so the system gets the input current first. |
| No battery | Yes, up to 450 mA | EN2 is tied to GND and EN1 to OUT, which selects USB500 (450/475/500 mA). The battery-detect toggling only affects BAT. C3 is 10 µF, inside the 4.7–47 µF range. |
| Flat battery | Yes, up to 450 mA | Above the limit the battery has to make up the difference. A flat cell pulls OUT down to about 3.0 V, the LDO drops out, and the RM2 radio is below its 3.2 V spec. |
| Unplug USB with a charged battery | No reset | The battery FET turns on when OUT falls 40 mV below VBAT, so OUT goes from 4.4 V to about 4.15 V. The LDO needs about 3.45 V at 500 mA (about 150 mV dropout). About 15 µF of effective VSYS capacitance covers about 28 µs at 0.5 A, and the switchover takes microseconds. |

The load condition is tighter than it looks. The radio supply pin connects straight to VSYS and draws 271 mA while transmitting. Add the 3V3 loads (RP2350 about 30 mA, flash 25, PSRAM 7, LED 15, microSD up to 100, GPIO about 20) and the worst case is about 470 mA, above the 450 mA minimum. A typical heavy load is about 370 mA, so you only hit the limit with no or flat battery, the radio transmitting, and microSD writes at the same time.

**Thermal: 7/10**

| Case | Part | Power | Junction temp at 25 °C |
|---|---|---|---|
| 5.5 V in, 0.5 A, charging 361 mA into a 3.0 V cell | BQ24074 | 1.07 W | 76–92 °C (it throttles itself at 125 °C) |
| Worst internal 3V3 load, about 230 mA from 4.5 V | TLV75733 | 0.28 W | 70–90 °C |
| 500 mA on 3V3 (Qwiic or header loads) | TLV75733 | 0.60 W | 110–125 °C |
| 1 A on 3V3 (the part's rating) | TLV75733 | 1.2 W | Thermal shutdown at 165 °C, which resets the board |

The temperatures are estimates. I used 45–60 °C/W for the charger and 100–160 °C/W for the LDO. Those sit between TI's figures for the LDO (231 °C/W on the standard test board, 100.8 °C/W on its evaluation board layout) and allow for heat from the other part 7 mm away.

The copper is adequate:
- All three inputs and outputs of the charger (VBUS, VBAT, VSYS) use 0.4 mm tracks at about 1.2 mΩ/mm, so no rail drops more than about 30 mV.
- The 3V3 plane on the second inner layer covers 1451 mm². The first inner layer is solid ground in one 1737 mm² piece.
- The charger's thermal pad has four 0.2 mm vias into ground.
- The LDO's ground pin connects to the top-layer pour plus a via.
- DRC shows 0 unconnected items. All 82 findings are missing footprint-library entries.

**Findings, in priority order**

1. **LDO rating vs. exposed 3V3.** The 3V3 rail is brought out to the Qwiic connector and the header pads. With USB present the LDO drops 1.1–1.2 V, so its real limit is about 300 mA of external load at room temperature, not 1 A. Either document a limit of about 250 mA on Qwiic plus headers, or use a buck or buck-boost converter.
2. **No battery temperature protection.** TS has a fixed 10 kΩ resistor in place of a thermistor. The charger runs at about 1 W and sits 6.7 mm from the battery connector. If the LiPo is mounted on the board, fit a 10 kΩ NTC thermistor on the cell.
3. **450 mA input limit with no or flat battery.** Accept and document it, or add a way to use ILIM mode (R5 1.6 kΩ gives about 1 A) when the USB-C source advertises 1.5 A on CC.
4. **EN1 tied to OUT.** With no battery, the charger starts in the 90 mA mode until OUT passes 1.4 V. The datasheet doesn't cover changing EN1 during operation. It probably works, because the loads draw little below 1.4 V, but test a cold start with no battery on the bench. The alternative is a 100 kΩ/100 kΩ divider from VBUS, which keeps EN1 under its 7 V maximum up to 14 V in.
5. **Charge timer.** At 330 mA with TMR open, the 5 h safety timer can end the charge on a cell above about 1500 mAh. Adjust ISET or TMR to suit the battery.
6. **Vias in pads.** 0.6/0.3 mm vias sit in the USB-C VBUS pads (0.6 mm wide) and the battery connector's GND pad. Solder can wick into them, so specify filled or capped vias, or move them out.

To ship: decide on items 1 and 2, then measure the charger and LDO temperatures at full charge and with 3V3 loaded.

Partway through, someone else re-synced the workspace and deleted my first scratch folder and the datasheet notes. I re-checked the board and netlist afterwards and they matched what I had measured. All the numbers above come from the second run.

## Subagent: Review crystal and buttons on RP2350 board in /home/ubuntu/review. Files upgraded via connector already. Read only in this folder/connector libraries. Use working-with-kicad skill and connector as needed, scratch files only under scratch/crystal. Inspect bom.csv, scratch/netlist.xml, mcu schematic, board placement and renders. Read web datasheets / RP2350 design guide. Decide crystal yes/no and buttons yes/no (must both electrically work per guide and physically accessible on assembled board). Return specific evidence with component values, pins, locations, calculations, URLs. No design edits. Don't write review.json.

Both get a yes. The crystal circuit matches Raspberry Pi's recommended design part for part. Both buttons are wired the way the design guide shows, sit on the top side, have silkscreen labels, and nothing blocks them. One thing is still unverified: I couldn't open the PTS810 pin drawing to confirm which switch pads are connected inside the part. I made no design edits and didn't write review.json.

**Crystal: yes**

| Item | Board | RP2350 design guide / datasheet |
|---|---|---|
| Y1 | Abracon ABM8-272-T3, 12 MHz, 10 pF load, 50 Ω max ESR, ±30 ppm (LCSC C20625731) | The crystal the guide recommends, with the same specs |
| Load caps | C25 and C26: 15 pF C0G 0402, Murata GRM1555C1H150JA01D, to GND | 15 pF each |
| Series resistor | R21: 1 kΩ between U1 pin 22 (XOUT) and Y1 pin 3 (net `XTAL_O`) | 1 kΩ on XOUT |
| MCU pins | XIN is U1 pin 21 and XOUT is pin 22 | QFN-60 pinout: XIN 21, XOUT 22 |
| Crystal pads | Y1 pins 1 and 3 carry the crystal, pins 2 and 4 go to GND | Matches the ABM8 drawing: 1 bottom-left, 3 top-right, 2 and 4 are ground |
| IOVDD | U1 pins 1, 11, 20, 30, 38 and 45 are on +3V3 from U6 (TLV75733, 3.3 V) | The 1 kΩ value is tuned for 3.3 V IOVDD |

Load capacitance:
- Caps in series: 15 × 15 / 30 = 7.5 pF.
- With the guide's 3 pF stray budget: 7.5 + 3 = 10.5 pF, against the crystal's 10 pF spec. The guide accepts this.
- Copper on this board: the traces are 0.127 mm wide over 0.11 mm prepreg (εr 4.29) with In1 as ground. That gives about 57 Ω and roughly 0.10 pF/mm. XIN is 4.6 mm of F.Cu and `XTAL_O` is 4.0 mm, so each side adds about 0.4 to 0.5 pF, well inside the 3 pF budget.

Layout:
- Y1 is at (121.6, 79.6), about 2 mm from U1's pins. C25 is at (121.45, 83.3), C26 at (124.4, 79.25) and R21 at (123.5, 82.05), all on F.Cu.
- In1.Cu is solid GND under the whole crystal area with no tracks.
- QSPI_SCLK (In2) and RUN (In2 and B.Cu) run under Y1. In1 ground shields them from the top layer.
- XOUT runs about 7 mm on B.Cu through 2 vias before reaching R21. That is longer than ideal, but it is on the driven side of the 1 kΩ.
- SD_D3 runs about 0.6 mm from the XIN trace. This is a minor crosstalk point, not a blocker.

Firmware needs no change. The RP2350 datasheet says the SDK's default 1 ms startup delay is enough for this crystal circuit.

![F.Cu around Y1](scratch/crystal/xtal_F.png)

**Buttons: yes**

| | SW1 (BOOT) | SW2 (RST) |
|---|---|---|
| Part | C&K PTS810SJM250SMTRLFS: 4.2 × 3.2 mm, 2.5 mm tall, 1.6 N | same |
| Net | U1 pin 60 `QSPI_SS` → R25 (1 kΩ) → SW1 → GND | U1 pin 26 `RUN` → SW2 → GND, also on J6 pin 10 |
| Design guide | Matches: 1 kΩ from QSPI_SS to the BOOTSEL button | Matches the Minimal design's RUN button. RUN has an internal pull-up of 32 to 86 kΩ at 3.3 V |
| Position | F.Cu (106.0, 84.6), rotated 90°, silkscreen "BOOT" at (102.9, 84.6) | F.Cu (106.0, 90.6), silkscreen "RST" at (102.9, 90.6) |

The 1 kΩ is 4.7 times stronger than the 4.7 kΩ the RP2350 datasheet calls a good value for pulling chip select low against its internal pull-up. Both switches are fitted (dnp no, in BOM).

Access on the assembled board:
- Both switches are on the top side with nothing above them, as `renders/iso.png` shows.
- The nearest taller part is J4, the JST PH battery connector, about 4.3 mm below SW2's body. Its opening faces the left board edge, so the battery cable doesn't cross the buttons.
- The headers J5 and J6 are not fitted. If someone fits them, J5's plastic ends at x = 102.54, about 1.9 mm from the switch bodies, which still leaves room to press.

![Buttons area](scratch/crystal/buttons.png)

**Remaining risk**
- **Switch pad pairing:** The KiCad footprint pairs pads "1" and "2" at opposite ends of the long side, 4.15 mm apart. The pin numbers I could extract from the Littelfuse datasheet agree with that, but the drawing itself was blocked and the headless browser wouldn't start. If the pairing were wrong, RUN or QSPI_SS would be shorted to GND all the time. A meter check on one loose switch settles it.

**Small non-blocking issues**
- Y1's Datasheet field `https://abracon.com/Resonators/ABM8-272-T3.pdf` returns 404. The working link is `https://abracon.com/datasheets/ABM8-272-T3.pdf`.
- bom.csv merges SW1 and SW2 into one line with Value "BOOTSEL", while the netlist gives SW2 the value "RESET".
- `sym-lib-table` points to `lib/board.kicad_sym`, but the file is `lib/rp2350_dev.kicad_sym`. This is why ERC and DRC show library warnings. ERC and DRC report 0 unconnected items and no real violations.
- LCSC had only 450 of the crystal in stock.

Something else is writing to `scratch/` while I work. `scratch/netlist.xml` and some of my own scratch files disappeared partway through, and I didn't delete them. All my evidence was collected before that.

Sources:
- https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf (sections 4 and 5.4)
- https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf (pin tables, XOSC startup, BOOTSEL)
- https://abracon.com/datasheets/ABM8-272-T3.pdf
- https://www.lcsc.com/product-detail/C20625731.html
- https://www.ckswitches.com/media/1476/pts810.pdf (now redirects to Littelfuse)

## Subagent: Review powerPath and thermal of RP2350 dev board in /home/ubuntu/review. Files upgraded via connector already. Read only in folder and connector libraries. Read working-with-kicad skill, use connector. Scratch output allowed under scratch/power. Inspect bom.csv, scratch/netlist.xml, power schematic, copper and placement. Web TI BQ24074 + TLV75733 datasheets and module current load. Determine powerPath boolean: USB runs while charging and absent/flat battery, unplug charged battery without 3.3V rail dropping/reset. Thermal integer 0-10 using supplied scale (9-10 ship,6-8 minor,3-5 clear reliability issues,0-2 stops working/build). Evaluate real copper/vias and full-load dissipation. Return evidence/calculations/URLs. No design edits or review.json.

**powerPath: `true`. Thermal: 8.**

The power path works in all three cases you listed. The thermal score is 8 because one minor issue remains: the 3.3 V LDO can't hold its 1 A rating at this board's input voltage. All on-board loads stay within limits.

One note on the workspace: it was re-provisioned at 12:49:09 while I was working. That deleted `scratch/netlist.xml`, `scratch/drc.json` and my first scratch files. I had already pulled the power nets out of the netlist, and they match `power.kicad_sch`. The board still has the same 1318 track segments and 274 vias, so I re-ran all the copper analysis on it. I made no design edits and wrote no `review.json`.

**Power path: why it's `true`**

| Case | What happens | Margin |
|---|---|---|
| USB with a battery that is absent or flat | BQ24074 OUT is regulated to a fixed 4.4 V (4.3 to 4.5 V) from IN, not from BAT. The whole system (U6 IN, RM2 VIN, header) runs from VSYS = OUT. DPPM cuts charge current first when the load rises. | LDO needs about 3.55 V. VSYS is 4.4 V. |
| USB while charging | EN2 = GND and EN1 = VSYS select USB500 (450 to 500 mA). R4 = 2.7 kΩ gives 890/2700 = 330 mA charge current (295 to 361 mA). TS has a fixed 10 kΩ, so 75 µA × 10 kΩ = 0.75 V, inside the 0.3 to 2.1 V window. CE = GND enables charging. | The system load takes priority over charging. |
| Unplug USB with a charged battery | OUT falls only to VBSUP1 ≈ VBAT − 40 mV ≈ 4.1 V, then Q2 carries the load (VDO(BAT-OUT) is 50 to 100 mV at 1 A). The LDO needs 3.3 V plus about 0.18 V at 0.4 A. | About 0.6 V of headroom, so no dip or reset. |
| Remove the battery while on USB | OUT keeps running from IN at 4.4 V. | None needed |

Start-up detail: because EN1 is tied to OUT, the charger runs in USB100 mode (100 mA) until OUT passes VIH = 1.4 V, then switches to USB500. TI says EN1 is "continuously monitored", so start-up still works. Below 1.4 V the only loads are capacitors charging and precharge, which is about 33 mA.

Caveats that don't change the boolean:
- **No battery or a flat battery leaves little margin.** The input limit is at least 450 mA. RM2 transmit is 271 mA, the RP2350, flash and PSRAM take about 75 mA, and an SD write takes up to 100 mA. That totals about 450 to 470 mA. Wi-Fi transmit at the same time as an SD write, or a Qwiic load, can brown out VSYS when no good battery is there to make up the difference. The cause is the hard-wired USB500 mode, not the topology.
- **R5 (1.6 kΩ, about 1 A ILIM) is never used.** EN2 = 0 means ILIM never sets the limit. The part is still required, because the datasheet says an open ILIM disables charging.
- RM2 VIN is rated 3.0 to 4.8 V, and VSYS tops out at 4.5 V, so that's fine.

**Thermal: worst-case dissipation**

| Part | Condition | P | RθJA used | TJ at 25 / 40 °C ambient |
|---|---|---|---|---|
| U5 BQ24074 (RGT) | VIN 5.25 V, 0.5 A in, VBAT 3.4 V, 361 mA charge | 0.425 + 0.361 = 0.79 W | 55 to 70 °C/W (datasheet 44.5 on a JEDEC board; this board is smaller) | 68 to 80 / 83 to 95 °C |
| U5 | VIN 5.5 V, VBAT 3.0 V | 1.06 W | same | up to 99 / 114 °C. That's below TJ(REG) = 125 °C, and the charger throttles itself above that. |
| U6 TLV75733 (DBV) | Typical 0.2 A, VIN 4.4 V | 0.22 W | 100 to 130 °C/W (TI EVM 100.8, JEDEC with no vias 231) | about 50 / 70 °C |
| U6 | All on-board loads at once, about 0.42 A, VIN 4.5 V | 0.50 W | same | 75 to 90 / 90 to 105 °C, under 125 °C |
| U6 | Rated 1 A from header loads, which needs battery supplement | 1.1 W (0.9 W at 4.2 V on battery) | same | 135 to 168 °C at 25 °C, which reaches thermal shutdown at 165 °C |

Sources for the on-board loads:
- RP2350 core regulator: up to 200 mA at 1.1 V, which is about 80 mA from 3.3 V. Add GPIO current on top.
- Flash: about 25 mA. PSRAM: about 40 mA.
- microSD: up to 200 mA.
- WS2812: about 15 mA.
- RM2: 271 mA, but it runs from VSYS, so this current never passes through the LDO. That keeps the LDO's dissipation down.

**Copper and vias**

The board is 30.5 × 70 mm with 4 layers of 1 oz (35 µm) copper. I refilled the pours on a scratch copy before measuring them:

| Layer | Pour |
|---|---|
| In1.Cu | GND, solid, one piece, 1737 mm² |
| B.Cu | GND, 1406 mm² |
| F.Cu | GND, 1258 mm² in 11 pieces |
| In2.Cu | +3V3, cut into 4 pieces by VBUS, VBAT and VSYS tracks |

Parts and connections:
- **U5 thermal pad:** 4 vias of 0.2 mm into In1, B.Cu and F.Cu GND. 59 of 64 mm² of In1 within ±4 mm is GND.
- **U6 GND pin 2:** one 0.2 mm via in the pad, plus F.Cu pour (6.9 of 16 mm² within ±2 mm) and In1 0.11 mm below.
- **U6 OUT:** connects to the +3V3 plane only through one 0.2 mm via. That via carries about 1.2 A for a 10 °C rise by IPC-2221, so it's fine at 0.4 A.

Power path traces, all 0.4 mm:

| Path | Length | Layers | Check |
|---|---|---|---|
| J1 to U5 IN | 21.4 mm | F.Cu and In2 | 26 mΩ, 13 mV drop at 0.5 A, about 6 °C rise (IPC-2221 inner, conservative) |
| J4 to U5 BAT | 7.7 mm | B.Cu and F.Cu | about 3 °C rise at 0.7 A, about 11 °C at 1.3 A |
| U5 OUT to U6 IN | 7.9 mm | F.Cu | |
| U5 OUT to C2 | 4.2 mm | F.Cu | |

**What keeps it from a 9**

- U6 can't meet its 1 A rating with a 4.4 V input on this copper. Only header 3V3 loads above about 0.6 A, with a battery present, can reach that.
- The USB500 hard-wire gives about 0 to 20 mA of headroom when Wi-Fi transmit and an SD write happen together with no battery.
- U5 has only 4 small thermal vias. The +3V3 plane is split by tracks on In2.

**URLs**

- TI BQ24074 datasheet: https://www.ti.com/lit/ds/symlink/bq24074.pdf. Sections used: device comparison table, Table 7-2, §8.4 to 8.5, §9.3.4, §12.3 and Equation 11.
- TI TLV757P datasheet: https://www.ti.com/lit/ds/symlink/tlv757p.pdf. Sections used: §5.3 to 5.5, §6.3.3 to 6.3.4.
- Raspberry Pi RM2 datasheet (Vin 3.0 to 4.8 V): https://pip-assets.raspberrypi.com/categories/1216-raspberry-pi-radio-module-2/documents/RP-008943-DS-7-Radio%20Module%202%20Datasheet.pdf
- RM2 currents (271 mA transmit, 43 mA receive): https://www.raspberrypi.com/products/radio-module-2/
- RP2350 datasheet (core regulator up to 200 mA): https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-3-rp2350-datasheet.pdf

Everything I wrote is in `scratch/power/`:
- `pcb.py`: copper stats and pour areas.
- `paths.py`: the starting version of the path tracer. The path widths in the table above came from an improved version I ran inline, which I didn't save.
- `fill/`: the refilled copy of the board.

## Subagent: Review physical layout and silkscreen of RP2350 board /home/ubuntu/review. Use working-with-kicad skill and KiCad connector. Files upgraded already. Read only folder and connector libraries, scratch outputs under scratch/physical. Inspect renders and layers and actual PCB for connectors/buttons edge, critical component closeness, antenna edge/clearances, assembly feasibility and markings. Score layout and silkscreen 0-10:9-10 ship as is,6-8 minor asks,3-5 clear problems hurt performance/reliability,0-2 prevents working/build. Return specific placement/overlap/label evidence. Datasheets web as needed. No design edits, don't write review.json.

I score the physical layout 5/10. Placement is good almost everywhere: the connectors sit on the right edges, the antenna placement meets the RM2 datasheet, and assembly checks pass. The RP2350 core regulator block does not follow Raspberry Pi's required layout, and that alone puts it in the 3–5 band. I score the silkscreen 7/10: it's correct, but there are a few minor asks. I made no design edits and didn't write `review.json`.

The workspace was replaced partway through, around 12:49, which also wiped `scratch/`. I re-copied the board and confirmed all 82 parts are in the same places, so the findings below are against the current files.

**Layout: 5/10**

**Clear problem: core regulator (U1 pins 46–50, L1, C22, C23, C24)**

Raspberry Pi's "Hardware design with RP2350" guide (pp. 6–8) says to copy the Pico 2 regulator layout, and that using any other layout is "at your own risk". This board doesn't follow it:

| Item | This board | RP reference |
|---|---|---|
| L1 placement | At (107.5, 78.35), about 3.8 mm from the VREG_LX pin, with C17 and C22 in between | Right next to pins 48–50 |
| VREG_LX path | 0.127 mm track, two vias at (110.95, 77.3) and (108.6, 78.4), runs on B.Cu (the GND plane layer) | Short, wide trace on the top layer |
| +1V1 from L1 to C23 and pin 50 | Three vias, 0.25 mm tracks on In2.Cu, which cut the +3V3 plane | Top layer, with C7 at the L1 end |
| PGND (pin 47) | 0.127 mm stub to a via at (111, 76.6); not tied on top to the GND pads of C22 and C23 | PGND and the C6/C7 grounds share a top-layer pour |
| Inductor polarity | Pad 1 is VREG_LX, and there's no dot on the silkscreen | Pad 1 (the dot) is +1V1 |

Raspberry Pi specifically warns that a reversed inductor upsets regulation. Here, an assembler lining the Abracon dot up with pad 1 puts the dot on VREG_LX, the opposite of the reference.

![VREG area: F.Cu with VREG_LX leaving through vias](scratch/physical/v_vreg.png)

**Areas that check out**

- **Antenna:** The RM2 module (U4) sits 0.5 mm from the top edge. The 35.5 × 18.5 mm keepout from datasheet Fig. 6 is on the board in two places: as a rule area at y 50–55.5 over the full width on all four copper layers, and inside the footprint. F.Cu and In1 are clear there. The nearest metal is the top pin pads of J5/J6 and FID1, about 1.3 mm below the keepout. USB is at the far end of the board.
- **USB-C (J1):** On the bottom edge. Its front face is 0.58 mm past the board edge, matching the footprint's "PCB Edge" line.
- **Qwiic (J3):** On the bottom edge, with its opening 0.7 mm in from the edge. There's 4 mm between the Qwiic plug and the USB-C overmold.
- **microSD (J2):** The slot faces the right edge and the card sticks out 3.3 mm, which is fine for a push-pull socket. It starts below the J6 header (y 96 vs 94).
- **LiPo connector (J4):** The opening faces the left edge, 0.7 mm in, below the J5 header.
- **Crystal:** Y1 XIN is 1.9 mm from pin 21.
- **Decoupling:** The IOVDD caps are 2.1–2.9 mm from their pins and the DVDD caps 2.7–4.0 mm. The flash (U2) is about 7–12 mm from the QSPI pins.
- **Assembly:** All SMD parts are on the top, so one reflow pass. `check_assembly` finds 0 blocking issues. There are 3 fiducials and no courtyard overlaps.

**Minor asks**

- **Header spacing:** The pin rows are 27.94 mm (1.1") apart. On a standard breadboard that puts the pins in columns a and j, leaving no free holes for wires. Is that intended?
- **Mounting holes:** The board has none.
- **USB ESD (U7):** It sits about 7 mm to the side and connects as a stub. D+ and D- also take separate paths around J1 through several vias. This is acceptable for full-speed USB, but it's untidy.
- **Parts near the edge:** C40 is 1.48 mm and R43 1.36 mm from the edge. That's fine for routed tabs but marginal for V-score panels.

**Silkscreen: 7/10**

- **What's correct:** All 30 header labels on the back match their pad nets. I checked every pin of J5 and J6 against the netlist. The back silkscreen also has "- GND" and "+ BAT" at J4 pins 1 and 2, which matches the nets. Pin-1 marks are present on U1, U2, U3, U5, U6, U7, D1, Y1 and the RM2, and D2 has a cathode mark. DRC finds no silk-over-copper or silk-to-edge warnings.

Minor asks:
1. Add a polarity dot on L1 at the +1V1 pad. Today, nothing on the board shows the inductor's orientation.
2. Put "+" and "−" for J4 on the top. JST PH battery polarity varies between vendors, and the current marks are on the back, under the connector.
3. Add top-side pin labels, at least numbers. When the board sits in a breadboard, the back labels are hidden. There's about 2 mm of room beside the left header and about 1.3 mm beside the right one.
4. Label D2 "CHG" and add short labels for USB, Qwiic and SD.
5. On F.Fab, the J5 and J6 reference text sits on top of the pin pads.
6. The text is 0.8 mm high with a 0.15 mm stroke. That's at the fab's minimum, so it may print poorly.

One thing outside this review: the saved board has unfilled zones. DRC without a refill shows 147 unconnected items, so refill the zones before exporting Gerbers.

My working files are in `scratch/physical/`, including the regulator view and the RM2 and RP2350 datasheet excerpts in `ds/`.

## Subagent: Review crystal suitability and BOOTSEL/RUN operation in /home/ubuntu/review for an RP2350 development board. Schematics/board have now been upgraded in place, no design edits allowed. Use working-with-kicad skill and connector API for inspection, web datasheets as needed. Read/write only workspace folder or connector/libraries. Work scratch/review-run/crystal/ only for new files, leave pre-existing scratch files untouched and don't rely on old review verdicts. Exported netlist at scratch/review-run/netlist.xml. Need evidence-backed true/false crystal and buttons; buttons includes assembled physical press access. Inspect guide oscillator ESR/load/drive requirements, exact BOM crystal and cap nets/layout, actual flash BOOTSEL wiring and RUN. Do not run DRC or refills (parent doing this); no design changes. Report concise evidence with source URLs and measurements, any important issues. Read-only review apart from scratch outputs.

| Check | Verdict |
|---|---|
| Crystal circuit suitability | **true**, with layout validation needed |
| BOOTSEL/RUN, including assembled press access | **true** for the open board using a narrow tool; fingertip access remains unverified |

**Crystal**

- Y1 is **Abracon ABM8-272-T3**, the exact [RP2350 guide](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf) recommendation. Its [datasheet](https://abracon.com/datasheets/ABM8-272-T3.pdf) specifies 12 MHz, ESR ≤50 Ω, 10 pF load, and 200 µW maximum drive.
- C25/C26 are 15 pF C0G Murata parts. R21 is 1 kΩ. Netlist and API copper connectivity confirm correct wiring, including C26 on the crystal side of R21 and grounded case pads.
- Load is **7.5 pF plus board/pin parasitics**. The guide's assumed 3 pF gives 10.5 pF, but that parasitic value is not measured here.
- Important layout concern: drawn track lengths are **XIN 4.63 mm, XTAL_O 4.01 mm, XOUT 8.78 mm**. XOUT changes layers through **two vias**. Validate startup across supply/temperature, frequency, and drive before release. This is not evidence of failure.

**Buttons**

- BOOTSEL correctly grounds **U1.60 QSPI_SS / U2.1 flash CS through R25 = 1 kΩ**. MCU-to-flash CS is direct.
- RUN correctly grounds **U1.26**, also connected to J6.10. Internal pull-ups support both circuits. The guide permits omitting the external CS pull-up for this W25Q128JVS flash family.
- Hold BOOTSEL while powering up, or hold it while pressing/releasing RUN.
- The top actuators are uncovered and **6.00 mm apart**. A centered 2 mm tool clears J5's drawn body by **2.46 mm**. RUN is **5.45 mm** from J4's body edge.
- **J5/J6 lack exact MPNs and are absent from the BOM.** Wider mating housings, cables, or an enclosure could obstruct access. Comfortable fingertip operation is not established.

[Full evidence, measurements and source URLs](scratch/review-run/crystal/review.md) · [Assembly render](scratch/review-run/crystal/buttons-assembled.png)

No design edits, DRC, or refills. New review outputs are confined to `scratch/review-run/crystal/`.

## Subagent: Review powerPath and thermal for RP2350 dev board in /home/ubuntu/review, designed brief USB-C power/data, LiPo charger power path no battery/flat battery, charged battery unplug USB should not reset/drop 3V3, full PCBWay assembly. Files upgraded in place no design edits. Read working-with-kicad and use connector API for board inspection, web TI/Raspberry Pi datasheets. Read/write only workspace or connector/libraries. Work scratch/review-run/power/ for outputs, do not use old scratch review verdicts as evidence. netlist.xml in scratch/review-run. Parent will run DRC and refill a copy scratch/review-run/check/board.kicad_pcb, coordinate don't run refills/DRC. Inspect BQ24074 and TLV757 topology, load currents and USB limits, switchover timing/dropout, charge startup; thermal copper EP vias narrow power routes worst full load. Return boolean powerPath, integer thermal 0-10 calibrated user:9-10 ship as-is;6-8 minor;3-5 hurts reliability;0-2 stops build/work. Give concrete evidence and datasheet URLs; challenge nominal assumptions and don't label guarantee without evidence.

```json
{"powerPath": false, "thermal": 5}
```

The basic topology is correct. The as-is design does not support the full operating brief without load and temperature limits.

**Power path**

- **Battery-independent startup is supported.** BQ24074 OUT feeds VSYS, then TLV75733 feeds 3V3. A missing or flat battery does not inherently prevent startup. DPPM reduces charging to prioritize the system.
- **USB current is the limiting factor.** EN1=VSYS and EN2=GND select USB500 permanently after startup. TI specifies **450/475/500 mA min/typ/max**, shared between system and charging. R5 does not provide a 1 A input budget in this mode.
- RM2 VIN is on VSYS, not 3V3. Its listed **271 mA TX operating point**, combined with a credible **300 mA 3V3 load**, requires approximately **571 mA**. A missing or flat battery cannot sustain this from USB500.
- R4 sets approximately **330 mA nominal charging**, **292–365 mA** including tolerances. That current is reduced under system load.
- USB-unplug operation is plausible with a healthy charged battery and modest load. It is **not a demonstrated no-reset guarantee**. TI provides no maximum transfer interruption time to check against effective capacitance, and there are no worst-load scope captures.
- At 1 A LDO load, a loaded 3.7 V battery minus the specified 100 mV charger-path drop and 475 mV LDO dropout leaves **3.125 V before PCB loss**. RP2350 VREG_AVDD and USB_OTP_VDD require at least **3.135 V**.

**Thermal: 5/10**

- U5 has useful thermal construction: a **1.68 mm exposed pad, four 0.20 mm thermal holes**, and broad filled ground copper. PCBWay must properly solder the EP and control solder wicking.
- U6 is **TLV75733PDBVR, ordinary DBV SOT-23**, not the thermally enhanced DYD package.
- U6 dissipates **0.48 W at 400 mA from 4.5 V**, or **0.8 W at 1 A from 4.1 V**. TI's DBV thermal figures are **100.8°C/W on its EVM** and **231.1°C/W on its JEDEC board**. Neither establishes this PCB's temperature, but they show why unrestricted continuous full load is unsafe to assume.
- The inspected power trunks are generally **0.40 mm**, with useful planes. IC linear losses dominate, rather than narrow trace self-heating.
- TS uses a fixed 10 kΩ resistor. **Battery temperature is not monitored.**

**Evidence and outputs**

[Full report](scratch/review-run/power/REPORT.md) · [Machine-readable verdict](scratch/review-run/power/verdict.json) · [Filled copper inspection](scratch/review-run/power/filled-F.Cu.png)

Sources: [BQ24074](https://www.ti.com/lit/ds/symlink/bq24074.pdf), [TLV757P](https://www.ti.com/lit/ds/symlink/tlv757p.pdf), [RP2350](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf), [RM2](https://datasheets.raspberrypi.com/rm2/rm2-datasheet.pdf).

Connector inspection and cleanup completed. No design edits, refills, or DRC runs performed.

## Subagent: Review physical layout, routing and silkscreen RP2350 dev board /home/ubuntu/review. Schematics and board now upgraded no design edits. Read working-with-kicad and use connector/KiCad view. Only read/write in workspace/connector/libraries. New outputs scratch/review-run/physical/; ignore pre-existing scratch verdicts. Parent runs DRC/refill in scratch/review-run/check/board.kicad_pcb; don't run DRC/refill. Check placement by function, antenna at edge/clear from RM2 guide, electrical short direct QSPI/USB/microSD routing and reference planes, power trace current, silkscreen pad overlaps text polarity labeling and readability. Original renders/ and layers/ exported in design KiCad version available. Read netlist scratch/review-run/netlist.xml and BOM. Return scores layout,routing,silkscreen 0-10:9-10 professional ship as is;6-8 minor;3-5 clear reliability/performance;0-2 stops working/build. Evidence measurements and source URLs. No edits except scratch reports/scripts/images. Parent independently grounding.

The main concerns so far are routing, rather than the overall component grouping. USB D+ and D- take separate paths instead of staying together, and the QSPI bus changes layers repeatedly. The core regulator's LX connection is also only 0.127 mm wide and uses two vias. I'm checking these measurements against Raspberry Pi's guidance and the parent's filled board before assigning scores.

## Subagent: Read-only review BOOTSEL/RUN for RP2350 dev board /home/ubuntu/review. User forbids design edits, DRC or refills. Only read/write workspace or connector/libraries; any NEW files ONLY scratch/review-run/crystal/ (use buttons-* prefix, do not touch pre-existing files). Do not read old review verdicts. Use working-with-kicad skill and connector API for current board inspection. Current exported netlist scratch/review-run/netlist.xml. Inspect actual flash wiring, resistor/pullups, MCU RUN, switch exact BOM PTS810SJM250SMTRLFS physical actuation access after assembly (bodies/heights from manufacturers, connector nearby etc.). Need evidence-backed true/false buttons includes physical access, concise measurement evidence sources URLs and caveats. Start own headless API socket under scratch/review-run/crystal/buttons.sock if needed, never save. Report conclusions to me and optional evidence file in allowed folder. Main agent handles oscillator; you own button electrical and mechanical investigation.

**buttons = true**, with an access caveat: both switches are electrically correct and reachable from above on the assembled open board. Comfortable fingertip operation with populated headers is not established.

| Check | Finding |
|---|---|
| BOOTSEL | SW1 pulls MCU U1.60 and flash U2.1 CS low through **R25 = 1 kΩ**. MCU-to-flash CS is direct. Current copper connectivity confirms this. |
| RUN/reset | SW2 grounds **U1.26 RUN**, also connected to J6.10. Current copper connectivity confirms this. |
| Pull-ups | Both use RP2350 internal pull-ups. Raspberry Pi's hardware guide permits omitting external CS pull-up for this W25Q128JVS flash family. |
| Exact switches | `PTS810SJM250SMTRLFS`: top-actuated, 4.2 × 3.2 mm body, 2.5 mm actuator height, nominal 1.6 N force. |
| Physical access | Centers are **6.00 mm apart**. Neither actuator is covered by another part. A 2 mm nonconductive tool has a clear vertical approach. |
| Nearby obstacles | J5 header body is **3.46 mm from each actuator center**. J4 LiPo body is **5.45 mm from RUN center**, with **3.35 mm body-to-body clearance**. J4 is 5.5 mm high and faces outward, away from the buttons. |

**Caveat:** J5/J6 lack exact manufacturer/MPN entries and are absent from the BOM. Their assembled heights and mating sockets cannot be certified. Cables, a carrier board, or an enclosure can change access.

Sources: [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf), [hardware guide §3.1](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf), [C&K/Littelfuse PTS810 drawing](https://www.littelfuse.com/assetdocs/littelfuse-ck-tactile-pts810-series-datasheet?assetguid=f1e4bc97-66e9-4beb-99c6-eaef0bd3bff4), [JST PH drawings, pages 2 and 4](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf).

[Full evidence and caveats](scratch/review-run/crystal/buttons-evidence.md) · [Placement image](scratch/review-run/crystal/buttons-placement.png) · [Assembly render](scratch/review-run/crystal/buttons-assembled.png)

No design edits, saves, DRC, or refills. Dedicated API server stopped.

## Subagent: Read-only independent review of LOAD CURRENT / supply-voltage requirements for RP2350 dev board workspace /home/ubuntu/review. Inspect fresh scratch/review-run/netlist.xml and bom.csv and relevant original schematics only, not old scratch verdicts. Fetch current Raspberry Pi RP2350 and relevant onboard WiFi/microSD/LED datasheets from official URLs. Quantify realistic and worst-case 3V3 loads, minimum rail requirements, and consequences for USB 100/500mA and TLV75733 1A. Do not edit designs, run DRC/refills, or touch outside workspace/connector/libraries. Scratch outputs only scratch/review-run/power/. Return concise concrete references and URLs plus what cannot be bounded (external connector loads). Main agent handles BQ24074/TLV757 topology and thermal/copper.

The 1 A TLV75733 has enough headroom for everything on the board. The tighter limit is the BQ24074's 450 mA minimum USB500 input limit, which also has to carry the RM2 radio and charging. There's one spec gap: the WS2812C's 3.3 V minimum supply leaves no margin on a 3.3 V ±1% rail.

I made no design edits and ran no DRC or refills. My notes, and the RP2350, RM2, TLV757P and BQ24074 PDFs, are in `scratch/review-run/power/`. There is no `bom.csv` in `scratch/review-run/`, so I used the root `bom.csv`. The schematic notes match `original/`.

**What the netlist shows**

- **+3V3 (U6 output):** all RP2350 supplies (VREG_VIN, VREG_AVDD through R20, IOVDD, QSPI_IOVDD, ADC_AVDD, USB_OTP_VDD), U2 flash, U3 PSRAM, the RM2's VDDIO only, J2 microSD, D1 WS2812C, J3 Qwiic pin 2, J5.4, J6.11, and the pull-ups.
- **VSYS (U5 OUT):** the LDO input, the RM2's VIN (U4.16), and J6.13. EN1 and R9 (to 3V3_EN, J5.14) also tie to VSYS.
- **VBUS:** the D2 charge LED through R6 (about 3 mA while charging), the R12/R13 divider (30 µA), and J6.14. J6.12 connects straight to VBAT.

**3V3 load (mA)**

| Load | Realistic | Worst | Reference |
|---|---|---|---|
| RP2350, all supplies | 16–30 | about 130 (VREG_VIN about 110 at the 200 mA core limit, plus QSPI_IOVDD 20) | RP2350 datasheet, tables 1683, 1689, 1693 |
| RP2350 GPIOs sourcing external loads | 0 | 100 (IIOVDD_MAX) | table 1683 |
| W25Q128JV flash | 2–12 | 25 (program or erase) | ICC3–ICC7 |
| APS6404L PSRAM | 1–7 | 7 | table 9 |
| microSD | 0.1–100 | 100 at Default Speed, 200 at High Speed (1 s average), with peaks of several hundred mA for about 1 ms | SD spec; Swissbit AN2111 |
| WS2812C-2020-V6 | 0–15 | 15 (5 mA per channel) | Worldsemi |
| RM2 VDDIO, pull-ups | 2–5 | about 7 | resistor values |
| **Onboard total** | **about 50 idle, about 150 during SD writes** | **about 385, or about 490 with GPIO sourcing** | |

The RM2's VIN is on VSYS, not 3V3. It draws 1.19 mA in power save, 43 mA receiving and 271 mA transmitting (MCS7 at 16 dBm). So the VSYS load is about 50–320 mA realistic and about 0.7 A worst case.

**Minimum rail voltages**

The tightest 3V3 limits are 3.135 V for the RP2350's VREG_AVDD and USB_OTP_VDD, and 3.3 V ±5% for the RM2's VDDIO. The WS2812C-2020-V6 needs at least 3.3 V, but the LDO can sit 1% lower. That puts it out of spec at nominal, with no margin at all.

The TLV75733 (SOT-23 package) has a maximum dropout of 425 mV at 1 A and 85 °C, or 475 mV at 125 °C. That is about 0.43–0.48 Ω.

| 3V3 load | VSYS to keep 3V3 ≥ 3.135 V | VSYS to stay in regulation (3.267 V) |
|---|---|---|
| 50 mA | 3.16 V | — |
| 150 mA | 3.20 V | 3.34 V |
| 400 mA | 3.31 V | 3.46 V |
| 1 A | 3.61 V | — |

The battery-to-VSYS drop is at most 100 mV at 1 A. The RM2 needs VIN of at least 3.0 V and loses RF performance below 3.2 V. So firmware should cut off at about 3.3–3.4 V on VBAT_SENSE (GPIO28). Below that, the 3V3 rail drops out of spec gradually, with no clean brownout.

**Effect on USB power**

The BQ24074 input limit is 450/475/500 mA (min/typ/max) in USB500 mode and 90/95/100 mA in USB100 mode. The 2.7 kΩ ISET resistor sets charging at 295–361 mA.

- **USB500 with a battery:** the realistic 50–320 mA load fits. During radio transmits, the charger's power-path control (DPPM) cuts the charge current instead.
- **USB500 without a battery:** SD writes plus a transmit burst come to about 420 mA, about 30 mA under the limit. Any external load or the worst-case SD or core current goes past 450 mA. VSYS then sags, and the board browns out.
- **USB100:** this fits only with Wi-Fi off and no charging.
- **USB compliance:** the design draws up to 500 mA before USB enumeration, with Rd-only Type-C default power. Strictly, USB 2.0 allows 100 mA until the host configures the device.
- **For your topology review:** EN1 is tied to VSYS, so the charger starts in USB100 mode until VSYS passes the 1.4 V logic threshold.

**TLV75733 rating**

The 1 A rating leaves at least 0.5 A over the roughly 0.4–0.5 A worst-case onboard load. Its current limit is 1.2 A min, 1.55 A typ, 1.78 A max, with 755 mA short-circuit foldback. At 4.4–4.5 V on VSYS, it dissipates 0.18 W at 150 mA, 0.48 W at 400 mA and 1.2 W at 1 A. Those numbers are for your thermal and copper check.

**Loads I can't bound**

- Qwiic J3 pin 2 and header pads J5.4 and J6.11 on 3V3. Only the LDO limit of 1.2–1.78 A caps them.
- GPIO sourcing. The RP2350 spec says 100 mA total, but nothing enforces it.
- J6.13 on VSYS. It takes from the same 450 mA USB budget and bypasses the LDO.
- J6.12 on VBAT. It bypasses the BQ24074, so only the cell's protection circuit limits it.
- J6.14 on VBUS. Its draw is set by the host or adapter.
- Hot-inserting a microSD card onto 3V3. There is no load switch, so the inrush dip can reach the RP2350. I didn't quantify it; it needs a bench test.

**Sources**

- RP2350 datasheet: https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf
- RM2 datasheet: https://datasheets.raspberrypi.com/rm2/rm2-datasheet.pdf
- Pico 2 W datasheet (recommends keeping its 3V3 pin under 300 mA): https://datasheets.raspberrypi.com/picow/pico-2-w-datasheet.pdf
- TLV757P (SBVS322C): https://www.ti.com/lit/ds/symlink/tlv757p.pdf
- BQ24074 (SLUS810N): https://www.ti.com/lit/ds/symlink/bq24074.pdf
- W25Q128JV: https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf
- APS6404L: https://www.apmemory.com/en/downloadFiles/032411212009597427
- WS2812C-2020-V6: https://www.world-semi.com/products/ws2812c-2020-v6.html and https://datasheet.lcsc.com/datasheet/pdf/8c7f104c99e52e4adb687ae84e594e95.pdf?productCode=C55109522
- SD Physical Layer Simplified Specification: https://www.sdcard.org/downloads/pls/
- Swissbit AN2111 (SD card supply current): https://www.astutegroup.com/wp-content/uploads/2024/07/AN2111en_SD_Memory_Card_Design-in.pdf

The RP2350 efficiency table didn't extract cleanly, so I assumed 63–72%. That puts the 110 mA worst-case VREG_VIN figure within about ±15%.

## Subagent: Read-only RP2350 physical review in /home/ubuntu/review. Task solely silkscreen: inspect original renders/ and layers/*Silkscreen.png plus actual board with KiCad connector/kicad-view (read working-with-kicad). Read BOM and scratch/review-run/netlist.xml for functions. Do not read pre-existing scratch verdicts. No DRC/refill, no design changes. Only read/write within workspace/connector/libraries; any new scripts/reports/images under scratch/review-run/physical/silkscreen/. Check text/pad overlaps, readability/min text geometry, connector functional labels and polarity. Give 0-10 score (9-10 professional ship as is;6-8 minor;3-5 clear reliability/performance;0-2 stops working/build), exact references, measured evidence and images. Use original board.kicad_pcb or parent-filled scratch/review-run/check/board.kicad_pcb when available read-only. Focus useful actionable findings, not cosmetic preference. Return concise findings; don't edit other tasks' files.

I updated [report.md](scratch/review-run/physical/silkscreen/report.md) with the source URLs and the corrections you asked for. The score stays at 7/10. The review is still read-only: no board copies, no DRC or zone refill, and no design changes.

What changed in the report:
- **Inputs:** it now says the root `board.kicad_pcb` was resaved in the KiCad 10.99 format, so it is not the original. The originals are in `scratch/review-run/original/`, and only `renders/` and `layers/*Silkscreen.png` come from the original design. Both boards have the same counts: 35 board texts, 417 silkscreen references and 82 footprints.
- **JLCPCB:** it is now labelled as one example fab, not a universal minimum, and I removed the claim that JLCPCB holds orders.
- **L1 dot side:** I also removed my claim that Raspberry Pi's reference puts the dot by the +1V1 pad. It came from a forum post and a third-party repo, not an official source. The fix now says to match the Minimal KiCad reference and confirm the side before release.

Sources (all four were checked; the three Raspberry Pi and Particle links returned HTTP 200 just now):
1. Inductor polarity and the dotted Abracon part, from Raspberry Pi's "Hardware design with RP2350": https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf
2. Raspberry Pi's Minimal KiCad reference design, to confirm which side gets the dot: https://datasheets.raspberrypi.com/rp2350/Minimal-KiCAD.zip
3. LiPo polarity, from Particle's battery page ("there is no standard for polarity"): https://docs.particle.io/hardware/power/batteries/
4. Example silkscreen minimums, from JLCPCB's capabilities page, Legend section: https://jlcpcb.com/capabilities/pcb-capabilities

## Subagent: Read-only RF placement review in /home/ubuntu/review RP2350 dev board. Task solely RM2 module antenna placement against official RM2 guide, surrounding module/board edge copper clearance. Read working-with-kicad and use connector kicad-view read-only, BOM and scratch/review-run/netlist.xml. Use official fresh source URLs via scrape/search; document actual measurements compared to guide. No DRC/refill and no design changes. Ignore pre-existing scratch verdicts. Only read/write workspace/connector/libraries and any new outputs under scratch/review-run/physical/rf/. Inspect original renders/layers and actual root board or parent-filled scratch/review-run/check/board.kicad_pcb. Parent independently grounding so focus RF placement/keepout and board edge, not whole grounding review. Return concise evidence/report/source URLs and confidence; no generic claims without board measurements.

U4 (the RM2) passes the official keepout. There is no copper of any kind inside the on-board part of the RM2 RF keepout, on any of the four layers. The antenna end sits 0.5 mm from the top board edge, centred. Confidence is high for the board geometry and medium for real-world RF, because part of the keepout lies off the board and depends on the enclosure.

I made no design edits and ran no DRC or refill, and the root `board.kicad_pcb` is untouched. Everything I wrote is under `scratch/review-run/physical/rf/`.

**What I measured**

The root board has no zone fills. So I measured the parent's filled `check/board.kicad_pcb` from a byte-identical copy, `filled_snapshot.kicad_pcb`. Its placement and copper match the root board. All values are absolute mm.

| Item | Datasheet guide (Fig. 6) | Board | Result |
|---|---|---|---|
| Module body | 14.5 × 16.5 | x 107.99–122.49, y 50.5–67.0, 0°, antenna toward the top edge | OK |
| Keepout | 35.5 × 18.5, centred, bottom edge 5.0 below module top | x 97.49–132.99, y 37.0–55.5 | Matches |
| Keepout on the board | | x 100–130.48, y 50–55.5 | |
| Keepout off the board | | 13.0 above the top edge, 2.51 past each side | |
| Module top to board edge | | 0.50 | At the edge |
| Module sides to board edges | | 7.99 left, 7.99 right | Centred |
| Copper inside the on-board keepout | None allowed | 0 tracks, vias, pads, fill or graphics on every layer | Pass |
| Top edge of the copper pours | At the keepout line | y = 55.500 on all four layers | Pass |
| Pour gap to the side board edges | | 0.30, the project's edge-clearance minimum | OK |
| RM2 pin 1 and pin 21 pad tops | Just below the keepout | 0.20 below | Matches |
| Nearest other copper | | J5.1/J6.1 GND header pads 1.27, FID1 1.60, GPIO19 via 1.85 | Outside |
| Nearest other part outlines | | J5/J6 0.34, R12/R13 about 3.9 | Outside |

The board's RM2 pads match Raspberry Pi's own KiCad footprint (RP-008966, Oct 2025) and the Fig. 6 dimensions. Raspberry Pi's footprint draws the keepout 20.0 mm tall instead of the datasheet's 18.5. Both share the same bottom edge, so the difference lands entirely off the board here.

**Findings**

1. **Pass:** the on-board keepout has no metal on any layer.
2. **Product-level risk:** 13 mm of the keepout above the board and 2.5 mm on each side are off the PCB. Enclosure metal, screws, a carrier board, the battery or cables must stay out of x 97.5–133, y 37–50. The board file can't check this.
3. **Low risk:** the J5 and J6 header pin 1 pads are the closest metal to the antenna. They start 1.27 mm below the keepout, so they comply.
4. **Library gap:** the stock KiCad `RF_Module:RMC20452T` footprint's own keepout leaves out In2.Cu. The board's "RM2 antenna keepout" rule area covers all four layers, so the board is protected today. If that rule area is deleted or the module moves, In2.Cu loses protection.
5. **For your grounding review:** under the module, below the keepout, the GND pour covers 99.4 % on In1.Cu, 94.0 % on B.Cu and 76.6 % on F.Cu. B.Cu is cut by the GPIO19/GPIO21 tracks near pins 17–21. In2.Cu under the module is +3V3, not GND.

One thing to watch if you check the renders: `kicad-view` shades zone outlines, not the actual fill. Its images look like copper reaches the board edge. `fill_keepout_4layers.png` and the original `layers/board-*_Cu.png` show the real fill, and both stop at y 55.5.

Evidence is in `scratch/review-run/physical/rf/`:
- [REPORT.md](scratch/review-run/physical/rf/REPORT.md)
- [fill_keepout_4layers.png](scratch/review-run/physical/rf/fill_keepout_4layers.png)
- [ds_p10_fig6.png](scratch/review-run/physical/rf/ds_p10_fig6.png)
- [measure.py](scratch/review-run/physical/rf/measure.py) and [measure_filled.json](scratch/review-run/physical/rf/measure_filled.json)

![Filled copper per layer with the datasheet keepout](scratch/review-run/physical/rf/fill_keepout_4layers.png)

**Sources**
- RM2 datasheet, Release 7, built 20/02/2026, sections 2.4 (Fig. 6) and 2.6: https://pip-assets.raspberrypi.com/categories/1216-raspberry-pi-radio-module-2/documents/RP-008943-DS-7-Radio%20Module%202%20Datasheet.pdf. The footprint's `https://datasheets.raspberrypi.com/rm2/rm2-datasheet.pdf` link redirects here.
- Raspberry Pi RM2 design files, including the KiCad footprint: https://pip.raspberrypi.com/categories/1223-design-files
- Not read: the RM2 antenna pattern documents on Raspberry Pi's product portal, because they need an account.
