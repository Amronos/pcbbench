# opus-5.5's review

## Final message

I've upgraded the schematics and board and written [review.json](review.json):

```json
{ "crystal": true, "buttons": true, "powerPath": true, "thermal": 5, "grounding": 3, "layout": 6, "routing": 3, "silkscreen": 7 }
```

**Upgrade:** all five `.kicad_sch` files and `board.kicad_pcb` were already in the connector's file format, so `kicad-cli … upgrade` refused to touch them. I re-ran it with `--force` to resave them with KiCad 10.99.0-6344. The only differences are formatting and default text effects. After the resave, DRC with zone refill finds 0 unconnected items and 0 schematic parity issues; the only warnings are 82 `lib_footprint_issues`. I deleted the `board.kicad_prl` file the resave created.

**Yes/no checks**

| Key | Answer | Why |
|---|---|---|
| `crystal` | yes | It uses the ABM8-272-T3 (10 pF, 50 Ω ESR), two 15 pF C0G capacitors and a 1 kΩ resistor on XOUT. That is exactly the circuit in the Raspberry Pi RP2350 hardware design guide. Y1 sits about 3 mm from XIN/XOUT. |
| `buttons` | yes | BOOTSEL pulls QSPI_SS to ground through 1 kΩ, and RUN goes straight to ground, as in the guide. Both PTS810 switches are top-actuated, on the top side, and nothing covers them. |
| `powerPath` | yes | The charger is a BQ24074 with EN1 high and EN2 low, so it runs in USB500 mode. Its output (VSYS) is held at 4.4 V from USB even with no battery or a flat one. Unplugging USB hands VSYS over to the battery, and the 3.3 V regulator (TLV75733) keeps enough headroom that 3.3 V doesn't drop. |

**Scores**

- **Grounding: 3**
  - The RP2350's exposed pad is the chip's only ground pin, but it has no vias. It connects through one 0.127 mm trace to a single via.
  - There are no ground vias between y = 55 and 69.5 mm. The radio module's six ground pads sit 6–10 mm from the nearest via.
  - The 354 mm² bottom-layer ground pour near the top of the board joins the rest of ground only through two header pins.
  - The inner ground layer (In1) is solid, which is good.
  - The saved board has no zone fills, so the pours must be refilled before exporting Gerbers.
- **Routing: 3**
  - The QSPI traces are 22–36 mm long for parts about 10 mm apart, with 3–6 vias each. Up to 12 mm of each runs on the bottom layer over gaps in the 3.3 V plane, which is cut into 4 pieces by traces on In2.
  - USB D+/D− run about 55 mm as uncoupled 0.127 mm traces with layer changes.
  - The switching node of the RP2350's core regulator goes through two vias on 0.127 mm trace.
  - Power traces are adequate: VBUS and VBAT are 0.4 mm, VSYS is at least 0.25 mm.
- **Thermal: 5**
  - The charger has 4 thermal vias and a pad on the bottom layer.
  - The RP2350's exposed pad has no heat-sinking vias.
  - The 3.3 V regulator drops 1.1 V in a SOT-23-5 package (θJA 231 °C/W). At 0.4–0.5 A it gets close to or past 125 °C.
- **Layout: 6**
  - The radio module sits at the top edge with its antenna area kept free of copper on all four layers.
  - The connectors are at the edges and the crystal and decoupling capacitors are close to the RP2350.
  - The flash and PSRAM are about 10 mm away, on a side that doesn't face the RP2350's QSPI pins.
  - The USB ESD chip sits off to the side of the path from connector to MCU.
- **Silkscreen: 7**
  - Pin-1 and LED polarity marks are present, BOOT/RST are labelled, nothing is on pads, and text is 0.8/0.15 mm, which meets PCBWay's minimum.
  - Battery + and − and the header pin names are only on the bottom side.
  - USB, Qwiic and microSD are not labelled.

**Outside the scored keys:**
- The headers J5 and J6 are marked do-not-populate and left out of the BOM. That conflicts with the brief's "assembly of every component".
- `sym-lib-table` points to `lib/board.kicad_sym`, but the file is `lib/rp2350_dev.kicad_sym`. This causes 178 ERC library warnings.
