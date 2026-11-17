# Manufacturing hold

This revision is a routed engineering prototype, not approved for fabrication or assembly. No order has been placed. The Gerbers and drill files describe the current CAD revision for review only.

## Layout changes required

| Block | Finding | Required change |
|---|---|---|
| TPS63001 U5 | VOUT leaves pin 1 through 0.12 mm copper. L1 is 6 mm above U5, with approximately 8–10 mm switching paths and narrow entries. Input/output capacitors are remote. | Re-place L1, C24–C27 against U5's pins and route short, wide supply and switching paths. Validate current and voltage drop. |
| Power exposed pads | U4 has no local thermal-via array. U5's exposed pad disables zone connection and relies on narrow copper. | Add local PGND copper and properly specified thermal vias into the ground planes. Recheck paste and filled-via requirements. |
| RP2350 core supply | C32 is about 10.6 mm from VREG_VIN. C31 is about 5.7 mm from VREG_AVDD. LX changes layers, and C5 lacks a nearby ground via. | Re-place U1/L2/C5/C31/C32/R32 around pins 46–50 following the RP2350 hardware guide's compact loop. |
| Marked inductor L2 | The electrical pad assignment is defined, but the footprint has no physical winding-dot mark. | Match the Abracon winding dot to the Raspberry Pi reference and mark it on the assembly drawing. Do not assume that reversing it is the fix. |
| Charger decoupling | C21 is about 4.8 mm from U4 IN; C22 is about 6.8 mm from BAT. | Bring both capacitors to their pins with local ground returns. |
| Radio supply | C28/C29 are about 20 mm from U6's supply pin at (163.25, 102.00) mm. | Move the capacitors beside pin 1 without entering the antenna keepout. |
| USB | Series resistors are remote from U1. MCU-side routes have roughly 6.9 mm length difference. Connector fanout includes an unmatched layer excursion and width changes. | Move R3/R4 beside pins 51/52 and rebuild the complete pair with continuous reference, consistent geometry, and PCBWay's approved 90 Ω stackup. |

Coordinates are absolute KiCad coordinates. Distances came from the routed board review, not signal-integrity or thermal simulation.

## Electrical and procurement conditions

Final checks report zero ERC findings, zero DRC errors, zero opens and zero schematic-parity issues. DRC still reports 106 warnings: 93 library mismatches from removed footprint silkscreen, 12 dangling vias and one dangling track. Keep these visible for review. Removing all flagged copper is unsafe because some single-layer vias join adjacent segments.

Six exact stock 3D models are missing: U1, U4, U5, J1, J3 and D2. The 3D image omits their bodies. Do not use that render to approve component clearances or connector fit.

- USB500 is permanently selected. This revision does not meet general legacy-host pre-enumeration/suspend current requirements. A compliant general-purpose USB-powered revision needs load/current control.
- The protected 1S LiPo and cell-mounted 10 kΩ B3435 NTC are external. Check the custom 3-pin connector polarity and pack current/temperature limits.
- Validate switched battery-sense startup and shutdown behavior before attaching a cell.
- PCBWay must confirm every exact MPN, including the low-stock or unavailable parts in [procurement.md](procurement.md), and assemble both through-hole headers.
- The current board contains via-in-pad at C19.2 and U2.4. Require IPC-4761 Type VII filled, capped and plated vias, or redesign these sites before release.
- Resolve all final DRC findings and inspect solder mask, silkscreen, footprint polarity and connector geometry. A zero-open report alone does not approve this layout.

After these changes, regenerate every export from the accepted PCB, rerun ERC and DRC with schematic parity, and complete the functional tests listed in [README](../README.md#review-before-release).
