# RP2350A development board — primary-source circuit research

Verified over the web on 2026-11-10. Scope: research and net recommendations only; no schematic or PCB was generated. Board target: 80 × 75 mm, four layers, F.Cu/B.Cu signals and both inner layers GND. Manufacturer facts are cited by source IDs below; added resistor/capacitor values and GPIO assignments are explicitly recommendations unless identified as reference-circuit values. Live distributor inventory, pricing, and assembler availability were not verified.

## Decisions and corrections to carry into generation

- Core supply: **TLV75801PDBVR adjustable LDO**, 10 kΩ/10 kΩ 0.1% feedback divider, nominal 1.1 V; do not use the previously proposed nonexistent `TLV75511PDBVR` ordering code.
- Main supply: **TPS63031DSKR fixed 3.3 V** from BQ24074 `SYS`. Keep the chosen part, but qualify its current margin at minimum battery voltage.
- Battery: protected, external 500 mAh single-cell 4.2 V pack with a cell-mounted 10 kΩ NTC; **JST S3B-PH-SM4-TB(LF)(SN)**, pin 1 BAT, pin 2 GND, pin 3 TS. Protection is in the pack; BQ24074 is not a protection IC.
- microSD: **Hirose DM3AT-SF-PEJM5**, replacing Molex 5031821852.
- LED: **Worldsemi WS2812B-2020-V6**, VDD on SYS, DIN from 3.3 V GPIO, no AHCT shifter. Actual manufacturer PDF gives VIH = **0.55 × VDD**; the separately reported 0.6 × VDD upgrade notice was not independently located. See voltage-margin and low-battery limitations below.
- ESP-AT correction: **ESP GPIO6 is UART1 RX; GPIO7 is UART1 TX**. The proposed GPIO7-RX/GPIO6-TX connection was reversed. Use hardware flow control provision: RP GP20 TX → ESP GPIO6 RX; RP GP21 RX ← ESP GPIO7 TX; RP GP22 CTS ← ESP GPIO4 RTS; RP GP23 RTS → ESP GPIO5 CTS. Move RADIO_EN to GP18 and RADIO_BOOT to GP19.
- `W25Q32JVSSIQ` is the **wide 208 mil SOIC-8**, not narrow SOIC-8. `APS6404L-3SQR` alone is not a complete packaged SMT ordering code: use **APS6404L-3SQR-SN** for 150 mil SOP-8, or **APS6404L-3SQR-ZR** for USON-8, with the matching footprint.

## 1. RP2350A: complete physical pad map

Sources [R1, R2]. RP2350A is QFN-60, 7 × 7 mm, with exposed GND pad 61. Do not use RP2040 or RP2350B pin numbering. The pin diagram and Raspberry Pi RP2350A minimal reference schematic were cross-checked; an IOVDD list in the datasheet appears to substitute pad 54 for pad 1, whereas pad 54 is specifically QSPI_IOVDD.

| Physical pad | Manufacturer name | Recommended board net / disposition |
|---:|---|---|
| 1 | IOVDD | 3V3; local 100 nF |
| 2 | GPIO0 | PSRAM_CSn, QMI/XIP CS1n function F9; 10 kΩ pull-up |
| 3 | GPIO1 | Spare |
| 4 | GPIO2 | Spare |
| 5 | GPIO3 | Spare |
| 6 | DVDD | 1V1; local 100 nF |
| 7 | GPIO4 | SD_MISO, SPI0 RX |
| 8 | GPIO5 | SD_CSn, software chip select |
| 9 | GPIO6 | SD_SCK, SPI0 SCK |
| 10 | GPIO7 | SD_MOSI, SPI0 TX |
| 11 | IOVDD | 3V3; local 100 nF |
| 12 | GPIO8 | I2C0_SDA to SH connector |
| 13 | GPIO9 | I2C0_SCL to SH connector |
| 14 | GPIO10 | CHG_N input, optional charger status |
| 15 | GPIO11 | PGOOD_N input, optional input-power status |
| 16 | GPIO12 | LED_DIN, PIO output |
| 17 | GPIO13 | Spare |
| 18 | GPIO14 | Spare |
| 19 | GPIO15 | Spare |
| 20 | IOVDD | 3V3; local 100 nF |
| 21 | XIN | Crystal terminal 1; 15 pF to GND |
| 22 | XOUT | Through 1 kΩ to crystal terminal 3 |
| 23 | DVDD | 1V1; local 100 nF |
| 24 | SWCLK | RP SWD clock header/test pad |
| 25 | SWDIO | RP SWD data header/test pad |
| 26 | RUN | Reset net; recommended 10 kΩ pull-up to 3V3 and momentary switch to GND |
| 27 | GPIO16 | USB_500_EN → BQ EN1; 100 kΩ pull-down |
| 28 | GPIO17 | SD_DETECT_N |
| 29 | GPIO18 | RADIO_EN → ESP EN; 10 kΩ pull-down at ESP EN |
| 30 | IOVDD | 3V3; local 100 nF |
| 31 | GPIO19 | RADIO_BOOT_N → ESP GPIO9; open-drain control |
| 32 | GPIO20 | UART1 TX → ESP GPIO6 RX, module pad 5 |
| 33 | GPIO21 | UART1 RX ← ESP GPIO7 TX, module pad 6 |
| 34 | GPIO22 | UART1 CTS ← ESP GPIO4 RTS, module pad 3 |
| 35 | GPIO23 | UART1 RTS → ESP GPIO5 CTS, module pad 4 |
| 36 | GPIO24 | Spare |
| 37 | GPIO25 | Spare |
| 38 | IOVDD | 3V3; local 100 nF |
| 39 | DVDD | 1V1; local 100 nF |
| 40 | GPIO26_ADC0 | BAT_ADC; see divider accuracy caveat |
| 41 | GPIO27_ADC1 | Spare ADC/GPIO |
| 42 | GPIO28_ADC2 | Spare ADC/GPIO |
| 43 | GPIO29_ADC3 | Spare ADC/GPIO |
| 44 | ADC_AVDD | 3V3; local 100 nF; quiet routing |
| 45 | IOVDD | 3V3; local 100 nF |
| 46 | VREG_AVDD | 3V3 in selected external-core configuration |
| 47 | VREG_PGND | GND |
| 48 | VREG_LX | NC in external-core configuration |
| 49 | VREG_VIN | 3V3 in external-core configuration |
| 50 | VREG_FB | GND in external-core configuration |
| 51 | USB_DM | USB_D− through 27 Ω near MCU |
| 52 | USB_DP | USB_D+ through 27 Ω near MCU |
| 53 | USB_OTP_VDD | 3V3; local 100 nF, required even without USB use |
| 54 | QSPI_IOVDD | 3V3; local 100 nF |
| 55 | QSPI_SD3 | Flash/PSRAM IO3, both package pad 7 |
| 56 | QSPI_SCLK | Flash/PSRAM CLK, both package pad 6 |
| 57 | QSPI_SD0 | Flash/PSRAM IO0, both package pad 5 |
| 58 | QSPI_SD2 | Flash/PSRAM IO2, both package pad 3 |
| 59 | QSPI_SD1 | Flash/PSRAM IO1, both package pad 2 |
| 60 | QSPI_SS | FLASH_CSn, directly to flash pad 1; 10 kΩ pull-up |
| 61 | GND exposed pad | GND plane, thermal/ground vias and appropriate paste apertures |

Spare pins above are intentionally available for later board functions. Do not hard-wire unspecified peripherals into the table during generation.

### 1.1 Selected external 1.1 V core supply

**RP datasheet §6.3.7, Figure 24 is the authoritative configuration [R1].** Connect VREG_VIN 49 and VREG_AVDD 46 together to 3V3, with the figure's local 4.7 µF bypass to GND. Connect VREG_FB 50 to GND, VREG_PGND 47 to GND, leave VREG_LX 48 unconnected, and power DVDD 6/23/39 from the external 1V1 rail. Add 100 nF at each DVDD pad. No internal-buck inductor is populated.

**Do not disable the regulator by grounding VREG_VIN or VREG_AVDD.** These supplies also power power-on-reset/brownout circuitry and must be powered together. The documented external configuration boots normally. The otherwise-unused switching regulator draws approximately 400 µA until firmware sets **POWMAN VREG.HIZ = 1**. Use the documented protected POWMAN register-write mechanism (upper-halfword password 0x5AFE), rather than assuming an ordinary unprotected bit write will take effect. Retain HIZ across power-state handling; the internal low-power LDO connects directly to DVDD and must not contend with the external source.

RP DVDD normal operating range is **1.05–1.16 V**, nominal 1.1 V [R1]. Verify the complete LDO accuracy budget, PCB drop, and startup/load transients against this range. USB_OTP_VDD requires **3.135–3.63 V** and must be powered even if USB is unused. GPIO/ADC domains remain 3.3 V; do not attach SYS or BAT directly to an RP input. Follow the datasheet supply-sequencing provisions, particularly the joint VREG supplies; the external LDO naturally starts after its 3V3 input.

**TLV75801PDBVR — DBV/SOT-23-5, exact pin map [P3]:**

| Pad | Name | Net / parts |
|---:|---|---|
| 1 | IN | 3V3; 2.2 µF X5R/X7R to GND |
| 2 | GND | GND |
| 3 | EN | 3V3 for always-on core |
| 4 | FB | Junction of two 10 kΩ, 0.1% resistors |
| 5 | OUT | 1V1; 2.2 µF X5R/X7R to GND |

Upper resistor: OUT/1V1 → FB, 10 kΩ. Lower resistor: FB → GND, 10 kΩ. VOUT = 0.55 V × (1 + Rupper/Rlower) = **1.100 V nominal**. Divider current is 55 µA. Keep FB and both resistors next to the LDO, away from TPS switching nodes. Stock KiCad symbol `Regulator_Linear:TLV75801PDBV` was inspected and matches the selected DBV pin map. The datasheet's WSON pin table must not be applied to this SOT-23 part.

TI specifies nominal input/output capacitance ≥1 µF and effective output capacitance ≥0.47 µF after bias/tolerance derating; the chosen 2.2 µF parts are appropriate if their effective capacitance satisfies that. Output maximum is 220 µF. Prefer 6.3 V or higher MLCCs and check the actual capacitance-vs-bias curve.

**Thermal limitation:** 500 mA is the electrical rating, not a guarantee that DBV can dissipate (3.3−1.1) × 0.5 = 1.1 W continuously. At 200 mA, dissipation is already 0.44 W; TI's DBV θJA 176.9 °C/W implies approximately 78 °C rise under its JEDEC test conditions. Actual board copper changes this result. Qualify sustained dual-core load and ambient temperature. If DBV runs too hot, exact same-family alternative **TLV75801PDRVR**, 6-pin WSON with exposed pad, is a different footprint/pin map and provides better heat conduction [P3]. Do not substitute it without updating connectivity. The external LDO also increases 3V3 current compared with an efficient internal buck.

### 1.2 Internal buck reference, retained only as research

The selected board uses the external LDO. If reconsidered, the August 24, 2026 Raspberry Pi hardware guide [R2] gives:

- VREG_VIN 49 → 3V3, local 4.7 µF to GND.
- VREG_LX 48 → **Abracon AOTA-B201610S3R3-101-T, 3.3 µH** → 1V1.
- VREG_FB 50 → 1V1; DVDD 6/23/39 → 1V1; 4.7 µF buck output bypass plus the individual DVDD bypasses.
- 3V3 → **33 Ω** → VREG_AVDD 46; local **4.7 µF** from AVDD to GND.
- VREG_PGND 47 → GND.

The reference inductor is not electrically polarized like a diode, but its **marked winding orientation relative to LX/output and the exact reference placement matter for noise coupling**. Follow the manufacturer's/reference-board marked orientation and Raspberry Pi layout; do not choose an unmarked generic 3.3 µH substitute by value alone. The guide's reference MLCCs include 0402 4.7 µF, 6.3 V, X5R parts. Do not mix this buck configuration's FB connection or 33 Ω AVDD feed into the chosen Figure 24 external configuration.

### 1.3 Crystal and debug/boot

Use Raspberry Pi's exact recommended **Abracon ABM8-272-T3**, 12 MHz, load capacitance 10 pF, ESR ≤50 Ω, frequency tolerance ±30 ppm [R2, §4]. This particular circuit is tuned for 3.3 V IOVDD.

- Crystal terminal 1 → RP XIN 21; **15 pF C0G/NP0** from this terminal to GND.
- RP XOUT 22 → **1 kΩ** damping resistor → crystal terminal 3; **15 pF C0G/NP0** from crystal terminal 3 to GND, on the crystal side of the resistor.
- Crystal case terminals 2 and 4 → GND.
- Short, symmetric crystal routes; keep converter switching copper away. The two 15 pF caps give 7.5 pF series load plus PCB/pin parasitics. A nominally similar crystal still requires startup/temperature qualification.

Recommended SWD header numbering: 1 GND, 2 SWDIO/RP25, 3 SWCLK/RP24, 4 3V3 reference, 5 RUN/RP26 if using a five-pin header. This is a board convention, not a standard connector assignment. BOOTSEL switch: FLASH_CSn/RP60 → **1 kΩ** → momentary switch → GND. **The 1 kΩ is in the switch branch, not in series between MCU and flash CS.** Keep the branch and pull-up close to the flash. Enter BOOTSEL by holding the switch during reset, rather than pulling down active XIP during arbitrary operation [R2, §3].

## 2. Shared QSPI: flash and PSRAM

Sources [M1, M2, R2]. Both devices run from 3V3, share SCLK and all four data wires, and require **independent active-low chip selects**. Use RP's dedicated QSPI_SS for primary boot flash and GPIO0/F9 CS1n for PSRAM. These are not the microSD SPI nets.

| Memory package pad | W25Q32JV function | APS6404L function | RP pad / net |
|---:|---|---|---|
| 1 | /CS | /CE | Flash → RP60 FLASH_CSn; PSRAM → GP0/RP2 PSRAM_CSn |
| 2 | DO / IO1 | SO / SIO1 | RP59 QSPI_SD1 |
| 3 | /WP / IO2 | SIO2 | RP58 QSPI_SD2 |
| 4 | GND | VSS | GND |
| 5 | DI / IO0 | SI / SIO0 | RP57 QSPI_SD0 |
| 6 | CLK | SCLK | RP56 QSPI_SCLK |
| 7 | /HOLD / IO3 | SIO3 | RP55 QSPI_SD3 |
| 8 | VCC | VDD | 3V3, separately decoupled |

Fit a **10 kΩ pull-up on each CS**. GPIO0 defaults to a pull-down; the PSRAM CS pull-up is especially important. Flash local bypass: 100 nF; PSRAM: **1 µF local** per AP Memory decoupling recommendation, with optional additional 100 nF. Keep all shared-bus branches short and flash/PSRAM adjacent to RP. Do not add arbitrary 1 kΩ data/clock series resistors. Small source damping, if needed, must be established from actual routing and waveform measurements.

### 2.1 W25Q32JVSSIQ selection

- **32 Mbit = 4 MiB** NOR flash, 2.7–3.6 V supply. Winbond Rev K, April 28, 2026 was read [M1].
- `SS` package is **208 mil wide SOIC-8**, body approximately 5.28 × 5.28 mm, 1.27 mm pitch, lead span approximately 7.9 mm. A 3.9 mm-body/150 mil stock footprint is wrong. Match the package drawing, including min/max lead span, before assigning a land pattern.
- Exact narrow-package alternative is **W25Q32JVSNIQ**, 150 mil SOIC-8, if that package is preferred and available. This is a package replacement, not a capacity change; qualify the exact ordering suffix and delivery stock.
- `IQ` option has QE factory-set/fixed to 1; standard SPI commands still work. In quad mode, pads 3/7 are IO2/IO3; **do not hard-tie them to 3V3** as /WP and /HOLD.
- Respect power-up read delay (tVSL 20 µs) and write-inhibit delay (5 ms). For a true brownout power-reset, the datasheet gives VCC below 0.8 V for at least 100 µs. An MCU RUN reset is not a flash power cycle; implement compatible XIP/continuous-read exit sequences.
- RP ROM initial boot uses serial 03h read with 24-bit addresses; this flash supports it. Configure the selected flash's quad/XIP mode with a suitable SDK boot stage, and retain recovery through BOOTSEL/SWD.

### 2.2 APS6404L-3SQR packaged alternatives and timing

- **64 Mbit = 8 MiB** PSRAM, 2.7–3.6 V supply [M2, Rev 2.7, Jan 5, 2024].
- `APS6404L-3SQR` appears in the bare-die/SIP ordering category. Specify **APS6404L-3SQR-SN** for SOP-8 150 mil, or **APS6404L-3SQR-ZR** for USON-8 3 × 2 mm. Do not send the unsuffixed identifier as a complete SMT BOM item.
- Linear burst clock limit **84 MHz**. Wrapped 32-byte bursts allow **109 MHz at 3.3 V ±10%**; the advertised **133 MHz is for 3.0 V ±10%**, so it is not a general guarantee on this 3.3 V rail.
- CE low maximum **8 µs** in standard-temperature operation, **3 µs** for the extended-temperature timing case; CE high minimum **18 ns**. Configure QMI transaction splitting/recovery accordingly. Continuous CE-low streaming is inappropriate for this self-refresh memory.
- At cold startup, allow **150 µs after VDD is stable** before access, then send the documented **66h/99h reset** sequence and observe reset timing (tRST 50 ns). The power-up specification asks CE to track VDD within 200 mV and clock/data to remain low during the startup interval. The shared flash bus means reset/boot timing must be checked; do not assume a CS pull-up alone satisfies every startup condition.
- Warm RP reset leaves PSRAM powered and potentially in a prior interface mode. Firmware must restore a known mode, initialize CS1 and QMI timing, and avoid unintended CS overlap. PSRAM is volatile and not boot flash.

## 3. ESP32-C3-WROOM-02-N4 UART radio coprocessor

Sources [E1, E2]. **BLE and Wi-Fi; no Bluetooth Classic.** N4 is 4 MiB module flash. Supply **3.0–3.6 V**, nominal 3.3 V; Espressif calls for a source capable of **at least 500 mA**. The documented RF test peak around 345 mA is not a substitute for that supply requirement. Fit 10 µF plus 100 nF next to module pad 1; 22–47 µF additional bulk is an engineering option after transient review.

### 3.1 All module pads

| Module pad | Function | Recommended board net |
|---:|---|---|
| 1 | 3V3 | 3V3, local bulk and bypass |
| 2 | EN | RADIO_EN from RP GP18/pad29; 10 kΩ pull-down |
| 3 | GPIO4 | ESP UART1 RTS → RP GP22/pad34 CTS |
| 4 | GPIO5 | ESP UART1 CTS ← RP GP23/pad35 RTS |
| 5 | GPIO6 | ESP UART1 RX ← RP GP20/pad32 TX |
| 6 | GPIO7 | ESP UART1 TX → RP GP21/pad33 RX |
| 7 | GPIO8 | Boot strap: recommended 10 kΩ pull-up to 3V3 |
| 8 | GPIO9 | BOOT_N; 10 kΩ pull-up, RP GP19/pad31 open drain, programming header |
| 9 | GND | GND |
| 10 | GPIO10 | NC/spare |
| 11 | GPIO20 / U0RXD | Programming/debug RX; programmer TX connects here |
| 12 | GPIO21 / U0TXD | Programming/debug TX; programmer RX connects here |
| 13 | GPIO18 / USB_D− | NC; not connected to RP USB pair |
| 14 | GPIO19 / USB_D+ | NC; not connected to RP USB pair |
| 15 | GPIO3 | NC/spare |
| 16 | GPIO2 | Boot strap: recommended 10 kΩ pull-up to 3V3 |
| 17 | GPIO1 | NC/spare |
| 18 | GPIO0 | NC/spare |
| 19 | Exposed GND | GND plane / proper module land pattern |

### 3.2 Verified ESP-AT defaults

Official ESP-AT hardware connection tables in **latest, release-v3.2.0.0 and release-v2.4.0.0** agree [E2]:

| Purpose | ESP pin | Opposite endpoint |
|---|---|---|
| AT commands received | GPIO6 / UART1 RX | RP GP20 / UART1 TX |
| AT replies transmitted | GPIO7 / UART1 TX | RP GP21 / UART1 RX |
| ESP ready-to-receive indication | GPIO4 / UART1 RTS | RP GP22 / UART1 CTS |
| ESP transmit permission | GPIO5 / UART1 CTS | RP GP23 / UART1 RTS |
| Download/log RX | GPIO20 / UART0 RX | Programmer TX |
| Download/log TX | GPIO21 / UART0 TX | Programmer RX |

Both UARTs default to **115200 baud** in those tables. CTS/RTS are required only when hardware flow control is enabled. The module datasheet's default UART0 GPIO20/21 assignments describe download/debug and do not override the ESP-AT UART1 communication table. Verify the actual flashed AT binary's configuration and enable flow control on **both endpoints**. Do not assume modules ship with the desired ESP-AT firmware. Select a C3-WROOM-02-compatible binary/build and preserve a dedicated download interface.

**Recommended six-pin programming header (explicit board convention):**

| Header pin | Net | Connection |
|---:|---|---|
| 1 | GND | Module GND |
| 2 | 3V3_REF | Module pad1; target voltage reference, normally not external power injection |
| 3 | ESP_U0RX | Module pad11 GPIO20; adapter TX |
| 4 | ESP_U0TX | Module pad12 GPIO21; adapter RX |
| 5 | ESP_EN | Module pad2 |
| 6 | ESP_BOOT_N | Module pad8 GPIO9 |

For download, GPIO8 high and GPIO9 low at EN rising; maintain strap levels for the specified approximately 3 ms hold interval. Keep GPIO2 in its recommended pulled-up state. Allow supply stabilization before enabling the module and respect the minimum EN timing (50 µs values in the module reset/power timing specification).

RADIO_EN's 10 kΩ pull-down keeps the module in reset at RP boot. Suggested **1 kΩ series resistor between GP18 and ESP EN**, with the pull-down on the ESP side, limits programming-header contention; drive GP18 high-impedance while an external programmer controls EN. At nominal 3.3 V the divider yields approximately 3.0 V; verify margin including RP VOH and ESP EN VIH at actual loads. RADIO_BOOT should sink GPIO9 only (open-drain output or output-low/Hi-Z), allowing the header to assert BOOT without opposing a push-pull high. EN low is reset, not complete removal of the module's supply. Avoid UART/header back-power and unapproved parallel 3.3 V sources.

**Antenna/layout:** use the exact WROOM-02 module land pattern and the primary antenna keepout drawing. Place the antenna at the board edge with the specified antenna region free of copper, vias, components and routing **on all four layers**, including both GND planes. Inner continuous GND planes are appropriate elsewhere; they do not override antenna keepout. Avoid placing the battery, card cage, USB shell or connector wiring over/in front of the antenna. Module is approximately 18 × 20 × 3.2 mm; include enclosure and insertion clearances.

## 4. BQ24074RGTR charger and power path

Source [P1]. RGT is 16-pin VQFN with a GND thermal pad; use the BQ24074 column of the family datasheet. The pin-description text gives IN operation up to 10.5 V, but the **recommended operating conditions table gives 4.35–10.2 V** for BQ24074; 10.5 V is its nominal OVP threshold. This board uses nominal USB 5 V. OUT/SYS is regulated to **4.4 V nominal, 4.3–4.5 V tolerance** with USB input, and follows the battery through the power-path FET when USB is absent. OUT is not the 3.3 V rail. BAT charge regulation is 4.2 V.

| Pad | Name | Concrete net recommendation |
|---:|---|---|
| 1 | TS | Battery connector pin3, external cell NTC to pack GND; optional 100 nF to GND at charger |
| 2 | BAT | BAT, battery connector pin1 |
| 3 | BAT | Same BAT net; 10 µF local to GND |
| 4 | CE | GND, active-low charge enable; do not float |
| 5 | EN2 | GND |
| 6 | EN1 | USB_500_EN, RP GP16/pad27; 100 kΩ pull-down |
| 7 | PGOOD | PGOOD_N, 10 kΩ pull-up to 3V3; RP GP11/pad15 input |
| 8 | VSS | GND, separately connected even with EP grounded |
| 9 | CHG | CHG_N, 10 kΩ pull-up to 3V3; RP GP10/pad14 input |
| 10 | OUT | SYS |
| 11 | OUT | SYS; 10 µF local to GND |
| 12 | ILIM | 3.24 kΩ to GND suggested, nominal ~497 mA in resistor-limit mode |
| 13 | IN | USB_VBUS; 4.7 µF local to GND recommended |
| 14 | TMR | NC: default timers |
| 15 | ITERM | NC: default termination |
| 16 | ISET | 3.57 kΩ to GND, preferably 1% |
| EP | Thermal pad | GND, thermal vias/paste per RGT drawing |

BAT/OUT capacitor specification is **4.7–47 µF**; selected 10 µF parts must retain enough effective capacitance. IN recommended local bypass is in the **1–10 µF** range. Include connector/VBUS capacitance in the USB inrush budget. Place the high-current IN/OUT/BAT copper and thermal pad appropriately; charger dissipation can be substantial with a discharged battery.

### 4.1 USB current control and charging values

- EN2=0, EN1=0: **USB100**. Actual limit is approximately 90–100 mA. The 100 kΩ pull-down on GP16 keeps this mode at boot.
- EN2=0, EN1=1: **USB500**, approximately 450–500 mA. Firmware asserts GP16 only after the host configuration permits 500 mA. Handle loss of configuration, unplug and reset by reverting to the required limit/state; enumeration alone is not blanket permission for every later USB state.
- **Selected EN2=GND cannot invoke USB suspend.** TI's suspend state requires **EN1=1 and EN2=1**; taking GP16 low only selects USB100, which is not a USB suspend-current solution. CE high stops charging but does not disconnect the USB-powered system. Exact control-net alternative: connect **BQ EN2/pad5 to spare RP GP13/pad17 with 100 kΩ pull-down**; retain GP16 on EN1. Then 00=USB100, EN1=1/EN2=0=USB500, EN1=0/EN2=1=ILIM mode, and 11=USB suspend. Sequence writes to avoid an unintended ILIM interval and qualify USB suspend behavior, especially without a battery. This alternative changes the selected EN2 wiring and is not silently applied in the pin table. With EN2 permanently grounded, do not claim full USB suspend compliance.
- Input current includes **system load plus charging**. DPPM reduces charging when the system consumes the input budget; the battery can supplement system current. The 250 mA charge setting does not guarantee 250 mA charging concurrently with radio/SD load.
- Do not leave ILIM floating simply because EN2 is grounded; TI specifies a resistor here, and an open ILIM can disable charging. The suggested 3.24 kΩ is only the otherwise-unused resistor-mode setting, not what sets USB100/500.
- ICHG ≈ 890 AΩ / RISET: **3.57 kΩ → 249 mA nominal**. Datasheet factor 797–975 gives approximately **223–273 mA**, before resistor tolerance and thermal/DPPM effects. Confirm the selected pack's permitted charge current.
- ITERM NC: **10%** default in USB500 / normal case (~25 mA at this setting), but **USB100 default is 3.3%**, not 10% universally.
- TMR NC: default **30 minute precharge / 5 hour fast-charge** timers. Safety-timer operation under thermal/current reduction follows TI's detailed rules; do not interpret 5 h as an unconditional wall-clock completion guarantee.
- PGOOD and CHG are open-drain active-low indications; pull them to 3V3, not SYS. Decode the documented charge/fault blinking behavior in firmware.

### 4.2 TS: real pack sensor, not an ambient substitute

Selected battery harness assignment: **1 BAT, 2 GND, 3 TS**. The **10 kΩ NTC is in the external pack, physically sensing the cell**, connected from TS to pack GND. BQ supplies an internal **75 µA nominal TS bias, 72–78 µA limits**; a 10 kΩ sensor at 25 °C gives approximately 0.75 V. Do **not** add an arbitrary 3V3 pull-up/divider. Hot threshold is **300 mV nominal, 270–330 mV limits**; cold threshold is **2.1 V nominal, 2.0–2.2 V limits** [P1]. Include these and NTC tolerances in the pack temperature-trip assessment; nominal hot/cold threshold resistance is approximately 4 kΩ / 28 kΩ.

TI's nominal approximately 0–50 °C window is associated with the specified **Vishay Type 2 10 kΩ NTC curve**, not every sensor sold as 10 kΩ. Specify and verify resistance-vs-temperature/Beta tolerance from the **pack supplier's actual NTC datasheet**. No exact pack was selected here, so exact temperature trip limits cannot yet be guaranteed. Open/missing TS should inhibit charging; verify this with the chosen harness. BQ TS handling does not replace pack short-circuit/overcharge/overdischarge protection.

**TS 100 nF tolerance:** no explicit mandatory 100 nF value or tolerance was found in the BQ24074 primary datasheet. A local **100 nF X7R, ±10%** TS-to-GND capacitor is an engineering EMI-filter recommendation, not a TI-mandated cell-safety component. At 10 kΩ it gives approximately 1 ms RC; TI's TS fault deglitch is approximately 50 ms. Cap tolerance changes filtering/startup settling, not the steady-state NTC threshold, provided leakage is negligible. Use a suitably low-leakage capacitor and check open/short sensor behavior and startup on the real cable. Keep the TS wire away from switching nodes and RF.

TI also documents **10 kΩ fixed TS-to-GND** for applications deliberately not using an NTC. That is **not the chosen circuit** and must not be populated as a bypass on this cell-charging board. A board-mounted ambient NTC likewise does not implement the selected cell-temperature requirement.

### 4.3 Battery ADC and undervoltage handling

User-selected divider: BAT → **470 kΩ** → BAT_ADC/RP GPIO26_ADC0 pad40 → **470 kΩ** → GND; **100 nF** from BAT_ADC to GND. Use 0.1% resistors if feasible, clean the board around this high-impedance node, and disable digital input pulls. At 4.2 V the ideal ADC input is 2.1 V and divider drain is **4.47 µA**. Thévenin resistance is **235 kΩ**, RC is **23.5 ms**, so allow approximately **120 ms** for five time constants after a change/switching event before a settled reading.

**This is not a precision divider directly into the RP ADC.** RP's input leakage limit of approximately **1 µA** corresponds to **235 mV error at the ADC**, or **470 mV referred to BAT**. The ADC sampling input also has finite loading (approximately 100 kΩ typical input impedance specification). The 100 nF helps sampling charge and transient noise but does not remove steady leakage/load error. Do not base a supposedly accurate 3.4 V battery cutoff on the ideal 2:1 formula without qualification.

Exact buffer alternative if preserving the low battery drain is important: **TLV9001IDBVR** unity-gain buffer [P6], DBV pin1 OUT → BAT_ADC, pin2 V− → GND, pin3 IN+ → divider junction, pin4 IN− → OUT, pin5 V+ → 3V3 with 100 nF. Keep the divider's 100 nF at IN+. Review ADC isolation/stability and add a small output isolating resistor if needed after checking TI's capacitive-load guidance. This is an optional additional part, not incorporated silently into the selected circuit. A much lower impedance divider plus calibration is another option, with increased pack drain.

BQ24074 does not provide the board's battery undervoltage cutoff. Firmware LED blanking below BAT 3.4 V is a requested behavior, not cell protection; the external protected pack provides the latter. ADC/reference accuracy, SYS drop under load, and MCU behavior before the pack cutoff must all be tested.

## 5. TPS63031DSKR fixed 3.3 V buck-boost

Source [P2]. **TPS63031 is fixed 3.3 V**, unlike adjustable TPS63030. VIN operating range **1.8–5.5 V** accommodates USB-powered SYS ≤4.5 V and a single-cell battery. DSK is **10-pin VSON with exposed PGND pad**; use the package drawing, not a generic ten-pin IC footprint.

| Pad | Name | Net / recommendation |
|---:|---|---|
| 1 | VOUT | 3V3; 2 × 10 µF output capacitors to GND |
| 2 | L2 | Inductor terminal 2 |
| 3 | PGND | GND, power return |
| 4 | L1 | Inductor terminal 1 |
| 5 | VIN | SYS; 10 µF input capacitor to GND |
| 6 | EN | SYS for always-on operation; do not bootstrap EN from its own 3V3 output |
| 7 | PS/SYNC | GND for power-save mode, or SYS for forced PWM; select deliberately |
| 8 | VINA | SYS; local 100 nF to GND |
| 9 | GND | GND, quiet control return |
| 10 | FB | **Directly to 3V3/VOUT** using quiet sense route; no external divider |
| EP | Thermal pad | GND/PGND |

Reference inductor is **1.5 µH Coilcraft LPS3015-1R5** between L1 and L2; TI discusses inductor current rating and saturation margin. Check the complete purchasable inductor suffix, DCR and saturation rating against the calculated peak current, allowing the recommended margin (approximately 20%). Input **10 µF**, output **2 × 10 µF**, VINA **100 nF** are reference starting values. TI limits VINA bypass to **0.22 µF maximum**; do not arbitrarily substitute 1 µF at that pin. Check all MLCCs after DC-bias derating.

For the first implementation, GND on PS/SYNC gives power-save behavior useful on battery; forced PWM is available by tying it to SYS if measured ripple/EMI demands it. Firmware must not assume this pin changes the converter's fixed output voltage. Keep VIN cap, switching stage, inductor and output caps tightly grouped; FB and VINA return must not share long, noisy switch-current paths.

**Current-budget caveat:** the advertised 1 A is typical average switch-current limit, not a 1 A regulated output guarantee. TI describes up to **800 mA in buck mode at VIN 3.6–5.5 V** and up to **500 mA in boost mode for VIN >2.4 V**. A radio source requirement of 500 mA plus RP core LDO current, microSD bursts, flash/PSRAM and other loads leaves little margin at low battery. Qualify actual simultaneous loads and regulator temperature; bulk capacitance cannot cure a sustained deficit.

If the selected TPS63031 cannot sustain the measured load, exact higher-current alternative **TPS63070RNMR** [P5] can be configured for 3.3 V but requires a new footprint, feedback divider, inductor and full application review. It is not a drop-in replacement; do not generalize its headline output current to every battery voltage. Keep TPS63031 in the chosen BOM pending this qualification.

Test at minimum allowed BAT and USB-only without a battery, including USB100 boot and USB500 operation. Radio held in reset reduces startup load, but the external core LDO remains active. Check USB100 boot draw before enabling radio, SD transactions, or bright LED output.

## 6. USB Type-C GCT USB4105-GF-A

Primary GCT drawing [C1], revision B4 dated 2023-12-18. USB 2.0 Type-C receptacle with **16 contacts**; mechanical shell stakes are through-hole while signal contacts are SMT. The all-SMT battery connector choice does not make this USB connector an all-SMT assembly.

| Contact(s) | Net / connection |
|---|---|
| A1, A12, B1, B12 | GND |
| A4, A9, B4, B9 | USB_VBUS → BQ IN13; join all VBUS contacts |
| A5 / CC1 | Separate **5.1 kΩ, 1%** Rd to GND |
| B5 / CC2 | Separate **5.1 kΩ, 1%** Rd to GND |
| A6, B6 | Join D+ locally → RP USB_DP52 via 27 Ω near RP |
| A7, B7 | Join D− locally → RP USB_DM51 via 27 Ω near RP |
| A8, B8 | SBU1/SBU2 NC |
| Shell mounting contacts | GND, short return/stitching near connector |

Do not join CC1 to CC2 or substitute one shared Rd. GCT's collective VBUS current rating is a connector capability, not USB permission to draw that current. Passive Rd makes this a sink; it does not implement detection of advertised Type-C current or USB-PD negotiation. The chosen BQ USB100→USB500 policy remains controlled by USB host configuration and firmware.

Use the exact USB4105 footprint/drawing; confirm contact pad aliases and the four shell slots/holes rather than using a superficially similar USB-C connector. Add suitable low-capacitance USB ESD protection adjacent to the connector as an implementation recommendation; an exact ESD part was not verified in this research. Route a short **90 Ω differential** D+/D− pair over continuous GND according to the fabricator's actual stackup, with short join stubs at the duplicated contacts and 27 Ω resistors near RP. Do not connect ESP USB pads to this same pair without a hub/multiplexer architecture.

## 7. Hirose DM3AT-SF-PEJM5 microSD

Sources [C2]. Verified manufacturer product code **CL0609-0031-0-00**, drawing **EDC-325165-00-00**, revision 4 dated 2024-09-02. Eight card contacts plus insertion-detect switch. Contact rating **0.5 A**, height **1.68 mm**, operating temperature **−25 to +85 °C**, 10,000 mating cycles.

Stock footprint inspected: **`Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5`**. Manufacturer detect contacts A/B correspond to the stock footprint's **pads 9/10**; closed when a card is inserted. `SH` pads are cage grounds. These are footprint pads, not additional microSD protocol contacts.

| Card / footprint pad | Card function | Proposed SPI-mode net |
|---:|---|---|
| 1 | DAT2 | 47 kΩ pull-up to 3V3; otherwise unused in SPI |
| 2 | CD/DAT3 | SD_CSn → RP GP5/pad8; 47 kΩ pull-up |
| 3 | CMD | SD_MOSI → RP GP7/pad10; 47 kΩ pull-up |
| 4 | VDD | 3V3; 10 µF + 100 nF close to socket |
| 5 | CLK | SD_SCK → RP GP6/pad9; optional 22 Ω source resistor near RP |
| 6 | VSS | GND |
| 7 | DAT0 | SD_MISO → RP GP4/pad7; 47 kΩ pull-up |
| 8 | DAT1 | 47 kΩ pull-up to 3V3; otherwise unused in SPI |
| 9 | Detect switch A | SD_DETECT_N → RP GP17/pad28; 10 kΩ pull-up |
| 10 | Detect switch B | GND |
| SH | Shield | GND |

Pull-up and series values are board recommendations. Firmware must implement SD SPI initialization (including low initial clock and required clocks with CS high), handle detect debounce/removal, and respect the selected card's current demand. Neither the socket's 0.5 A contact rating nor its drawing establishes every card's supply transient requirement.

Retain the stock footprint's manufacturer-derived **top-copper keepout** under the moving/contact region. This is distinct from the ESP's all-layer antenna keepout. Ensure card insertion/ejection clearance at the board/enclosure edge. Hirose specifies **250 °C maximum reflow peak**, no more than **two reflow cycles**, and a **0.12 mm reference stencil**; reconcile this with the assembler's process and all other parts. Do not assume a generic 260 °C profile is suitable for the socket.

Molex **5031821852** is superseded. Its exact manufacturer drawing was not successfully verified in this session; no interchangeable pad map or drop-in compatibility with Hirose is asserted.

## 8. JST connectors and pack harness

Primary JST SH and PH catalogs [C3, C4]. Signal/net choices below are board conventions, not manufacturer-defined power assignments.

### 8.1 BM04B-SRSS-TB(LF)(SN), SH four-pin, top entry

1.00 mm pitch, rated **1 A with AWG28**, 50 V, −25 to +85 °C. Stock footprint inspected: **`Connector_JST:JST_SH_BM04B-SRSS-TB_1x04-1MP_P1.00mm_Vertical`**. Mechanical `MP` pads are not extra electrical signal pins.

| Pin | Proposed net |
|---:|---|
| 1 | GND |
| 2 | 3V3 |
| 3 | I2C0_SDA, RP GP8/pad12 |
| 4 | I2C0_SCL, RP GP9/pad13 |

Recommend 4.7 kΩ bus pull-ups to 3V3 on SDA/SCL, accounting for any pull-ups in connected accessories. The selected mapping follows a common Qwiic-style net order; cable mating view and connector orientation must still be checked. Mating housing **SHR-04V-S / SHR-04V-S-B**, crimp **SSH-003T-P0.2-H**, AWG28–32. Do not substitute a different 1 mm connector family by pitch alone.

### 8.2 S3B-PH-SM4-TB(LF)(SN), PH three-pin, side entry SMT

2.00 mm pitch, rated **2 A with AWG24**, 100 V. This is the selected battery header; mating housing **PHR-3**, contacts **SPH-002T-P0.5S** for AWG24–30 or **SPH-004T-P0.5S** for AWG28–32, subject to wire/insulation specifications.

| Pin | Pack harness net |
|---:|---|
| 1 | BAT, protected pack positive |
| 2 | GND, protected pack negative |
| 3 | TS, cell-mounted NTC lead; other NTC lead internally to pack GND |

Inspect pin 1 from the manufacturer mating/PCB view and label it in assembly documentation. There is **no universal lithium-pack JST-PH polarity**. Require the cable supplier to deliver this exact harness order and confirm with a continuity/polarity test before connecting a cell. Keep pack protection and NTC specifications with the BOM. The earlier **BM02B-PH-S-TBT** and **S2B-PH-SM4-TB(LF)(SN)** are two-pin variants and cannot carry the chosen separate TS connection; they are superseded, not alternate populations of this three-pin footprint.

## 9. Worldsemi WS2812B-2020-V6 on SYS, no shifter

Sources [L1]. Manufacturer product page explicitly gives **3.3–5.5 V**. The downloadable filename ends in `1.0`, but the PDF internal footer is **V1.4**. Its electrical supply table gives **3.3–5.3 V**, while the page says 5.5 V; both include this board's USB-powered SYS maximum 4.5 V. Use the exact **V6** ordering identity; generic WS2812B-2020 stock does not prove the same supply/logic specification.

### 9.1 Verified V6 pad map and stock KiCad orientation

| V6 pad | Function | Board net |
|---:|---|---|
| 1 | DOUT | NC for a single LED |
| 2 | GND | GND |
| 3 | DIN | LED_DIN from RP GP12/pad16 through recommended 330 Ω |
| 4 | VDD | **SYS**, not 3V3; 100 nF directly to GND at LED |

An optional 100 kΩ DIN pull-down establishes low input during MCU startup. Set firmware output low before configuring PIO; LED reset/blanking state should be deterministic.

Manufacturer **top-view drawing** places **DIN3 upper left, GND2 upper right, VDD4 lower left, DOUT1 lower right**. Inspected stock KiCad symbol **`LED:WS2812B-2020`** uses the same function-to-pad numbers. Stock footprint **`LED_SMD:LED_WS2812B-2020_PLCC4_2.0x2.0mm`** has the following pad centers in its local coordinates:

| Pad | X mm | Y mm |
|---:|---:|---:|
| 1 | −0.915 | −0.55 |
| 2 | −0.915 | +0.55 |
| 3 | +0.915 | +0.55 |
| 4 | +0.915 | −0.55 |

The stock footprint orientation is **180° relative to that manufacturer top-view diagram**, while the pad-number/function mapping matches. **Do not renumber pads to match an unrotated picture.** Reconcile the physical polarity mark, reel orientation and assembler's placement rotation explicitly. Manufacturer land pattern center pitch is 1.83 mm horizontal / 1.10 mm vertical, consistent with those centers; stock pad size is 0.7 × 0.7 mm. Confirm the V6 mechanical envelope and stencil with the assembler rather than trusting the generic name alone.

### 9.2 Direct 3.3 V logic assessment

The actual V6 PDF specifies **VIH minimum 0.55 × VDD**, VIL maximum **0.7 V**. At SYS maximum **4.5 V**, required high is **2.475 V**. RP's specified high-level minimum around **2.62 V at nominal 3.3 V under the specified load condition** exceeds this at nominal rail voltage; the LED input is lightly loaded. Assess the full rail/VOH tolerance and measured waveform, including the series resistor, ground offset, temperature and rise/fall times.

The user's reported upgrade notice value **0.6 × VDD** would require **2.7 V at 4.5 V** and is **not covered by the RP 2.62 V worst-case figure merely because its nominal GPIO rail is 3.3 V**. That notice was not separately verified; the direct-drive recommendation is based on the retrieved manufacturer's **0.55 × VDD** PDF, with qualification of the actual supplied V6 lot. No shifter is included in the selected plan.

Current is approximately **12 mA per color channel**, so budget approximately **36 mA for full white**, not 12 mA total. Data is 24-bit **GRB**, approximately 800 kbit/s; V6 timing includes T0H **220–380 ns**, T1H **580 ns–1 µs**, reset low **>280 µs**. Use PIO timing for this revision rather than assuming every older WS2812 timing example is sufficient.

### 9.3 Low battery limitation and rejected shifter

Firmware shall blank the LED below measured **BAT 3.4 V**, per the selected plan. On battery, SYS is BAT minus power-path drop; heavy load may pull SYS below **3.3 V even above BAT 3.4 V**. Blanking color data does not disconnect LED VDD: the IC remains supplied below its documented minimum when the pack/SYS falls lower. Therefore the blanking policy is a power-saving behavior, **not a guarantee of specified LED operation throughout discharge**. Validate SYS under load and consider a SYS-aware higher blank threshold or a switched LED supply if operation below the rated range is unacceptable. Do not silently treat an unbuffered, uncalibrated high-impedance BAT ADC as an accurate threshold detector.

Original **SK6812MINI-E** is superseded; its exact primary pad map was not independently verified and is not reused for the V6 LED. **SN74AHCT1G125DCKR** is also superseded. Its verified DCK pin map [L2] is **1 /OE, 2 A, 3 GND, 4 Y, 5 VCC**, but its normal supply requirement is **4.5–5.5 V**: it is unsuitable for 3V3 or nominal **4.4 V SYS**, much less battery-following SYS. Do not populate it as an optional universal SYS-powered fix.

## 10. Manufacturing and sourcing gates

1. Freeze full manufacturer ordering codes and package drawings: especially wide `W25Q32JVSSIQ`, packaged `APS6404L-3SQR-SN`/`-ZR`, V6 LED revision, TLV DBV versus DRV, TPS DSK, and exact JST side/top-entry variants. Manufacturer active status is not evidence of immediate assembler stock.
2. Recheck every symbol-to-footprint pad number before netlist generation. RP has physical GND61; module has exposed GND19; power IC exposed pads must be represented electrically and grounded. KiCad generic names are not proof of package equivalence.
3. Use both inner GND planes as requested, interrupted only by documented keepouts such as the ESP antenna. Ensure short local returns and stitching at layer changes; route QSPI, USB and converter loops over the appropriate reference plane. Confirm actual fabricator stackup before specifying USB trace geometry.
4. Follow each package's thermal pad, solder-mask and segmented paste recommendations. Avoid open untented thermal vias that drain paste unless the assembler specifically accommodates them. Verify available QFN/VSON/WSON assembly and inspection capability; external-core DBV simplifies inspection but needs thermal qualification.
5. Reconcile Hirose's 250 °C/two-cycle limit, LED handling/reflow requirements, module moisture label and GCT shell soldering with the assembler. USB shell stakes are through-hole; plan their solder process separately from SMT battery/SH contacts.
6. Retain primary reference layouts for switching components and crystal. The selected external core avoids the RP internal inductor orientation issue, but does not remove TPS switching-layout or core-LDO thermal constraints.
7. Before production, measure USB100 startup input draw; USB500 radio+SD+charge behavior; minimum-BAT 3V3 regulation; core 1V1 startup/transients/temperature; PSRAM cold/warm resets; NTC open/short/trip behavior; actual BAT ADC error; LED SYS/VIH margin; and RF performance with the intended enclosure, card and battery.
8. No substitute pack, generic 10 kΩ thermistor, connector cable or unqualified LED revision should be accepted just because its headline value matches. Maintain pack protection/NTC curve and cable pin order in the purchasing documents.

## 11. Primary-source URLs and verification record

Page numbers refer to printed datasheet pages where available; PDF viewers may count the cover separately. Manufacturer URLs can serve updated revisions later, so record the retrieved revision when freezing the design.

| ID | Primary source, retrieved document / relevant locations | URL |
|---|---|---|
| R1 | Raspberry Pi RP2350 datasheet; QFN60 pinout, electrical limits, §6.3.7 Figure24 external DVDD; external-supply figure around printed p409 | https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf |
| R1a | Exact resolved RP datasheet asset inspected | https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008373-DS-3-rp2350-datasheet.pdf |
| R2 | Raspberry Pi Hardware design with RP2350; revision history Aug24 2026; power, §3 memory/BOOTSEL, §4 crystal, complete QFN60 reference schematic R4-S1 | https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf |
| R2a | Exact resolved hardware-guide asset | https://pip-assets.raspberrypi.com/categories/1214-rp2350/documents/RP-008280-DS-2-hardware-design-with-rp2350.pdf |
| M1 | Winbond W25Q32JV RevK Apr28 2026; pinout p6, QE p17, startup p61, SS package p69, ordering p79 | https://www.winbond.com/resource-files/W25Q32JV%20RevK%2004272026%20Plus.pdf |
| M1a | Winbond primary product/ordering page for SS part | https://www.winbond.com/hq/product/code-storage-flash/qspi-nor/w25q-jv/?__locale=en&partNo=W25Q32JVSSIQ |
| M2 | AP Memory APS6404L Rev2.7 Jan5 2024; pinout p4, ordering p7, startup p10, decoupling p25, AC limits p27 | https://www.apmemory.com/en/downloadFiles/032411212009597427 |
| M2a | AP Memory SPI/QSPI IoT RAM primary catalog | https://www.apmemory.com/en/product/iotram/SPIQSPI |
| E1 | Espressif ESP32-C3-WROOM-02 datasheet v1.7; pinout pp10–11, straps/reset pp12–15, power/current pp22–23, layout drawings | https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf |
| E1a | Resolved Espressif document host | https://documentation.espressif.com/esp32-c3-wroom-02_datasheet_en.pdf |
| E2 | ESP-AT latest C3 hardware connection table: UART1 GPIO6RX/7TX/5CTS/4RTS; UART0 GPIO20RX/21TX | https://docs.espressif.com/projects/esp-at/en/latest/esp32c3/Get_Started/Hardware_connection.html |
| E2a | Independently checked release-v3.2.0.0 table, same mapping | https://docs.espressif.com/projects/esp-at/en/release-v3.2.0.0/esp32c3/Get_Started/Hardware_connection.html |
| E2b | Independently checked release-v2.4.0.0 table, same mapping | https://docs.espressif.com/projects/esp-at/en/release-v2.4.0.0/esp32c3/Get_Started/Hardware_connection.html |
| P1 | TI BQ24074 family SLUS810N, revised Oct2021; BQ24074 pin column, USB limit truth table, ISET/ITERM/TMR, TS bias/thresholds and Figure9-9 | https://www.ti.com/lit/ds/symlink/bq24074.pdf |
| P2 | TI TPS63030/31 SLVS696D, revised Apr2020; p3 exact DSK pinout, fixed FB wiring, application components, current capability and layout | https://www.ti.com/lit/ds/symlink/tps63031.pdf |
| P3 | TI TLV758P SBVS351D, revised Oct2023; Figure4-2 DBV pinout, VFB, capacitance/thermal data; package addendum confirms PDBVR/PDRVR | https://www.ti.com/lit/ds/symlink/tlv758p.pdf |
| P5 | TI TPS63070 primary datasheet; optional different-package higher-current alternative | https://www.ti.com/lit/ds/symlink/tps63070.pdf |
| P6 | TI TLV9001 family SBOS833R; Figure6-1 p7 DBV buffer pinout | https://www.ti.com/lit/ds/symlink/tlv9001.pdf |
| C1 | GCT USB4105 primary mechanical/contact drawing, B4 Dec18 2023, two pages | https://gct.co/files/drawings/usb4105.pdf |
| C2 | Hirose DM3AT-SF-PEJM5 primary product page, CL0609-0031-0-00 | https://www.hirose.com/ja/product/p/CL0609-0031-0-00 |
| C2a | Hirose English drawing content via manufacturer document endpoint, EDC-325165-00-00, six pages | https://www.hirose.com/ja/product/p/CL0609-0031-0-00/documents?path=%2Fapi%2Fv1%2Fproducts%2FCL0609-0031-0-00%2Fdocuments%2Fdrawing_2d%2Fcontent%3Flang%3DEN |
| C3 | JST SH primary catalog/product page | https://www.jst-mfg.com/product/index.php?series=231 |
| C3a | JST SH primary drawing/catalog PDF | https://www.jst-mfg.com/product/pdf/eng/eSH.pdf?new=1 |
| C4 | JST PH primary catalog/product page | https://www.jst-mfg.com/product/index.php?series=199 |
| C4a | JST PH primary drawing/catalog PDF | https://www.jst-mfg.com/product/pdf/eng/ePH.pdf?new=1 |
| L1 | Worldsemi WS2812B-2020-V6 primary product page, 3.3–5.5 V | https://www.world-semi.com/products/ws2812b-2020-v6.html |
| L1a | Worldsemi V6 datasheet, filename1.0/internalV1.4; scanned pin/mechanical and electrical pages visually inspected | https://www.world-semi.com/downloads/datasheets/en/ws2812b-2020-v6-1.0.pdf |
| L2 | TI SN74AHCT1G125 primary datasheet; DCK pinout and 4.5–5.5 V operating supply | https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf |

Verification boundaries: primary PDFs/HTML above were fetched and read, with scanned/vector diagrams visually inspected where text extraction did not establish pad placement. Local stock KiCad symbols/footprints were read only for pad-map comparison. Abracon crystal/inductor selection and reference component values are established by Raspberry Pi's primary hardware guide; no independent Abracon ordering-stock claim is made. Superseded Molex/SK6812 exact primary drawings, a specific protected pack/NTC curve, the reported separate Worldsemi 0.6×VDD upgrade notice, and current distributor/assembler stock remain unverified.

## 12. Appended revision — UART, EN2, ADC buffer, TPS63070 and LED supply

2026-11-10 follow-up. **This appendix supersedes conflicting recommendations above.** Only research.md was appended; no circuitry files were edited. TPS63070 and Coilcraft primary PDFs were fetched again for this revision. Exact selected substitutions and unresolved requirements are distinguished below.

### 12.1 Revised GPIO allocation and BQ suspend controls

The ESP-AT UART table [E2] and C3 module pad map [E1] establish these connections:

| RP GPIO / physical pad | Net / function | Destination or source |
|---|---|---|
| GP20 / 32 | UART1 TX | → C3 GPIO6 RX / module pad5 |
| GP21 / 33 | UART1 RX | ← C3 GPIO7 TX / module pad6 |
| GP22 / 34 | UART1 CTS | ← C3 GPIO4 RTS / module pad3 |
| GP23 / 35 | UART1 RTS | → C3 GPIO5 CTS / module pad4 |
| GP18 / 29 | RADIO_EN | → C3 EN / module pad2; 10 kΩ pull-down at EN |
| GP19 / 31 | RADIO_BOOT_N | → C3 GPIO9 / module pad8; open drain, 10 kΩ pull-up to 3V3 |
| GP16 / 27 | USB_500_EN / BQ_EN1 | → BQ EN1 / pad6; 100 kΩ pull-down |
| **GP17 / 28** | **BQ_EN2** | → BQ EN2 / pad5; **100 kΩ pull-down**, replacing the hard GND tie |
| **GP13 / 17** | **SD_DETECT_N** | ← Hirose detect pad9; 10 kΩ pull-up; pad10 remains GND |

**GP17 is no longer SD detect.** GP13 was spare and is now the explicit SD-detect reassignment. Charger CHG/PGOOD remain GP10/GP11; LED data remains GP12; other allocations remain as above. ESP UART0 download header remains GPIO20RX/module11 and GPIO21TX/module12, separate from UART1 AT communication. Enable hardware CTS/RTS on the RP and in the actual flashed ESP-AT configuration.

| BQ EN1 (GP16) | BQ EN2 (GP17) | TI mode |
|---:|---:|---|
| 0 | 0 | USB100, default at reset |
| 1 | 0 | USB500, after host permits this load |
| 0 | 1 | Resistor-programmed ILIM mode; avoid accidental selection |
| 1 | 1 | USB suspend |

Recommended sequencing: USB500→suspend sets EN2 high while EN1 stays high; suspend→USB100 clears EN2 first, then EN1. From USB100 to suspend, set EN1 high before EN2, with the shortest controlled interval, and review whether that transient USB500 state is permitted. Prefer an atomic GPIO write for both bits where practical. Maintain the 3.24 kΩ ILIM resistor from BQ12 to GND. The pin controls now allow TI suspend mode, but host compliance still requires firmware/USB-state handling and measured suspend current. With no battery, suspending the input can collapse SYS/3V3 and reset the controller; account for this in resume/re-enumeration behavior.

### 12.2 Selected battery buffer: TLV9001IDBVR

Exact TI DBV pin map is Figure6-1, p7 [P6]; do not substitute the different TLV9001U/TLV9001 SC70 pin map. The revised circuit is:

| Item / pin | Connection |
|---|---|
| Upper divider resistor | BAT → BAT_DIV, **470 kΩ** |
| Lower divider resistor | BAT_DIV → GND, **470 kΩ** |
| Divider capacitor | BAT_DIV → GND, **100 nF**; retained from the original plan |
| TLV9001 pad1 OUT | BAT_BUF; directly to its pad4 IN− |
| TLV9001 pad2 V− | GND |
| TLV9001 pad3 IN+ | BAT_DIV |
| TLV9001 pad4 IN− | BAT_BUF, **feedback before the output resistor** |
| TLV9001 pad5 V+ | 3V3, **100 nF** local supply bypass |
| Output resistor | BAT_BUF → BAT_ADC, **100 Ω** |
| ADC filter capacitor | BAT_ADC → GND, **1 nF** |
| RP ADC endpoint | BAT_ADC → RP GPIO26_ADC0 / pad40 |

This is unity gain, not another 2:1 gain stage. The battery-to-ADC scale remains nominally 2:1. Buffer input bias replaces the RP's much larger input leakage as the divider load; include op-amp offset/bias, divider matching and ADC/reference calibration in the final accuracy budget. The 100 Ω isolates the op-amp from the 1 nF ADC capacitor; that filter has **100 ns RC / approximately 1.59 MHz pole**. It supplies ADC sampling charge and isolates switching transients, but it is not a slow battery averaging filter. The retained 470 kΩ/470 kΩ and 100 nF input filter still has **23.5 ms RC**, approximately 120 ms for five time constants. Ground the filter capacitor close to the ADC return.

Use 0.1% divider resistors and disable RP ADC input pulls. Check the real 3.4 V battery threshold with calibrated measurements and hysteresis under radio load. If future power control turns 3V3 off while BAT remains connected, review TLV9001 input overvoltage/back-power through BAT_DIV; normal operation here keeps the main regulator enabled from SYS. The buffer is not battery protection.

### 12.3 TPS63070RNMR: exact connections and 3.3 V feedback

Primary TI **SLVSC58B**, revised March2019, fetched for this appendix: https://www.ti.com/lit/ds/symlink/tps63070.pdf . Exact ordering addendum confirms **TPS63070RNMR**, adjustable output, **RNM0015A 15-pad VQFN-HR**, approximately **2.5 × 3.0 mm** body. **Not TPS630701**, which is fixed 5 V, and not the former TPS63031 DSK footprint.

**RNM uses enlarged underside power pads 9/10/11; do not invent a generic GND exposed pad16.** Pad9 is L2 and pad11 is L1, both switching nodes; only pad10 is PGND. The package drawing/stencil explicitly distinguishes their solder areas. A generic QFN with a large center pad grounded would be wrong. No exact stock TPS63070 symbol/RNM footprint was found in the inspected local KiCad libraries; the generation task must use a verified device/library definition matching the TI RNM drawing.

| Pad | TI name | Concrete selected net recommendation |
|---:|---|---|
| 1 | PS/SYNC | **GND for forced PWM** initially; alternatively SYS for automatic PWM/PFM power save |
| 2 | PG | 3V3_PGOOD, open drain; optional 100 kΩ pull-up to 3V3, test pad or spare RP input |
| 3 | VAUX | **100 nF to GND only**; internal regulator output, not SYS or 3V3, no external load |
| 4 | GND | Quiet GND return for FB divider/VAUX |
| 5 | FB | Junction of 100 kΩ upper / 32.0 kΩ lower resistors |
| 6 | FB2 | NC, unused voltage-scaling output |
| 7 | VOUT | 3V3, connected with pad8 and output capacitors |
| 8 | VOUT | 3V3 |
| 9 | L2 | Inductor terminal2, switching copper; **not GND** |
| 10 | PGND | GND, short high-current return and vias per layout |
| 11 | L1 | Inductor terminal1, switching copper; **not GND** |
| 12 | VIN | SYS, joined to pad13 and input bypass |
| 13 | VIN | SYS |
| 14 | EN | SYS for always-on operation; not self-powered from 3V3 |
| 15 | VSEL | GND, disables unused feedback scaling |

**PS/SYNC polarity is opposite the earlier TPS63031:** TPS63070 low = forced PWM, high = power save. Forced PWM is the initial recommendation for bounded output accuracy and ripple while qualifying the ADC/USB/RF rail. Its feedback accuracy is ±1% in PWM; power-save accuracy is listed −1%/+3% with VIN ≥3 V, so do not assume that figure guarantees every 2.8 V input case.

Feedback reference is **0.800 V**. Recommended board resistor choice: **Rupper = 100 kΩ, 0.1%, 3V3→FB; Rlower = 32.0 kΩ, 0.1%, FB→GND**. Then VOUT = 0.8 × (1 + 100/32) = **3.300 V nominal**; divider current = 25 µA. TI's approximate table entry **470 kΩ/150 kΩ** gives **3.3067 V**, not exactly 3.300 V; it is a valid reference example, but the lower-impedance 100k/32k choice reduces sensitivity to the specified 100 nA FB leakage and switching pickup. Account for reference accuracy, resistor tolerance, leakage and load/line regulation; 3.300 V nominal is not an exact physical voltage.

Initial component recommendation for **2.2 µH**: **2 × 10 µF** input MLCCs close to VIN/PGND; **2 × 47 µF, preferably 10 V** output MLCCs, with a small local output bypass close to the VOUT/PGND pads if bulk placement warrants it; **100 nF VAUX**. Select actual output capacitors with documented **combined effective capacitance ≥40 µF at 3.3 V**, including tolerance, DC bias and temperature. Increase nominal capacitance if the chosen MLCCs do not meet this. Do not merely copy the old TPS63031 2×10 µF output network.

TI §9.2.2 requires **COUT,effective [µF] ≥10 × L,effective [µH]**. With 2.2 µH +20% tolerance, that alone requires **≥26.4 µF**; the ≥40 µF recommendation gives extra margin for the low-input/high-load condition. TI's 2.2 µH filter table shows higher output-capacitance combinations (68/100 µF nominal under its assumed derating). Keep the divider next to FB and Kelvin-sense 3V3 from the output capacitor. Preserve short switching loops and the exact RNM solder-mask/paste rules.

#### Critical 2.8 V requirement: running versus cold startup

TI p6 explicitly states **VIN ≥3.0 V for startup while VOUT <3.0 V**; after startup with VOUT ≥3.0 V, VIN may fall to **2.0 V**. Thus TPS63070 can be a good **1 A at 3.3 V while already running at 2.8 V** candidate, but it **does not satisfy guaranteed cold boot from a 2.8 V pack**. Actual converter VIN is SYS, slightly below BAT through the BQ path; BAT=3.0 V is not automatically enough either. The input/output headline range must not obscure this condition.

For running at VIN=2.8 V, VOUT=3.3 V, IOUT=1 A, η=90%: average inductor/input current is approximately **1.31 A**; at L=2.2 µH and f=2.4 MHz, ripple is approximately **0.080 A peak-to-peak**, peak ≈1.35 A. Use lower actual SYS, minimum inductance/frequency, efficiency and transient load for final sizing. A ≥4 A saturation target is conservative for this 1 A operating point and provides overload margin, but does not establish a guaranteed output-current rating.

The same nominal point gives TI's boost RHP-zero estimate approximately **172 kHz**, below its recommended 400 kHz threshold. TI therefore calls for additional output capacitance/reduced crossover and qualification at minimum VIN and maximum load. The proposed effective ≥40 µF is a starting design recommendation, not a substitute for stability/load-step validation. TI's 3.6 A typical average input limit is characterized at VIN5 V/VOUT6.5 V; do not label it a guaranteed 3.6 A output or universal low-input current limit.

**Exact alternative if ≥1 A and cold startup at BAT2.8 V are both mandatory: TPS63802DLAR.** Its primary datasheet explicitly specifies **2 A output at VIN ≥2.3 V, VOUT3.3 V**, with startup **VIN >1.8 V**: https://www.ti.com/lit/ds/symlink/tps63802.pdf (SLVSEU9D, Jan2021). It is a **10-pad DLA VSON-HR, 3×2 mm**, different pinout/footprint/control behavior and requires its approximately **0.47 µH** inductor and application network; **do not carry the 2.2 µH TPS63070 network into it**. Recommend TPS63802DLAR for the stricter cold-start requirement. Keep the requested TPS63070RNMR only if the product accepts its ≥3.0 V-at-SYS startup limitation; no schematic substitution is made here.

### 12.4 Coilcraft 2.2 µH comparison and available KiCad footprints

Primary PDFs were downloaded from Coilcraft's own server; product HTML pages encountered a browser challenge and were not used as rating evidence. Manufacturer current specifications below are **25 °C reference measurements**, not guaranteed absolute current ceilings; review temperature derating and actual PCB heating.

| Exact candidate | DCR typ / max | Isat measurement | Irms: 20 °C / 40 °C rise | Decision |
|---|---|---|---|---|
| **XFL4020-222MEC** | 21.35 / 23.50 mΩ | 3.1 A at 10% L drop; 3.5 A at 20%; **3.7 A at 30%** | 6.0 / 8.0 A | Good low DCR, but **does not meet requested ≥4 A saturation** |
| **XAL4030-222MEC** | Not established | Not established | Not established | **Not listed** in current primary XAL40xx table; do not assume purchasable/verified |
| **LPS4018-222MRC** | max 70 mΩ | 2.7 A at 10%; 2.8 A at 20%; **2.9 A at 30%** | 1.5 / 2.0 A | **Does not meet ≥4 A saturation**, less thermal margin and higher DCR |
| **XAL4020-222MEC**, exact replacement recommendation | 35.20 / 38.70 mΩ | **5.6 A at 30% typical L drop** | **4.0 / 5.5 A** | **Choose this for requested 2.2 µH / ≥4 A saturation** |

The current Coilcraft table places **2.2 µH in XAL4020**, while XAL4030 begins at 3.3 µH. This is why changing only the height number in the part code is unsafe. XAL4020-222MEC is ±20%, max height **2.1 mm**, body **4.0±0.3 mm square**. Its 5.6 A saturation figure uses a 30% typical inductance reduction criterion; if the intended requirement means **4 A with ≤10% L reduction**, that must be checked against the manufacturer L-vs-current curve and temperature rather than treating all Isat definitions as equal.

**Installed stock KiCad footprint exists:** `Inductor_SMD:L_Coilcraft_XAL4020-XXX`. Inspected pads: pad1 centered **(−1.185,0) mm**, pad2 **(+1.185,0) mm**, each **0.98×3.40 mm**. This matches the primary land pattern's **2.37 mm center spacing / 0.98 mm width / 3.4 mm length**. Use pad1→L1/RP supply converter pad11, pad2→L2/converter pad9 as a board numbering convention, then reconcile the physical winding-start mark with switching EMI guidance. The part is not diode-polarized. Coilcraft marks the short/start lead and recommends the high-dv/dt connection there; follow its orientation guidance rather than arbitrary placement rotation.

Also found locally: `Inductor_SMD:L_Coilcraft_XAL4030-XXX` and `Inductor_SMD:L_Coilcraft_LPS4018`. **No exact XFL4020-named footprint was found** in the inspected library. XAL/XFL land patterns can look similar, but a verified XAL footprint does not establish XFL body/height/assembly identity. “Available KiCad footprint” here means library availability, **not verified live component inventory**. Obtain stock/lead-time confirmation from Coilcraft or an authorized distributor for **XAL4020-222MEC** before BOM release.

Primary documents:

- XFL4020, Document745, revised **03/10/26**: https://www.coilcraft.com/getmedia/50632d43-da1b-4cdb-8ab4-3029cab51df3/xfl4020.pdf (legacy primary alias https://www.coilcraft.com/pdfs/xfl4020.pdf redirects here).
- XAL40xx, Document806, revised **02/25/26**, ratings p1 and common land pattern p4: https://www.coilcraft.com/getmedia/6adcb47d-8b55-416c-976e-1e22e0d2848c/xal4000.pdf .
- LPS4018, Document435, revised **02/23/22**: https://www.coilcraft.com/getmedia/31b05c96-4c4c-4498-8dbb-fe092de76bad/lps4018.pdf (legacy primary alias https://www.coilcraft.com/pdfs/lps4018.pdf redirects here).

### 12.5 LED: exact map confirmed, supply recommendation

**Confirmed existing KiCad WS2812B-2020 symbol map:** **4 VDD, 3 DIN, 2 GND/VSS, 1 DOUT**. The local symbol was re-read; it matches the Worldsemi V6 diagram already inspected [L1a]. Keep the same electrical pad numbering. The generic KiCad symbol's linked datasheet is an older V1.3 copy, so the BOM and attached primary source must explicitly identify **WS2812B-2020-V6**. Retain the footprint/180° drawing-orientation check from §9.1.

**A nominal 3.3 V fixed rail is not a guaranteed in-range LED supply.** The Worldsemi page, re-fetched for this appendix, gives minimum **3.3 V**. Negative regulator tolerance, trace drop and load transients can take the actual LED below 3.3 V; even TPS63070 PWM ±1% alone allows approximately 3.267 V before other errors. Undervoltage does not automatically mean electrical damage, but specified LED behavior is not guaranteed. Do not raise the shared RP/USB rail casually to solve one LED: USB_OTP_VDD and all connected 3V3 devices have their own supply limits.

The prior SYS connection works within the rated LED range on USB, but goes below 3.3 V as the battery discharges. Firmware blanking at BAT3.4 V does not power-disconnect the IC. **For guaranteed LED supply throughout the intended discharge range, recommend a dedicated, switchable approximately 5 V LED boost rail and a logic shifter.** This supersedes the earlier no-shifter recommendation only if this full-range LED option is adopted. If retaining SYS/direct GPIO to save circuitry, explicitly accept the documented low-battery operation limitation and blank conservatively using calibrated BAT readings and measured SYS sag.

**5 V changes the logic requirement:** at VDD5.0 V, the verified V6 VIH=0.55VDD requires **2.75 V**, exceeding RP's approximately 2.62 V specified VOH minimum; at a positive boost tolerance it is higher still. Therefore **a 5 V boost alone with direct GPIO is not the guaranteed solution**. Exact suitable shifter is the previously researched **SN74AHCT1G125DCKR**, now powered from LED_5V: pad1 /OE→GND, pad2 A←RP GP12, pad3 GND, pad4 Y→330 Ω→LED DIN3, pad5 VCC→LED_5V with 100 nF. Its 4.5–5.5 V supply and 2.0 V TTL VIH make it suitable on the regulated LED rail, unlike the previous SYS4.4 V use. LED pad4→LED_5V with 100 nF, pad2→GND, pad1 DOUT NC.

Exact optional LED boost candidate **TPS61023DRLR**, primary TI SLVSF14B: https://www.ti.com/lit/ds/symlink/tps61023.pdf . It supports startup at **1.8 V**, input up to **5.5 V**, output **2.2–5.5 V**, and true input/output disconnection in shutdown. Supply it from **SYS**; reserve spare **RP GP14/pad18 as LED_PWR_EN**, with 100 kΩ pull-down, if this option is adopted. Its small 6-pad DRL/SOT563 pin map is **1 FB, 2 EN, 3 VIN, 4 GND, 5 SW, 6 VOUT**; inductor connects SYS to SW5. Do not connect SW to the LED.

For a concrete approximately 5 V feedback starting point: **732 kΩ upper / 100 kΩ lower, 0.1%**, giving **4.950 V** with TI's **595 mV PWM reference**, approximately **5.000 V** with its **601 mV typical PFM reference**. The PWM reference limits 580–610 mV imply approximately **4.826–5.075 V** before resistor/regulation/transient errors, fitting both LED and AHCT supply ranges with sensible margin. This IC's reference is **not an exact 0.600 V**. Follow TI's complete inductor/capacitor/stability selection for the optional boost; its typical circuit uses **1 µH**, so do not copy the main regulator's 2.2 µH network blindly. Budget at least the LED's approximately 36 mA full-white load plus shifter and conversion losses.

Hold LED data low before boost enable/disable; avoid a high RP output into an unpowered shifter/LED. Wait for LED_5V to settle, then issue the V6 reset-low interval (>280 µs) and data. Keep this LED boost off during USB100 startup/suspend as required. The additional boost and shifter are **recommended for guaranteed full-discharge LED operation**, not silently instantiated in any design file.
# Final switched LED supply — 2026-11-10

U10 TPS22919DCKR switches VSYS to LED_VDD under PWR_EN, with C45 1uF at IN.
D1, C24 and C36 use LED_VDD; the main 3.296V regulator is unchanged. This prevents
a latched-on RGB state persisting when SW5 disables the logic rails. It does not
remove the V6 LED's 3.3V minimum supply requirement; firmware must blank the LED
near VBAT 3.6V under load and operation below LED_VDD 3.3V is not guaranteed.

Primary source: https://www.ti.com/lit/ds/symlink/tps22919.pdf, SLVSEN5B,
revised May 2019. Verified supply 1.6–5.5V, ON high >=1V / low <=0.35V,
SC70-6 pinout 1 IN, 2 GND, 3 ON, 4 NC, 5 QOD, 6 OUT. NC remains floating.
Section 5 expressly permits QOD directly tied to OUT for internal-resistor
discharge. The local symbol models QOD as passive instead of the stock
open-collector classification because that classification incorrectly conflicts
with OUT power-output during ERC for the manufacturer-approved connection.
No pin numbers or land pattern are changed and no ERC finding is excluded.

