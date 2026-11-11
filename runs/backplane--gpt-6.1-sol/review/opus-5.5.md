# opus-5.5's review

## Final message

I wrote `review.json`. The board fails the power-path check because the USB TVS diode is placed backwards, which shorts USB VBUS. The crystal and the buttons pass.

```json
{ "crystal": true, "buttons": true, "powerPath": false, "thermal": 3, "grounding": 4, "layout": 5, "routing": 3, "silkscreen": 5 }
```

I upgraded `board.kicad_sch` and `board.kicad_pcb` in place with `kicad-cli … upgrade` and changed nothing else. KiCad also created a `board.kicad_prl` settings file. After the upgrade, ERC is clean. DRC shows 0 unconnected items, 0 parity issues and two warnings: a dangling via on `XOUT_DRV` and a dangling stub on `SD_CS`. I deleted my scratch folder.

**Yes/no answers**

| Key | Answer | Evidence |
|---|---|---|
| `crystal` | yes | Abracon ABM8-272-T3 (12 MHz, 10 pF load), 15 pF C0G caps and a 1 kΩ resistor on XOUT. That is the part and values the RP2350 datasheet recommends, and the crystal footprint's pins match the part. |
| `buttons` | yes | RUN goes to ground through SW1 (with a 10 kΩ pull-up and 100 nF cap). BOOTSEL connects QSPI_SS through 1 kΩ (R9) and SW2 to ground. Both are top-pressed switches on the front, 8 mm apart, with nothing tall around them. |
| `powerPath` | no | D1 is an SMF5.0A, which conducts one way only, but the schematic uses a two-way symbol. Its pad 1, the cathode-band end, is on GND and its anode is on `VBUS_RAW`, before the fuse. The diode conducts as soon as USB is plugged in, so VBUS collapses and the board can't run from USB. |

The charger chip (BQ24074) and the 3.3 V buck-boost would otherwise do the job. Switching to battery on unplug would be seamless. There is a smaller problem: pull-downs on EN1 and EN2 leave the charger at a 100 mA input limit at power-up, so firmware must raise it before the Wi-Fi module starts transmitting.

**Scores**

- **Thermal, 3:**
  - The charger's thermal pad (U6) has no vias, and it dissipates about 0.9–1 W while charging at 500 mA.
  - The RP2350's ground pad has no vias of its own.
  - The buck-boost's inductor traces (`BB_L1`/`BB_L2`) are 0.18 mm wide for about 1.5–2 A peaks.
  - `VSYS` narrows to 0.15 mm.
- **Grounding, 4:**
  - The In1 ground plane is solid, and the outer ground pours are cut into 40 (front) and 27 (back) stitched pieces.
  - The RP2350's only ground, its exposed pad, reaches the plane through a 34 mm² copper patch with one via.
  - Signals on the back and on In3 reference the 3.3 V plane, not ground.
- **Layout, 5:**
  - Blocks are grouped well. USB-C, microSD, the GPIO sockets and the ESP UART header are at the edges, and the antenna hangs past the edge with a keepout on every layer.
  - The crystal is about 9 mm from the RP2350 and the flash about 10 mm away.
  - The buttons sit mid-board, and the Qwiic connector is set 8 mm back from the edge.
- **Routing, 3:**
  - The crystal's XIN trace is 25 mm long with 6 vias.
  - The SD clock path is about 136 mm long.
  - USB D+ runs partly on an inner layer while D− stays on top.
  - The QSPI traces are 20–29 mm long.
- **Silkscreen, 5:**
  - Pin-1 and polarity marks are there, no silkscreen sits on pads, and the text is readable.
  - The two 12-pin GPIO sockets have no label or pin names at all.
  - The "BAT+ GND NTC" text is spaced wider than the 2 mm pins, so "GND" sits over the NTC pin.
