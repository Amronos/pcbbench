# PCBBench

> [!NOTE]
> PCBBench is still under development.

PCBBench compares AI models and agents on PCB design performance across 40+ metrics.

## The task

The prompt is [bench/prompt.md](bench/prompt.md).

## Results

### Board score

| Run | Design review (50) | Circuit checks (20) | Orderable (20) | Parts data (10) | Score (100) | 1 board | AI cost |
|---|---|---|---|---|---|---|---|
| [`sprocket--fable-5.2`][sprocket] | 33.2 | 20 | 20 | 9.4 | 82.6 | $189.77 | $87.61 |
| [`sprocket--opus-5.5`][sprocket] | 31.1 | 14.2 | 20 | 8.6 | 73.8 | $278.13 | $40.73 |
| [`sprocket--gpt-6.1-sol`][sprocket] | 28.6 | 19.5 | 19.1 | 5 | 72.2 | $661.63 | $64.51 |
| [`codex-desktop--gpt-6.1-sol`][codex] | 30.4 | 19.5 | 19.2 | 0 | 69.1 | $246.31 | $6.41 |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 33.2 | 20 | 9.4 | 4.7 | 67.3 | $297.32 | $14.36 |
| [`backplane--opus-5.5`][backplane] | 35.7 | 13.2 | 9.7 | 7.8 | 66.3 | $185.16 | $56.77 |
| [`backplane--fable-5.2`][backplane] | 31.1 | 12.1 | 9.7 | 6 | 58.9 | $187.53 | $49.09 |
| [`backplane--gpt-6.1-sol`][backplane] | 25.4 | 4.5 | 18.9 | 4.8 | 53.6 | $741.00 | $5.81 |

The score covers the board only. Price, AI cost and time are left out of it, so they can be weighed separately. Each item earns its points times a fraction from 0 to 1:

| Group | Item | Points | Fraction |
|---|---|---|---|
| Design review | Yes or no questions | 15 | yes votes over all answers |
| | Scores | 35 | total of the mean scores over 50 |
| Circuit checks | Decoupling | 7 | RP2350 power pins with a capacitor within 3.2 mm |
| | USB impedance | 7 | 1 within ±10% of 90 Ω, falling linearly to 0 at ±35%, 0 with no stackup |
| | Antenna keepout | 6 | 1 when there are keepouts and no copper is in them |
| Orderable | PCB | 10 | 1 when the PCB needs no fixes |
| | BOM lines | 10 | BOM lines that need no fixes |
| Parts data | 3D models | 5 | parts with a 3D model |
| | Supplier part numbers | 3 + 1.5 + 0.5 | BOM lines with a valid number from at least one, two, and all three suppliers |

A board missing a prompt feature is capped at 50. None is. `bench/score.ts` computes the score and writes it under `score` in `metrics.json`. Differences under about 5 points aren't meaningful. Moving 10 points between any two groups keeps `sprocket--fable-5.2` first, and moves other runs by up to 3 places.

### Time, cost and price

| Run | Minutes | AI cost | Tokens, incl. cache reads | Board size (mm) | 1 board | 5 boards, per board | Prices after fixes |
|---|---|---|---|---|---|---|---|
| [`codex-desktop--gpt-6.1-sol`][codex] | 78.1 | $6.41 | 21.0M | 80 × 65 | $246.31 | $77.64 | yes |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 96.0 | $14.36 | 52.4M | 80 × 75 | $297.32 | $87.53 | yes |
| [`backplane--opus-5.5`][backplane] | 170.5 | $56.77 | 124.9M | 80 × 38 | $185.16 | $51.57 | yes |
| [`backplane--gpt-6.1-sol`][backplane] | 98.2 | $5.81 | 28.6M | 85 × 70 | $741.00 | $181.34 | yes |
| [`backplane--fable-5.2`][backplane] | 225.4 | $49.09 | 55.6M | 76.2 × 22.86 | $187.53 | $52.68 | yes |
| [`sprocket--opus-5.5`][sprocket] | 129.1 | $40.73 | 75.7M | 30.5 × 70 | $278.13 | $70.99 | no |
| [`sprocket--gpt-6.1-sol`][sprocket] | 183.6 | $64.51 | 185.0M | 80 × 65 | $661.63 | $159.09 | no |
| [`sprocket--fable-5.2`][sprocket] | 270.5 | $87.61 | 100.4M | 76.2 × 25.4 | $189.77 | $56.34 | no |

- **Minutes:** the time the agent was working.
- **AI cost:** the run's API cost at market prices, including subagents.
- **Board price:** PCB, assembly and parts, at PCBWay's normal instant-quote prices, without shipping or the new-customer $29 promo. PCBWay makes at least 5 bare PCBs, so "1 board" means 5 PCBs with 1 assembled. "5 boards" is 5 PCBs, all assembled. Parts are priced at distributor list prices for the larger of the quantity needed and the minimum order.
- **Prices after fixes:** The design couldn't be ordered exactly as delivered, so the price covers the changes listed under `fixes` in `metrics.json`. Examples are invalid or legacy part numbers, or a fab option PCBWay doesn't offer.

### BOM and 3D models

| Run | Missing 3D models | BOM lines | BOM lines fixed | Valid LCSC part numbers | Valid Digi-Key part numbers | Mouser part numbers |
|---|---|---|---|---|---|---|
| [`codex-desktop--gpt-6.1-sol`][codex] | 121 | 51 | 1 | 0% | 0% | 0% |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 7 | 53 | 2 | 0% | 0% | 0% |
| [`backplane--opus-5.5`][backplane] | 4 | 38 | 0 | 100% | 0% | 0% |
| [`backplane--gpt-6.1-sol`][backplane] | 5 | 54 | 1 | 0% | 0% | 0% |
| [`backplane--fable-5.2`][backplane] | 7 | 36 | 0 | 50% | 0% | 0% |
| [`sprocket--opus-5.5`][sprocket] | 0 | 32 | 0 | 100% | 40.6% | 0% |
| [`sprocket--gpt-6.1-sol`][sprocket] | 0 | 43 | 0 | 0% | 0% | 0% |
| [`sprocket--fable-5.2`][sprocket] | 2 | 37 | 0 | 91.9% | 94.6% | 32.4% |

- **Parts:** footprints on the board that aren't marked board-only, excluded from the BOM or DNP, and aren't bare test pads.
- **Missing 3D models:** parts with no 3D model, or with one that the run's own KiCad version can't load from its stock libraries and the project's files.
- **Supplier part numbers:** the share of BOM lines that give a valid part number for that supplier. An LCSC number is valid when LCSC lists it under the line's manufacturer part number. A Digi-Key number is valid when Digi-Key lists it as a variation of that part. Mouser numbers can't be looked up, so any Mouser number counts. `suppliers` in `metrics.json` has the counts.
- Every BOM covers every part. No BOM listed a designator that isn't on the board, had a Qty that doesn't match its designators, or left out a manufacturer part number.
- `backplane--fable-5.2` and `sprocket--opus-5.5` mark their pin headers as excluded from the BOM, so PCBWay wouldn't fit them. They aren't counted as parts. The judges see this.

### Design and fab checks

| Run | DRC errors | DRC warnings | ERC errors | ERC warnings | BOM lines LCSC or Digi-Key stocks for 5 boards | Lines discontinued at LCSC or Digi-Key |
|---|---|---|---|---|---|---|
| [`codex-desktop--gpt-6.1-sol`][codex] | 0 | 0 | 0 | 0 | 92.2% | 3 |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 0 | 0 | 0 | 0 | 98.1% | 6 |
| [`backplane--opus-5.5`][backplane] | 3 | 0 | 0 | 0 | 97.4% | 0 |
| [`backplane--gpt-6.1-sol`][backplane] | 0 | 2 | 0 | 0 | 88.9% | 5 |
| [`backplane--fable-5.2`][backplane] | 0 | 1 | 0 | 0 | 97.2% | 0 |
| [`sprocket--opus-5.5`][sprocket] | 0 | 0 | 0 | 0 | 100% | 0 |
| [`sprocket--gpt-6.1-sol`][sprocket] | 0 | 0 | 0 | 0 | 90.7% | 4 |
| [`sprocket--fable-5.2`][sprocket] | 0 | 0 | 0 | 0 | 100% | 0 |

- **DRC:** run with zones refilled, because some boards were saved with stale fills. It includes the schematic parity check. No board had unconnected items or parity issues. Copper narrower than the board's minimum connection width (`connection_width`) counts as an error, though KiCad only warns. The only cases are on `backplane--opus-5.5`, where inner-layer copper necks down to 0.079 mm, below the 5 mil (0.127 mm) minimum its PCBWay quote orders. Footprints that differ from their library copy (`lib_footprint_mismatch`) aren't counted. `metrics.json` has the counts by type.
- **Stock:** a line counts as stocked when LCSC or Digi-Key has its quantity × 5 on hand. Digi-Key is searched by manufacturer part number, including packaging variants such as `/TR`.
- **Discontinued:** LCSC lists the part as discontinued, or every Digi-Key listing of it is Obsolete or Discontinued at Digi-Key. Some of these parts are still in stock.
- **Fab files:** every Gerber and drill file in the order zip matches a fresh export from the board, layer by layer, within 0.1% of the drawn area. Every zip has all copper layers, Edge.Cuts, both masks, F.Silkscreen, paste for each side with surface-mount parts, and the drill files.
- **Placement:** every placement file lists every surface-mount part once, on the right side and at the board's rotation. After lining up the file's origin and axes with the board, every part is within 0.5 mm of its board position.
- **Footprints:** each part's pad count matches LCSC's footprint for its part number. Connectors aren't compared, because libraries split shield tabs and doubled contacts differently.
- **Prompt features:** every BOM has a part for the RP2350, QSPI flash, PSRAM, USB-C, Wi-Fi and BLE, microSD, Qwiic, an RGB LED and a power-path charger. Every board monitors the battery, with a fuel gauge or a resistor from a battery net to an ADC pin.
- **Deliverables:** every run has a README, a schematic and project file next to the board, and a fab folder.
- The files checked are `board`, `bom`, `placement` and `fabZip` in `info.json`. `metrics.json` lists the designators and per-layer results.

### Circuit and layout checks

| Run | RP2350 power pins with a capacitor within 3.2 mm | Pins farther away (mm) | Battery divider | Divider current at 4.2 V (µA) | Divider switched | Antenna keepouts | Copper in the keepouts |
|---|---|---|---|---|---|---|---|
| [`codex-desktop--gpt-6.1-sol`][codex] | 13 of 14 | QSPI_IOVDD 54: 3.43 | R25 100k / R26 100k, buffered by U8 | 21 | no | U9 footprint | none |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 14 of 14 | none | R10 470k / R11 470k, buffered by U9 | 4.47 | no | U6 footprint | none |
| [`backplane--opus-5.5`][backplane] | 14 of 14 | none | R9 200k / R10 100k | 14 | no | U7 footprint, board | none |
| [`backplane--gpt-6.1-sol`][backplane] | 9 of 14 | DVDD 6: 3.45, IOVDD 11: 3.66, DVDD 23: 3.59, DVDD 39: 6.4, ADC_AVDD 44: 12.15 | R25 100k / R26 100k | 21 | no | U8 footprint, board | /3V3 fill on In4.Cu |
| [`backplane--fable-5.2`][backplane] | 8 of 14 | IOVDD 1: 3.34, DVDD 6: 7.34, IOVDD 11: 3.69, IOVDD 20: 4.27, DVDD 23: 6.05, DVDD 39: 4.08 | R12 200k / R13 200k | 10.5 | no | board | none |
| [`sprocket--opus-5.5`][sprocket] | 12 of 14 | DVDD 23: 3.97, VREG_AVDD 46: 3.54 | R10 100k / R11 100k | 21 | no | U4 footprint, board | none |
| [`sprocket--gpt-6.1-sol`][sprocket] | 13 of 14 | VREG_AVDD 46: 3.67 | fuel gauge U8 | - | - | U7 footprint | none |
| [`sprocket--fable-5.2`][sprocket] | 14 of 14 | none | R13 100k / R14 100k | 21 | no | U7 footprint, board | none |

| Run | D+ length (mm) | D- length (mm) | Mismatch (mm) | Vias | Width (mm) | Gap (mm) | Side by side (mm) | Differential impedance (Ω) | ESD parts on D+ and D- |
|---|---|---|---|---|---|---|---|---|---|
| [`codex-desktop--gpt-6.1-sol`][codex] | 51.45 | 52.84 | 1.39 | 2 | 0.15 | 0.15 | 37.66 | 87.9 | U5 |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 28.51 | 24.53 | 3.98 | 4 | 0.15 | 0.15 | 8.29 | 95.5 | U8 |
| [`backplane--opus-5.5`][backplane] | 38.02 | 38.29 | 0.27 | 0 | 0.25 | 1.25 | 11.78 | 120.9 | U1 |
| [`backplane--gpt-6.1-sol`][backplane] | 58.54 | 42.65 | 15.89 | 6 | 0.22 | 1.68 | 9.93 | no stackup | U5 |
| [`backplane--fable-5.2`][backplane] | 44.52 | 42.26 | 2.26 | 3 | 0.15 | 0.16 | 4.86 | 114.7 | U6 |
| [`sprocket--opus-5.5`][sprocket] | 59.86 | 60.9 | 1.04 | 5 | 0.127 | 1 | 0.99 | 114.5 | U7 |
| [`sprocket--gpt-6.1-sol`][sprocket] | 36.51 | 38.61 | 2.1 | 6 | 0.234 | 0.15 | 14.58 | 96.5 | U4 |
| [`sprocket--fable-5.2`][sprocket] | 29.55 | 29.6 | 0.05 | 4 | 0.22 | 0.15 | 12.04 | 90.7 | U6 |

- **Decoupling:** for each RP2350 IOVDD, DVDD, QSPI_IOVDD, USB_OTP_VDD, ADC_AVDD, VREG_VIN and VREG_AVDD pad, the nearest capacitor with one pad on that pin's net and the other on a ground net, on either side of the board. The distance is from the center of the pin's pad to the center of the capacitor's nearest pad. Pins are found by the pads' pin functions, or by RP2350A pad numbers when the footprint names none. Hardware design with RP2350 asks for decoupling close to the power pins without giving a distance. Its own Minimal board, whose capacitors it calls slightly further from the chip than optimal, has one within 3.2 mm of every power pin.
- **Battery divider:** the resistor from the battery to the ADC input, or to the op-amp follower that drives it, and the resistor from there to ground. The current is 4.2 V over their sum, from the footprint values. A divider is switched when its top resistor reaches the battery through a transistor or load switch rather than directly.
- **USB:** D+ and D- run from the RP2350 pins through the series resistors to the USB-C connector. Lengths add every track segment and arc on those nets, including stubs. Width and gap are for the longest stretch where D+ and D- segments run parallel on one layer within 2 mm of each other, and "side by side" is that stretch's length. The impedance uses the IPC-2141 edge-coupled microstrip formula with that width and gap and the board's stackup. `backplane--gpt-6.1-sol` has no stackup in its board file.
- **ESD parts:** parts other than the connector and the RP2350 with pads on both D+ and D-.
- **Antenna keepouts:** rule areas in the Wi-Fi module's footprint or on the board that overlap the module's courtyard and forbid copper. Copper in them counts tracks, vias, zone fills and other parts' pads on every copper layer, including layers the rule area doesn't cover. The rule area in the `backplane--fable-5.2` module footprint lies off the board, so only its board rule area counts.
- `design` in `metrics.json` has the per-pin distances, resistor values, net names and keepout layers.

### Fixes needed before PCBWay can make and assemble the board

| Run | PCB manufacturing | Assembly |
|---|---|---|
| [`codex-desktop--gpt-6.1-sol`][codex] | no | L2 is a legacy part. C5 C16 C18 C22 C37, D1 and L1 aren't stocked. |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 0.5 oz inner copper. R42's 0402 footprint doesn't fit its 0603 substitute. | C26 C27 have an invalid MPN. R42 isn't sold. C29 isn't stocked. |
| [`backplane--opus-5.5`][backplane] | 0.5 oz inner copper. 3 DRC errors. | C8 C9 C10 aren't stocked. |
| [`backplane--gpt-6.1-sol`][backplane] | no | R3 has an invalid MPN. C3 C16 C40, C17 C21, C28 C29 C30 C34, R40 and D2 aren't stocked. |
| [`backplane--fable-5.2`][backplane] | 0.5 oz inner copper. | C19 C20 C21 aren't stocked. |
| [`sprocket--opus-5.5`][sprocket] | no | no |
| [`sprocket--gpt-6.1-sol`][sprocket] | no | C5 C7 C8, C21 C29, C22 C23 C24 C30 C33 and C26 C27 C32 aren't stocked. |
| [`sprocket--fable-5.2`][sprocket] | no | no |

- **PCB manufacturing:** a `fixes` entry for the fab notes or the board, DRC errors, unconnected items, or fab files that are missing or differ from the board. PCBWay doesn't offer 0.5 oz inner copper.
- **Assembly:** a `fixes` entry for the BOM, lines not stocked for 5 boards, footprint pad counts that differ from the part, or BOM and placement file problems. Discontinued parts that are still stocked don't count.
- `needsFixes` in `metrics.json` has the full list for each run.

### Design review

| Run | Crystal | Buttons | Power path | Thermal | Grounding | Layout | Routing | Silkscreen | Total of 50 |
|---|---|---|---|---|---|---|---|---|---|
| [`codex-desktop--gpt-6.1-sol`][codex] | 2 of 2 | 2 of 2 | 2 of 2 | 4 | 5 | 3.5 | 3.5 | 6 | 22 |
| [`codex-desktop`][codex][`-texttocad--gpt-6.1-sol`][texttocad] | 2 of 2 | 2 of 2 | 2 of 2 | 5 | 4.5 | 6.5 | 4 | 6 | 26 |
| [`backplane--opus-5.5`][backplane] | 2 of 2 | 2 of 2 | 2 of 2 | 4 | 7 | 6 | 6.5 | 6 | 29.5 |
| [`backplane--gpt-6.1-sol`][backplane] | 2 of 2 | 2 of 2 | 0 of 2 | 3.5 | 4.5 | 5 | 3 | 6 | 22 |
| [`backplane--fable-5.2`][backplane] | 2 of 2 | 2 of 2 | 1 of 2 | 5 | 6.5 | 6.5 | 3.5 | 5 | 26.5 |
| [`sprocket--opus-5.5`][sprocket] | 2 of 2 | 2 of 2 | 1 of 2 | 5 | 5.5 | 5.5 | 3.5 | 7 | 26.5 |
| [`sprocket--gpt-6.1-sol`][sprocket] | 2 of 2 | 2 of 2 | 1 of 2 | 4 | 6.5 | 5 | 3.5 | 4 | 23 |
| [`sprocket--fable-5.2`][sprocket] | 2 of 2 | 2 of 2 | 1 of 2 | 4.5 | 6.5 | 7 | 5.5 | 6 | 29.5 |

- **Judges:** gpt-6.1-sol and opus-5.5, each on high reasoning in the Sprocket CLI with its KiCad connector, review every board. fable-5.2 wasn't used as a judge. Each judge sees only an anonymous copy of the board: the KiCad project, the BOM, and renders and layer images exported with the run's KiCad version. It upgrades the project to the connector's KiCad before inspecting it. [bench/judge/README.md](bench/judge/README.md) has the details.
- **Yes or no columns:** how many judges answered yes. The board score counts the share of yes votes. Scores are integers from 0 to 10, averaged across the judges, and the total adds the five averages. The rubric gives each score a one-line description and bands for 9–10, 6–8, 3–5 and 0–2. It is in [bench/judge/prompt.md](bench/judge/prompt.md).
- `runs/<run-id>/review/<model>.json` has each judge's review, and `<model>.md` has its final message and the reports of the subagents it started.

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
  check.ts               checks the BOM, placement file, parts and prompt features, and lists the fixes PCBWay needs
  inspect.ts             runs DRC and ERC, matches the fab files, checks 3D models and renders the board, with the run's KiCad version
  fab-match.ts           compares the delivered Gerbers and drill files with a fresh export
  board.ts               reads a run's board footprints, pads, tracks, zones and stackup
  judge/                 the design review: anonymous board packages, the judges' rubric and the driver, with a README
  score.ts               the board score, and how the ranking changes when weights shift
  bom.ts                 reads a run's BOM CSV
  lcsc.ts                looks up LCSC parts
  digikey.ts             looks up Digi-Key stock and part status
runs/<run-id>/
  output/                everything the agent left in its work folder
  renders/               top.png, bottom.png and iso.png from kicad-cli pcb render, with the run's KiCad version
  review/                each judge's review of the board and its reasoning
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

## Notes on the runs

- In `sprocket--gpt-6.1-sol`, 34 of 70 subagents used opus-5.5. The cost split by model is in `costByModel` in its `metrics.json`.

[sprocket]: https://usesprocket.dev/
[backplane]: https://backplaneworks.com/
[codex]: https://openai.com/codex/
[texttocad]: https://texttocad.dev/
