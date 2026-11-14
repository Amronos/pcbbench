# PCBBench

> [!NOTE]
> PCBBench is still under development.

PCBBench compares AI models and agents on PCB design performance across 40+ metrics.

## The task

The prompt is [bench/prompt.md](bench/prompt.md).

## Results

### Complete scores

| Run                                                            | Design review (20) | Circuit checks (20) | Layout checks (30) | Orderable (20) | Parts data (10) | Failed gate | Score (100) | 5 boards, per board | AI cost |
| -------------------------------------------------------------- | ------------------ | ------------------- | ------------------ | -------------- | --------------- | ----------- | ----------- | ------------------- | ------- |
| [`sprocket--opus-5.5`][sprocket]                               | 9                  | 18.2                | 24.1               | 20             | 9.9             |             | **81.2**    | $73.36              | $53.31  |
| [`sprocket--gpt-6.1-sol`][sprocket]                            | 8                  | 19.3                | 19                 | 20             | 5               |             | **71.3**    | $148.08             | $53.72  |
| [`backplane--opus-5.5`][backplane]                             | 17                 | 17.8                | 15.4               | 10             | 9.8             |             | **69.9**    | $51.57              | $56.77  |
| [`backplane--fable-5.2`][backplane]                            | 16                 | 16.5                | 14                 | 15             | 7               |             | **68.4**    | $52.68              | $49.09  |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 11                 | 20                  | 16.7               | 4              | 4.7             |             | **56.4**    | $87.53              | $14.36  |
| [`backplane--gpt-6.1-sol`][backplane]                          | 9                  | 9.2                 | 14.5               | 12             | 4.8             | −20         | **29.5**    | $181.34             | $5.81   |
| [`codex-desktop--gpt-6.1-sol`][codex]                          | 7                  | 15.6                | 9.2                | 14             | 0               | −20         | **25.9**    | $77.64              | $6.41   |

The score covers the board only. Price, AI cost and time are left out of it, so they can be weighed separately. Each item earns its points times a fraction from 0 to 1:

| Group          | Item                  | Points | Fraction                                                                                                    |
| -------------- | --------------------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| Design review  | Layout                | 10     | 1 minus 0.1 per minor and 0.2 per major layout finding, down to 0                                           |
|                | Routing               | 10     | the same, for routing findings                                                                              |
| Circuit checks | Decoupling            | 5      | RP2350 power pins with a capacitor within 3.2 mm                                                            |
|                | USB protection        | 5      | 0.5 for an ESD part on D+ and D-, plus 0.25 for each line with a series resistor                            |
|                | Antenna keepout       | 5      | 1 when there are keepouts and no copper is in them                                                          |
|                | Battery drain         | 5      | 1 at 5 µA or less drawn by unswitched battery dividers, falling linearly to 0 at 25 µA                      |
| Layout checks  | Thermal pads          | 10     | mean over the exposed pads of their vias over the number needed, 0 for a pad with no plane on another layer |
|                | Grounding             | 10     | USB, QSPI and microSD track length over a ground plane on the next layer                                    |
|                | Silkscreen            | 5      | texts at least 0.8 mm high                                                                                  |
|                | Board size            | 5      | 1 at the Feather RP2350's 50.8 × 22.8 mm area or less, falling linearly to 0 at 5 times that area           |
| Orderable      | Fab notes             | 5      | 1 when every fab option in the notes can be ordered from PCBWay                                             |
|                | Board                 | 5      | 1 when the board needs no rework                                                                            |
|                | BOM lines             | 10     | 1 minus 0.2 for each BOM line that needs a fix, down to 0                                                   |
| Parts data     | 3D models             | 5      | parts with a 3D model                                                                                       |
|                | Supplier part numbers | 5      | BOM lines with a valid number from at least one supplier                                                    |

A board that fails a gate loses 20 points. The gates are a missing prompt feature, a failed crystal, button or power-path check, and a fatal review finding. Two boards fail one, each from a fatal finding listed under [Design review](#design-review). The group columns leave out the penalty. `bench/score.ts` computes the score and writes it under `score` in `metrics.json`. Differences under about 5 points aren't meaningful. Moving 10 points between any two groups moves runs by up to 2 places, and `sprocket--opus-5.5` stays first every time. `backplane--opus-5.5` and `backplane--fable-5.2`, 1.5 points apart, swap places in most shifts.

### Time, cost and price

| Run                                                            | Minutes | AI cost | Tokens, incl. cache reads | Board size (mm) | 1 board | 5 boards, per board | Prices after fixes |
| -------------------------------------------------------------- | ------- | ------- | ------------------------- | --------------- | ------- | ------------------- | ------------------ |
| [`codex-desktop--gpt-6.1-sol`][codex]                          | 78.1    | $6.41   | 21.0M                     | 80 × 65         | $246.31 | $77.64              | yes                |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 96.0    | $14.36  | 52.4M                     | 80 × 75         | $297.32 | $87.53              | yes                |
| [`backplane--opus-5.5`][backplane]                             | 170.5   | $56.77  | 124.9M                    | 80 × 38         | $185.16 | $51.57              | yes                |
| [`backplane--gpt-6.1-sol`][backplane]                          | 98.2    | $5.81   | 28.6M                     | 85 × 70         | $741.00 | $181.34             | yes                |
| [`backplane--fable-5.2`][backplane]                            | 225.4   | $49.09  | 55.6M                     | 76.2 × 22.86    | $187.53 | $52.68              | yes                |
| [`sprocket--opus-5.5`][sprocket]                               | 291.0   | $53.31  | 90.1M                     | 28 × 78.54      | $282.37 | $73.36              | no                 |
| [`sprocket--gpt-6.1-sol`][sprocket]                            | 95.8    | $53.72  | 185.1M                    | 85 × 65         | $659.08 | $148.08             | no                 |

- **Minutes:** the time the agent was working.
- **AI cost:** the run's API cost at market prices, including subagents.
- **Board price:** PCB, assembly and parts, at PCBWay's normal instant-quote prices, without shipping or the new-customer $29 promo. PCBWay makes at least 5 bare PCBs, so "1 board" means 5 PCBs with 1 assembled. "5 boards" is 5 PCBs, all assembled. Parts are priced at distributor list prices for the larger of the quantity needed and the minimum order.
- **Prices after fixes:** The design couldn't be ordered exactly as delivered, so the price covers the changes listed under `fixes` in `metrics.json`. Examples are invalid or legacy part numbers, or a fab option PCBWay doesn't offer.

### BOM and 3D models

| Run                                                            | Missing 3D models | BOM lines | BOM lines fixed | Valid LCSC part numbers | Valid Digi-Key part numbers | Mouser part numbers |
| -------------------------------------------------------------- | ----------------- | --------- | --------------- | ----------------------- | --------------------------- | ------------------- |
| [`codex-desktop--gpt-6.1-sol`][codex]                          | 121               | 51        | 1               | 0%                      | 0%                          | 0%                  |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 7                 | 53        | 2               | 0%                      | 0%                          | 0%                  |
| [`backplane--opus-5.5`][backplane]                             | 4                 | 38        | 0               | 100%                    | 0%                          | 0%                  |
| [`backplane--gpt-6.1-sol`][backplane]                          | 5                 | 54        | 1               | 0%                      | 0%                          | 0%                  |
| [`backplane--fable-5.2`][backplane]                            | 7                 | 36        | 0               | 50%                     | 0%                          | 0%                  |
| [`sprocket--opus-5.5`][sprocket]                               | 1                 | 40        | 0               | 100%                    | 0%                          | 0%                  |
| [`sprocket--gpt-6.1-sol`][sprocket]                            | 0                 | 55        | 0               | 0%                      | 0%                          | 0%                  |

- **Parts:** footprints on the board that aren't marked board-only, excluded from the BOM or DNP, and aren't bare test pads.
- **Missing 3D models:** parts with no 3D model, or with one that the run's own KiCad version can't load from its stock libraries and the project's files.
- **Supplier part numbers:** the share of BOM lines that give a valid part number for that supplier. An LCSC number is valid when LCSC lists it under the line's manufacturer part number. A Digi-Key number is valid when Digi-Key lists it as a variation of that part. Mouser numbers can't be looked up, so any Mouser number counts. `suppliers` in `metrics.json` has the counts.
- Every BOM covers every part. No BOM listed a designator that isn't on the board, had a Qty that doesn't match its designators, or left out a manufacturer part number for a fitted part.
- `backplane--fable-5.2` excludes its pin headers from the BOM and `sprocket--opus-5.5` marks its pin headers do not populate, so PCBWay wouldn't fit them. They aren't counted as parts. The judge sees this.

### Design and fab checks

| Run                                                            | DRC errors | DRC warnings | ERC errors | ERC warnings | BOM lines LCSC, JLCPCB or Digi-Key stocks for 5 boards | Lines discontinued at LCSC or Digi-Key |
| -------------------------------------------------------------- | ---------- | ------------ | ---------- | ------------ | ------------------------------------------------------ | -------------------------------------- |
| [`codex-desktop--gpt-6.1-sol`][codex]                          | 0          | 0            | 0          | 0            | 94.1%                                                  | 3                                      |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 0          | 0            | 0          | 0            | 98.1%                                                  | 6                                      |
| [`backplane--opus-5.5`][backplane]                             | 3          | 0            | 0          | 0            | 100%                                                   | 0                                      |
| [`backplane--gpt-6.1-sol`][backplane]                          | 0          | 2            | 0          | 0            | 92.6%                                                  | 5                                      |
| [`backplane--fable-5.2`][backplane]                            | 0          | 1            | 0          | 0            | 100%                                                   | 0                                      |
| [`sprocket--opus-5.5`][sprocket]                               | 0          | 0            | 0          | 0            | 100%                                                   | 1                                      |
| [`sprocket--gpt-6.1-sol`][sprocket]                            | 0          | 0            | 0          | 0            | 100%                                                   | 7                                      |

- **DRC:** run with zones refilled, because some boards were saved with stale fills. It includes the schematic parity check. No board had unconnected items or parity issues. Copper narrower than the board's minimum connection width (`connection_width`) counts as an error, though KiCad only warns. The only cases are on `backplane--opus-5.5`, where inner-layer copper necks down to 0.079 mm, below the 5 mil (0.127 mm) minimum its PCBWay quote orders. Footprints that differ from their library copy (`lib_footprint_mismatch`) aren't counted. `metrics.json` has the counts by type.
- **Stock:** a line counts as stocked when LCSC, JLCPCB or Digi-Key has its quantity × 5 on hand, because PCBWay buys from many distributors. JLCPCB is searched by LCSC number when the line has one, else by manufacturer part number. Digi-Key is searched by manufacturer part number, including packaging variants such as `/TR`. Every run's stock was checked on the same day.
- **Discontinued:** LCSC lists the part as discontinued, or every Digi-Key listing of it is Obsolete or Discontinued at Digi-Key. Some of these parts are still in stock.
- **Fab files:** every Gerber and drill file in the order zip matches a fresh export from the board, layer by layer, within 0.1% of the drawn area. Every zip has all copper layers, Edge.Cuts, both masks, F.Silkscreen, paste for each side with surface-mount parts, and the drill files.
- **Placement:** every placement file lists every surface-mount part once, on the right side and at the board's rotation. After lining up the file's origin and axes with the board, every part is within 0.5 mm of its board position.
- **Footprints:** each part's pad count matches LCSC's footprint for its part number. Connectors aren't compared, because libraries split shield tabs and doubled contacts differently.
- **Prompt features:** every BOM has a part for the RP2350, QSPI flash, PSRAM, USB-C, Wi-Fi and BLE, microSD, Qwiic, an RGB LED and a power-path charger. Every board monitors the battery, with a fuel gauge or a resistor from a battery net to an ADC pin, directly or through a transistor.
- **Deliverables:** every run has a README, a schematic and project file next to the board, and a fab folder.
- The files checked are `board`, `bom`, `placement` and `fabZip` in `info.json`. `metrics.json` lists the designators and per-layer results.

### Circuit checks

| Run                                                            | RP2350 power pins with a capacitor within 3.2 mm | Pins farther away (mm)                                                                    | Battery divider                     | Divider current at 4.2 V (µA) | Divider switched | Antenna keepouts    | Copper in the keepouts |
| -------------------------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------- | ----------------------------------- | ----------------------------- | ---------------- | ------------------- | ---------------------- |
| [`codex-desktop--gpt-6.1-sol`][codex]                          | 13 of 14                                         | QSPI_IOVDD 54: 3.43                                                                       | R25 100k / R26 100k, buffered by U8 | 21                            | no               | U9 footprint        | none                   |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 14 of 14                                         | none                                                                                      | R10 470k / R11 470k, buffered by U9 | 4.47                          | no               | U6 footprint        | none                   |
| [`backplane--opus-5.5`][backplane]                             | 14 of 14                                         | none                                                                                      | R9 200k / R10 100k                  | 14                            | no               | U7 footprint, board | none                   |
| [`backplane--gpt-6.1-sol`][backplane]                          | 9 of 14                                          | DVDD 6: 3.45, IOVDD 11: 3.66, DVDD 23: 3.59, DVDD 39: 6.4, ADC_AVDD 44: 12.15             | R25 100k / R26 100k                 | 21                            | no               | U8 footprint, board | /3V3 fill on In4.Cu    |
| [`backplane--fable-5.2`][backplane]                            | 8 of 14                                          | IOVDD 1: 3.34, DVDD 6: 7.34, IOVDD 11: 3.69, IOVDD 20: 4.27, DVDD 23: 6.05, DVDD 39: 4.08 | R12 200k / R13 200k                 | 10.5                          | no               | board               | none                   |
| [`sprocket--opus-5.5`][sprocket]                               | 9 of 14                                          | DVDD 6: 4.53, IOVDD 11: 4.53, IOVDD 20: 7.05, DVDD 23: 6.17, IOVDD 30: 6.43               | R14 470k / R15 470k                 | 4.47                          | no               | U7 footprint        | none                   |
| [`sprocket--gpt-6.1-sol`][sprocket]                            | 12 of 14                                         | DVDD 6: 3.3, IOVDD 11: 3.3                                                                | R23 100k / R24 100k                 | 21                            | yes              | U6 footprint        | none                   |

| Run                                                            | D+ length (mm) | D- length (mm) | Mismatch (mm) | Vias | Width (mm) | Gap (mm) | Side by side (mm) | Differential impedance (Ω) | ESD parts on D+ and D- |
| -------------------------------------------------------------- | -------------- | -------------- | ------------- | ---- | ---------- | -------- | ----------------- | -------------------------- | ---------------------- |
| [`codex-desktop--gpt-6.1-sol`][codex]                          | 51.45          | 52.84          | 1.39          | 2    | 0.15       | 0.15     | 37.66             | 87.9                       | U5                     |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 28.51          | 24.53          | 3.98          | 4    | 0.15       | 0.15     | 8.29              | 95.5                       | U8                     |
| [`backplane--opus-5.5`][backplane]                             | 38.02          | 38.29          | 0.27          | 0    | 0.25       | 1.25     | 11.78             | 120.9                      | U1                     |
| [`backplane--gpt-6.1-sol`][backplane]                          | 58.54          | 42.65          | 15.89         | 6    | 0.22       | 1.68     | 9.93              | no stackup                 | U5                     |
| [`backplane--fable-5.2`][backplane]                            | 44.52          | 42.26          | 2.26          | 3    | 0.15       | 0.16     | 4.86              | 114.7                      | U6                     |
| [`sprocket--opus-5.5`][sprocket]                               | 66.19          | 50.77          | 15.42         | 0    | 0.2        | 0.15     | 32.9              | 100.3                      | U4                     |
| [`sprocket--gpt-6.1-sol`][sprocket]                            | 23.84          | 25.79          | 1.95          | 2    | 0.22       | 0.15     | 8.76              | 90.7                       | D1                     |

- **Decoupling:** for each RP2350 IOVDD, DVDD, QSPI_IOVDD, USB_OTP_VDD, ADC_AVDD, VREG_VIN and VREG_AVDD pad, the nearest capacitor with one pad on that pin's net and the other on a ground net, on either side of the board. The distance is from the center of the pin's pad to the center of the capacitor's nearest pad. Pins are found by the pads' pin functions, or by RP2350A pad numbers when the footprint names none. Hardware design with RP2350 asks for decoupling close to the power pins without giving a distance. Its own Minimal board, whose capacitors it calls slightly further from the chip than optimal, has one within 3.2 mm of every power pin.
- **Battery divider:** the resistor from the battery to the ADC input, or to the op-amp follower that drives it, and the resistor from there to ground. The current is 4.2 V over their sum, from the footprint values. A divider is switched when its top resistor reaches the battery through a transistor or load switch rather than directly.
- **USB:** D+ and D- run from the RP2350 pins through the series resistors to the USB-C connector. Lengths add every track segment and arc on those nets, including stubs. Width and gap are for the longest stretch where D+ and D- segments run parallel on one layer within 2 mm of each other, and "side by side" is that stretch's length. The impedance uses the IPC-2141 edge-coupled microstrip formula with that width and gap and the board's stackup. `backplane--gpt-6.1-sol` has no stackup in its board file.
- **ESD parts:** parts other than the connector and the RP2350 with pads on both D+ and D-.
- **USB impedance isn't scored.** The RP2350 only does USB full speed. Its edges take 4 ns or more, so traces a few centimeters long behave as plain wires, and 90 Ω matching doesn't change how the link works. The same goes for how close the series resistors sit to the RP2350, which is why USB protection only checks that the ESD part and resistors are there.
- **Battery drain:** a LiPo board draws this current all the time, even when off, unless the divider is switched. `sprocket--gpt-6.1-sol` switches its divider with Q1, so it scores full points. The op-amp followers on `codex-desktop--gpt-6.1-sol` and `codex-desktop-texttocad--gpt-6.1-sol` aren't counted.
- **Antenna keepouts:** rule areas in the Wi-Fi module's footprint or on the board that overlap the module's courtyard and forbid copper. Copper in them counts tracks, vias, zone fills and other parts' pads on every copper layer, including layers the rule area doesn't cover. The rule area in the `backplane--fable-5.2` module footprint lies off the board, so only its board rule area counts.
- `design` in `metrics.json` has the per-pin distances, resistor values, net names and keepout layers.

### Layout checks

| Run                                                            | Exposed pad vias, of those needed | Thermal points | Grounded USB / QSPI / microSD | Grounding points | Texts at least 0.8 mm | Silkscreen points | Board area (mm²) | Board size points |
| -------------------------------------------------------------- | --------------------------------- | -------------- | ----------------------------- | ---------------- | --------------------- | ----------------- | ---------------- | ----------------- |
| [`sprocket--opus-5.5`][sprocket]                               | U1 9 of 9, U5 4 of 5, U6 4 of 4   | 9.3            | 100% / 45% / 55%              | 5.9              | 30 of 30              | 5                 | 2199             | 3.9               |
| [`sprocket--gpt-6.1-sol`][sprocket]                            | U1 0 of 9, U4 4 of 5, U5 4 of 4   | 6              | 93% / 64% / 83%               | 7.7              | 8 of 8                | 5                 | 5525             | 0.3               |
| [`backplane--opus-5.5`][backplane]                             | U4 9 of 9, U2 0 of 5              | 5              | 100% / 72% / 57%              | 7.1              | 5 of 65               | 0.4               | 3040             | 3                 |
| [`backplane--fable-5.2`][backplane]                            | U1 5 of 9, U4 1 of 5              | 3.8            | 68% / 75% / 28%               | 4.9              | 7 of 39               | 0.9               | 1742             | 4.4               |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | U1 4 of 9, U4 1 of 5              | 3.2            | 92% / 89% / 80%               | 8.5              | 16 of 16              | 5                 | 6000             | 0                 |
| [`codex-desktop--gpt-6.1-sol`][codex]                          | U1 0 of 9, U6 0 of 5, U7 0 of 5   | 0              | 98% / 55% / 66%               | 6.8              | 5 of 14               | 1.8               | 5200             | 0.6               |
| [`backplane--gpt-6.1-sol`][backplane]                          | U1 0 of 9, U6 0 of 5, U7 4 of 5   | 2.7            | 84% / 87% / 56%               | 6.8              | 11 of 11              | 5                 | 5950             | 0                 |

- **Thermal pads:** vias in the exposed pads of the RP2350, the charger and the regulator. The RP2350 needs 9, the 3×3 grid in Raspberry Pi's RP2350A Minimal reference design. The BQ2407x, TPS6300x and TPS6306x need the vias drawn in TI's land patterns: 5, 4 and 5. A pad scores 0 when no ground plane on another layer is under it. Every pad here has one.
- **Grounding:** the share of USB, QSPI and microSD track length with a ground fill on an adjacent copper layer, sampled every 0.1 mm. The nets include the far side of series resistors. The score uses the total length over all three buses, so long microSD runs weigh the most. A larger board leaves more room for planes and routing, which is why board size is scored next to it.
- **Silkscreen:** text on the silkscreen layers below 0.8 mm, PCBWay's minimum legend height. PCBWay clips legend off exposed copper, so silkscreen over pads isn't counted. Reference designators aren't checked, because the prompt asks to leave them off.
- **Board size:** the PCBWay quote's width × height. Adafruit's Feather RP2350 at 50.8 × 22.8 mm fits everything in the prompt but Wi-Fi and microSD.
- **Gates:** every board passes all three. The crystal has load capacitors within 25% of what its datasheet needs, with 3 pF of board capacitance. BOOT pulls QSPI_SS to ground through a switch, and RUN has its own switch to ground. The charger takes USB VBUS, charges the battery connector and feeds the 3.3 V regulator.
- `layout` and `gates` in `metrics.json` have the per-pad, per-bus and per-text results.

### Fixes needed before PCBWay can make and assemble the board

| Run                                                            | Fab notes            | Board                                                 | Assembly                                                                       |
| -------------------------------------------------------------- | -------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------ |
| [`codex-desktop--gpt-6.1-sol`][codex]                          | no                   | no                                                    | L2 is a legacy part. C5 C16 C18 C22 C37 and D1 aren't stocked.                 |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 0.5 oz inner copper. | R42's 0402 footprint doesn't fit its 0603 substitute. | C26 C27 have an invalid MPN. R42 isn't sold. C29 isn't stocked.                |
| [`backplane--opus-5.5`][backplane]                             | 0.5 oz inner copper. | 3 DRC errors.                                         | no                                                                             |
| [`backplane--gpt-6.1-sol`][backplane]                          | no                   | no                                                    | R3 has an invalid MPN. C3 C16 C40, C17 C21 and C28 C29 C30 C34 aren't stocked. |
| [`backplane--fable-5.2`][backplane]                            | 0.5 oz inner copper. | no                                                    | no                                                                             |
| [`sprocket--opus-5.5`][sprocket]                               | no                   | no                                                    | no                                                                             |
| [`sprocket--gpt-6.1-sol`][sprocket]                            | no                   | no                                                    | no                                                                             |

- **Fab notes:** a `fixes` entry for a fab option PCBWay doesn't offer, such as 0.5 oz inner copper. Changing the option on the order form fixes it.
- **Board:** a `fixes` entry for the board, DRC errors, unconnected items, or fab files that are missing or differ from the board. These need the design edited.
- **Assembly:** a `fixes` entry for the BOM, lines not stocked for 5 boards, footprint pad counts that differ from the part, or BOM and placement file problems. Discontinued parts that are still stocked don't count.
- `needsFixes` in `metrics.json` has the full list for each run.

### Design review

| Run                                                            | Layout minor / major | Layout points | Routing minor / major | Routing points | Fatal |
| -------------------------------------------------------------- | -------------------- | ------------- | --------------------- | -------------- | ----- |
| [`sprocket--opus-5.5`][sprocket]                               | 1 / 0                | 9             | 2 / 4                 | 0              | 0     |
| [`sprocket--gpt-6.1-sol`][sprocket]                            | 3 / 0                | 7             | 3 / 3                 | 1              | 0     |
| [`backplane--opus-5.5`][backplane]                             | 0 / 0                | 10            | 3 / 0                 | 7              | 0     |
| [`backplane--fable-5.2`][backplane]                            | 0 / 0                | 10            | 4 / 0                 | 6              | 0     |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 2 / 0                | 8             | 3 / 2                 | 3              | 0     |
| [`codex-desktop--gpt-6.1-sol`][codex]                          | 4 / 0                | 6             | 3 / 3                 | 1              | 1     |
| [`backplane--gpt-6.1-sol`][backplane]                          | 1 / 0                | 9             | 2 / 7                 | 0              | 1     |

- **Judge:** opus-5.5 on high reasoning in the Sprocket CLI with its KiCad connector reviews each board once, on its own machine. It sees only an anonymous copy of the board: the KiCad project, the BOM, and renders and layer images made with the run's KiCad version. It upgrades the project to the connector's KiCad before inspecting it. [bench/judge/README.md](bench/judge/README.md) has the details.
- **Findings:** the judge lists layout and routing problems, each with its parts, nets and evidence, and rates each one `minor`, `major` or `fatal`. A fatal finding means the assembled board can't work, a part gets damaged or PCBWay can't build it, and it can come from any part of the design. The judge gives no scores. Each area starts at 10 points and loses 1 per minor and 2 per major finding. The rubric is in [bench/judge/prompt.md](bench/judge/prompt.md).
- **Fatal findings:** `backplane--gpt-6.1-sol` fits a unidirectional SMF5.0A TVS on USB VBUS with its cathode on ground, so it conducts across the 5 V input. The microSD socket on `codex-desktop--gpt-6.1-sol` faces into the board, and resistors and capacitors sit where the card would go.
- Most major findings are power traces too narrow for the charger's current and QSPI, microSD or USB lines that detour with many vias.
- `runs/<run-id>/review/opus-5.5.json` has the findings, and `opus-5.5.md` has the judge's final message and the reports of the subagents it started.

## Repo layout

```text
bench/                   benchmark code (Bun + TypeScript)
  prompt.md              the task prompt
  runs.ts                run list, models and time limit
  harnesses/<harness>/   machine setup and run driver for each harness, with a README
  collect.ts             copies a finished run's outputs into runs/<run-id>/ and its logs into bench/.state/logs/
  usage.ts               token usage from Claude Code and Codex session logs
  price.ts               prices the board from the PCBWay quote and distributor prices
  part-prices.json       prices for parts LCSC doesn't sell, with sources and fixes
  check.ts               checks the BOM, placement file, parts, prompt features, gates and layout, and lists the fixes PCBWay needs
  gates.ts               the crystal, button and power-path gates
  layout-checks.ts       thermal pad vias, grounding and silkscreen
  netlist.ts             nets and parts shared by the gates and layout checks
  geometry.ts            point, polygon and arc helpers
  inspect.ts             runs DRC and ERC, matches the fab files, checks 3D models and renders the board, with the run's KiCad version
  fab-match.ts           compares the delivered Gerbers and drill files with a fresh export
  board.ts               reads a run's board footprints, pads, tracks, zones and stackup
  judge/                 the design review: anonymous board packages, the judge's rubric and the driver, with a README
  score.ts               the board score, and how the ranking changes when weights shift
  bom.ts                 reads a run's BOM CSV
  lcsc.ts                looks up LCSC parts
  digikey.ts             looks up Digi-Key stock and part status
runs/<run-id>/
  output/                everything the agent left in its work folder
  renders/               top.png, bottom.png and iso.png from kicad-cli pcb render, with the run's KiCad version
  review/                the judge's review of the board and its reasoning
  info.json              harness, model, machine, tool versions, and the final board, BOM, placement file and order zip
  metrics.json           timing, tokens, AI cost, board size, fixes, board cost and check results
  pcbway-quote.json      the PCBWay quote and how the fab notes map to its options
  components-pricing.json  the price of every BOM line
```

## Running it

Run `nix develop`, or use direnv, to get Bun. Then run `bun install`.

1. Start the run with the harness's driver. Each harness README covers the machine image, sign-in and the exact commands: [Backplane](bench/harnesses/backplane/README.md), [Codex desktop](bench/harnesses/codex-desktop/README.md) and [Sprocket](bench/harnesses/sprocket/README.md).
2. Collect the run from `bench/` when it ends. Linux runs need the box's address.

   ```shell
   bun collect.ts <run-id> [ubuntu@<ip>]
   ```

   Sprocket token usage and cost aren't in its local logs, so they are copied into `metrics.json` from the web UI.

3. Set `board`, `bom`, `placement` and `fabZip` in `runs/<run-id>/info.json` to the final `.kicad_pcb`, BOM CSV, placement CSV and order zip, relative to `output/`.
4. Price the board. Save the run's PCBWay quote as `runs/<run-id>/pcbway-quote.json` first, then run:

   ```shell
   bun price.ts <run-id>
   ```

   The script prices every BOM line from LCSC or `part-prices.json`. It stops with an error if any line has no price.

5. Run the checks. Run `inspect.ts` first, because `check.ts` uses its DRC and fab results. `inspect.ts` needs the `kicad-cli` of the KiCad version in `info.json`, and stops if the versions differ. `check.ts` needs `DIGIKEY_CLIENT_ID` and `DIGIKEY_CLIENT_SECRET` from a Digi-Key Product Information v4 app.

   ```shell
   bun inspect.ts <run-id> <path to kicad-cli>
   bun check.ts <run-id>
   ```

   The Backplane fork installs with `harnesses/backplane/install-kicad.ts`. KiCad nightlies for Linux, matching the Mac's version, are at [downloads.kicad.org](https://downloads.kicad.org/kicad/linux/explore/nightlies).

6. Run the design review as in [bench/judge/README.md](bench/judge/README.md). Then score every run:

   ```shell
   bun score.ts
   ```

Run `bun run check` and `bun run lint` before committing.

[sprocket]: https://usesprocket.dev/
[backplane]: https://backplaneworks.com/
[codex]: https://openai.com/codex/
[texttocad]: https://texttocad.dev/
