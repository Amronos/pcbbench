# PCBWay assembly instructions — Aster2350 revision A

## Scope of quotation

Quote **turnkey component procurement, PCB fabrication, stencil, assembly of every BOM line, AOI/X-ray, and electrical bare-board testing**. No customer-supplied/consigned electronic parts are assumed. Order the exact manufacturer part numbers in `BOM.csv`; this is not an LCSC-only design. Source through manufacturer-authorized distributors where appropriate. Verify stock/lead times when quoting; they have not been reserved.

All purchased parts are fitted. There are **no DNP components, loose headers, user-soldered parts, or alternate assembly variants**. TP pads, mounting holes, and fiducials are PCB features and deliberately excluded from the purchased-parts BOM. The battery, USB cable, microSD card, external Qwiic devices and debug probe are external accessories, not board components.

## PCB specification

| Parameter | Requirement |
|---|---|
| Outline | 80.00 × 65.00 mm; use Edge.Cuts, not silkscreen |
| Layers, top to bottom | F.Cu / In1.Cu (GND) / In2.Cu (3.3 V pour plus signal routing) / B.Cu |
| Thickness | 1.60 mm nominal, ±10% |
| Material | FR-4, Tg ≥150°C; lead-free compatible |
| Copper | 35 µm nominal finished copper on all four layers |
| Finish | ENIG |
| Mask / legend | Green mask, white legend, both sides |
| Electrical limits | 0.10 mm minimum track/space; do not round to a coarser rule |
| Ordinary vias | 0.60 mm land, 0.30 mm finished hole, 0.15 mm annular ring |
| Local processor escape | One conventional 0.50 mm land / 0.20 mm finished-hole via, 0.15 mm annular ring; no laser drilling |
| USB controlled impedance | 90 Ω differential ±10%, F.Cu to continuous In1.Cu ground |
| Nominal USB geometry | 0.15 mm width, 0.15 mm edge-to-edge spacing; ~0.10 mm F.Cu–In1 dielectric |
| Nominal stack | 35 / 100 / 35 / 1240 / 35 / 100 / 35 µm copper/dielectric/copper…; mask additional |
| Testing | 100% electrical continuity/isolation against IPC-D-356 |
| Plated slots | J1 USB-C shell slots, specified in the plated drill file |
| NPTH | Four 2.70 mm mounting holes and USB connector locating holes |

The stack is a **requested nominal stack**, not a measured impedance model. PCBWay must confirm its actual prepreg, finished copper and dielectric constant, solve the USB impedance, and provide an impedance coupon/report. Small controlled-impedance trace-width adjustments are acceptable if they preserve clearances and the USB routing topology; no routing, component, net or outline changes without design review. Maintain solid In1 ground underneath the USB route. The 1 mm bottom-side USB polarity-merge link is a short local crossover, not the main controlled-impedance route.

There are **no blind/buried vias, HDI microvias, castellations, or filled/capped via-in-pad requirements**. Thermal ground connections use conventional through vias outside the open solderable pads. Keep the antenna area free of copper on every layer and do not add panel rails, copper thieving, stickers, metal hardware, test fixtures or fiducials in that area. Manufacturer panelization is permitted outside the board; depanelize the antenna edge cleanly without damaging the module. No panel design is prescribed.

## Assembly process

- Top-side SMT reflow, lead-free SAC process. Use `F-Paste` for the top stencil. No bottom-side electronic components.
- Factory solder the three THT components: battery connector J2 and GPIO headers J6/J7. Solder all four J1 USB-C plated shell tabs as well as its SMT contacts. Selective or careful manual soldering by PCBWay is acceptable; none is left to the user.
- J1, J2, J3, J4, J5, J6 and J7 are all installed, not supplied loose. USB opens through the bottom edge; microSD opens through the right edge; the other connectors face upward.
- QFN/WSON exposed ground pads on U1, U4, U6 and U7 and the module's central ground pad on U9 must be soldered. Use the supplied segmented paste apertures. Do not enlarge them into full-area apertures. X-ray U1/U4/U6/U7/U9 ground joints and check for bridges/voiding according to the agreed IPC class.
- Inspect 0.4 mm-pitch RP2350 leads and 0.5 mm-pitch USB-C contacts carefully. Use the local pad shapes exactly, not a generic QFN60 or USB-C footprint.
- Do not substitute APS6404L with 1.8 V memory or a different package. U3 is **SOP-8/150 mil**; U2 is **SOIC-8/208 mil**. U9 must be the **WROOM-02-N4 with PCB antenna**, not WROOM-02U or MINI.
- D1 pin numbering is unusual: 1 DOUT, 2 GND, 3 DIN, 4 +5V_RGB. Observe the pin-1 dot on the footprint/assembly drawing. Do not rotate it based on appearance alone.
- L1 and L2 are shielded inductors. L1 is the external TPS63060 inductor, not an RP2350 on-chip-regulator inductor; no winding-polarity requirement applies here.

## Coordinates and orientation

`placements.csv` is the assembly placement file. Units are mm, origin is the PCB bottom-left corner, X right, Y up, rotation is KiCad's positive-counterclockwise convention viewed from the top, and every BOM part is on the top side. `placements-THT.csv` separates the three through-hole bodies for selective/manual solder planning. Native KiCad files and assembly drawings are provided as cross-checks. Coordinates are footprint datums; verify pin 1 and package datum against the assembly drawing before programming the placement machine. Do not rotate mirrored bottom-side graphics as if they were bottom-side components.

## Programming and first article

The design includes boot/debug/programming access but **does not include production firmware binaries**. An empty RP2350 flash can enter the RP2350 USB ROM loader using BOOTSEL/RESET. U9 requires an ESP32-C3 firmware build configured for the UART and flow-control pins documented in the README. Programming and functional-test services require separately approved images and a agreed test script/fixture; do not infer that the module ships with the correct AT firmware.

Before any volume assembly, obtain a PCBWay DFM/BOM confirmation and build/test a small first-article lot. Request a hold for approval after that lot. No physical board has been built, characterized, EMC-tested or safety-certified by the design author. The supplied ERC/DRC/netlist checks are CAD checks, not functional validation.

## First-article checklist

1. Inspect polarity, fitted MPNs, solder joints, exposed pads and connector retention. Test power-to-ground resistance before powering; do not use a LiPo for the initial short-circuit test.
2. Feed 5.0 V to USB with a current-limited bench source and no battery. Check VSYS ≈4.4 V, main rail ≈3.31 V and core rail ≈1.10 V. Radio and RGB should remain off. Confirm USB boot enumeration in both cable orientations.
3. Load RP2350 diagnostic firmware. Exercise SWD, reset, flash identification/read/write, and all 8 MiB PSRAM at conservative clocks; test QSPI timing before enabling higher speeds.
4. Enable the radio load switch, verify its switched rail, program the ESP32-C3 and test bidirectional UART/CTS/RTS, Wi-Fi traffic and Bluetooth LE advertising/connection. Test RF sensitivity/range with the intended enclosure.
5. Exercise microSD initialization/read/write/card detect, 400 kHz I2C with a 3.3 V Qwiic peripheral, every GPIO header pin and all RGB colors. Keep external loads within the stated budget.
6. With a battery simulator/protected test pack and 10 kΩ NTC, verify ~250 mA fast-charge limit, termination, USB100/USB500 input limits, power-path changeover and battery ADC calibration. Test NTC open/short/hot/cold inhibition. Test USB removal under combined radio/SD load. No temperature sensing resistor is pre-fitted across TS: the actual pack NTC is required.
7. Measure load transients, rail ripple, regulator/charger temperatures, USB suspend current and charge safety behavior. Record test firmware versions, silicon revision, stack/coupon result and all measured limits before releasing volume production.
