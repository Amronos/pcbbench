Review the RP2350 development board in this folder. It was designed to this brief:

> Design an RP2350 development board in KiCad that PCBWay can fully manufacture: PCB fabrication plus assembly of every component by PCBWay. The board must have: RP2350 with QSPI flash and PSRAM; USB-C for power and data; single-cell LiPo charger with power-path from USB, and battery voltage monitoring; Wi-Fi and Bluetooth LE; microSD card slot; Qwiic/STEMMA QT I²C connector; addressable RGB LED.

The folder has the KiCad project (`board.*` and its libraries), `bom.csv`, 3D renders in `renders/` and one image per layer in `layers/`.

## How to work

- Use the `designing-pcbs` skill and the KiCad connector.
- First upgrade every schematic and the board in place to the connector's KiCad version. Don't change the design otherwise. Use scratch copies to try things.
- Read datasheets on the web as needed. Read and write only in this folder, the connector and its libraries. Nobody will answer questions.
- If you spawn subagents, every `spawn_subagent` call must set `model` to {{MODEL}} and `reasoning` to high. Put this same rule, word for word, in every subagent's prompt.
- Skip the `/cleanup` skill, since you change no code.

## What to review

Automated checks already cover the crystal circuit, the BOOTSEL and RUN buttons, the charger's power path, decoupling distance, USB impedance, the antenna keepout, thermal vias, the ground plane under signals, silkscreen, board size, DRC, ERC, the BOM and part stock. Don't report on those unless they cause a fatal fault. Don't report on cost, or the choice of parts when the chosen part works.

Report findings in three areas:

- `layout`: where parts are placed. Flash and PSRAM next to the QSPI pins, the crystal next to XIN and XOUT, the charger and regulator grouped by the power input, connectors and buttons at an edge where a user can reach them, and the antenna at an edge with nothing in front of it.
- `routing`: how traces run. Short direct QSPI, SD, USB and crystal traces, few vias and no stubs on them, and power traces wide enough for their current. Take the charger output and battery path at 1.5 A.
- `other`: fatal faults outside layout and routing, such as a part fitted backwards or a pin on the wrong net.

Give each finding one severity:

- `minor`: a reviewer would ask to fix it, but the board works as is. For example, flash 12 mm from the QSPI pins, or one extra via on a QSPI line.
- `major`: it hurts performance or reliability. For example, a 0.2 mm trace carrying the 1.5 A charger output, QSPI lines that detour across the board, or the antenna facing into the board.
- `fatal`: the assembled board can't work, a part gets damaged, or PCBWay can't build it. For example, a TVS diode fitted backwards across 5 V, or a connector placed facing into the board.

Report each problem once, at its highest severity. Only report what you confirmed in the board files and, where a part's behavior matters, its datasheet. Leave out suspicions you couldn't confirm.

## What to answer

Write `review.json` here as a list of findings, or `[]` if you found none:

```json
[
	{
		"area": "routing",
		"severity": "major",
		"refs": ["U4"],
		"nets": ["/VSYS"],
		"issue": "The charger output to the regulator is a 0.2 mm trace, but it carries up to 1.5 A.",
		"evidence": "Track from U4 pad 10 to U5 pad 1 on F.Cu at (112.4, 68.0) is 0.2 mm wide."
	}
]
```

`area` is `layout`, `routing` or `other`. `other` findings must be `fatal`. `evidence` names the board coordinates, pads or datasheet section that show the problem.
