# Revision A release status

Engineering package for PCBWay turnkey **first-article manufacture and assembly**. All 118 BOM components are fitted and procured by PCBWay. This design has not been physically built or characterized; release a batch only after the first article passes the documented qualification tests.

Independent saved-file checks:

- Schematic ERC: **0 violations**.
- PCB DRC: **0 errors, 0 unrouted connections**.
- Schematic/PCB parity: **0 issues**, including the excluded mounting-hole and fiducial symbols.
- PCB: **125 unique footprint IDs**, comprising 118 fitted components, four NPTH mounting holes, and three copper fiducials.
- Electrical intent: **416 connected pins checked**, with zero mismatches in both the exported schematic netlist and the actual saved PCB pad nets.
- Assembly: BOM and placement exports must reconcile to exactly **118 fitted references**, including SMT and through-hole components; the automated reconciliation is supplied in verification/.

Two non-error DRC warnings remain visible: a redundant 0.0354 mm SD_CS track tail on In2.Cu and an XOUT_DRV via connected on only one copper layer. These concern unused copper; all required pad connections pass the independent connectivity check. No DRC exclusions hide these warnings. See verification/drc-final.json for exact item IDs and coordinates.

Manufacturing requirements are in PCBWAY-INSTRUCTIONS.md and FABRICATION-SPEC.pdf. Filled/capped vias are mandatory, including the core-feedback via in its small solder land and RF-module thermal holes. Connectors are all fitted. Use the specified protected 1S battery with its NTC as an external accessory, not a factory-installed component.

Firmware binaries are not part of this hardware release. The RP2350 supports ROM USB/SWD programming; the ESP programming UART is separately exposed. Electrical qualification, memory timing, USB power policy, radio/SD peak-load operation, RF performance, and thermal/charger behavior require the firmware-assisted tests in TEST-PLAN.md. Do not treat ERC/DRC as proof of these functions.

The canonical source was authored with Backplane KiCad 10.99.0-bp.4. source-kicad10/ is the compatibility copy; its conversion report is in verification/. Manufacturing CAM is exported from the canonical saved board. Backplane returned the canonical file paths but did not confirm viewer refresh/history; static PDF drawings and PNG previews are supplied for review.
