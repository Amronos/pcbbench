# PCBWay assembly and first-article instructions

Revision A is a fully routed, physically untested first-article candidate, not approved for manufacture. Core-power and ESD PCB repairs and metadata/netlist synchronization are complete. Final root ERC and DRC report zero findings, zero opens and zero schematic-parity findings. The live BOM validates all 92 fitted components; the final assembly audit reports zero blocking and advisory findings. Supplier process confirmation, USB impedance review and a test plan are required before ordering. The board has not been manufactured, powered, or measured.

Use the candidate's `assembly/BOM.csv`, `assembly/placement.csv`, F/B assembly PDFs/PNGs and schematic PDF to quote the build. Follow [the release checklist](FABRICATION.md#release-checklist) before ordering. Candidate generation needs no custom approval inputs. `FIRST_ARTICLE` labels an untested candidate, not order or production approval. Top/isometric renders and a bottom render when needed are visualization references, not mechanical certification. Optional 3D model binaries are excluded.

## Procurement and assembly

1. PCBWay sources and assembles all 92 fitted BOM components, SMT and through-hole. No part is consigned by the customer, there are no DNP parts, and the user must not need to purchase or solder fitted components.
2. Fit SMT components on the side specified by the actual placement file's `Side` field. C6 is bottom-side 0603, 22 µF Murata `GRM188R61A226ME15D`, at (57.8, 49.1) mm. C20 is bottom-side 0201, 100 nF Murata `GRM033Z71C104KE14D`, at (57.9, 52.75) mm. Quote both-side assembly. Solder every exposed ground/thermal pad using matching F/B paste and PCBWay's stencil process.
3. Fit and solder the J3, J6 and J7 through-hole pin headers as part of the same order, by selective or hand soldering after reflow. Solder the USB-C shell tabs and the microSD and JST mechanical pads as well. Include the through-hole work in the assembly quote.
4. Test points, mounting holes and fiducials are PCB features, not purchased components. Keep test-pad and fiducial surfaces clean.
5. Follow the approved assembly drawings and pad 1 markings, not silkscreen alone. Verify L1's marked orientation against the reviewed regulator schematic and final footprint.
6. U1: source production RP2350A, A4 preferred. Reject unidentified/early engineering samples. U2 must be W25Q128JVSIQ with the quad-enable ordering option. U3 must be the 3.3 V SOP-8 `-SN` variant, not a 1.8 V part or USON package.
7. D1 must be Worldsemi WS2812B-V6, 5050. Do not substitute older generic WS2812B parts. The radio must be `ESP32-C3-WROOM-02-N4` with onboard antenna, not the `02U` external-antenna module. U8 must be `MAX17048G+T10` in the 2 × 2 mm TDFN-8 package, DigiKey product ID `3758921`. Do not fit the WLP `MAX17048X` or the 2-cell MAX17049.
8. Connector substitutions require approval of footprint, pin numbering, mating direction and mechanical drawing. Passive substitutes must preserve value, tolerance, voltage rating, effective capacitance under DC bias and footprint. Do not substitute inductors based on inductance alone.
9. Maintain the radio overhang and keep antenna area clear of adhesive, metal fixtures and packaging that bends the module. Use ESD-safe handling and observe each part's moisture/reflow limits.
10. Supply first-article photos of top, bottom, connector edges, radio overhang and the fine-pitch IC solder joints before the remaining assembly batch. AOI and X-ray of the exposed-pad ICs are requested.

The external LiPo pack, microSD card, USB cable and programming fixtures are test accessories, not fitted board components. Quote any required test accessories as supplier-provided items, not customer purchases. No application firmware binary is included or approved for programming.

## C6 capacitance qualification

C6 changed to a 22 µF, 10 V, ±20%, X5R 0603 part. The [Murata ratings sheet](https://www.farnell.com/datasheets/2047978.pdf) identifies `GRM188R61A226ME15D`. The design review used the official [SimSurfing viewer](https://ds.murata.com/simsurfing/mlcc.html?partnumbers=%5B%22GRM188R61A226ME15%22%5D) with 10 mVrms excitation:

| DC bias | Temperature | Typical capacitance |
|---|---:|---:|
| 3.3 V | 10 °C | 7.691 µF |
| 3.3 V | 25 °C | 7.956 µF |
| 3.3 V | 40 °C | 8.111 µF |
| 3.6 V | 10 °C | 7.094 µF |

The engineering allowance at 3.3 V is `7.956 × 0.8 × 0.85 × 0.9 = 4.869 µF`: nominal tolerance, X5R temperature allowance and a 10% engineering aging reserve applied to the 25 °C typical value. At 3.6 V, the 10 °C typical value gives `7.094 × 0.8 × 0.9 = 5.108 µF`; temperature is already included in that sample. Typical ESR is 2.83 mΩ at 1 MHz to 12.78 mΩ at 5 MHz.

These typical curves and engineering reserves support part selection, not a manufacturer-guaranteed minimum. Confirm capacitance, regulator startup, stability and transients on the assembled first article. Keep battery charging supervised at 10–40 °C.

## Staged checks

The following is a proposed plan, not measured results or ordering approval. Review limits and procedures for the repaired layout and approve test firmware before testing. Start the approved first article without a battery. Do not proceed to a production batch until its results have been reviewed.

| Stage | Procedure | Expected result |
|---|---|---|
| Unpowered | Inspect orientation, solder bridges, headers and battery polarity. Measure resistance of VBUS, BAT, SYS and 3V3 to GND. | No hard shorts. Capacitor charging may change resistance readings. |
| USB startup | Apply 5.0 V to USB-C with a 100 mA source limit, no battery. | Radio held in reset, charging disabled. SYS about 4.4 V, 3V3 within regulator tolerance, core about 1.1 V. Stop on excess current, heating or oscillation. |
| Bootloader | Hold RP BOOT and press/reset power. Connect to a USB host. | RP2350 UF2 bootloader enumerates. This does not test PSRAM or radio. |
| Processor/memory | Load a reviewed test firmware through USB or SWD. Verify flash ID and a destructive PSRAM write/read test outside firmware storage. | 16 MB flash and 8 MB PSRAM accessible. Check clock and PSRAM refresh timing. |
| USB current control | Test firmware starts in USB100 with radio/charging off, then selects USB500 only after configuration. | Source draw within the selected input limit. Record suspend behavior separately. |
| Battery | Use a known protected 1S 400 mAh LiPo pack or a four-quadrant battery simulator. Confirm J2 pin 1 GND, pin 2 BAT first. Enable charging in firmware. | Charge current 91–114 mA (102.8 mA nominal, R11 = 8.66 kΩ) when there is enough input headroom. About 4.2 V regulation at completion. Safety timer 6.74–11.46 h (9.08 h nominal, R14 = 68.1 kΩ). No abnormal temperature. |
| Fuel gauge | Read the MAX17048 at 7-bit I²C address 0x36 on GPIO20 (SDA) and GPIO21 (SCL), 100 kHz. Compare VCELL with a DMM at the BAT test point. | Device responds at 0x36. VCELL agrees with the DMM within the gauge's datasheet accuracy. SOC is read back. |
| ADC0 | Apply a known voltage between 0 V and 3.3 V to J6 pin 5 and read GPIO26 / ADC0. | Reading tracks the applied voltage. |
| Power-up and leakage | Check PSRAM cold starts and repeated power cycles, including the data-low initialisation deviation. Measure gauge-bus leakage with BAT present / 3V3 off and with USB present / pack disconnected. | Record initial pin states, memory-test results and leakage currents. Reviewer approves the measured behavior before production. |
| Power path | Insert/remove USB while operating from battery. Exercise radio and SD at low battery voltage. Scope SYS, 3V3 and core. | No resets, large dips, sustained oscillation or overheating at the approved load. Determine the maximum supported concurrent load. |
| Radio | Program a reviewed ESP-AT/ESP-IDF image through J3. Enable EN and command UART/RTS/CTS. Test Wi-Fi and BLE. | Commands and both radio modes work. Verify range away from metal and inside the intended enclosure. |
| SD | Insert a known microSD, check active-low detect, create/read/verify a file over SPI. | Correct detect and reliable read/write. Begin at ≤10 MHz SPI. |
| I²C | Attach a known 3.3 V Qwiic device and scan/read it at 100 kHz. | Correct pinout and successful transactions. |
| RGB | Send red, green, blue and low-brightness white to D1. | Correct GRB ordering and no startup flicker. |
| Final | Record test firmware hashes, pack type, supply current, scope captures, temperatures and failures. | Reviewer approves the first article before production. |

First-article approval is separate from production validation. Record the supported loads and operating limits, and obtain a separate production approval. These checks do not establish USB suspend compliance, controlled impedance, ESD immunity, EMC or product safety certification. The board has no reverse-battery protection or cell temperature sensing: the pack has no thermistor and R13 is a fixed 10 kΩ TS resistor. Do not describe it as a temperature-monitored charger. Charge only under supervision.

R2 is 1.8 kΩ to hold PSRAM CS high against GPIO0's reset pull-down. R20/R21 are 3.3 kΩ gauge-bus pull-ups, targeting 300 ns rise time at approximately 106 pF maximum bus capacitance. Validate rise time with the intended header wiring and peripherals.
