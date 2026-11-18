# Prototype release review

This package is for a first prototype build after PCBWay's engineering and sourcing approval. No board has been built, bench-tested or ordered. It is not a production release.

## Layout revisions

| Block | Implemented change |
|---|---|
| RP2350 core regulator | Copied Raspberry Pi's compact placement, pad geometry, top copper, feedback and local return geometry. Removed extra top GND beneath L2 and In1 copper beneath LX. L2 pad numbering preserves the schematic, with its winding dot at the lower-left 1V1 end. |
| Charger and 3.3 V converter | Moved switching inductor and bypass capacitors to their pins. Main power copper is 0.5–0.6 mm, with short fine-pitch pad escapes. U4/U5 each have four thermal vias. |
| L1 sourcing | Replaced the discontinued part with SRN4018-2R2M and Bourns' dedicated land pattern. |
| USB | Moved the connector near U1, moved both series resistors beside the MCU, and rebuilt the pair. Main trunks use 0.22 mm width and 0.15 mm gap. Local connector/MCU fanout departs from this geometry. |
| Radio | Moved C28/C29 beside the module supply. EN defaults low and is enabled by firmware. |
| Input-current control | GP6 selects USB100/USB500 through R19, with R20 holding USB100 at reset. |
| Libraries and 3D | Project-local land patterns preserve the customized geometry. All component bodies are represented. J1/J3/D2 models are visualization-only approximations. |

## Manufacturer approval before purchase

- Confirm exact BOM sourcing, through-hole headers J5/J6, and no unapproved substitutions.
- Confirm the proposed 1.6 mm, four-layer, 35 µm copper stack and recalculate USB for 90 Ω ±10%, including solder mask and nearby copper. The engineer may adjust dielectric/trace geometry before fabrication; return any changes for CAD review.
- Require IPC-4761 Type VII nonconductive resin fill, planarization and copper capping at via-in-pad sites. Do not reflow over open barrels.
- Review QFN/SON paste, panel rails, tooling and fiducials. Keep panel features out of the ESP antenna region.
- Reconcile connector polarity and placement rotations against assembly drawings.

## Limits and qualification

The board is a USB 5 V sink/device. It has no USB PD negotiation or host function. It defaults to USB100, but does not guarantee generic legacy-host pre-enumeration/suspend compliance. Hardware does not gate SD/RGB/Qwiic power, and the ROM loader has no board-specific power policy. Use an explicitly permitted 500 mA source for USB-only development, or a protected battery with a qualified host.

Use an external protected 1S 4.2 V LiPo with cell-mounted 10 kΩ B3435 NTC. J3 pin 1 is BAT+, pin 2 GND, pin 3 NTC. Check the pack's polarity and charge/discharge ratings. The charger does not replace pack protection.

Short U5 0.24 × 0.8 mm pad escapes have an estimated 1.64 mΩ resistance at 35 µm copper. At 1.2 A each dissipates about 2.4 mW. These are copper-loss estimates, not measured temperature rises. Do not rate the board for 1.2 A throughout the battery range. TI specifies lower boost-mode capability, and all board and external loads share the 3.3 V budget.

VINA uses direct local bypassing rather than TI's 100 Ω RC filter. TI says operation without the filter is possible. Check control-supply noise and converter stability during buck/boost crossover and radio/SD load steps before production approval.

Bench tests must cover USB enumeration in both orientations, ROM boot/SWD, flash/PSRAM stress, SD writes, Wi-Fi/BLE, RGB, Qwiic, battery ADC, USB/battery insertion sequences, charger/NTC open and short conditions, current limits and temperature. No firmware image or measured result is supplied.
