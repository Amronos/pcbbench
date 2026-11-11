# Sprocket 2350

An 80 × 65 mm RP2350A development board with USB-C, battery power, Wi-Fi/Bluetooth LE, removable storage, and sensor expansion. PCBWay is to source and assemble all 92 fitted components, including the radio module and through-hole headers. No fitted component requires customer purchasing or soldering.

Revision A is a fully routed, physically untested first-article candidate, not approved for manufacture. Core-power and USB ESD PCB repairs and metadata/netlist synchronization are complete. Final root ERC and DRC report zero findings, zero opens and zero schematic-parity findings. The live BOM validates all 92 fitted components; the assembly audit reports zero blocking and advisory findings. USB controlled impedance and supplier process confirmation remain unresolved. The board has not been manufactured, powered, or measured.

## Hardware

| Function | Implementation |
|---|---|
| Processor | Raspberry Pi RP2350A, production A4 stepping preferred |
| Program storage | Winbond W25Q128JVSIQ, 16 MB QSPI flash |
| External RAM | AP Memory APS6404L-3SQR-SN, 8 MB QSPI PSRAM, separate CS on GPIO0 |
| USB | GCT USB4105-GF-A USB-C receptacle, USB 2.0 full-speed device, two CC resistors and USB ESD protection |
| Battery charging | TI BQ24074, power-path and battery supplementation, approximately 100 mA charging |
| Battery monitoring | Analog Devices / Maxim MAX17048, TDFN-8, battery voltage and estimated state of charge over I²C |
| System supply | TI TPS63001, fixed 3.3 V buck-boost |
| Wireless | Espressif ESP32-C3-WROOM-02-N4, 2.4 GHz Wi-Fi and Bluetooth LE |
| Storage | Hirose DM3AT-SF-PEJM5 microSD socket, SPI interface and card detection |
| Sensors | JST-SH 4-pin Qwiic/STEMMA QT connector, 3.3 V I²C |
| RGB | Worldsemi WS2812B-V6, 5050 package, direct 3.3 V supply and data |
| Debug/expansion | SWD header, separate radio programming header, 20-pin GPIO header, BOOT/RESET/radio BOOT buttons and test pads |

## Files and manufacturing

- `sprocket2350.kicad_pro`, `.kicad_sch`, `.kicad_pcb`: editable KiCad project.
- `sprocket2350.net`: exported electrical netlist for review.
- `fab/`: manufacturing instructions and candidate exports. Include both-side paste and assembly references, schematic PDF, top/isometric renders, a bottom render when components are fitted there, treatment map/coordinates, fresh checks, the USB diagnostic audit and matching editable sources. Candidate generation does not approve an order.
- `tools/`: design metadata, synchronization, layout and export helpers. `sync_design.py` validates schematic values, footprints and manufacturer/MPN metadata against `design.py`, exports the netlist, then imports it with `update_footprints=False` and saves the PCB. It does not replace footprints or reposition the routed board.

The project uses the KiCad 10.99 development file format and may not open in KiCad 9 or 10.0. Standard KiCad libraries and project-local `lib/` definitions supply symbols and footprints. The schematic embeds its symbol definitions and the PCB embeds its footprints. Include the matching `.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `lib/`, `sym-lib-table`, `fp-lib-table`, and any project-local design rules in the final package so the design remains editable.

The release snapshot includes local symbol/footprint libraries and 3D provenance documents, but excludes optional 3D model binaries. J2 model redistribution rights are unconfirmed. Missing visualization models do not prevent schematic or PCB editing.

After release approval, order turnkey PCB fabrication and assembly, not a bare board or consigned-parts service. Include through-hole/secondary assembly for J3, J6 and J7. Read [the fabrication specification](fab/FABRICATION.md) and [assembly instructions](fab/ASSEMBLY.md). PCBWay must quote the exact BOM and confirm availability before accepting the order. The user must not need to purchase or solder fitted board components. No parts have been purchased or reserved.

## Decisions and limits

### Power and battery

The selected fabrication exception permits a 0.100 mm `connection_width` minimum only on ordinary `/+3V3` copper zones. The tested plane neck remains 0.102 mm; it was not widened. Routed traces, clearances and the default board connection minimum stay at 0.127 mm. Retain 0.25 mm zone `min_thickness`: the rejected 0.35 mm setting disconnected the pin-20 supply island. Include the targeted `.kicad_dru` in the final project and obtain supplier confirmation before ordering. See [the plane-neck decision](fab/FABRICATION.md#3v3-plane-neck).

USB powers the BQ24074 input. Its OUT rail powers the buck-boost regulator. The battery connects to BAT, not to the regulator input directly. This keeps the system load out of the charge termination measurement and allows a battery to cover radio bursts.

The repaired layout keeps AVDD power routing away from LX crossings, connects bottom-side C6 directly through a local two-via loop, gives bottom-side C20 a local core via, and uses wider In2.Cu CORE distribution. C6 is now 22 µF Murata `GRM188R61A226ME15D` in 0603. Its typical-data qualification and engineering reserves are recorded in [the assembly instructions](fab/ASSEMBLY.md#c6-capacitance-qualification); they are not a manufacturer guarantee or bench validation.

Use an external protected, single-cell, 4.2 V-charge LiPo pack, nominally 400 mAh, rated for at least 114 mA charging and 1.5 A discharge pulses. Confirm these ratings with the pack supplier. J2 pin 1 is GND and pin 2 is BAT. JST-PH cable polarity is not universal, so check it before connecting a pack. There is no reverse-battery protection.

R11 is 8.66 kΩ, setting 102.8 mA nominal charge current, about 91–114 mA including charger and 1% resistor tolerance. R14 is 68.1 kΩ, setting a 9.08-hour nominal fast-charge safety timer, 6.74–11.46 hours including tolerance. Input limiting or thermal regulation can reduce charge current and extend the dynamic timer, so the timer does not predict charge completion time. The TS input uses a fixed 10 kΩ resistor, R13, and the pack has no thermistor connection. The board does not measure cell temperature. Charge only in a supervised 10–40 °C environment with a suitable protected pack. It is not an unattended battery product or a safety-certified charger.

The charger starts in USB100 mode. GPIO10 selects USB500. GPIO11 controls active-high charge disable and defaults high. Radio EN defaults low. Firmware must configure USB before enabling charging/radio on USB power. This avoids an always-on radio drawing a large current before enumeration.

USB500 limits input to 450–500 mA. A healthy battery is required for worst-case simultaneous radio, microSD and processor loads. Battery supplementation can discharge a battery even while USB is attached. The TPS63001's 800 mA boost-mode headline rating does not cover every transient at every temperature. Validate the combined load at low battery voltage. External accessories share this budget. Start with a 50 mA Qwiic/header allowance.

No physical power switch is fitted. Disconnect the battery for storage. USB suspend-current compliance depends on firmware and must be measured.

U8, MAX17048G+T10, measures battery voltage and estimates state of charge. It sits on I²C0, GPIO20 SDA and GPIO21 SCL, with 3.3 kΩ pull-ups R20/R21 to 3V3 and 7-bit address `0x36`. These pull-ups target a 300 ns rise time with approximately 106 pF maximum bus capacitance. Include header wiring and external devices in that budget. Read VCELL and SOC using the datasheet's register format. The gauge is powered from BAT. Without a connected battery, its readings do not describe a cell even if the charger energises BAT. SOC is an estimate, not a cell protection mechanism. Validate it with the chosen pack. Temperature compensation needs firmware and an external temperature measurement that this board does not provide.

### Radio and firmware

The radio is a certified module rather than a custom antenna/transceiver design. Its antenna overhangs the north edge. Keep metal, batteries and cables at least 15 mm away from the antenna in the final enclosure. Module certification does not certify the finished product.

The command UART uses Espressif's ESP-AT GPIO assignments. The radio's UART0 is separate and exposed on J3 for programming. Do not assume the purchased module contains useful AT firmware. This delivery is hardware only, with no application firmware. To use wireless features, flash an ESP32-C3 ESP-AT build that includes the desired Wi-Fi/BLE commands, or your own ESP-IDF companion firmware. Provide production binaries separately if asking PCBWay to program/test functional firmware.

| RP2350 GPIO | Function | Other end |
|---:|---|---|
| 0 | Native QMI CS1n | PSRAM CE |
| 2, 3 | I²C1 SDA, SCL | Qwiic J5 |
| 4, 5, 6, 7 | SPI0 RX, CS, SCK, TX | microSD J4 |
| 8 | Card detect, active low | J4 switch |
| 9 | RGB data | D1 via 330 Ω |
| 10 | USB500 select | Charger EN1 |
| 11 | Charge disable, high disables | Charger CE |
| 12 | UART0 TX | ESP GPIO6, command RX |
| 13 | UART0 RX | ESP GPIO7, command TX |
| 14 | UART0 CTS | ESP GPIO4, command RTS |
| 15 | UART0 RTS | ESP GPIO5, command CTS |
| 16 | Radio enable/reset | ESP EN via 1 kΩ |
| 20, 21 | I²C0 SDA, SCL, gauge address `0x36` | MAX17048 U8 and J6 pins 9/10 |
| 26 | ADC0 / GPIO26 | J6 pin 5 |
| 1, 17–19, 22–25, 27–29 | General-purpose/ADC expansion | J6 |

Start with UART at 115200 baud, 8-N-1, and configure RTS/CTS consistently on both processors. Release radio BOOT before normal startup. For radio download, hold SW3, drive EN low, then release EN while keeping BOOT low for at least 3 ms. J3 pin 2 is radio TX, pin 3 is radio RX, pin 4 is EN, and pin 1 is GND. A programmer must use 3.3 V logic and must not inject a power supply into the board.

PSRAM is not automatically ordinary C/C++ heap memory. Initialise the device after its power-up interval and configure QMI CS1 command/timing/refresh settings. Start QSPI at no more than 50 MHz for bring-up. The PSRAM's unrestricted linear-burst limit is 84 MHz, and its wrapped-burst limits differ. GPIO0 is reserved for PSRAM.

R2 is 1.8 kΩ, `RC0603FR-071K8L`, so PSRAM CS stays high against GPIO0's reset pull-down. The PSRAM data-low power-up initialisation recommendation is not established by this hardware. Validate the deviation and the firmware's initial pin sequence with cold-start and repeated power-cycle tests before production.

D1 must be a WS2812B-V6. Older WS2812B versions are not guaranteed for this 3.3 V supply. Send GRB data with a reset-low interval of at least 300 µs. Start at low brightness to preserve the power budget.

### Connectors

All expansion pins are 3.3 V only. Do not connect 5 V logic or feed the 3.3 V pins from another supply. A powered peripheral can back-power an unpowered board through I/O. Power external peripherals from this board, and disconnect external programmers before removing board power.

J5 is standard Qwiic/STEMMA QT: 1 GND, 2 3V3, 3 SDA, 4 SCL. Its I²C1 pull-ups are 5.1 kΩ. Use short cables and 100 kHz initially, and account for parallel pull-ups on sensor boards.

J7 SWD: 1 3V3 reference, 2 SWDIO, 3 GND, 4 SWCLK. J6 uses the usual odd/even two-row numbering:

| Odd pin | Signal | Even pin | Signal |
|---:|---|---:|---|
| 1 | 3V3 | 2 | GND |
| 3 | GPIO1 | 4 | Radio BOOT, active low |
| 5 | ADC0 / GPIO26 | 6 | GPIO17 |
| 7 | GPIO18 | 8 | GPIO19 |
| 9 | Gauge SDA / GPIO20 | 10 | Gauge SCL / GPIO21 |
| 11 | GPIO22 | 12 | GPIO23 |
| 13 | GPIO24 | 14 | GPIO25 |
| 15 | ADC1 / GPIO27 | 16 | ADC2 / GPIO28 |
| 17 | ADC3 / GPIO29 | 18 | RUN, active low |
| 19 | 3V3 | 20 | GND |

J6 pins 9/10 share the gauge's I²C0 bus. Keep external devices there at 3.3 V and avoid address `0x36`. The charger's CHG status output is on TP6.

## BOM and placement exports

Generate review files with the connector's Python, which includes `kipy`:

```bash
kicad-python tools/export_package.py
```

The helper writes `fab/unreleased/BOM.csv` and `fab/unreleased/placement.csv`, or another directory given with `--output`. It reads the root PCB or an explicit `--board` snapshot and checks references, values, footprints, manufacturers and exact MPNs against that snapshot's sibling `tools/design.py`. It exports saved positions, sides and angles without saving CAD or approving release.

The BOM groups identical fitted parts and gives quantities per board. It includes all 92 SMT and through-hole components, including J3/J6/J7. TP1–TP8, H1–H3 and FID1–FID3 are fabricated PCB features, excluded from procurement and placement. The external pack and test accessories are also excluded. PCBWay must source and assemble every BOM item; substitutions need approval.

Matching PCB metadata does not prove part availability. PCBWay must confirm supply and quote the exact BOM, including `MAX17048G+T10` for U8.

Placement coordinates are in mm from KiCad's absolute origin, X right and Y down, with native KiCad footprint rotation in degrees. Bottom-side coordinates are not mirrored. They are footprint anchors, which may differ from body centroids. Header anchors may be pad 1. PCBWay must confirm origin, rotation and centroid conversion against the final assembly drawings before use.

The placement file's `Side` field controls assembly on both sides. C6 and C20 are fitted on the bottom. Use matching F/B paste and assembly PDFs/PNGs rather than assuming all SMT parts are on top. Bottom drawings are mirrored bottom views; placement coordinates are not mirrored.

The default CSVs are unreleased review files, not a fabrication package. A CSV status label does not run ERC/DRC or approve release. Follow [the release checklist](fab/FABRICATION.md#release-checklist) for the complete package and first-article approval.

## Verification and release

The fully routed root PCB has completed core-power and ESD layout repairs and metadata/netlist synchronization. Final root ERC reports zero findings; DRC reports zero violations, opens and schematic-parity findings. The live BOM validates all 92 fitted components. The copper check reported "NO WEIRD THINGS", and the final assembly audit reports zero blocking and advisory findings. These checks do not establish physical performance.

Before ordering a first article, review the completed layout and ESD design and obtain supplier confirmation of the stackup, USB impedance, drilling and filled/capped-hole process described in the fabrication specification.

Run ERC and zone-refilled DRC with schematic parity on the final matching sources. Include fresh reports with the exports. Old reports, exclusions, zero reported findings, and package status labels are not release approval. ERC/DRC check only the modeled rules and connectivity, not circuit correctness, ESD effectiveness, USB impedance or compliance, radio performance, charge safety, EMC, thermal margin, or load-transient stability.

The first-article plan must also cover PSRAM power-up initialisation and gauge leakage/back-powering with BAT present and 3V3 off, and with USB/3V3 present and the pack disconnected. These behaviors are unvalidated. Manufacture and test only an approved first article, following the assembly instructions. Production requires a separate review of measured results and the intended operating limits.

Use `tools/release.py` as described in [the release checklist](fab/FABRICATION.md#release-checklist). No custom approval inputs are required. The helper gates quote-ready package generation on fresh ERC/DRC with schematic parity and exports the checked staged snapshot without changing root CAD. Render appearance is under investigation; model references are visualization aids, not certification. Candidate export and its diagnostic audit do not approve an order or qualify production.

## Design sources

- [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf) and [hardware design guide](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf).
- [BQ24074](https://www.ti.com/lit/ds/symlink/bq24074.pdf), [TPS63001](https://www.ti.com/lit/ds/symlink/tps63001.pdf).
- [MAX17048/MAX17049 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/MAX17048-MAX17049.pdf).
- [Winbond W25Q128JV](https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf), [AP Memory APS6404L-3SQR](https://www.apmemory.com/cn/downloadFiles/032411212009597427).
- [ESP32-C3-WROOM-02 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf), [ESP-AT UART wiring](https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/Get_Started/Hardware_connection.html).
- [Worldsemi WS2812B-V6 V1.4](https://www.tme.eu/Document/88f56341f2c21fd586036db245cb26cf/WS2812B-V6_V1.4_EN.pdf).
- [PCBWay PCB capabilities](https://www.pcbway.com/capabilities.html) and [turnkey assembly service](https://www.pcbway.com/pcb-assembly.html).
