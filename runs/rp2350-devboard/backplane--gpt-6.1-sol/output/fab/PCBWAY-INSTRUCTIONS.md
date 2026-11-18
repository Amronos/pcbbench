# PCBWay turnkey manufacturing instructions — RP2350 Connect rev A

Consult RELEASE-STATUS.md before production. This order scope is PCB fabrication plus procurement and assembly of **all 118 BOM components**. No DNP, consigned, or customer-supplied components. H1–H4 are unplated mounting holes; FID1–FID3 are PCB copper fiducials, not purchased parts. Batteries, cards, cables, mating housings, and programmers are not fitted accessories.

## PCB fabrication

- Finished dimensions 85.00 × 70.00 mm, rectangular outline as Edge.Cuts; four 2.7 mm NPTH mounting holes for M2.5 hardware.
- Six layers, 1.6 mm finished thickness, FR-4 Tg ≥150 °C, lead-free compatible. ENIG finish, green solder mask, white silkscreen. Finished outer copper nominal 35 µm; inner nominal 35 µm. Adjust dielectric build to 1.6 mm.
- Layer order: L1 F.Cu signals/GND fill; L2 In1.Cu GND; L3 In2.Cu signals; L4 In3.Cu signals; L5 In4.Cu 3V3; L6 B.Cu signals/GND fill. Keep this order. Closely couple L1/L2 and L5/L6; use PCBWay's manufacturable symmetric stackup. No impedance coupon required for this USB full-speed revision; do not advertise it as USB high speed.
- Minimum track 0.127 mm (5 mil), minimum copper clearance 0.10 mm (approximately 4 mil), minimum via drill 0.20 mm. Typical routing via 0.45 mm pad / 0.20 mm drill; some power/thermal vias 0.55 / 0.25 mm. Hole-to-hole clearance ≥0.25 mm. Edge copper clearance ≥0.30 mm.
- **Resin fill and copper cap through vias (IPC-4761 type VII)**. This includes MCU/regulator/module thermal vias and vias in component pads. Do not substitute open or simply tented vias in solder lands. Gerber mask defines required component solder apertures; capping must leave flat solderable pads. Apply solder mask over non-pad capped vias as plotted. Use solder-mask process suitable for 0.4 mm pitch QFN, allowing gang openings where necessary.
- Separate PTH and NPTH drill files are supplied. Preserve connector plated slots and NPTH mechanical features. Do not plate mounting holes. Electrically test bare boards against the IPC-D-356 netlist.
- Antenna copper/track/via keepout is intentionally empty on every layer. ESP module antenna extends beyond the north board edge. Do not add copper, rails, panel tabs, or metal under it. Add panel tooling/rails outside the assembled board only; remove before shipment. Keep rail/tab support away from the antenna overhang and USB/card mouths.

## Procurement and assembly

Use BOM.csv (grouped) with BOM-ungrouped.csv for individual references. Buy exact listed MPNs. **U1 RP2350A must be A2 or later silicon**; confirm traceability/revision with the supplier before purchase. Do not use A1 or RP2350B. U8 must be the PCB-antenna ESP32-C3-WROOM-02-N4, not the U antenna variant or a different flash capacity. Memory part variants and connector footprints are not interchangeable by value alone. Any unavailable MPN requires an engineering-reviewed substitution and matching footprint, rather than silently changing the assembly.

All components are on the top side. Reflow the SMT parts and assemble/solder all through-hole connectors/sockets, including J2, J3, J6, and J7; J1 has both fine SMT contacts and mechanical anchors. Fit J8 as the through-hole Samtec FTSH-105-01-L-D-K with its keyed position. No manual customer soldering should remain. Use lead-free solder; thermal profile must respect the radio module, SD socket, RGB LED, and connector ratings. Inspect QFN/SON and module ground joints by X-ray where hidden, plus AOI for accessible contacts. Inspect USB-C fine contacts for bridges and shell anchoring.

Use assembly-top.pdf and the source footprints for orientation, including pin-1 markers on F.Fab. CPL coordinates are millimetres, KiCad footprint anchors, native zero origin with Y increasing upward in the CSV; board bounds are X=100..185, Y=-170..-100. Gerbers and drills use the same native origin. CSV rotations are KiCad rotations, counterclockwise viewed from the top, not guaranteed tape-feeder zero rotations. Resolve any rotation convention before programming placement equipment. Do not offset the BOM/CPL independently from the fabrication origin.

Critical orientation: USB-C mouth faces west; microSD insertion mouth faces east; Qwiic mouth faces west; ESP antenna faces north and overhangs the edge. D1 cathode is VBUS_RAW and anode GND; D2 pin 4 is LED_5V, pin 2 GND, pin 3 DIN. Battery J2 pin 1 is positive, pin 2 GND, pin 3 NTC. Verify silkscreen labels against schematic pad numbers, not a generic two-pin battery convention.

Provide one first article for electrical and firmware-assisted qualification before batch release. Perform the initial power checks in TEST-PLAN.md. No approved programming binary is included: leave RP flash and ESP firmware unchanged/blank unless an approved later programming package is supplied. Report procurement substitutions, failed checks, and rework. Clean flux as allowed by component specifications; do not contaminate the SD contacts or radio antenna.
