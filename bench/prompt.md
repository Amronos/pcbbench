Design an RP2350 development board in KiCad that PCBWay can fully manufacture: PCB fabrication plus assembly of every component by PCBWay. The board must have:

- RP2350 with QSPI flash and PSRAM
- USB-C for power and data
- Single-cell LiPo charger with power-path from USB, and battery voltage monitoring
- Wi-Fi and Bluetooth LE
- microSD card slot
- Qwiic/STEMMA QT I²C connector
- Addressable RGB LED

Choose everything else yourself.

Work autonomously. Nobody is available to answer questions, so make reasonable decisions yourself and record them.

Put everything in this folder. Deliverables:

- The KiCad project: schematic and PCB.
- A `fab/` folder with everything PCBWay needs to manufacture and assemble the board.
- A `README.md` describing the board, your key design decisions, and anything a reviewer should know.

If you spawn subagents, every `spawn_subagent` call must set `model` to {{MODEL}} and `reasoning` to {{EFFORT}}. Put this same rule, word for word, in every subagent's prompt.
