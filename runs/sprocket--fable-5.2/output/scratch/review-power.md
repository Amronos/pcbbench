# Power block review, RP2350 dev board

Source: `scratch/rp2350-devboard.net`. Datasheets: BQ24074 (SLUS810N, local copy), TLV757P (SBVS322C), USBLC6-2 (DS4260 rev 7), RP2350 datasheet (section 14.9, appendix D.5.1), part numbers from `scratch/parts-candidates.md`.

Result: no must-fix found. The charger straps, pinouts and USB-C wiring are correct. Five should-fix items and some notes follow.

## Findings

| # | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| 1 | Should fix | VBUS and +BATT sit on adjacent header pins, with GND next to +BATT. A probe slip or solder bridge puts 5 V on the cell and on U4 BAT, or shorts the cell. | J6.1 = `VBUS`, J6.2 = `+BATT`, J6.3 = `GND`. BQ24074 abs max BAT = 5 V (8.1). VBUS can be 5.25 V or more. No fuse between J2 and J6.2. | Put GND between them, or drop +BATT from the header, or feed J6.2 through a small PTC or 1 kΩ sense-only resistor. |
| 2 | Should fix | GPIO28 is driven above its absolute maximum when 3V3 is off and a battery is fitted. | `/VBAT_SENSE` = `+BATT`/2, up to 2.1 V, through R13 100 kΩ. With `/EN` low the TLV757P pulls 3V3 to ground through 120 Ω, so IOVDD = 0 V. GPIO26-29 are "Standard" pads, limit IOVDD + 0.5 V (table 1680). They are not fault tolerant. Section 6.1.4 note says ADC inputs above IOVDD leak through the ESD diodes. Current is limited to about 15 µA by R13. | Switch the divider top with a P-FET that is on only when 3V3 is up. If you accept it instead, record why: the current is 15 µA and the original Pico does the same on GPIO29. |
| 3 | Should fix | The divider drains the battery all the time. | R13 + R14 = 200 kΩ on `+BATT`: 21 µA at 4.2 V. BQ24074 sleep current is 6.5 µA max and the LDO shutdown current is 1 µA max, so the divider is about 75% of the off-state drain. | Same P-FET as item 2, or raise to 1 MΩ / 1 MΩ and keep C30. |
| 4 | Should fix | The brief says VSYS is on a header pin. It is not. | `/VSYS` nodes: C2, C4, R10, R11, R12, U4.10, U4.11, U5.1 only. J6 has VBUS, +BATT, GND. J7 has 3V3, EN, RUN, GND. | Decide which is intended. If VSYS should be exposed, it can replace +BATT on J6.2, which also solves item 1. |
| 5 | Should fix | With no battery the board can brown out. USB500 mode limits the input to 450 to 500 mA and nothing can supplement it. | U4 EN2 = GND, EN1 high: IINmax 450/475/500 mA (8.5). Load is RP2350 + RM2 Wi-Fi transmit + microSD + WS2812, all through a linear LDO, so the 3V3 current equals the VSYS current. When the limit is hit, OUT falls (9.3.4.1.2). | Decide if no-battery operation is supported. If yes, add 22 to 33 µF on `/VSYS` (stay at or below 47 µF total on OUT) and measure peak current. Do not raise the limit above 500 mA unless you read the CC voltage, because 5.1 kΩ Rd alone only entitles the board to default USB current. |
| 6 | Note | 3V3 leaves regulation below about 3.5 V battery. Nothing disconnects a low battery. | VSYS = VBAT minus up to 100 mΩ × I (VDO(BAT-OUT)). TLV75733 dropout is 425 to 475 mV max at 1 A, so about 0.2 V at 400 mA. The '74 variant has no SYSOFF and no battery undervoltage cutoff. `/EN` goes only to the header, so firmware cannot switch the LDO off. | Use a protected cell. In firmware, stop Wi-Fi and SD writes below about 3.4 V. Flash, PSRAM and SD need 2.7 V. I did not check the RM2 minimum. |
| 7 | Note | The brief lists a SYSOFF strap. The BQ24074 has none. | Pin 15 is ITERM on the '74 (table 7-1). SYSOFF exists on the '75 and '79 only. U4.15 is unconnected, which selects the default 10% termination, about 49 mA. | Nothing to change. Switch to BQ24075 only if you want a battery disconnect, and note its OUT is 5.5 V, above the LDO's 5.5 V recommended input limit. |
| 8 | Note | ILIM resistor R5 has no effect in the strapped mode. | R5 = 1.5 kΩ gives 1610/1500 = 1.07 A, but ILIM is used only with EN2 = 1, EN1 = 0. | Keep R5 fitted: an open ILIM disables charging (table 7-1). |
| 9 | Note | The real charge current will be below 494 mA. | Charge plus system current share the 475 mA typical input limit. DPPM cuts the charge current and slows the safety timer in proportion (9.3.5.6). | None. Use a cell of 500 mAh or more so 494 mA stays at or below 1C. |
| 10 | Note | VBUS net is not 28 V tolerant even though U4 IN is. | U6.5 on `VBUS` breaks down at 6 V min. EN1 sees 0.425 × VBUS through R8/R9 and the internal 285 kΩ, so it passes 7 V abs max at 16.5 V. C1 is 25 V. | Label the VBUS header pin as 5 V only. |
| 11 | Note | VBUS header pin connects straight to the USB connector. | J6.1 on `VBUS` with J1 A4/A9/B4/B9, no diode. 5 V fed into the header back-feeds a connected host. On battery the pin is not a 5 V output. | Document it, or add a Schottky if the header is meant as a second 5 V input. |
| 12 | Note | Do not feed 3V3 from the header when VSYS is absent. | TLV757P abs max VOUT = VIN + 0.3 V. Reverse current flows through the pass FET body diode (7.1.4). | Document it. |
| 13 | Note | Firmware cannot tell if USB is present. On battery, an enabled D+ pull-up also lifts the `VBUS` net to about 2.7 V through U6. | No GPIO on `VBUS` or `/~{PGOOD}`. Path: USB_DP 1.5 kΩ pull-up, R3, U6 I/O1 upper diode, U6.5. Load there is R8 + R9 = 200 kΩ, so about 13 µA. It stays below the 3.3 V UVLO of U4, so U4 ignores it. | Optional: route a VBUS divider or `/~{PGOOD}` with a 3V3 pull-up to a spare GPIO. RP2350 has a `usb_muxing_vbus_detect` function. |
| 14 | Note | Battery has no reverse-polarity protection. | J2.1 = `+BATT`, J2.2 = GND, which matches `scratch/jst-polarity.md`. BAT abs min is -0.3 V. | Silk "+" and "-" at J2. A P-FET is optional. |
| 15 | Note | Green LED is dim and goes out in supplement mode. | Wurth 150060GS75000 has Vf about 3.2 V. (4.4 - 3.2) / 2.2 kΩ = 0.55 mA. If OUT drops to battery voltage the LED has no headroom. | Acceptable. Use a 2 V green LED if you want it brighter. |
| 16 | Note | RP2350 A2 erratum E9 affects `/VBAT_SENSE` if the digital input is left enabled. | Source impedance is 50 kΩ. E9 leakage is about 120 µA towards 2.2 V (D.5.1). | Call `adc_gpio_init(28)` so the input buffer is off. |

## Plug order and supply states

| Case | Behaviour | Verdict |
|---|---|---|
| Battery only | Q2 on, VSYS = VBAT minus up to 100 mV/A. `/EN` pulled up by R12, LDO starts at 1.3 V. Both LEDs off, because PGOOD and CHG are high impedance. | OK, see item 6 |
| Battery first, then USB | PGOOD low after 1.2 ms, EN1 rises with VBUS, VSYS steps to 4.4 V, charging starts. | OK |
| USB first, no battery | Q1 starts at 100 mA until OUT passes 0.9 V, which is before the LDO UVLO, then 475 mA. BAT charges C3 to 4.2 V, terminates, then cycles in battery detection. CHG is high impedance for "battery absent" (table 9-2). `/VBAT_SENSE` reads a false 3.6 to 4.2 V. | Works, see item 5 |
| USB first, then battery | Detection finds the cell and charging starts. | OK |
| USB removed, battery present | OUT falls to VBAT after tDGL(NO-IN) = 20 ms. The LDO holds 3.3 V if VBAT is above about 3.5 V. | OK |
| `/EN` low, battery present | 3V3 off and discharged. GPIO28 is still driven. | Items 2 and 3 |
| Battery-only cold start | C2 + C4 = 11 µF charge through Q2 well inside the 250 µs short-circuit deglitch. Total behind OUT is about 36 µF including the 3V3 rail, below the 47 µF limit. | OK |

## Checked and correct

- BQ24074RGT pin map against table 7-1, '74 column: 1 TS, 2/3 BAT, 4 CE, 5 EN2, 6 EN1, 7 PGOOD, 8 VSS, 9 CHG, 10/11 OUT, 12 ILIM, 13 IN, 14 TMR, 15 ITERM, 16 ISET, 17 pad to GND.
- ISET: R6 1.8 kΩ, 890 / 1800 = 494 mA, inside the 590 Ω to 8.9 kΩ range.
- Input limit: EN2 = GND, EN1 = 2.1 V at VBUS 5 V and 1.85 V at 4.35 V, above VIH 1.4 V. USB500 mode, 450 to 500 mA.
- TMR open: default timers, 18000 s = 5 h charge and 30 min precharge.
- TS: R7 10 kΩ × 75 µA = 0.75 V, inside the 0.3 V to 2.1 V window, and the value the datasheet specifies.
- CE to GND enables charging. No BQ24074 input is left floating except TMR and ITERM, which the datasheet allows.
- Capacitors: IN C1 10 µF 25 V (1 to 10 µF required, and within the USB 10 µF limit). OUT C2 10 µF 25 V + C4 1 µF 10 V (4.7 to 47 µF). BAT C3 10 µF 25 V (4.7 to 47 µF). LDO input shares C2/C4, output C5 10 µF + C6 4.7 µF 6.3 V (1 to 200 µF). All voltage ratings are above the rail maximum.
- LEDs: R10/R11 2.2 kΩ from VSYS give 0.55 mA and about 1.1 mA. The pins are specified at 5 mA with 15 mA abs max.
- TLV75733PDBV pin map: 1 IN, 2 GND, 3 EN, 4 NC, 5 OUT. EN pulled to VSYS by R12 100 kΩ, so EN never exceeds VIN. VSYS max 4.5 V against 5.5 V recommended and 6 V abs max. VIH 1.0 V, VIL 0.3 V.
- LDO heat: (4.4 - 3.3) V × 0.4 A = 0.44 W, about 44 °C rise at roughly 100 °C/W for SOT-23-5.
- USB-C: R1 and R2 5.1 kΩ separately on CC1 (A5) and CC2 (B5). A4/A9/B4/B9 to VBUS. A1/A12/B1/B12 and shell to GND. A6 + B6 joined as D+, A7 + B7 joined as D-. SBU pins open. Footprint pad names match.
- USBLC6-2SC6: pins 1 and 6 on D+, pins 3 and 4 on D-, pin 2 GND, pin 5 VBUS. It sits on the connector side of R3/R4 27 Ω. D+ goes to U1.52 USB_DP and D- to U1.51 USB_DM.
- ADC level when powered: 2.1 V max at GPIO28, below IOVDD. C30 100 nF with 50 kΩ gives a 5 ms time constant.

## Not checked

- PCB layout: thermal pad vias for U4, U6 placement relative to J1, trace widths.
- DC-bias derating of the 10 µF 0603 parts. Expect roughly half the nominal value at 4.4 V. Confirm in Murata SimSurfing that OUT and BAT stay near 4.7 µF.
- Nothing was measured. All results come from the netlist and datasheets.
