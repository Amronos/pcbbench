# Release verification — Aster2350 Rev A

Design date: 2026-11-09. Final packet verified: 2026-11-10 UTC. **Unbuilt engineering prototype.**

## Automated checks

- KiCad ERC: zero reported errors or warnings.
- KiCad DRC: zero reported violations and zero unconnected items, with zones refilled.
- KiCad schematic parity: zero issues, including component fields and pin nets.
- Independently exported schematic XML netlist matches PCB pad nets, including grounded JST SH mounting pads. Intentionally no-connect singleton nets are excluded from this independent connectivity comparison; KiCad parity checks them separately.
- 121 purchased parts, 51 grouped exact-MPN BOM lines, all populated: 118 top SMT and three top THT. The custom placement coordinates/rotations are independently cross-checked against native KiCad CSV export.
- In1 contains no non-ground signal tracks. RF antenna keepout contains no copper pads, tracks, vias or filled pours.
- Conventional via drill geometry does not intersect any open top SMD solder pad. No filled/capped via-in-pad or microvia process is specified.
- Primary PCB exported to KiCad 10.0 format without `--force`, then DRC and schematic parity run again on that delivered file.
- Four copper Gerbers, both masks and legends, both paste layers, board outline, separate plated/nonplated Excellon drills, plated-slot routing, drill maps, IPC-D-356, BOM, placements and assembly/fabrication PDFs are supplied.

Machine-readable results: `validation.json`, `DRC.json`, `ERC.json`. Build:
KiCad 10.99.0-6353-g0ef63a79e8. Default non-electrical checks such as missing
courtyards on bare PCB features, tuning-profile geometries and footprint filters
are not evidence of physical validation. Electrical shorts, clearances, unconnected
items, footprints missing from libraries and schematic parity are not waived.

## Not verified by CAD

PCBWay has not received an order, reserved parts, approved the requested stack
or signed off this design. Component sourcing, land-pattern DFM, assembly process,
impedance coupon and X-ray/AOI acceptance must be agreed at quotation. Component
origin/rotation conventions must be translated into the assembler's machine setup.

Analogue power behavior, thermal performance, charge safety with the selected pack,
USB enumeration/compliance/suspend, memory timing, RF range/EMC, card interoperability
and firmware functionality need a physical first article. No production firmware,
certification, fabrication approval or test result is implied by clean ERC/DRC.
Follow the hold and test checklist in `ASSEMBLY.md` before volume manufacture.

## Reproduction

Normal engineering edits use KiCad with the project-local libraries. After editing,
install `tools/requirements.txt` in a Python environment and run `tools/release.py`
with `KICAD_CLI` set to the compatible KiCad executable. The script stops if any
required CAD/consistency check fails. It refills zones, exports manufacturing files,
cross-checks BOM/placements and creates the ZIP/checksum manifest.

**Do not run `tools/design.py` over the finished project**: it produces the initial
unrouted layout and intentionally replaces the routed board. Routing-session inputs
are not needed to open or manufacture the delivered design.
