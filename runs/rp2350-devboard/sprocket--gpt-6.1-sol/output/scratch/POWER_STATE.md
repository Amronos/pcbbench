# Power revision

Root board and schematic are read-only. Power work uses `power-revision.kicad_pcb` copied with `copy_board.py`.

`tools/power_layout.py` places U4/U5/L1/C21-C27/R13-R20 and rebuilds their local copper. U4/U5 each have four 0.45/0.20 mm GND vias with filled/capped drill attributes. Fabricator must confirm IPC-4761 type VII resin fill and copper cap.

Baseline DRC: 106 violations, zero unconnected. Baseline report: `power-baseline-drc.json`.

Trial result: zero unconnected, zero shorts/clearance/courtyard errors, assembly audit zero blockers. Unrelated tracks/vias match root when document-parent UUID is excluded. No In1 tracks. Root and schematic are unchanged.

Completed full owned-net route to `power-routed.kicad_pcb`, copied with copy_board to `power-revision.kicad_pcb`. Log: `power-route-full.log`. Improvement gate accepts. Final DRC: 0 errors, 0 opens, 106 warnings. Strict-size exit 3 includes explicit short pad necks and preserved USB VBUS stubs. Do not claim strict-size success. No power jobs remain active. See `power-review.md` for placement and metrics.

Sources fetched from TI: BQ24074 SLUS810N, October 2021; TPS63001 SLVS520C, October 2015. Electrical review found R14 inactive in USB500 mode, discontinued LQH44PN2R2MP0L and an unverified inductor land pattern. No electrical edits were made.
