# Layout work

`tools/design.py` uses the KiCad headless API. `tools/circuits.py` defines parts and placement.
The first trial route uses F.Cu, In2.Cu and B.Cu. In1.Cu remains a ground plane.
The accepted review snapshot is `finished.kicad_pcb`, copied to the root board, with metadata synchronized. Routing uses 0.12 mm signal widths, 0.11 mm clearance and 0.45/0.20 mm vias with escalation disabled. Ground stitching and teardrops are present. No jobs remain active.
The root board and `fab/` are on manufacturing hold. See `fab/release-review.md`; scratch variants must not be manufactured.
Do not treat trial outputs as released manufacturing data.
