# opus-5.5's review

## Final message

I wrote `review.json`:

```json
{ "crystal": true, "buttons": true, "powerPath": true, "thermal": 5, "grounding": 4, "layout": 6, "routing": 3, "silkscreen": 6 }
```

I upgraded the six schematics from format 20250114 to 20261106. The board was already in the connector's format (20261031), and a forced re-save produced a byte-identical file, so its design is unchanged. After the upgrade, ERC, DRC (with zone refill and schematic parity, all severities) and the unconnected count all came back at 0. Every Atlas footprint matches the stock KiCad one except the custom TPS63070 footprint. I checked that one's pin order against TI's pinout and it matches.

**Yes/no answers**

- **`crystal` (yes):** The ABM8-272-T3 (12 MHz, 10 pF load) with 15 pF C0G load capacitors and a 1 kΩ resistor on XOUT is exactly the circuit in the RP2350 hardware design guide. The pin mapping is correct. One layout fault doesn't change the answer: the SD_DETECT trace runs on In1 directly under the XIN pad.
- **`buttons` (yes):**
  - RUN has a 10 kΩ pull-up and SW1 pulls it to GND.
  - BOOTSEL (SW2) pulls QSPI_SS to GND through 1 kΩ, which overrides the 10 kΩ pull-up. This matches the guide.
  - Both are top-side TL3342 switches 8 mm apart with nothing over them, so a user can press both.
- **`powerPath` (yes):**
  - The BQ24074 holds OUT at a fixed 4.4 V from USB, so the board runs with no battery or a flat one.
  - Pulling USB switches OUT to the battery through the internal FET. The TPS63070 buck-boost (2–16 V input) keeps 3.3 V up, so the RP2350 doesn't reset.
  - Caveat: EN1 and EN2 default low, which limits USB input to 100 mA until firmware raises it. That is enough for the RP2350 to boot, because the ESP32 is held in reset.
  - Caveat: if a battery without an NTC is plugged in, the TS pin floats and the board won't charge it.

**Scores**

| Area | Score | Main findings |
|---|---|---|
| thermal | 5 | The BQ24074's exposed pad has one via and dissipates up to about 0.65 W. The VBAT trace is 0.15 mm, mostly on the thinner inner copper (17.5 µm), and carries battery current. The fuse F1 holds 0.5 A, about the same as the charger's 0.5 A input limit, so it can trip when warm. The TPS63070 has one PGND via. |
| grounding | 4 | All four layers are GND pours with 132 stitching vias and no islands. But about 16 signal nets run on In1, the plane next to the top layer. They slice it under the RP2350, the crystal, the QSPI memories and the SD lines. In2 and B.Cu are cut too. |
| layout | 6 | Blocks are grouped well: power and USB-C on the left, the ESP32 antenna hanging off the top edge and clear, Qwiic on the right edge. But all four buttons, the GPIO header, the SWD header and the ESP programming header sit mid-board. The microSD slot is about 4 mm in from the edge, and the flash is about 10 mm from the RP2350 with 20 mm of clock trace. |
| routing | 3 | Signals use the In1 ground plane as a routing layer. USB D+ and D− aren't routed as a pair: D− changes layer through four vias. QSPI hops to B.Cu over a cut In2 plane, and SD_MISO and SD_DETECT run mostly on In1. Some nets wander, like RGB_DATA at 100 mm with 7 vias. VBAT is undersized. |
| silkscreen | 6 | Connectors and buttons are labelled, with pin-1 marks and no silkscreen on pads (DRC clean). But "BAT+ GND NTC" is a horizontal row above vertically stacked pins, with no "+" at the pad. "PWR" is about 10 mm from the slide switch and has no ON/OFF marks. The 20-pin GPIO header has no pin labels, and "USB-C" and "SWD" sit over vias. |
