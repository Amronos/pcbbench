# Aster2350 — RP2350 development board

Revision A · designed November 9, 2026 · 80 × 65 mm · four layers

A USB-C and single-cell LiPo development board with RP2350A, 16 MiB QSPI flash, 8 MiB QSPI PSRAM, 2.4 GHz Wi-Fi/Bluetooth LE, microSD, Qwiic/STEMMA QT, an addressable RGB LED, SWD and populated GPIO headers. **PCBWay assembles every purchased component**, including the battery connector and both GPIO headers. No component is designated DNP or left for user soldering.

## Files

- `Aster2350.kicad_pro`, `Aster2350.kicad_sch`, `Aster2350.kicad_pcb`: the project and routed board. The schematic has three child sheets: `processor.kicad_sch`, `power.kicad_sch`, `interfaces.kicad_sch`.
- `libraries/`, `sym-lib-table`, `fp-lib-table`: project-local symbols and footprints. No external symbol/footprint libraries or proprietary CAD plug-ins are required. 3D models are not required or bundled.
- `fab/`: Gerbers, plated/nonplated drill files, stencil layers, BOM, placements, assembly/fabrication drawings, schematic PDF, electrical-test netlist and CAD verification reports. `fab/ASSEMBLY.md` is the PCBWay order specification. The manufacturing ZIP is the same manufacturing packet, not a different design variant.
- `design-data.json`: component/pin assignments, MPNs, physical placement and decisions in machine-readable form.
- `references/`: source documents used for the design, with a source index. These are reference material, not fabrication instructions.
- `tools/`: design-generation, routing-session import and release/check tools. **Do not rerun the design generator on the delivered routed board unless you intend to regenerate and reroute it.** Normal edits are made in KiCad.

Open the project, not an isolated sheet, so hierarchical/global-label cross references resolve. The design is generated and checked with KiCad 10.99.0-6353-g0ef63a79e8. The delivered primary board is exported in **KiCad 10.0-compatible format without forced feature dropping**, then rechecked for DRC and schematic parity; `fab/Aster2350-KiCad10.kicad_pcb` is an identical compatibility copy. Project-local libraries carry the actual pad geometries used. Do not assume compatibility with KiCad 9 or earlier.

## Release status — read before ordering

Final CAD checks: **0 ERC violations, 0 DRC violations, 0 unconnected items, 0 schematic parity issues**, plus an independent XML-netlist-to-PCB-pad comparison. There are **121 fitted purchased parts across 51 BOM lines: 118 top SMT parts and 3 factory-soldered THT parts**. The USB-C connector also has four plated shell slots that PCBWay must solder. `fab/validation.json` and `fab/VALIDATION.md` record the checks and their limitations.

Send `fab/Aster2350-RevA-PCBWay.zip` for a **turnkey fabrication + full assembly quote**. It contains manufacturing outputs and a self-contained `source/` project. `fab/SHA256SUMS` checks the packet files and archive. See `fab/ASSEMBLY.md` for the exact stack, procurement policy, first-article hold and programming requirements.

This is an **unbuilt engineering prototype**, not a physically validated or certified product. CAD electrical, connectivity and clearance checks are supplied; they cannot verify analogue stability, QSPI margins, USB impedance/compliance, radio range, charging temperatures or firmware behavior. Obtain PCBWay DFM/procurement confirmation, order a small first-article lot, and complete the tests in `fab/ASSEMBLY.md` before a volume order. Component inventory/lead times have not been reserved, and no factory purchase/order has been submitted.

The PCB/assembly package is intended for turnkey manufacture. External accessories (battery, cable, card, debug probe and Qwiic peripherals) and production firmware binaries are not included. The board can boot through the RP2350 USB ROM loader with blank flash. Wi-Fi and BLE require ESP32-C3 firmware and a host driver configured for this board's pins; **do not assume the module's factory image is compatible**.

## Hardware and key decisions

| Function | Selection / rationale |
|---|---|
| Main MCU | RP2350A, QFN60, 30 GPIO, nominal 150 MHz; no overclocking assumption |
| Flash | Winbond W25Q128JVSIQ, 128 Mbit = 16 MiB, 3 V SOIC8/208 mil |
| PSRAM | AP Memory APS6404L-3SQR-SN, 64 Mbit = 8 MiB, 3.3 V SOP8/150 mil |
| Memory bus | Shared QSPI D0–D3/clock; independent flash CS and GPIO0/QMI CS1n for PSRAM; 4.7 kΩ CS pull-ups prevent PSRAM contention during reset |
| Clock | Abracon ABM8-272-T3, 12 MHz, 10 pF load; 15 pF load caps and 1 kΩ XOUT damping resistor from the Raspberry Pi reference approach |
| Core supply | External TLV75801PDRVR adjustable LDO, fixed 1.10 V via equal 10 kΩ divider resistors; avoids the RP2350 internal switcher's placement/polarized-inductor dependency |
| Main supply | TPS63060 buck-boost, nominal 3.31 V, 1.5 µH shielded XFL4020; supports a LiPo below or above 3.3 V and the charger's 4.4 V system output |
| USB | GCT USB4105-GF-A, USB 2.0 full-speed device, both orientations; separate 5.1 kΩ CC terminations, ESD array, 27 Ω PHY resistors and 500 mA resettable fuse |
| Charging | BQ24074, 4.2 V 1S charging, USB/battery power path, system-load priority/DPPM, hardware current/timer/NTC protection |
| Battery monitoring | 100 kΩ/100 kΩ divider, RC filter, TLV9001 voltage follower, 1 kΩ ADC isolation and 100 nF reservoir; buffered specifically to avoid large divider error from RP2350 GPIO leakage |
| Wireless | ESP32-C3-WROOM-02-N4, 4 MiB internal module flash, PCB antenna; Wi-Fi 2.4 GHz b/g/n + Bluetooth LE, **not Bluetooth Classic** |
| Radio power | TPS22919 load switch, reset RC, strap pull-ups and ESP BOOT button; radio off by default to respect USB startup power |
| Storage | Molex 104031-0811 microSD socket, SPI mode, clock damping, pull-ups on all required data/CS pins, mechanical card detect |
| I2C | JST SH 1 mm four-pin Qwiic/STEMMA QT, 3.3 V, I2C0, 2.2 kΩ pull-ups |
| RGB | WS2812B-2020, dedicated switched ~5.06 V boost and SN74AHCT1G125 TTL-input 5 V buffer; no reliance on a 3.3 V-powered LED outside its supply specification |
| Development | Populated 2.54 mm 1×8 headers, 3-pin JST SH SWD, reset/boot buttons and factory test pads |

The core-supply connection follows RP2350 datasheet §6.3.7, Figure 24: **VREG_VIN and VREG_AVDD still receive 3.3 V, VREG_FB is grounded, VREG_PGND is ground and VREG_LX is intentionally open.** Firmware must set the internal regulator's `VREG.HIZ` field after boot. Its voltage-changing APIs do not change the external core supply. Fixed 1.1 V is a deliberate choice; firmware must not assume an increased core voltage when selecting an overclock.

The UART coprocessor architecture is chosen instead of a CYW43439 SDIO/SPI radio: the Espressif module packages its own crystal, flash and RF matching/antenna, and is a straightforward turnkey part. This costs a host/coprocessor firmware boundary but avoids discrete RF assembly and licensing/dependency assumptions. BLE runs on the ESP32-C3 and is exposed to the RP2350 through the selected radio firmware/protocol, not through an RP2350-native BLE controller.

## Power and battery rules

- **J2 is a three-pin JST PH battery port:** pin 1 BAT+, pin 2 pack NTC, pin 3 GND. Use a protected 1S Li-ion/LiPo pack with 4.20 V charge voltage, ≥500 mAh capacity, ≥300 mA permitted charge current, ≥1 A discharge capability, and a 10 kΩ at 25°C / approximately 3435 K NTC connected between pins 2 and 3. Confirm the actual pack's pinout and NTC temperature thresholds before use. A conventional two-wire JST-PH LiPo plug is **not** the connector for this board.
- The cell/protection board/cable are external accessories. The charger is **not cell over-discharge, short-circuit, reverse-polarity or cell-balancing protection**. The pack must provide the first two; correct polarity is mandatory. Do not use LiFePO4, 4.35 V cells, multicell packs, bare unprotected cells or batteries without a suitable NTC. NTC open/short inhibits charging; there is no fixed resistor pretending to sense the cell temperature.
- Maximum fast-charge setting is nominally `890 / 3570 = 249 mA`; tolerance increases the possible maximum, hence the ≥300 mA permitted-charge requirement. In USB500 mode the programmed termination is `0.03 × 3300 / 3570 ≈ 27.7 mA`, and in USB100 mode it is approximately 9.2 mA. R18 gives a nominal 6.65-hour fast-charge timer (temperature/DPPM may extend elapsed time). Check actual thresholds against the pack specification.
- USB starts in **100 mA input-limit mode**. GPIO23 may select 500 mA only after USB configuration with an appropriate descriptor, or after explicit source qualification. CC resistors alone do not grant 500 mA, 1.5 A or 3 A. There is no PD controller, higher-voltage negotiation, OTG host mode, or automatic Type-C advertised-current detector. Firmware must handle suspend/reset/disconnect and return the board to a compliant low-power/input-limit state.
- VSYS is about 4.4 V with USB present and follows the protected battery when USB is absent. The BQ24074 supplies system loads first and reduces charging current as required; a battery can supplement USB load peaks. It does not put the system load across the cell in a way that prevents charge termination.
- Radio and RGB enable inputs are pulled low by default. A USB-only board in ROM/startup mode has neither enabled. For USB-only use, keep combined 3.3 V system load conservatively ≤500 mA and RGB brightness low; battery-supported loads can be higher subject to thermal/transient first-article measurements. Do not budget 500 mA charging **plus** 500 mA system input. Simultaneous radio TX, high-current card writes, external peripherals and full-white RGB should use a suitable connected battery and be characterized.
- External 3.3 V header + Qwiic load budget is **100 mA combined**, not per connector, and depends on available input power. Do not feed external power into the 3.3 V, VSYS or core rail. USB is the supported external supply input. LiPo is the supported battery input.
- Battery ADC nominal conversion: `VBAT = 2 × ADC_count / 4095 × measured_ADC_reference`. Use ADC3 on GPIO29, disable digital pulls/input as required, allow the RC network to settle, and calibrate gain/offset/reference against a DMM. The divider continuously draws ~21 µA at 4.2 V. The buffer is powered whenever the board is powered. No mechanical power switch is fitted; disconnect the pack for storage.

The charger is a linear charger: when the cell is low, charging can dissipate several hundred mW. Copper/thermal paths are supplied, but thermal derating and real cell temperature behavior must be measured. The RF module's certificates do not certify this complete board, charging system or end product.

## RP2350 pin map

| GPIO | Function |
|---|---|
| 0 | PSRAM CS, QMI CS1n; not a free GPIO |
| 1, 2, 3, 8, 9, 15 | GPIO A header |
| 4 | UART1 TX → ESP32-C3 IO20/RXD (`RADIO_RX`) |
| 5 | UART1 RX ← ESP32-C3 IO21/TXD (`RADIO_TX`) |
| 6 | UART1 CTS ← ESP IO5/RTS (`RADIO_RTS`) |
| 7 | UART1 RTS → ESP IO4/CTS (`RADIO_CTS`) |
| 10 / 11 / 12 / 13 | SPI1 SCK / MOSI / MISO / microSD CS |
| 14 | microSD detect, active low |
| 16 | RGB data, 800 kbit/s GRB |
| 17 | RGB boost enable, high = on |
| 18 / 19 | GPIO B header |
| 20 / 21 | I2C0 SDA / SCL, Qwiic/STEMMA QT |
| 22 | Radio load-switch enable, high = powered |
| 23 | BQ24074 EN1: low = USB100, high = USB500; EN2 hard low |
| 24 | VBUS detect; 5.1 kΩ/6.8 kΩ divider, ~2.86 V at 5 V VBUS |
| 25 | Charger status, active low, open-drain with 3.3 kΩ pull-up |
| 26 / 27 / 28 | GPIO B header, ADC0 / ADC1 / ADC2 |
| 29 | Buffered battery measurement, ADC3 |

Dedicated QSPI pins are D0/D1/D2/D3/clock/flash CS. PSRAM must be configured explicitly by firmware; merely fitting it does not automatically add it to the normal SRAM heap. Begin memory/card testing at conservative clock rates and qualify faster modes on real hardware. Do not use SDMMC mode without a new routing/firmware design; this socket is connected for SPI.

GPIO A / J6 pins 1→8: **3V3, GND, GPIO1, GPIO2, GPIO3, GPIO8, GPIO9, GPIO15**. GPIO B / J7 pins 1→8: **GND, GPIO18, GPIO19, GPIO26/ADC0, GPIO27/ADC1, GPIO28/ADC2, RUN, 3V3**. Pin 1 is the square pad/footprint mark. GPIO is 3.3 V logic, not 5 V tolerant. The RP2350 leakage erratum can affect high-impedance signals; the onboard battery input is buffered and external header analog inputs should be driven from a suitable low-impedance source or buffer.

Qwiic / J4 pins 1→4: **GND, 3V3, SDA, SCL**. It supplies 3.3 V only. More external pull-ups appear in parallel with the onboard 2.2 kΩ resistors; check sink current/capacitance before chaining many boards.

SWD / J5 pins 1→3: **SWCLK, GND, SWDIO**, matching the 3-pin Raspberry Pi Debug Probe convention. The target is self-powered; no debug connector power input is provided.

## Firmware and bring-up obligations

1. Boot the RP2350, configure the fixed external core-supply policy, and set `VREG.HIZ`. Leave radio/RGB disabled initially. Disable pulls and digital input circuitry on the ADC pin according to the datasheet.
2. Enable the normal flash QSPI boot configuration; initialize PSRAM as the second QMI device with GPIO0 CS1n. Its reset pull-up is important and must remain fitted. Follow PSRAM power-up/reset timing and maximum CS-active/refresh intervals; use at most 84 MHz for linear bursts, not its higher wrapped-burst rating. Validate chip ID, capacity and data integrity before increasing clock speed.
3. USB firmware declares its actual current requirements and controls GPIO23 after successful host configuration. Implement suspend and disconnect behavior. USB compliance/idle/suspend current is not claimed without measurements.
4. Build ESP32-C3 firmware with RX IO20, TX IO21, CTS IO4 and RTS IO5. UART signal names in the schematic are from the **radio** perspective. An AT firmware build or a custom framed UART coprocessor protocol is possible; ESP32-C3's Wi-Fi/BLE capabilities need a host application/driver.
5. Before cutting radio power, make all four RP UART signals high impedance to avoid back-powering the unpowered module. Wait for power/reset settling before sending UART data. IO8/IO2 are strapped high; hold ESP BOOT/IO9 low across power-on to use its UART downloader.
6. Hold RGB data low before enabling/disabling the 5 V RGB boost; wait for rail settling before transmitting. The AHCT buffer is not an independent hot-plug level translator for an unpowered rail. Initialize SPI card detect/pull states and I2C using the pin table.

Hold BOOTSEL while resetting or applying power to enter the RP2350 USB ROM loader. The BOOTSEL switch pulls only flash CS through 1 kΩ; PSRAM remains deselected. RESET resets the RP2350. ESP BOOT is a separate coprocessor download-mode button, not a global board reset.

## Layout and manufacture

The four-layer arrangement reserves In1 exclusively for ground, including uninterrupted USB reference ground. In2 contains the 3.3 V distribution pour **and signal routing**; it is not an uninterrupted power plane. Power-path distribution uses a local VSYS bottom copper region and conventional through vias. Buck switching paths are short, protected top-layer routes with wider copper; there is no RP2350 internal switching loop. Exposed pads have segmented paste and conventional external ground vias. The module footprint's under-pad thermal holes were removed to avoid an unquoted via-in-pad process; pad 19 is still soldered and grounded. Ordinary vias are 0.60/0.30 mm; one RP2350 escape uses 0.50/0.20 mm with the same 0.15 mm annular ring. No via drill intersects an open SMD pad.

The module sits at the top edge. Its antenna/side clearance has an all-layer no-track/no-via/no-pad/no-pour region. Do not put metal, a battery, a card, a cable shield, a conductive enclosure wall or new routing in this keepout. RF performance and enclosure clearance still require testing.

The USB PHY series resistors are close to U1, the two CC pins are independently terminated, and duplicated data pins are merged locally for either plug orientation. The principal USB pair is protected top-layer copper. Its impedance is conditional on the PCBWay-approved stack, not guaranteed by the drawn width alone.

All purchased components use ordinary QFN/WSON/SOP/SOIC/SOT/0402–1206/SMD-connector/THT-header processes available to a turnkey assembler. Component substitution and first-article approval requirements are in `fab/ASSEMBLY.md`. For quantities large enough to panelize, let PCBWay choose assembly rails/tooling outside the board while respecting the antenna edge.

## References and attribution

The Raspberry Pi RP2350 datasheet/external-core circuit and hardware-design guide, TI charger/regulator/boost/load-switch/amplifier datasheets, Espressif WROOM-02 module documentation, Winbond flash documentation, and manufacturer land-patterns were used. See `references/SOURCES.md` for source URLs and verification notes. No assertion is made that downloaded datasheets prove distributor stock or that CAD checks prove RF/USB/electrical compliance.

Vendored KiCad symbols/footprints originate from the installed KiCad standard libraries and are covered by their library license, including the standard board-use exception. Local modifications are documented in `libraries/README.md`; custom PSRAM/boost symbols use manufacturer pin assignments. Keep library attribution/license information when redistributing library material.
