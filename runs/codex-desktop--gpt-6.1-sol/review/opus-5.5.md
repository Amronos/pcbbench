# opus-5.5's review

## Final message

I wrote `review.json`. The schematic is sound on all three yes/no checks, but the layout has clear thermal, grounding and routing problems.

```json
{ "crystal": true, "buttons": true, "powerPath": true, "thermal": 3, "grounding": 4, "layout": 5, "routing": 3, "silkscreen": 5 }
```

I upgraded the four schematics and the board in place to the connector's format (schematics 20261106, board 20261031) and made no other changes. ERC and DRC both pass with no violations, including after refilling the zones, so the problems below are ones DRC doesn't catch. I deleted my scratch files and the `board.kicad_prl` file that the upgrade created.

**Yes/no checks**

- **Crystal: yes.** It is the ABM8-272-T3 (10 pF load) with 15 pF caps and a 1 kΩ series resistor on XOUT. That matches the RP2350 hardware design guide exactly, and the pins are mapped correctly. One weakness: Y1 sits about 6 mm away and XIN runs about 10 mm on an inner layer, which adds stray capacitance.
- **Buttons: yes.** BOOTSEL connects QSPI_SS through 1 kΩ to the button, as the guide shows. The 4.7 kΩ pull-up still pulls the pin down to about 0.58 V when pressed, below the 0.8 V input-low limit. RUN has a 10 kΩ pull-up, 100 nF and a button to GND. Both TL3342 buttons are on the top side, about 10 mm apart, with nothing over them.
- **Power path: yes.** The BQ24074 holds its output at 4.4 V from USB and charges the battery from what's left. It runs with no battery (an open thermistor pin only stops charging) and from a flat one. When USB is unplugged it switches to the battery internally. The TPS63060 buck-boost accepts 2.5 to 12 V, so 3.3 V doesn't drop. The RP2350's external 1.1 V core supply, with VREG_FB grounded and VREG_LX open, is a setup the RP2350 datasheet supports. Note that input current defaults to 100 mA until firmware raises GPIO23.

**Scores**

| Area | Score | Main reasons |
|---|---|---|
| Thermal | 3 | No vias in any exposed pad: RP2350, BQ24074, TPS63060, TLV75801 or ESP32. The TPS63060's power ground is only its exposed pad, and the nearest GND via is 5 mm away. The 500 mA PTC runs at its hold current at full USB load, so it can trip in warm conditions. |
| Grounding | 4 | In1 is a solid GND plane, but only 28 GND vias stitch an 80×65 mm board. The RP2350's ground pad sits on a top-layer copper island with one via. Most decoupling-cap grounds are 3 to 7 mm from a via. B.Cu has no ground, and the In2 3.3 V plane is cut into pieces by traces. |
| Layout | 5 | Blocks are grouped sensibly. The antenna is at an edge with copper kept clear, and the USB, microSD, Qwiic and headers are at edges. But the BOOT, RESET and ESP BOOT buttons, SWD and the battery connector sit inside the board. The USB connector is far from the RP2350's USB pins. |
| Routing | 3 | The battery path is a 0.15 mm trace and VBUS uses 0.15 mm traces with vias, for 0.5 to 1 A. QSPI hops through B.Cu and In2 with 18 to 34 mm traces between chips about 10 mm apart. SD runs long on In2 or B.Cu, which reference a cut-up 3.3 V plane or a plane 1.24 mm away. USB is about 50 mm long, though it does run over solid GND. |
| Silkscreen | 5 | It has pin-1 marks, the J2 "1+" mark, and labels for the buttons and most connectors. The GPIO headers J6 and J7 have no pin labels, and the test points have none. Most text is 0.7 mm high with 0.12 mm strokes, below PCBWay's 0.8 mm / 0.15 mm minimum. Nothing is printed on pads. |

Separately, no footprint has a 3D model, which is why the renders show bare pads.
