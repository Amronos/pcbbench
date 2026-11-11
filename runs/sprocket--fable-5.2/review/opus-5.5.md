# opus-5.5's review

## Final message

I wrote [review.json](review.json). The three yes/no checks pass. The layout and routing scores lose points mainly for the charger's missing thermal vias and the QSPI/SD routing.

```json
{ "crystal": true, "buttons": true, "powerPath": true, "thermal": 4, "grounding": 6, "layout": 6, "routing": 5, "silkscreen": 7 }
```

**Upgrade:** both files were already in the connector's format (board 20261031, schematic 20261106, generator 10.99), so `kicad-cli … upgrade` reported nothing to do. I re-saved both with `--force`. In the board, that only reordered and renumbered the auto-generated teardrop zones; the schematic lost one `embedded_fonts no` line. DRC on the result found 0 unconnected items and 0 schematic-parity errors; the only findings were library-path warnings. ERC also gave only library-path warnings.

| Key | Answer | Why |
|---|---|---|
| crystal | yes | It is the ABM8-272-T3 with 15 pF C0G load caps and a 1 kΩ series resistor on XOUT, exactly as the RP2350 hardware design guide specifies. That gives about 10.5 pF load against the crystal's 10 pF. The pin mapping is right and the crystal sits about 4.5 mm from XIN/XOUT. |
| buttons | yes | BOOT pulls QSPI_SS to GND through 1 kΩ (R17, next to the flash). RST pulls RUN to GND, with a 10 kΩ pull-up. Both buttons are on the top side at the right-hand corners, with nothing taller next to them. The headers mount on the bottom. |
| powerPath | yes | The BQ24074 runs in 500 mA USB mode (EN1 is set high by a divider from VBUS, EN2 is tied to GND). Its output is regulated to 4.4 V, so the board runs with no battery or a flat one. On unplug, the internal FET connects the battery to the output, giving about 4.2 V into the 3.3 V regulator (TLV75733). That keeps it well above dropout, so the 3.3 V rail stays up. TMR, ITERM and TS are wired as the datasheet allows. |
| thermal 4 | | The BQ24074 thermal pad has no vias; the nearest GND via is 2.55 mm away. The charger can dissipate about 0.9 W while charging a low battery, so it will hit its thermal limit and cut the charge current. The regulator's GND pin also has no via nearby, and it drops about 0.5 W at full load in a SOT-23-5 (about 100 to 230 °C/W), which is marginal. The RP2350 center pad has 5 vias. |
| grounding 6 | | In1 is one solid GND plane stitched with 85 vias, and no pour fragment is left unconnected. But the F.Cu GND pour is split into 21 pieces, B.Cu traces sit over a 3.3 V plane rather than ground, and the charger and regulator ground pads have no vias. |
| layout 6 | | Parts are grouped well: USB and battery on the left edge, connectors on the edges, buttons in the corners, and the radio antenna at the right edge with its keep-out clear of copper. The RP2350's regulator parts, flash and crystal are close to it. The PSRAM is the exception: it sits about 14 mm away in the charger area. |
| routing 5 | | The QSPI_SD1, QSPI_SD2 and PSRAM_CS lines run 19 to 21 mm on B.Cu and cross slots in the In2 3.3 V plane, where the RUN and PGOOD traces cut through it. SD_DAT0 and SD_DAT1 also cross In2 slots. RUN (about 60 mm) and the BOOT line (about 45 mm) run the length of the board. USB is routed at 0.22/0.15 mm over solid GND, and power trace widths are adequate (0.5 mm VBUS/VSYS, 0.3 mm battery). |
| silkscreen 7 | | The board has the battery "+" mark, LED cathode marks, IC pin-1 marks, BOOT/RST labels and a clean DRC. But the USB, battery, Qwiic, SWD and microSD connectors are labeled only on the bottom. The status LEDs are unlabeled, some header labels run together ("GNDRUN", "SYSGND"), and the radio module's pin-1 triangle sits right next to the BOOT button. |

The original files, the netlist, the DRC/ERC reports, the zoomed layer crops and the analysis scripts are in `scratch/`.
