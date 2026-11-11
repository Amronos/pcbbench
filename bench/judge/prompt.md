Review the RP2350 development board in this folder. It was designed to this brief:

> Design an RP2350 development board in KiCad that PCBWay can fully manufacture: PCB fabrication plus assembly of every component by PCBWay. The board must have: RP2350 with QSPI flash and PSRAM; USB-C for power and data; single-cell LiPo charger with power-path from USB, and battery voltage monitoring; Wi-Fi and Bluetooth LE; microSD card slot; Qwiic/STEMMA QT I²C connector; addressable RGB LED.

The folder has the KiCad project (`board.*` and its libraries), `bom.csv`, 3D renders in `renders/` and one image per layer in `layers/`, exported with the KiCad version the board was designed in.

## How to work

- Use the `working-with-kicad` skill and the KiCad connector.
- First upgrade every schematic and the board in place to the connector's KiCad version. Don't change the design otherwise. Use scratch copies to try things.
- Read datasheets on the web as needed. Read and write only in this folder, the connector and its libraries. Nobody will answer questions.

## What to answer

Write `review.json` here with exactly these keys:

```json
{ "crystal": true, "buttons": true, "powerPath": true, "thermal": 0, "grounding": 0, "layout": 0, "routing": 0, "silkscreen": 0 }
```

Yes or no:

- `crystal`: the crystal and its load capacitors suit the RP2350's oscillator.
- `buttons`: BOOTSEL and RUN work as in the RP2350 hardware design guide, and a user can press both on the assembled board.
- `powerPath`: the board runs from USB while the battery charges, and with no battery or a flat one. Unplugging USB with a charged battery switches to the battery without the 3.3 V rail dropping or the RP2350 resetting.

Scores, as integers from 0 to 10:

- 9–10: a professional would ship it as is.
- 6–8: minor issues a reviewer would ask to fix.
- 3–5: clear problems that hurt performance or reliability.
- 0–2: it would stop the board working or being built.

The scores:

- `thermal`: parts that dissipate power get the needed copper and vias, and stay within their ratings at full load.
- `grounding`: a continuous ground reference under signals, stitched pours, and no isolated copper.
- `layout`: parts placed by function, with critical parts close to the RP2350, connectors and buttons at the edges, and the antenna at an edge and clear.
- `routing`: short direct traces, a continuous reference plane under QSPI, USB and SD, and power traces sized for their current.
- `silkscreen`: polarity and pin-1 marks, labeled connectors and buttons, nothing on pads, and readable text.
