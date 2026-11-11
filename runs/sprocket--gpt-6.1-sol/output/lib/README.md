# Project footprints

`Board.pretty` derives from the installed KiCad 10.0 footprint libraries. Pad dimensions remain those of the original library footprints.

- Abracon AOTA: adds a visible winding-terminal mark. **Pad 1, the marked terminal, is the core output; pad 2 is VREG_LX.** This follows Raspberry Pi's [Minimal-KiCAD R4 reference](https://datasheets.raspberrypi.com/rp2350/Minimal-KiCAD.zip). The official land pattern is 0.7 × 1.7 mm at ±0.7 mm; the KiCad manufacturer's pattern used here is 0.8 × 1.6 mm at ±0.75 mm.
- ESP32-C3-WROOM-02: limits the antenna rule area to this board's four copper layers and omits silkscreen that would lie outside the PCB under the overhanging antenna. The pin-1 triangle remains on Fab. Ground-pad thermal holes are 0.2 mm, as in the library footprint.
- Hirose microSD: preserves the manufacturer's pad/switch/shell geometry and five top-layer keepouts.
- WS2812B: moves the redundant numeric pin-1 text to Fab. The package outline/polarity notch remains.

Rule-area thermal settings are normalised to the connector's 0.25/0.5 mm serialised values. These settings do not affect copper because the areas are keepouts.

Original libraries: [KiCad footprints](https://gitlab.com/kicad/libraries/kicad-footprints). Retain the applicable KiCad library licence and attribution when redistributing these footprints.
