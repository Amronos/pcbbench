# Prototype fabrication and assembly package

The revised design and exports are ready for PCBWay engineering review and quoting. Obtain the confirmations in [release-review.md](release-review.md) before ordering. No board has been built or bench-qualified.

## Package contents

| Path | Contents |
|---|---|
| `BOM.csv` | 93 fitted references grouped by exact manufacturer/MPN/footprint |
| `schematic.pdf`, `schematic.png`, `schematic/` | Current schematic exports |
| `erc.json`, `drc.json` | All-severity checks; `ignored_checks` lists KiCad checks disabled in project settings |
| `sprocket2350.net` | Schematic netlist |
| `gerbers/` | Four copper layers, solder mask, silkscreen, paste and board outline |
| `drill/` | Metric Excellon plated/nonplated holes, drill maps and report |
| `positions.csv` | All fitted parts, including through-hole headers, in mm |
| `via-in-pad.csv` | Absolute coordinates of 18 vias requiring Type VII processing |
| `assembly/` | Top/bottom assembly drawings |
| `sprocket2350.d356` | Fabrication connectivity file |
| `board-3d.png`, `board-top.png` | Review renders |
| `sprocket2350-review-gerbers.zip` | Gerbers and drill files only, for fabrication review |
| `sprocket2350-prototype-package.zip` | Fabrication, assembly, sourcing and review files, plus KiCad sources, libraries and tools |

The final all-severity ERC and DRC reports contain zero violations, zero unconnected items and zero schematic parity issues. These checks do not establish electrical, thermal or USB compliance.

## Proposed PCBWay build

- One 85 × 65 mm rectangular board, four-layer FR-4, 1.6 mm finished thickness, ENIG, green mask and white top silkscreen.
- Layer order: F.Cu signal/components, In1.Cu GND, In2.Cu 3.3 V with residual GND, B.Cu signals/GND. No tracks on In1.Cu. A local In1 copper cutout beneath the RP2350 LX node follows the chip's layout guidance; it does not cross the USB reference corridor.
- Quote target: 35 µm finished copper on all four layers, 0.1855 mm outer prepregs with DK 4.74, and a 1.030 mm core with DK 4.6. This follows PCBWay's regular four-layer nominal 1.6 mm stack, published as 1.61 mm ±10%. The KiCad stack and Gerber job record this target, not an approved impedance stack.
- PCBWay must confirm actual laminate, finished copper, solder-mask thickness and dielectric loss, and recalculate the USB trunks for 90 Ω ±10% including nearby copper. KiCad's mask thickness and loss-tangent defaults are placeholders. Main USB trunks are 0.22 mm wide with a 0.15 mm gap; local fanout differs. Return any geometry changes for CAD review.
- Current global minimum rules: 0.11 mm track/clearance, 0.45 mm via diameter, 0.20 mm drill, 0.10 mm annular ring, 0.20 mm copper-to-foreign-hole, 0.25 mm hole-to-hole, 0.30 mm copper-to-edge. Routed signal width is generally 0.12 mm. Confirm the selected PCBWay process supports these figures.
- Require IPC-4761 Type VII nonconductive resin fill, planarization and copper capping at all 18 sites in `via-in-pad.csv`. Ordinary vias may be tented. Do not leave open barrels in solder-paste apertures.
- All parts fit on top. PCBWay supplies and installs all references, including J5/J6 through-hole headers. No DNP parts or user soldering.
- Keep the ESP antenna beyond the top board edge clear of copper, metal, panel features and the intended enclosure. PCBWay must propose panel rails, tooling and fiducials without entering that keepout.

The outline is at absolute X = 100–185 mm, Y = 100–165 mm. Export Gerbers and drills with the same absolute origin. Preserve KiCad's signed Y convention in the position CSV; do not independently shift or mirror it. PCBWay must reconcile rotations and pin 1 against the assembly drawings before placing parts.

See [assembly.md](assembly.md) for assembly instructions and [procurement.md](procurement.md) for sourcing risks. No quote, sourcing approval, fabrication release or purchase is implied.

## Operating limits

USB100 is selected at reset and the radio defaults off. Firmware must select USB500 only when permitted and enable the radio deliberately. Hardware does not gate SD/RGB/Qwiic power, and the ROM loader has no board-specific power policy. Generic legacy-host pre-enumeration and suspend compliance is not guaranteed. For USB-only development, use a source explicitly permitting 500 mA. See [release-review.md](release-review.md) for battery requirements and prototype qualification tests.
