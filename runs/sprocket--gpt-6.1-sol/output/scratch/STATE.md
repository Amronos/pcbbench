# Working state

Root `sprocket2350.kicad_pcb` is the final routed first-article candidate. Root schematic, netlist, project, rules and component metadata match. Do not replace root with scratch variants.

Latest matching checks: `final-parity-drc.json` has zero violations, opens and parity findings; `final-erc.json` has zero findings. `final-assembly-check.json` has zero blocking/advisory findings. `final-bom/` validates 92 fitted parts, 43 BOM rows, C6/C20 bottom. `final-weird.log` reports no weird things, with 58 via-end advisories. `final-via-map/` covers 279 filled/capped vias and 12 plated thermal holes.

Final read-only power review found no unresolved must-fix for supervised first articles. Physical testing remains required. C6 uses manufacturer typical capacitance curves with engineering margin, not guaranteed operating minima.

USB audit has zero reference-plane crossings. It does not validate 90 ohm impedance. Supplier must confirm stackup, 0.15 mm drilling, Type VII treatment, the 0.102 mm +3V3 pour neck and all-component turnkey assembly.

Renderer isolation found J2's model offset was incorrectly saved in nm instead of mm. `finish_layout.py` and root now use -3.2 mm Y offset and 270 degree X rotation, placing its housing above the board. Genuine fully populated renders work. Only model transforms changed; copper is unchanged. Release uses scoped viewer settings and never changes global preferences. Run only one heavy CAD job at a time.

First end-to-end release succeeded at `../fab/releases/sprocket2350-first-article/`: fresh ERC0, DRC0, opens0, parity0; 92 parts; 279 vias +12 thermal holes; complete fabrication exports and genuine populated renders. Fresh root assembly audit after the model correction, `released-assembly-check.json`, remains blocking0/advisory0 and resolves all92 model heights.

Preferred final delivery: `../fab/releases/sprocket2350-rev-a/sprocket2350-FIRST_ARTICLE.zip`. It contains 66 ZIP entries. ZIP CRC, all65 checksums and all root/staged source hashes pass. Fresh package ERC0/DRC0/opens0/parity0. BOM/placement92 and treatment291 pass. Final cropped black-on-white assembly drawings and populated top/isometric/bottom renders were inspected; U7's Fab reference now clears its thermal-hole outlines. Earlier `sprocket2350-first-article*` directories are superseded candidates, not the preferred delivery.

Final archive SHA256: `3d0f3a766fc162e20993eb5d349a27f3da4cbb5d3205f86b351b8a038d29f124`. Optional3D binaries are deliberately omitted from the archive; provenance and fetch helper remain. No manufacturing approval or physical validation is implied.

Obsolete `tools/build.py`, `tools/fix_placement.py` and `tools/prepare_planes.py` were deleted. Scratch scripts and boards are experiments, not release sources.

All subagents use gpt-6.1-sol, medium reasoning. No git repository, PR, quote, purchase, firmware release or hardware test exists.
