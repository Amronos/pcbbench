# RP2350 Connect — revision A

An 85 × 70 mm RP2350A development board designed for PCBWay turnkey PCB fabrication and assembly. All 118 electrical components are fitted, including the connectors and sockets. PCBWay procures every BOM item; there are no customer-supplied parts or DNP options. A protected LiPo battery, microSD card, USB cable, and debugger are external accessories.

Open `boards/rp2350-connect/rp2350-connect.kicad_pro`. Its schematic, board, and local symbol/footprint libraries form the canonical project. `.backplane.json` points to it. Manufacturing outputs are in `fab/`; scripts and intermediate verification files are in `scripts/` and `build/`.

## Hardware

| Function | Implementation |
|---|---|
| Processor | Raspberry Pi RP2350A, QFN-60; **A2 or newer silicon required** |
| Program flash | Winbond W25Q128JVSIQ, 16 MB QSPI |
| Working memory | AP Memory APS6404L-3SQR-SN, 8 MB PSRAM; shared QSPI bus, independent CS on GPIO0 |
| USB | USB-C, USB 2.0 full-speed power/data; two 5.1 kΩ CC resistors, ESD protection, TVS, resettable fuse |
| Battery charging | TI BQ24074, USB/battery power path, nominal 499 mA charge current, pack thermistor input |
| Main rail | TPS63060 buck-boost, regulated 3.3 V from the charger system output |
| Core rail | TPS62823 external 1.101 V buck supply |
| Wireless | ESP32-C3-WROOM-02-N4, 2.4 GHz Wi-Fi and Bluetooth LE, RP2350 UART with RTS/CTS |
| Storage | Hirose microSD slot, SPI1, switched 3.3 V supply |
| I²C | JST SH Qwiic/STEMMA QT connector; 3.3 V, 4.7 kΩ pullups |
| RGB | SK6812MINI; separate 5 V boost and AHCT level buffer |
| Debug/expansion | Installed SWD header, separate ESP UART0 socket, two 12-pin GPIO sockets, reset and boot buttons |
| PCB | Six copper layers, 1.6 mm FR-4, ENIG; all components on top |

## Design decisions and operating requirements

The ESP module provides both required radios without RP2350 RF circuitry. Its PCB antenna overhangs the north edge; keep the antenna area clear of copper, batteries, metal, and enclosure hardware. The final stack is F.Cu signal/GND pour, In1.Cu GND, In2.Cu signal, In3.Cu signal, In4.Cu 3V3, B.Cu signal/GND pour. The extra signal layers make room for the fine-pitch MCU escapes. Minimum copper spacing is 0.10 mm, minimum track width 0.127 mm, and routing vias are 0.45/0.20 mm. Filled and copper-capped vias are required, including vias under solder pads.

The RP2350 uses an external core regulator per the external-supply circuit in the RP2350 datasheet. VREG_FB is grounded and LX is intentionally unconnected. Firmware must set VREG.HIZ and must not attempt to change core voltage through the internal regulator. This also avoids the special polarity requirement of the RP2350 internal-regulator inductor. The core rail is fixed near 1.10 V; qualify any overclocking separately.

The battery connector is **JST PH, three pins: 1 = battery positive, 2 = ground, 3 = 10 kΩ NTC thermistor**. This is not the usual two-pin hobby battery connector. Use a protected single-cell 4.2 V lithium-ion/LiPo pack, at least 1000 mAh and rated for at least 500 mA charging, with an appropriate 10 kΩ NTC. The charger does not replace pack overcurrent/undervoltage protection. Do not connect two cells, LiFePO4, or a pack without its required thermistor. Verify mating-cable polarity before use. Battery voltage is `2 × ADC(GPIO26)`, using the measured ADC reference; the divider draws approximately 21 µA at 4.2 V.

At reset the charger input limit is 100 mA, ESP is held in reset, and microSD power is off. Firmware must enumerate USB and obtain its power budget before enabling the radio/card and increasing the input limit. BQ24074 EN1/EN2: `0/0 = 100 mA`, `1/0 = 500 mA`, `0/1 = resistor-programmed limit`, `1/1 = input suspend`. The resistor limit is approximately 500 mA; it is not USB-C current-advertisement detection. CE is active low: GPIO19 high disables charging. Dynamic power management gives the board load priority over charging. Respect USB suspend and unconfigured-device current limits. Standalone USB charger operation requires a firmware power policy; no USB-PD negotiation is provided. Keep RGB brightness low until the available power is known. External 3V3 loads share this budget; no maximum expansion current is guaranteed without thermal/load qualification.

Initialize SD bus outputs low or as inputs before GPIO1 enables its supply. Avoid driving unpowered card inputs high. Start at standard SD initialization speed, then qualify operation up to 24 MHz. Start QSPI PSRAM conservatively and validate timing before increasing its clock. The PSRAM CS uses GPIO0, which requires board-specific memory initialization rather than a generic Pico board configuration.

## GPIO assignment

| GPIO | Use |
|---|---|
| 0 | PSRAM CS1 |
| 1 | SD power enable; also J6 pin 3 |
| 2 / 3 | I²C SDA / SCL |
| 4 / 5 | RP UART TX / RX to ESP GPIO6 RX / GPIO7 TX |
| 6 / 7 | RP CTS / RTS to ESP GPIO4 RTS / GPIO5 CTS |
| 8 / 9 / 10 / 11 | SD MISO / CS / clock / MOSI |
| 12–15 | Expansion GPIO |
| 16 / 17 | ESP enable / boot strap |
| 18 / 20 | Charger EN1 / EN2 |
| 19 | Charger disable (CE high) |
| 21 / 22 | Charger status / USB power-good, active low |
| 23 | RGB data, GRB at 800 kHz |
| 24 | microSD detect, active low |
| 25 | Expansion GPIO |
| 26 | Battery ADC; also exposed at J7 pin 6 |
| 27–29 | Analog-capable expansion GPIO |

Qwiic J5 pins: GND, 3V3, SDA, SCL. Expansion and debug pin-by-pin definitions are in `fab/connector-pinout.csv` and the schematic. Exposed status/control nets already have board functions: take care when driving them from external hardware. GPIOs are 3.3 V logic.

## Programming and manufacture

The RP2350 ROM supports USB recovery: hold BOOT, press/release RESET, then release BOOT and load a board-specific UF2. SWD is available at J8. ESP UART0 is independently available at J3 for loading the official **ESP32-C3-WROOM-02 ESP-AT** firmware. Its command UART is GPIO6/7/5/4, not the UART0 programming pins. Use a 3.3 V UART adapter, share ground, and power the board through USB/battery rather than connecting an adapter supply. Drive ESP EN high and hold ESP BOOT low during reset to enter download mode; release BOOT afterward. For an empty RP2350, EN can be driven from the programming fixture because the MCU pin is initially high impedance. Match flashing offsets to the exact official firmware archive. Application firmware and radio firmware binaries are not included; this is a hardware design, and PCBWay should leave flash blank unless a subsequently approved binary is supplied.

`fab/PCBWAY-INSTRUCTIONS.md` specifies procurement, stackup, via treatment, assembly, orientation, and first-article checks. `fab/TEST-PLAN.md` describes hardware acceptance and the additional firmware-assisted tests needed to qualify the first article. Gerbers, separate plated/non-plated drill files, BOM, placement CSV, assembly drawings, schematic PDF, electrical netlist, and verification reports are included. The position file includes both SMT and through-hole components. PCBWay must check rotations against the assembly drawing and local footprints rather than assuming a distributor's rotation convention.

## Review status

Verification results are recorded in `fab/verification/` and `fab/RELEASE-STATUS.md`. This revision has not been physically built or measured. Firmware timing, RF performance, USB signal integrity, charger thermistor thresholds, thermal behavior, and battery operation require first-article validation. The schematic nets were independently compared to the frozen component specification. Hardware checks do not establish functional firmware correctness.

KiCad was authored with Backplane KiCad 10.99.0-bp.4. A compatibility export, when provided in `fab/source-kicad10/`, is accompanied by its conversion report; use the canonical source for edits. Backplane returned the canonical viewer path but did not confirm viewer refresh/history, so exported drawings serve as the static review evidence.

Manufacturer references: [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf), [BQ24074](https://www.ti.com/lit/ds/symlink/bq24074.pdf), [TPS63060](https://www.ti.com/lit/ds/symlink/tps63060.pdf), [TPS62823](https://www.ti.com/lit/ds/symlink/tps62823.pdf), [ESP32-C3-WROOM-02](https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf), and [official ESP-AT hardware pinout](https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/Get_Started/Hardware_connection.html).
