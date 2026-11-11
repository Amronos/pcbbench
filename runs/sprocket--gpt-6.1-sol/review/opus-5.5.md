# opus-5.5's review

## Final message

I wrote [review.json](review.json):

```json
{ "crystal": true, "buttons": true, "powerPath": true, "thermal": 4, "grounding": 5, "layout": 5, "routing": 3, "silkscreen": 4 }
```

**Upgrade:** I didn't need to change anything. Both files already use the connector's format (generator 10.99, board `20261031`, schematic `20261106`). `kicad-cli … upgrade` reported "not updated", and the board, schematic and project files are byte-for-byte the same as before. ERC and DRC (with zone refill and schematic parity) found only missing-library warnings: 0 unconnected items and 0 parity issues.

The files in `renders/` don't match the board. They show "SPROCKET 2350" on the silkscreen, but the board says "KESTREL 2350". I reviewed the board file itself, using fresh renders and copper views.

**Yes/no answers**

| Key | Answer | Evidence |
|---|---|---|
| crystal | yes | Y1 is the ABM8‑272‑T3: 12 MHz, 10 pF load, approved by Raspberry Pi. It has 15 pF load caps and a 1 kΩ resistor on XOUT, as in the design guide. Its placement and traces are poor (see layout). |
| buttons | yes | BOOTSEL connects QSPI_SS through 1 kΩ to GND. RUN has a 10 kΩ pull-up and a button to GND. Both buttons are top-mounted TL3342s about 9 mm apart with nothing over them. |
| powerPath | yes | The BQ24074 feeds SYS, which feeds the TPS63001 buck-boost (input range 1.8–5.5 V). SYS stays regulated with no battery or a flat one. On unplug, the charger's battery switch takes over, and the buck-boost holds 3.3 V down to a battery of about 3 V. Two things depend on firmware: input current starts limited to 100 mA (EN1 pulled down), and charging starts disabled (CE pulled up). |

**Why the scores are low**

- **Thermal (4):**
  - The whole 3.3 V output runs from U6 over 0.127 mm traces and one via into the In2 plane.
  - Every via on the board is 0.45/0.15 mm. Single vias carry:
    - USB power into the charger.
    - The charger's output into SYS.
    - Both switching nodes of the buck-boost inductor, with peaks over 1 A.
  - U5's thermal pad has no vias, and U6's pad has one.
- **Grounding (5):**
  - In1 is one solid GND plane, which is good.
  - The top and bottom GND pours are broken into dozens of pieces. Several pieces of about 100 mm² hang on a single via.
  - There is no via fence along the board edge, and the RP2350's centre pad has one via.
  - In2, the 3.3 V plane under the bottom-layer signals, carries 2 mm GND traces and many signal traces. That cuts slots in the plane.
- **Layout (5):**
  - The USB‑C, LiPo, microSD and Qwiic connectors sit at the edges, and the antenna hangs past the corner. All good.
  - The crystal is about 12 mm from the RP2350, and the flash about 10 mm.
  - BOOT and RUN sit mid-board, not at an edge.
  - The SD card is at the bottom-right, but its GPIO4–7 pins are on the chip's left side.
- **Routing (3):**
  - Power traces are too thin: 0.127 mm on the 3.3 V output and the core regulator's switch node (VREG_LX).
  - QSPI traces run 21–42 mm and SD traces 44–70 mm, with up to 8 vias each.
  - XIN runs 20 mm through two vias and crosses RUN.
  - 25 bottom-layer QSPI, SD and XIN segments cross the slots in In2.
- **Silkscreen (4):**
  - The "LiPo + -" label puts "+" over the GND pin.
  - "RST" sits about 13 mm from SW2, next to the crystal and the SWD header.
  - The GPIO, SWD and radio UART headers have no labels, and the test points are unlabeled.
  - The pin-1 marks for the ESP32 module and the RGB LED were moved to the fab layer, so they won't be printed.
  - All text has a 0.12 mm stroke, below PCBWay's 0.15 mm minimum, so it may print illegibly.

The board can still be built at PCBWay. The 0.15 mm drills are within its range but cost extra, and the two capacitors on the bottom need a second assembly pass. The WS2812B‑V6 is fine at 3.3 V; its datasheet supports it.
