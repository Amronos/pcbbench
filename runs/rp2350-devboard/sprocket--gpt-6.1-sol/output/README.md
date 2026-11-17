# Sprocket 2350

RP2350A development board with 16 MiB QSPI flash, 8 MiB PSRAM, USB-C device interface, rechargeable single-cell battery power, ESP32-C3 Wi-Fi/BLE, SPI microSD, Qwiic/STEMMA QT and an addressable RGB indicator.

## Release status

Prototype design. No hardware has been built or tested. The revised layout uses the Raspberry Pi regulator core, a compact charger/buck-boost stage, local radio bypassing and a shorter USB route. The files in `fab/` support PCBWay's prototype quote and engineering review. They do not establish bench performance or manufacturer acceptance.

Before ordering, PCBWay must confirm exact sourcing, controlled impedance, filled/capped vias and complete assembly. Qualify the built prototype before production release. See [release-review.md](fab/release-review.md).

## Design choices

| Item | Choice |
|---|---|
| MCU | Bare RP2350A, current stepping to be confirmed by supplier |
| Memory | W25Q128JVSIQ flash; APS6404L-3SQR-SN PSRAM on shared QSPI bus with GPIO0 CS1 |
| Radio | ESP32-C3-WROOM-02-N4, integrated antenna beyond the PCB edge |
| Power | BQ24074 power-path charger, approximately 303 mA charge setting; TPS63001 fixed 3.3 V buck-boost |
| Battery | External protected 1S 4.2 V LiPo pack, cell-mounted 10 kΩ B3435 NTC, keyed 3-pin JST PH |
| PCB | 85 × 65 mm, four copper layers, top-side components and two factory-installed through-hole headers |
| Debug | RP2350 SWD header; RP BOOTSEL/reset and ESP boot/reset buttons |
| RGB | WS2812C-2020-V6, manufacturer-supported 3.3 V operation, not an older WS2812 substitution |

PCBWay must source and install every BOM reference, including headers J5/J6. No part is reserved for user assembly.

## Interfaces and firmware

| Function | RP2350 GPIO |
|---|---|
| PSRAM CS | 0, QMI CS1n |
| Qwiic SDA / SCL | 2 / 3, I²C1 |
| ESP RX / TX | RP TX 4 → ESP RX20; RP RX 5 ← ESP TX21, UART1 |
| microSD MISO / CS / CLK / MOSI | 8 / 9 / 10 / 11, SPI1 |
| RGB data | 20, PIO |
| ESP EN / BOOT | 23 / 24. Drive EN high to enable; drive BOOT low/release for download mode. |
| USB input limit | 6. Low/high impedance selects USB100; high selects USB500. J5 pin 4 is unused. |
| Card detect | 25, low when inserted |
| Battery monitor | 26 / ADC0, VBAT = 2 × measured ADC voltage |

Initialize PSRAM through QMI. Observe the manufacturer's startup/reset, refresh and maximum chip-select duration limits. Begin with conservative QSPI and SD clock rates. The ESP module needs application firmware or a compatible ESP-AT build. RP firmware can bridge the UART to program the ESP while controlling its boot/reset pins. No firmware image is included or tested.

Hold RP BOOTSEL while releasing RESET to enter the USB ROM loader. BOOTSEL alone does not reset the MCU. SWD reference voltage is an output, not a board power input.

### Expansion header J5

Numbering follows the square pin-1 pad on the assembly drawing. All signals are 3.3 V.

| Odd pin | Signal | Even pin | Signal |
|---:|---|---:|---|
| 1 | 3V3 output | 2 | GND |
| 3 | GP1 | 4 | Unused |
| 5 | GP7 | 6 | GP15 |
| 7 | GP16 | 8 | GP17 |
| 9 | GP18 | 10 | GP19 |
| 11 | GP12 | 12 | GP13 |
| 13 | GP14 | 14 | GP22 |
| 15 | CHG, active low | 16 | GP21 |
| 17 | GP27 / ADC1 | 18 | GP28 / ADC2 |
| 19 | GP29 / ADC3 | 20 | GND |

J6 pins 1–4 are 3V3 reference output, SWDIO, SWCLK and GND. J4 pins 1–4 are GND, 3V3 output, SDA and SCL.

## Power and safety limits

- USB is a 5 V sink/device, not USB PD and not a host. Separate 5.1 kΩ CC resistors are fitted.
- Startup selects USB100 and holds the ESP disabled. Firmware may drive GP6 high only after the source permits 500 mA. Keep GP23 low until the supply budget allows radio operation. Do not enable the radio, SD writes or external Qwiic loads on a 100 mA budget.
- This prototype does not guarantee generic legacy-host pre-enumeration or suspend compliance. SD, RGB and Qwiic power are not hardware-gated, and the ROM loader does not implement this board's power policy. Use a source explicitly allowing 500 mA for USB-only development, or a protected battery with a qualified USB host. Do not advertise USB certification.
- The 500 mA USB budget includes both system load and charging. The charger reduces charging and can supplement from the battery. Wi-Fi transmission, SD writes and Qwiic loads must be qualified together. Do not assume USB-only operation supports every combined peak.
- Use a protected 4.2 V single-cell pack that permits at least 335 mA charging and the measured peak discharge current. The board charger is not pack overdischarge or short-circuit protection.
- J3 pin 1 is BAT+, pin 2 GND, pin 3 NTC. NTC must connect to GND in the pack and contact the cell. This is not a standard two-wire JST battery pinout. Check polarity before connecting.
- The direct NTC circuit allows approximately 0–50°C charging, with tolerance. Only use cells qualified for that range; cells limited to 45°C need tighter charge inhibition.
- Battery monitoring uses a PMOS switch enabled from the live 3.3 V rail through an NMOS. This avoids an always-connected battery divider when the MCU is unpowered. Its startup/shutdown transient still needs bench validation.
- Do not drive GPIO, SWD, I²C or UART from powered external equipment while the board is unpowered. Expansion pins are 3.3 V interfaces. Do not inject power through J4/J5/J6.
- WS2812C-V6's below-3.3 V behavior is not specified. Qualify indicator operation at worst-case rail tolerance and temperature. Do not substitute older 5 V-only LED revisions.

## Manufacturing files

Open `sprocket2350.kicad_pro` with KiCad 10.99 or a compatible newer release. Embedded symbols and footprints allow inspection without regeneration. Generation tools use the connector's `kicad-python`, headless API and KiCad 10 library tables.

[Fabrication package](fab/README.md), [BOM](fab/BOM.csv), [assembly instructions](fab/assembly.md) and [procurement checks](fab/procurement.md) are in `fab/`. The package includes Gerbers, drills, position CSV, schematic PDF, assembly drawings and check reports for review.

Final all-severity ERC and DRC report zero violations, zero opens and zero schematic parity issues under the project's recorded check settings. The BOM, schematic, PCB and placement file agree on all 93 fitted references. All component model files exist. The package identifies 18 vias requiring filled/capped processing.

PCBWay must confirm sourcing in its quote; distributor stock is not PCBWay inventory. No quote or order has been placed.

## Review before release

1. Review final ERC/DRC reports, confirm complete routing and accept zero opens/shorts. Review all warnings; do not dismiss physical violations as library noise.
2. Verify L2's lower-left winding dot on the assembly drawing. Check filled/capped vias and the charger/regulator paste process.
3. Have PCBWay confirm the proposed four-layer stackup and 90 Ω ±10% USB impedance. The nominal dielectric dimensions are a quote target, not a field-solver or manufacturer sign-off.
4. Verify footprints and pin 1 against ordered USB, JST, SD and QFN package drawings. RF antenna area must remain copper- and enclosure-free.
5. Confirm component sourcing, full through-hole assembly and panel rails/fiducials with PCBWay.
6. After building an accepted prototype, test USB enumeration in both plug orientations, ROM boot/SWD, flash/PSRAM stress, SD writes, Wi-Fi/BLE, RGB, Qwiic, battery ADC and all USB/battery insertion sequences. Test NTC open/short and charger current/temperature before production release.

## Sources

- [RP2350 hardware design guide](https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf)
- [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf)
- [BQ24074 datasheet](https://www.ti.com/lit/ds/symlink/bq24074.pdf)
- [TPS63001 datasheet](https://www.ti.com/lit/ds/symlink/tps63001.pdf)
- [ESP32-C3-WROOM-02 datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf)
- [PCBWay fabrication capabilities](https://www.pcbway.com/capabilities.html) and [assembly service](https://www.pcbway.com/pcb-assembly.html)
