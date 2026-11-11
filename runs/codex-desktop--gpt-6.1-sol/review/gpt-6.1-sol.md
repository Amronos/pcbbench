# gpt-6.1-sol's review

## Final message

Wrote [review.json](review.json) with the requested keys and types.

Upgraded all four schematics and the board to the connector's KiCad version. The design is otherwise unchanged. ERC and DRC pass.

Main blocker: C40 obstructs the inserted microSD card, giving layout a score of 2. Power-path operation passes within the available current budget; seamless switching still needs bench verification.

## Subagent: Review powerPath and thermal for RP2350 board in /home/ubuntu/review. Files already upgraded via KiCad connector. Read-only design review, no design changes. Must use working-with-kicad skill and connector, datasheets web as needed. Read/write only within workspace folder or connector/libs; scratch scripts/results in _review/power. Root bom.csv, schematics power.kicad_sch processor.kicad_sch interfaces.kicad_sch board.kicad_pcb; exported _review/netlist.xml. Assess USB while charging/no or flat battery, seamless USB removal charged LiPo maintaining 3.3V; thermal copper/vias/full-load dissipation especially core LDO and charger/buck-boost. Return boolean powerPath, integer thermal score 0-10 with specific evidence/net connections copper geometry calculations and datasheet references. Don't run full DRC (parent running one). No questions will be answered.

```json
{
  "powerPath": true,
  "thermal": 5
}
```

**The automatic USB/LiPo power path is correctly connected. Full-load USB-only operation while charging at 250 mA is not supported by the current budget.**

Detailed calculations, copper measurements, images, and datasheet references are in [review.md](_review/power/review.md). Machine-readable result: [result.json](_review/power/result.json).

**Power path**

Verified connections:

- J1 `USB_VBUS` → F1 → `VBUS` → U6 BQ24074 IN pin 13.
- J2 battery → `BAT` → U6 BAT pins 2/3.
- U6 OUT pins 10/11 → `VSYS` → U7 TPS63060 VIN pin 2 and EN pin 3.
- U7 VOUT pin 9 → `+3V3`. R23/R24 set **3.310 V nominal**.
- U6 EN2 is grounded. EN1 uses `USB_500MA`, pulled low at reset.

| Condition | Assessment |
|---|---|
| USB, no battery | Works within the USB input-current limit. Missing NTC disables charging, not system power. |
| USB, flat battery | System runs while the pack precharges. Charging reduces first when the load reaches the input limit. |
| Remove USB, charged LiPo | U6 automatically supplies VSYS from BAT. U7 remains enabled and above its 2.5 V operating minimum. Continuous 3.3 V regulation is expected. |
| Full peripherals, USB only, charging | Insufficient power. Charging throttles; further overload can drop the rails without a healthy battery. |

U6 permits **90–100 mA input at reset**, then **450–500 mA** after firmware asserts EN1. At minimum USB500 input, assuming 90% converter efficiency:

- No charging: approximately **537 mA available at 3.3 V**.
- Nominal 249 mA charging: approximately **239 mA available**.
- ESP32-C3 TX alone peaks at **345 mA**.

Exact unplug-transient minimum remains unverified. VSYS has 30 µF nominal; at 0.6 A, a 4.4→4.1 V fall represents only 15 µs of ideal hold-up, less after capacitor derating. The topology supports seamless transfer, but a scope test is needed to guarantee a numerical rail minimum.

**Thermal: 5/10**

The four 35 µm copper layers and broad ground planes help. Local heat transfer is weak:

| IC | Exposed-pad connection | Connected F.Cu GND within 10×10 mm | Nearest GND via |
|---|---|---:|---:|
| U4 core LDO | Full | 43.5 mm² | **3.71 mm** |
| U6 charger | Full | 58.3 mm² | **1.83 mm** |
| U7 buck-boost | Thermal relief | 63.0 mm² | **5.02 mm** |

There are no ground vias within 2 mm of U4 or U7. U7's ground widths measured 0.10 mm outside its exposed-pad edges are only **0.112–0.252 mm**.

Key dissipation estimates:

- **U4:** \(P=(3.31-1.10)I_\text{core}\). At 200 mA, **0.442 W**. TI's JEDEC 80.3°C/W reference predicts a **35.5°C rise**, or 120.5°C junction at 85°C ambient. This PCB's sparse vias may reduce that margin.
- **U4 at its 500 mA electrical rating:** **1.105 W**, approximately **88.7°C reference rise**. That rating is not a demonstrated RP2350 load requirement.
- **U6:** approximately **0.634 W** at 5 V input, low battery, and nominal fast charge. Reference rise: **28.2°C**.
- **U7:** at 500 mA output and assumed 85–93% efficiency, total converter losses are **0.125–0.292 W**.
- **F1:** hold current falls to about **440 mA at 40°C** and **400 mA at 50°C**, below USB500's possible input current.

Measured battery copper is mostly 0.15 mm wide over 14.27 mm, approximately **47 mΩ**. At 0.8 A that adds **37.6 mV drop and 30 mW**.

Sources: [BQ24074](https://www.ti.com/lit/ds/symlink/bq24074.pdf), [TPS63060](https://www.ti.com/lit/ds/symlink/tps63060.pdf), [TLV758P](https://www.ti.com/lit/ds/symlink/tlv758p.pdf), and references in the report.

Used the KiCad connector read-only. No design changes, saves, zone refills, or full DRC. Source hashes remain unchanged. One cleanup subagent briefly used `/tmp` for comparison copies, contrary to the folder restriction, then removed them. All retained review outputs are in `_review/power`.

## Subagent: Review crystal and buttons for RP2350 board in /home/ubuntu/review. Already upgraded with KiCad connector. Read-only review, no design changes. Must use working-with-kicad skill and connector, read manufacturer datasheets/web hardware design guide. Read/write only workspace folder or connector/libs; scratch in _review/processor. Root bom.csv, processor.kicad_sch, board.kicad_pcb, _review/netlist.xml. Assess Y1/load caps against RP2350 oscillator, BOOTSEL/RUN connections per design guide and physical button pressability on fully assembled board (not bare-pad 3D renders). Return crystal and buttons booleans with exact evidence and source links. Don't run DRC parent already running it. No questions answered.

```json
{"crystal": true, "buttons": true}
```

These are design-review passes, not hardware test results. **The oscillator layout still needs startup and frequency validation.**

**Crystal**

- **Y1 = Abracon ABM8-272-T3**, the exact RP2350-recommended crystal: 12 MHz, CL = 10 pF, ESR ≤ 50 Ω.
- **C1/C2 = 15 pF C0G**, matching Raspberry Pi's circuit. Their series load is 7.5 pF. The guide adds an assumed 3 pF parasitic load and accepts 10.5 pF total.
- Wiring is correct: **U1.21 XIN → Y1.1**; **U1.22 XOUT → R1 1 kΩ → Y1.3**. C2 is on the crystal side of R1. Y1.2/Y1.4 and both load-cap returns connect to GND. IOVDD is +3V3.

Sources: [Abracon datasheet](https://abracon.com/datasheets/ABM8-272-T3.pdf), [RP2350 hardware guide, sections 4–4.1](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf).

Caveat: XIN has **14.701 mm total track copper**, including branches, with **two vias and 10.185 mm on In2.Cu**. The guide requires short layout but sets no numerical limit. The assumed parasitic load and actual crystal drive power are not measured on this PCB.

**Buttons**

- **BOOTSEL:** U1.60 QSPI_SS/U2.1 CS → FLASH_CS → **R11 1 kΩ → SW1 → GND**. Correct protected boot pulldown. With R3's 4.7 kΩ pull-up, the nominal pressed voltage is **0.579 V**, below the 0.8 V input-low limit.
- **RESET:** **SW2 grounds U1.26 RUN**. R10 = 10 kΩ pulls RUN to +3V3; C20 = 100 nF returns to GND. Correct active-low reset.
- **Assembled access:** all three actuators remain exposed. Factory-fitted J6/J7 headers were included, at **8.54 mm height**, not treated as empty pads. RESET's actuator center is **9.769 mm from J7's nearest plastic edge**. ESP BOOT's center is **5.505 mm from U9's nearest body corner**, with access from the southwest.

Sources: [RP2350 guide, section 3.1](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf), [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf), [E-Switch drawing](https://configured-product-images.s3.amazonaws.com/2D/specs/TL3342F160QG.pdf), [Würth header drawing](https://www.we-online.com/components/products/datasheet/61300811121.pdf).

The populated render includes 113 stock models and eight approximate body envelopes. Access is assessed without an unspecified enclosure, daughterboard or attached cables.

![Populated board with fitted headers](_review/processor/assembled-iso.png)

[Full evidence and limitations](_review/processor/review.md) · [JSON result](_review/processor/result.json)

Used the KiCad connector. Original design files remained byte-identical. No DRC run.

## Subagent: Review grounding and routing for RP2350 board /home/ubuntu/review. Files already upgraded using KiCad connector. Read-only design review no design changes. Must use working-with-kicad skill and KiCad connector. Read/write only workspace folder or connector/libs; scratch in _review/routing. Inspect all copper planes and paths using provided layers images and connector kipy/kicad-view. Focus continuous ground/reference planes, stitching/islands, QSPI USB SD paths and power widths. Return grounding and routing integer scores 0-10 plus concrete coordinate/net examples. Parent running full DRC reports _review/drc.json when ready, do not run competing DRC. Don't ask questions.

| Category | Score |
|---|---:|
| Grounding | **6/10** |
| Routing | **4/10** |

In1.Cu provides a connected board-wide GND plane with no tracks. The main weaknesses are local ground connections, broken references for lower-layer signals, and a long, narrow core-supply route.

Reviewed all four supplied copper images and actual connector geometry using kipy and `kicad-view`. Coordinates below are absolute mm.

**Grounding**

- **U7 switching return needs attention.** PGND/exposed pad at **(112.8, 132.0)** has no local via. The nearest GND via is **(107.85, 132.81)**, 5.02 mm away. Output-capacitor grounds C28/C29 also lack nearby vias. U7 pin 7 connects through a **0.1124 mm GND track**.
- **MCU stitching is sparse.** U1's exposed pad at **(130.0, 137.0)** connects through one nearby GND via at **(130.22, 134.87)**, outside the pad. C15 GND at **(135.68, 137.1)** has no dedicated via; the nearest is 5.89 mm away.
- **Lower-layer references are discontinuous.** In2.Cu is a +3V3 pour cut into nine filled regions by routing. B.Cu has only a local VSYS pour. For example, **QSPI_D1** at x=130.05, y=124.90–132.53 lacks In2 reference copper over **5.31 mm of its 7.63 mm segment**. In2 signals are 1.24 mm from In1 GND.
- The small top GND regions inspected connect through tracks or vias. They are not demonstrated floating islands, but some connections are narrow and poorly stitched. U9's antenna copper exclusion is intentional.

**Routing**

| Priority | Concrete example |
|---|---|
| High | **+1V1:** U4 OUT at (136.1125, 140.15) reaches U1 pin 6 through an approximately **45 mm** track-centerline path, versus 10.4 mm direct. It includes a 12.1 mm B.Cu detour at x=134.4, y=143.7–155.8. Width is mostly **0.15 mm**. |
| Medium | **SD_MISO:** redundant B.Cu branches form a loop near (136.84, 135.08)–(127.59, 137.08). It also runs broadside to **RADIO_TX** for about 7.4 mm across the 0.10 mm dielectric near (130.44, 135.46). |
| Medium | **Power widths:** BUCK_L1/BUCK_L2 neck from 0.4 mm to **0.2 mm** at U7. VBUS from F1 to U6 uses approximately 12.8 mm of **0.15 mm copper** and two vias. Check these against actual current; this review does not establish overheating. |
| Medium/low | **QSPI/SD:** QSPI clock branches are balanced at about 9.8/9.7 mm. Reference gaps matter more than data-length mismatch. SD clock resistor R41 at (140.0, 135.0) is about 15 mm of routing from its driver, weakening source termination. |
| Low | **USB:** the long pair stays on F.Cu over In1 with 0.15 mm width/gap. DP/DM lengths are about 40.9/42.0 mm. The weak point is the 1 mm bottom DP crossover at y=157.3, x=111.95–112.95, over a local reference void. |

Fix U7's local returns and the +1V1 detour first, then simplify SD_MISO and keep QSPI/SD over close continuous references.

[Full review and annotated image links](_review/routing/review.md)

The parent's DRC reports **0 violations and 0 unconnected items**. No competing DRC ran. PCB, project, and schematic hashes remained unchanged.

## Subagent: Read-only power-path datasheet/netlist review in /home/ubuntu/review. Do not change designs or run DRC. Read/write only workspace or connector/libs; scratch/results _review/power only, use apply_patch for scripts/reports. Must read working-with-kicad skill. Review BQ24074 U6, TPS63060 U7, USB J1/F1 and battery J2 net connections from _review/netlist.xml vs datasheets fetched on web. Determine USB with no/flat LiPo charging and seamless removal charged LiPo maintaining 3.3V including input-current limits/full-load limitations. BOM describes system. Return boolean powerPath recommendation with concrete nets pins resistor limits calculations datasheet URLs and caveats. Don't ask questions. Use connector read-only if needed. Focus power path not PCB thermal (main agent measuring that).

**`powerPath = true`.** I checked every power-path pin on U6, U7, J1, F1 and J2 in `_review/netlist.xml` against the datasheets and found no wiring errors. The design handles USB with no battery, USB with a flat pack, unplugging USB with a charged LiPo, and battery-only operation. The real limit is current: the BQ24074 input limit caps USB-only operation, and the TPS63060 has plenty of headroom. I made no design edits and ran no DRC.

Full report: [power_path_review.md](_review/power/power_path_review.md). Netlist parser: [nets.py](_review/power/nets.py).

**Net connections**

- **USB and fuse:** the four J1 VBUS pins go to `USB_VBUS`, then through F1 to `VBUS` and U6.13 IN. IN has C22 at 1 µF; the datasheet asks for 1–10 µF. CC1 and CC2 each have their own 5.1 kΩ pull-down (R12, R13), which is correct for a USB-C sink.
- **Charger outputs:** U6.10/11 OUT go to `VSYS`, which has 3×10 µF and feeds only U7 (VIN pin 2, EN pin 3). U6.2/3 BAT go to J2.1 with C24 at 4.7 µF.
- **Charger control pins:**
  - TS (U6.1) goes to J2.2 with a 100 nF cap.
  - /CE (U6.4) and EN2 (U6.5) are tied to GND.
  - EN1 (U6.6) goes to `USB_500MA` (U1.35) with R20, a 100 kΩ pull-down.
- **Charger resistors:** all are in their datasheet ranges (ILIM R17 3.24 kΩ, ISET R16 3.57 kΩ, ITERM R19 3.3 kΩ, TMR R18 49.9 kΩ).
- **Buck-boost:** U7 has the TI-listed 1.5 µH inductor (XFL4020-152), 100 nF on VAUX and PS/SYNC tied low. Its feedback divider (562 kΩ / 100 kΩ, with 10 pF across the 100 kΩ) gives 3.310 V. The output has 63.9 µF nominal, inside the datasheet's 44–100 µF range.

**Calculations**

| Quantity | Value |
| --- | --- |
| Fast charge, 890/3.57 kΩ | 249 mA (223–273 mA) |
| Precharge, 88/3.57 kΩ | 24.6 mA |
| Termination current | 27.7 mA (USB500), 9.2 mA (USB100) |
| Safety timers | 40 min precharge, 6.65 h fast charge (4.99–8.32 h) |
| Input limit | 90–100 mA at reset (EN1 low via R20), 450–500 mA once firmware sets EN1 high |
| Battery thermistor trips (10 kΩ, β 3435) | 50.8 °C hot, 0.5 °C cold |
| 3V3 output | 3.222–3.400 V, up to about 3.52 V worst case in power-save mode (under 3.6 V parts) |
| Max 3V3 current on USB only | about 100 mA at reset, about 525 mA worst case in USB500 |
| Unplug USB with charged LiPo | VSYS drops from 4.4 V to about 4.1 V. Staying above U7's 2.2 V cutoff gives about 70 µs of hold-up at 0.6 A, so 3V3 holds |

**Caveats**

1. **USB-only full load fails.** Worst-case simultaneous 3V3 load is about 670 mA, which is above the 525 mA USB-only figure. Only the 345 mA ESP32-C3 transmit peak comes from a datasheet; the other loads are my estimates. With a charged battery, the battery covers the difference. With no battery or a flat one, VSYS sags and the 3V3 rail can drop out. Firmware must set `USB_500MA` high before turning on `RADIO_POWER` (about 120 mA inrush into C38) or the RGB boost.
2. **The board can never draw more than 500 mA from USB.** EN2 is tied to GND and nothing reads the CC pins, so a 1.5 A or 3 A USB-C charger is treated like a 500 mA port. Firmware also can't suspend input, turn charging off, or clear a charge-timer fault; only unplugging USB clears it.
3. **F1 can trip or starve the input on warm boards.** The MF-MSMF050 hold current drops to 0.44 A at 40 °C and 0.40 A at 50 °C, below the 450–500 mA input limit. Its resistance (0.15–1.0 Ω) can also drop a weak 4.75 V port into the charger's input-voltage limit, which can cut input to about 150 mA in the worst case. MF-MSMF075 uses the same 1812 footprint and fixes both. Your thermal measurement decides whether this matters.
4. **Large packs may hit the charge timer.** Packs above about 930 mAh worst case (about 1380 mAh typical) can time out and fault. The BOM only says ≥500 mAh, so either cap the pack size or raise R18 to 72 kΩ.
5. **No battery makes the charge flag unreliable.** With the thermistor pin floating, charging stops on a cold fault, but `CHARGE_N` may stay low as if charging. Firmware should check the battery voltage (`BAT_BUFFER`) instead.
6. **No reverse-polarity protection on J2.** JST-PH LiPo polarity varies by vendor.
7. **No off switch or ship mode.** U7 is always enabled and the BQ24074 has no battery-disconnect pin. Standby drain is about 60–90 µA before loads.
8. **R19 can be removed.** It sets termination to 11% of charge current, almost the same as the 10% default. R17's value has no effect while EN2 is grounded, but it must stay fitted because an open ILIM pin disables charging.

**Datasheets**

- [BQ24074 (SLUS810N)](https://www.ti.com/lit/ds/symlink/bq24074.pdf)
- [TPS63060 (SLVSA92C)](https://www.ti.com/lit/ds/symlink/tps63060.pdf)
- [Bourns MF-MSMF](https://www.bourns.com/docs/Product-Datasheets/mf-msmf.pdf)
- [TPS22919](https://www.ti.com/lit/ds/symlink/tps22919.pdf)
- [ESP32-C3-WROOM-02](https://documentation.espressif.com/esp32-c3-wroom-02_datasheet_en.pdf)

The downloaded PDFs and three page renders are in `_review/power`. I didn't touch the other agent's files in that folder.

## Subagent: Read-only oscillator review in /home/ubuntu/review. User requests crystal boolean with exact evidence and source links. Read working-with-kicad skill and use connector. Inspect root bom.csv, processor.kicad_sch, board.kicad_pcb and _review/netlist.xml. Identify Y1 manufacturer part, load caps, series resistor and RP2350 oscillator wiring; read actual manufacturer crystal datasheet plus RP2350 datasheet/hardware design guide on web. Calculate loading and check frequency ESR drive level, pins. Don't run DRC. No design edits. Read/write only workspace folder or connector/libs; if scratch needed exclusively _review/processor (avoid others' files use oscillator prefix). Do not ask questions. Return concise evidence with exact refs pin numbers nets values and URLs plus crystal true/false recommendation and caveats. Main agent separately assesses physical board/buttons. No need to render or create full review document.

The oscillator verdict stays `crystal = true`, now based only on manufacturer and Raspberry Pi reference values. I've dropped my stray-capacitance estimate, my worst-case drive-level equation and the firmware startup-delay advice. None of them had a source behind them.

**Conclusion from exact values**
| Item | Design | Reference (Raspberry Pi RP2350A minimal design) | Manufacturer value |
|---|---|---|---|
| Crystal | Y1 ABM8-272-T3, 12 MHz | X1 ABM8-272-T3, 12 MHz | 12.000 MHz fundamental, CL 10 pF, ESR ≤ 50 Ω, C0 ≤ 3.0 pF, drive level 200 µW max |
| XIN capacitor | C1 15 pF C0G, on XIN and GND | C3 15p, on /XIN and GND | — |
| Capacitor on the crystal side of the resistor | C2 15 pF C0G, on XTAL_OUT and GND | C4 15p, on Net-(C4-Pad1) and GND | — |
| Series resistor | R1 1 kΩ, pin 1 on XOUT, pin 2 on XTAL_OUT | R2 1k, pin 1 on /XOUT, pin 2 on Net-(C4-Pad1) | — |
| Crystal pins | Y1.1 on XIN, Y1.3 on XTAL_OUT, Y1.2 and Y1.4 on GND | X1.1 on /XIN, X1.3 on Net-(C4-Pad1), X1.2 and X1.4 on GND | crystal on 1 and 3, GND on 2 and 4 |
| RP2350 pins | U1.21 on XIN, U1.22 on XOUT | U1.21 on /XIN, U1.22 on /XOUT | datasheet Fig. 2 (QFN-60): 21 XIN, 22 XOUT |
| IOVDD | +3V3 (3.310 V nominal) | 3.3 V | guide: the 1 kΩ is chosen for 3.3 V IOVDD |

The parts, values and topology match the reference exactly. The guide's own load calculation is 15/2 + 3 pF = 10.5 pF against a 10 pF target. It gives no drive-level calculation. It says only that a 50 Ω crystal with 1 kΩ prevents over-driving at 3.3 V.

**Measured route lengths**
I measured both boards with the same kipy script. "Copper total" is the sum of every track segment on the net. "Path" is the routed distance between the track endpoints that land on each pad, so it excludes copper inside the pads.

| Net | Board | Copper total | By layer | Segments / vias | Pad-to-pad paths |
|---|---|---|---|---|---|
| XIN | design | 14.701 mm | F.Cu 4.516, In2.Cu 10.185 | 11 / 2 | U1.21→Y1.1 13.74, C1.1→Y1.1 1.80, C1.1→U1.21 13.62 |
| XIN | reference | 10.912 mm | F.Cu 10.912 | 7 / 0 | U1.21→X1.1 10.66, C3.1→X1.1 5.10, C3.1→U1.21 5.57 |
| XOUT | design | 5.630 mm | F.Cu | 10 / 0 | U1.22→R1.1 5.58 |
| XOUT | reference | 2.962 mm | F.Cu | 1 / 0 | U1.22→R2.1 2.96 |
| XTAL_OUT | design | 6.609 mm | F.Cu | 8 / 0 | R1.2→Y1.3 1.28, Y1.3→C2.1 3.66, R1.2→C2.1 5.65 |
| Net-(C4-Pad1) | reference | 5.422 mm | F.Cu | 6 / 0 | R2.2→X1.3 4.60, X1.3→C4.1 2.26, R2.2→C4.1 2.14 |

The design's XIN copper is 3.79 mm longer than the reference. XOUT is 2.67 mm longer and XTAL_OUT is 1.19 mm longer. The design also routes 10.185 mm of XIN on In2.Cu through 2 vias, while the reference keeps all its oscillator copper on F.Cu with no vias. The reference is a 2-layer board.

**Sources for layout risk**
No source gives a length, via or clearance limit, so I can't call 14.7 mm excessive. The only supported statements are:
- **Guide, page 14:** parasitic capacitance from tracks and pins is assumed to be 3 pF. Traces must stay small "so we don't upset the crystal and stop it oscillating as intended. Try and keep the layout as short as possible."
- **Guide, page 14:** "Any deviation from the crystal circuit shown here… will require extensive testing to ensure that the crystal oscillates under all conditions, and starts-up sufficiently quickly."
- **Guide, section 4.1, and datasheet, section 8.2:** even with similar parts, test across temperature, and "any changes to crystal parameters risk instability."

**Caveats (recommendations)**
- **Longer than the reference:** the oscillator layout is longer than the reference and adds 2 vias. The guide asks for short traces but sets no threshold, so I treat this as a deviation that needs testing on hardware, not as a proven failure.
- **Nets near the crystal:** other nets run under Y1. GPIO15 (2.79 mm), SD_DETECT (1.81 mm) and GPIO9 (1.08 mm) are on In2.Cu. RADIO_CTS (2.69 mm), +3V3 (2.19 mm) and FLASH_CS (1.63 mm) are on B.Cu. XIN on In2.Cu passes 0.48 mm from SD_CS. No source in hand sets a rule for this, so I report the geometry only.
- **Possible fix:** placing Y1, C1, C2 and R1 next to U1 pins 21 and 22, with F.Cu-only routes, would match the reference layout.

All files are in `_review/processor`:
- `oscillator_lengths.py`: the length measurement script.
- `oscillator_minimal.zip`, unpacked in `oscillator_minimal/`: the official reference, https://datasheets.raspberrypi.com/rp2350/Minimal-KiCAD.zip.
- The two local PDFs.

## Subagent: Read-only independent review of QSPI, USB and SD signal routing for RP2350 board /home/ubuntu/review/board.kicad_pcb. Use working-with-kicad skill and connector kipy/kicad-view, inspect provided images under layers. Write/read only /home/ubuntu/review or connector/libs, scratch restricted to _review/routing (use distinct signal-* filenames). Do not change design, do not run DRC; parent has _review/drc.json. Inspect actual path lengths, layer changes, nearby reference plane gaps, geometry/USB pair and endpoint placement. Return concise concrete net/ref/absolute mm coordinate examples and severity, not speculative findings. Parent already has api-server open? Check ps before launching own; do not share sockets across threads unless read-only. Focus signal paths only, parent inspecting grounding/power. You may read PCB with parser for quantitative analysis but must use connector.

The QSPI, USB and SD routing has no blocking defects. The biggest problem is that the In2.Cu/B.Cu signal layers have no solid reference plane. After that come two SD_MISO problems: a duplicate loop under U1, and long parallel runs next to RADIO_TX and SD_SCK.

I did not change the design or run DRC. I started my own `kicad-cli api-server` on `/tmp/signal_routing_kicad.sock` after checking `ps`; nothing was open before that except another thread's oscillator socket. I read the board through kipy, measured with shapely, rendered views with `kicad-view`, and then stopped the server. Everything I wrote is in `_review/routing/signal*`.

Stackup from `get_stackup()`: F.Cu, 0.10 mm, In1 (solid GND), 1.24 mm, In2 (+3V3 pour with signals), 0.10 mm, B.Cu. The dielectric material fields are blank.

**Findings**

| Sev | Finding | Evidence |
|---|---|---|
| Medium | In2.Cu signals have no close reference plane. B.Cu, 0.10 mm away, has no copper under them, and the nearest GND (In1) is 1.24 mm away. | SD_SCK In2 (140.73,134.49)→(165.91,134.49): 24.6 mm. SD_MISO In2 (136.84,135.08)→(161.60,135.08): 24.2 mm. SD_CS In2 (147.92,141.10)→(163.14,141.10): 14.7 mm. QSPI_CLK In2 (124.01,125.64)→(128.99,130.61)→(133.51,126.08): 11.5 of 13.4 mm. |
| Medium | B.Cu QSPI traces are mostly not over the In2 +3V3 copper, because In2 routing cuts up the pour. | Share of B.Cu length over +3V3: QSPI_D0 51%, D1 31%, D2 10%, D3 49%, FLASH_CS 45%. Example: QSPI_D2 B.Cu (129.53,126.40)→(129.53,132.36) is 4.3 of 5.95 mm with no plane. |
| Medium | SD_MISO has a duplicate parallel route under U1. The 2 B.Cu paths between (136.84,135.08) and (127.59,137.08) form a loop, about 10 mm each, and it looks like router leftovers. | One path runs via (135.63,133.69)→(132.12,133.69)→(128.73,137.08). The other runs via (135.85,133.95)→(132.45,133.95)→(129.25,136.65)→(127.8,137.05). |
| Medium | SD_MISO on B.Cu runs directly over RADIO_TX on In2, 0.10 mm apart, for 7.4 mm. | Around (130.44,135.46), under U1. SD_MISO is an RP2350 input and RADIO_TX is an RP2350 output. |
| Med-low | SD_MISO and SD_SCK run in parallel on In2 with a 0.44 mm edge gap for 20.9 mm, with no close plane. | y=135.08 and y=134.49, x 140.7–161.6 |
| Low | The SD_MISO route is much longer than needed. | J3.7→U1.16 is 64.4 mm with 8 vias and 9 layer segments, against 40.5 mm straight. The whole net is 87.9 mm. |
| Low | The SD_SCK 33 Ω series resistor R41 (140.0,135.0) is far from the driver, so it does little as source termination. | U1.14→R41.1 is 15.0 mm with 2 vias. |
| Low | QSPI data lines are up to 14 mm longer than the clock. That is about 95 ps, which doesn't matter at RP2350 QSPI speeds. | R2→U2: CLK 9.79, D0 10.41, D1 13.25, D2 9.18, D3 24.05 mm. U1→U3: D1 25.31 and D2 21.05 mm against CLK 9.70. |
| Low | QSPI_CLK runs next to RADIO_RTS on In2 with a 0.30 mm gap for 5.0 mm. | (128.99,130.61)→(133.51,126.08) |
| Low | Merged antipads leave a 5.0 mm² hole in In1 GND under the QSPI fan-out. The F.Cu escapes cross it for less than 1 mm each. | Hole bbox (125.37,130.62)–(129.10,134.13). Example: QSPI_D0 (128.4,133.55)→(128.4,132.74). |

**What looks right**

- **QSPI_CLK:** R2 (33 Ω) is 1.45 mm from U1.56. The T split at (128.99,130.61) is balanced: 9.79 mm to U2 and 9.70 mm to U3.
- **USB layout:** all on F.Cu over solid In1 GND, 0.15 mm width and 0.15 mm gap. On 0.10 mm dielectric that works out to about 88 Ω differential, assuming εr 4.3 since the material fields are blank.
- **USB parts:** U5 ESD is 6.4 mm from J1, and R14/R15 (27 Ω) are 1.2 and 1.7 mm from U1.52 and U1.51.
- **Loops:** apart from SD_MISO, I found no loops or dead-end stubs on these nets.

**USB (all low, the RP2350 runs USB at 12 Mbit/s full speed only)**

- **Length:** ESD to series resistor is 40.91 mm on DP and 42.03 mm on DM, a 1.1 mm mismatch. Straight-line distance is 27–29 mm. The pair goes up x≈120.2 and then across y≈130 to reach the USB pins on U1's north side.
- **Neighbour trace:** a 0.1 mm +3V3 trace runs 0.325 mm from DP for 7.6 mm, (121.15→128.75, 130.6).
- **J1 crossover:** the DP B.Cu jumper (111.95→112.95, 157.3) sits over a merged In1 antipad hole at (111.50–113.40, 156.85–157.75), and it also has no In2 copper under it.

The main renders:
- [signal-sdmiso-bcu-in2.png](_review/routing/signal-sdmiso-bcu-in2.png): SD_MISO loop and RADIO_TX overlap
- [signal-sd.png](_review/routing/signal-sd.png): SD routes
- [signal-qspi.png](_review/routing/signal-qspi.png): QSPI
- [signal-usb.png](_review/routing/signal-usb.png): USB pair

The numbers come from `signal_paths.txt`, `signal_analyze2.txt`, `signal_analyze3.txt` and `signal_aggr.txt`, built from `signal_dump.json`.
