# PCBWay package — RP2350 Connect rev A

Read RELEASE-STATUS.md and PCBWAY-INSTRUCTIONS.md before quoting or production. Procure and fit all 118 components; no consigned parts and no DNP options. Start with one first article.

| File/folder | Purpose |
|---|---|
| BOARD-README.md | Board features, design decisions, GPIO assignment and operating requirements |
| gerbers/ | Six copper layers, mask, silk, paste, and exact board outline |
| drill/ | Separate PTH/NPTH Excellon files, PDF drill maps, drill summary |
| BOM.csv / BOM-ungrouped.csv | Exact manufacturers/MPNs, grouped procurement and individual references |
| placement.csv | All 118 SMT and through-hole component anchors/rotations, top side |
| assembly-top.pdf / assembly-bottom.pdf | Placement, orientation, reference and solder-side review |
| FABRICATION-SPEC.pdf / PCB-features.csv | Stackup/process requirements, board dimensions and mechanical features |
| schematic.pdf / schematic.net | Electrical review and schematic netlist |
| rp2350-connect.ipc | IPC-D-356 bare-board electrical test netlist |
| connector-pinout.csv | Pin-by-pin connector definitions |
| TEST-PLAN.md | Hardware and firmware-assisted first-article qualification |
| verification/ | ERC, DRC, intent and BOM/CPL reconciliation, compatibility reports |
| source-kicad10/ | Self-contained compatibility copy for KiCad 10 |
| source-native/ | Exact canonical native project and local electrical libraries |
| SHA256SUMS | Checksums of package contents |

Coordinate and rotation conventions, polarity, antenna overhang, via fill/cap requirements, silicon revision, and external battery requirements are specified in PCBWAY-INSTRUCTIONS.md. Do not substitute connector, module, or memory variants silently. No approved programming binary is included.
