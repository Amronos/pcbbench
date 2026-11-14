# opus-5.5's review

## Final message

I wrote `review.json` with three findings, all `minor`. I found nothing fatal and no layout problems: I'd expect this board to work as built.

**Upgrade**

I upgraded all five schematics and the board in place with `kicad-cli sch upgrade` and `kicad-cli pcb upgrade`:

- Schematics: from format 20260306 (KiCad 10.0) to 20261106 (10.99).
- Board: from 20260901 to 20261031.

Nothing else in the design changed. DRC on the upgraded board finds 0 unconnected items and 3 connection-width warnings in the copied RPi regulator copper.

**Findings**

| # | Area | Nets | Problem |
|---|---|---|---|
| 1 | routing | VSYS, VBAT | The charger output and battery path are 0.4 mm tracks on 35 µm copper. At 1.5 A that is about a 16 °C rise by IPC-2221; a 10 °C rise needs about 0.53 mm. VSYS reaches the header through a single 0.3 mm via. |
| 2 | routing | QSPI_SD0, SD1, SS | Each path has 2 vias, and one sits under the RP2350 body at (137.47, 117.77). The Raspberry Pi reference uses none. The PSRAM branches run 1.7 to 2.3 times their straight distance. |
| 3 | routing | SD_D3, SD_D2 | SD_D3 is 38.9 mm long against 14.6 mm straight, looping on B.Cu under the crystal. SD_D2 has 4 vias and a 10 mm stub to its pull-up. |

**What I checked and left out**

- **Matches the Raspberry Pi reference:** I downloaded the Raspberry Pi RP2350A minimal reference board and compared it pad by pad. The RP2350 footprint, the regulator inductor and its orientation, the crystal and the flash sit exactly where the reference puts them, rotated 90°. That is why I didn't report the flash at about 10 mm or the crystal at about 9 mm from their pins.
- **Pinouts on the right nets:** I checked these against datasheets or standard pinouts:
  - BQ24074 charger: EN2 high and EN1 low select the ILIM resistor, and TMR and ITERM left open select the defaults.
  - ESP32-C6-MINI-1 module: pins and land pattern, and it isn't mirrored.
  - Flash, PSRAM, microSD, LDO, ESD array, RGB LED, LEDs, SWD and Qwiic pinouts.
- **Connectors and antenna face out:** the USB-C edge line is at x = 100. The JST, Qwiic, SWD and microSD openings face their edges, and the antenna ends at x = 179.85 with nothing in front of it.
- **Not reported, because your automated checks cover it:** USB D+ and D− run about 5 mm apart over roughly 10 mm, so they aren't a coupled pair. That only matters for impedance, and full-speed USB tolerates it.

I put my scratch files in `.scratch/` inside the folder and deleted them at the end, along with the `board.kicad_prl` that `kicad-cli` created. Two slips: I briefly copied the project to `/tmp` before moving the copy into the folder, and I wrote one scratch script with a shell heredoc instead of `apply_patch`.
