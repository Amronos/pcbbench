# PCBWay fabrication specification

Revision A is a fully routed, physically untested first-article candidate, not approved for manufacture. Core-power and ESD PCB repairs and metadata/netlist synchronization are complete. Final root ERC and DRC report zero findings, zero opens and zero schematic-parity findings. The live BOM validates all 92 fitted components; the final assembly audit reports zero blocking and advisory findings. USB controlled impedance and supplier process confirmation remain unresolved. The specifications below are quote requirements, not supplier-approved capabilities.

| Item | Specification |
|---|---|
| Finished board size | 80 × 65 mm; profile in Edge.Cuts |
| Layers | Four, ordered F.Cu / In1.Cu / In2.Cu / B.Cu |
| Material | FR-4, Tg ≥150 °C, lead-free compatible |
| Finished thickness | 1.60 mm ±10% |
| Copper | 35 µm (1 oz) on each of the four copper layers |
| Finish | ENIG, lead-free assembly |
| Solder mask | Green both sides |
| Silkscreen | White; use the exported F/B artwork |
| Minimum routed track/clearance | 0.127 / 0.127 mm, unchanged |
| 3V3 plane connection exception | Targeted `connection_width` minimum 0.100 mm for ordinary copper zones on `/+3V3` only. Tested neck is 0.102 mm, not widened. Default board minimum connection remains 0.127 mm. Obtain supplier confirmation. |
| Drilling | Use actual drill data and the treatment coordinate CSV. Distinguish PCB vias from plated through-hole thermal pads embedded in footprints. Confirm drill/finished-hole sizes and aspect ratios with PCBWay. |
| Filled/capped treatment | Conservatively require nonconductive resin fill and copper cap, IPC-4761 Type VII, plated flat, for ALL actual PCB vias and for in-pad plated through-hole thermal footprint holes. Match the annotated map and coordinate CSV to drill data. Obtain fabrication confirmation before ordering. Do not fill component-lead holes. |
| Electrical test | 100% bare-board test against supplied IPC-D-356 netlist |
| Profiling | Routed profile, no V-score through this individual board |
| Holes | Separate PTH and NPTH Excellon files; oval slots must be routed as plated slots where specified |
| Panelisation | PCBWay to panelise with assembly rails, tooling holes and panel fiducials. Obtain approval of the panel drawing. |

## 3V3 plane neck

The selected rule applies only to `connection_width` on ordinary `/+3V3` copper zones. It does not lower routed trace widths, copper clearances or the default 0.127 mm board connection minimum. The user-tested snapshot passed this rule with an actual 0.102 mm plane neck and the original 0.25 mm zone `min_thickness`. DRC acceptance is a scoped constraint decision, not a physical widening or a measured current/thermal margin.

Raising zone `min_thickness` to 0.35 mm opened the supply island feeding RP2350 pin 20 through the via at (53.8, 57.4) mm. That change was dropped; retain 0.25 mm and verify the island's connectivity after the final refill. Include the targeted `.kicad_dru` with the final editable sources, not a global relaxation.

[PCBWay's published capabilities](https://www.pcbway.com/capabilities.html) list 0.10 mm minimum trace/space and 0.15 mm CNC drilling, with extra charges below 0.20 mm drill size. These general capabilities are not approval of this board. Obtain explicit confirmation of the 0.102 mm 3V3 neck, copper thickness, etch tolerance and drilling before ordering.

## Stackup and USB impedance

| Layer | Thickness |
|---|---|
| F.Cu | 35 µm |
| Dielectric (prepreg) | 0.21 mm |
| In1.Cu, ground reference | 35 µm |
| Core | 1.04 mm |
| In2.Cu | 35 µm |
| Dielectric (prepreg) | 0.21 mm |
| B.Cu | 35 µm |
| Total, excluding solder mask | 1.60 mm nominal |

The root PCB currently records this stackup and ENIG. Its four copper layers and three dielectrics total 1.60 mm excluding solder mask. These are CAD values, not a supplier-approved stackup. Obtain PCBWay's material, pressed thickness, copper and finished-thickness tolerances before ordering, then reconcile the CAD and candidate exports with that confirmation.

In1.Cu is the intended ground reference plane. Do not swap the layer order. USB targets 90 Ω differential impedance, but the geometry and supplier process are not approved. Obtain PCBWay's dielectric data, agreed pair width/spacing, impedance tolerance and verification method. Review pad escapes, vias, resistor transitions and reference-plane continuity. Do not silently change track geometry or substitute the stackup.

`set_usb_pour_clearance.py` replaces named `USB side-ground spacing` rule areas around actual F/B USB tracks, using a 0.30 mm track-edge corridor that excludes copper pours only. It does not use custom two-item `.dru` rules, which are unreliable for zone fills here. Actual ground gaps vary near pads, vias, other clearances and wider voids. The latest user-reported audit found zero reference-plane crossings; that result applies only to its inspected snapshot and does not guarantee 90 Ω. The candidate includes `checks/USB-diagnostic.json`; its findings are diagnostic, not a candidate-generation gate or certification.

Despite its name, `z0_measured` in the diagnostic report is a software impedance estimate, not a physical bench measurement.

Core decoupling placement and power routing have been repaired against the reviewed regulator schematic. Obtain a quote and process confirmation for actual drill sizes and finished-hole aspect ratios at 1.6 mm thickness.

Global via filling/capping defaults may remain `no`, but `finish_layout.py` explicitly sets each actual via to filled and capped. Global defaults alone do not describe per-via treatment. The coordinate CSV records each drilled item's saved fill/cap overrides alongside its required treatment, object type, location and dimensions. Neither CAD setting proves the fabrication process. Reconcile the candidate's map and CSV with drill data, including the separate in-pad plated thermal footprint holes. PCBWay must confirm Type VII resin fill, copper cap and planarity before ordering.

The radio antenna extends beyond the north board edge. Keep copper, panel rails, tooling tabs and enclosure metal out of its keepout. Panel support must contact the main PCB away from the overhang. Show its orientation and keepout in the final assembly drawing.

## File use

Use copper/mask/silkscreen/outline Gerbers and Excellon drills for fabrication. F.Paste and B.Paste are stencil data, not copper layers. F/B assembly PDFs/PNGs include references; bottom drawings are mirrored bottom views, while placement coordinates are not mirrored. The schematic PDF is a reference, not fabrication artwork. The BOM and placement file control parts, sides and orientation. CSVs under `fab/unreleased/` are for review only.

The candidate must also contain matching editable KiCad CAD, local symbol/footprint libraries, library tables and any project-local rules in use. Retain 3D provenance documents but exclude optional 3D model binaries because J2 redistribution rights are unconfirmed. Renders use available models and may contain missing or substituted geometry, recorded in `checks/render-models.json`; they are not mechanical sign-off. No supplier stackup approval, controlled-impedance coupon, engineering order approval or PCBWay quotation has been obtained.

## Release checklist

- Preserve the synchronized, checked sources. Final root ERC/DRC and schematic parity have zero findings, and the live BOM validates all 92 fitted components. Regenerate checks if the sources change.
- Run fresh ERC and zone-refilled DRC with schematic parity on the final sources. Resolve findings and review exclusions. Include the reports with the matching exports; stale reports are not acceptance evidence. Passing ERC/DRC does not validate circuit correctness, ESD effectiveness, impedance, power stability or product compliance.
- Include and review the targeted `/+3V3` zone connection rule. Verify the 0.102 mm neck and pin-20 supply-island connectivity with 0.25 mm zone `min_thickness`; confirm fabrication acceptance without lowering the 0.127 mm routed trace/clearance floors.
- Generate Gerbers, F/B paste, separate PTH/NPTH drills and plated slots, IPC-D-356 data, F/B assembly PDFs/PNGs, schematic PDF, top/isometric renders and a bottom render when needed, treatment map/coordinates, BOM and placement from the same checked snapshot. Include editable sources, fresh checks and the diagnostic USB audit; exclude stale reports.
- Before ordering, obtain PCBWay's stackup, USB impedance, drilling and Type VII process confirmation. Match the candidate board, drill data and treatment map/CSV to those requirements. Review the completed core-power layout and ESD design.
- Confirm exact BOM availability and a turnkey quote for all 92 fitted SMT/through-hole components, including J3/J6/J7. No fitted part may require customer purchasing or soldering. Approve the panel drawing and any substitutions.
- Inspect the exported outline, copper, masks, paste, holes, orientations and placement origin. Reconcile every fitted BOM item with the assembly files.
- Approve the package and first-article test plan explicitly before ordering. Include PSRAM initialisation and gauge powered-off leakage in that plan. Review measured first-article results and operating limits separately before authorising production.

Generate the quote-ready package from the candidate project root:

```bash
kicad-python tools/release.py
```

Optionally pass `--output new-directory`. The default destination is `fab/releases/sprocket2350-first-article`; other workspace destinations must also be under `fab/releases/`. No custom approval files are required. Fresh ERC/DRC and schematic parity gate package publication. Supplier process confirmation and order approval remain separate requirements before manufacture.

The destination must be new; existing packages are not overwritten. The helper snapshots sources, refills and saves zones only in the staged PCB, then runs fresh ERC/DRC with schematic parity. Any reported finding, including an exclusion, blocks publication. Checks and exports use that same snapshot; the root CAD remains unchanged.

The package contains editable `source/`, fresh `checks/` and the diagnostic USB audit, `assembly/` with BOM, placement, F/B PDFs/PNGs, schematic PDF and renders, `gerbers/`, `drills/`, IPC-D-356 data, CAD stackup JSON, `fabrication/` with treatment map/coordinates, `release.json`, `SHA256SUMS`, and `sprocket2350-FIRST_ARTICLE.zip`. The ZIP includes editable sources. CAD stackup JSON is not supplier approval; audit and model geometry references are not certification. Redundant native position CSVs are omitted. A `FIRST_ARTICLE` candidate remains physically untested, is not order approval, and is not production qualified.
