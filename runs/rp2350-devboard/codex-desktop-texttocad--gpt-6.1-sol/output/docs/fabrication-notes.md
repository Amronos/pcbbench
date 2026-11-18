# Atlas2350 Rev A fabrication requirements

Date: **2026-11-10**. **Status: complete prototype CAM package.** The final revision includes U10/C45 for switched LED power; [checks/verification.json](../checks/verification.json) is **PASS with all 432 declared pin assignments checked**, **115 components / 128 footprints**, and **final ERC/DRC each report zero errors**. **Final CAM parse is PASS: 10 Gerbers, 374 PTH, 7 NPTH, and 334 filled/capped holes registered within a 0.00051 mm export-rounding tolerance**. All QSPI including FLASH_CS remains F/B only. Use the matching final source/export hashes and verification reports for the order. This is a **prototype first-article package**, with no supplier quote/stock commitment, DFM approval or physical/functional testing claimed. Initial quote quantity is **five completely assembled boards**.

Native PCB: KiCad **10.99.0 development**, format **20261031**; require a compatible **KiCad 11 development/nightly build**, not stable9/10. Native schematic format: **20250114**. Suppliers may use the final CAM and schematic PDF instead of editing the development-format native project.

## Board and stackup

| Item | Requirement |
|---|---|
| Board envelope | 80.0 × 75.0 mm, nominal |
| Outline | Eight-sided rectangle with 2 mm clipped corners; vertices (2,0), (78,0), (80,2), (80,73), (78,75), (2,75), (0,73), (0,2) mm |
| Layer count | 4 copper layers |
| F.Cu / B.Cu | Signal routing, power distribution and full GND pours; nominal1 oz copper each |
| In1.Cu / In2.Cu | Predominantly stitched GND pours **with low-speed escape corridors on both layers**; nominal0.5 oz copper each; **not continuous planes** |
| Copper/dielectric construction thickness | 1.600 mm nominal excluding mask coatings; factory to quote achieved finished thickness/tolerance |
| Finish | ENIG on exposed solder/probe lands |
| Material | Suitable lead-free FR-4; fabricator to supply stackup/material details |
| Mask / silkscreen | **Green soldermask / white silkscreen**, both sides |
| Impedance | **No controlled-impedance specification or claim**; all QSPI including FLASH_CS is F/B, and USB is hand-routed F/B; first-article SI qualification required |
| Release class | **Five completely assembled prototype first articles** for initial quote; workmanship class to be agreed in the order |

**The corrected native PCB encodes this requested nominal fabrication stackup**, replacing default finish=None, all-copper 1 oz and uniform dielectric metadata. Quote ENIG and the following front-to-back construction; do not silently substitute an unspecified stock stackup.

| Layer / material | Requested nominal thickness | Notes |
|---|---:|---|
| F.SilkS | Not included in construction sum | White silkscreen |
| F.Mask | 0.010 mm | Green coating; excluded from 1.600 mm copper/dielectric sum |
| F.Cu | 0.035 mm / 35 µm | Outer copper, nominal 1 oz |
| F.Cu–In1.Cu dielectric | 0.120 mm | FR-4 prepreg, requested cured thickness |
| In1.Cu | 0.0175 mm / 17.5 µm | Inner copper, nominal 0.5 oz |
| In1.Cu–In2.Cu dielectric | 1.255 mm | FR-4 core |
| In2.Cu | 0.0175 mm / 17.5 µm | Inner copper, nominal 0.5 oz |
| In2.Cu–B.Cu dielectric | 0.120 mm | FR-4 prepreg, requested cured thickness |
| B.Cu | 0.035 mm / 35 µm | Outer copper, nominal 1 oz |
| B.Mask | 0.010 mm | Green coating; excluded from construction sum |
| B.SilkS | Not included in construction sum | White silkscreen |
| Copper + dielectric total | **1.600 mm** | 0.105 mm copper + 1.495 mm dielectric |

These are **requested nominal values**, not an approved supplier stackup or cured-thickness measurement. With both nominal mask coatings the arithmetic total is 1.620 mm, excluding silk/finish; the supplier must state its finished-thickness convention and achievable tolerances. Supplier quotation must identify actual FR-4 materials, cured prepreg/core dimensions and copper build/plating. Native dielectric-property entries are nominal design metadata, not measured material characterization. The stackup is **not controlled-impedance qualified**, and no controlled-impedance order is specified.

Fabricate the exported copper on all four layers as supplied; do not replace either inner layer with a solid plane that shorts its low-speed escape corridors. Both inner layers predominantly carry stitched GND, while outer pours complete ground connectivity and the exposed-pad link. Evaluate return paths and plane interruptions on the actual final copper. USB/QSPI signal integrity has not been measured or certified; conservative firmware startup limits are **QSPI≤31.25 MHz and SD≤12.5 MHz**, with the card's required slower initialization. Power-current paths need current/thermal qualification; minimum signal width alone is not a current rating. Use the selected green mask and white silkscreen.

## Minimum geometry and holes

| Feature | Current target / minimum |
|---|---|
| Signal track width | 0.15 mm |
| Copper clearance | 0.127 mm |
| Connection width | 0.15 mm |
| Routing via pad | 0.60 mm |
| Routing via finished hole | 0.30 mm |
| Via annular ring | 0.15 mm |
| Minimum through drill rule | 0.30 mm; actual component holes per footprint |
| Copper-to-board-edge clearance | 0.25 mm |
| Hole-to-hole minimum | 0.25 mm |
| Hole clearance rule | 0.178 mm |
| Silkscreen clearance | 0.15 mm |
| Mounting holes | Three **2.7 mm NPTH** for M2.5 hardware |
| J6 finished lead holes | Ten **0.70 mm PTH**, enlarged from 0.65 mm; **1.00 mm copper lands**, nominal **0.15 mm annular ring**; open, not filled/capped |

The above dimensions record the design geometry requirements. The final revision's verification.json is PASS with 432 pin assignments checked and DRC zero errors; reconcile the CAM revision/hash with that evidence. Intentional local U6/J3/J6 footprint edits match the saved board. Fabricator must reconcile plated finished-hole sizes with tooling compensation and provide tolerances; a 0.30 mm finished via hole is not an uncompensated drill-tool size.

## Mandatory via-in-pad process

**ALL routing vias require IPC-4761 Type VII: nonconductive resin-filled and copper-capped on both sides.** This applies whether or not an individual via visibly overlaps a pad. Included features are GND decoupler vias, exposed-pad ground vias, signal/power routing vias, and **all twelve 0.30 mm plated thermal holes in U6's pad19**. Those twelve radio holes are encoded as small PTH pad features, but their intended role is a via network: they must receive the same fill/cap process as routing vias.

Reconcile [filled-capped-hole-schedule.csv](../fab/drill/filled-capped-hole-schedule.csv) with the final drill data: **322 routing vias + twelve U6 0.30 mm thermal PTH features = 334 resin-filled/copper-capped holes**. Total PTH is **374**, comprising the 334 filled/capped features and **40 open component lead/shell holes**. Total NPTH is **7**, unplated and unfilled. Fill/cap every routing via and all twelve module thermal holes, never component lead/shell holes. The final schedule and drill classification govern processing.

Requirements for quotation and fabrication:

1. Quote resin fill, planarization and copper cap as an explicit included process. Soldermask tenting, plugging, solder fill, or resin fill without copper cap is not equivalent.
2. Use a process suitable for solderable via-in-pad lands, maintaining final pad planarity and cap integrity. The factory must state process capability, inspection and any required pad/drill changes before manufacture.
3. Identify the twelve U6 thermal holes in the drill/assembly review, even if the drill export groups them with plated component holes. Their net is GND and their finished diameter is 0.30 mm.
4. Fill/cap only vias and the identified thermal-via features. **Do not fill/cap THT component lead holes or J1 shell stake holes**: J5/J6/J7 and the shell must accept leads and be soldered.
5. H1–H3 are NPTH mechanical holes. Do not plate, fill or cap them; mounting hardware is not supplied in the component BOM.
6. Reconcile via count and thermal-feature count with the final drill files after routing. A drill diameter alone is insufficient to classify a hole's intended process.

This process is mandatory because the design uses via-in-pad on ground decouplers and exposed pads. A standard unfilled via order can drain solder paste and compromise assembly. If the selected supplier cannot provide TypeVII on the final geometry, hold the order for engineering disposition; do not silently substitute tented or open vias.

## Mechanical placement and clearances

| Feature | Final placement intent |
|---|---|
| H1 | Center (4,4) mm, 2.7 mm NPTH |
| H2 | Center (4,71) mm, 2.7 mm NPTH |
| H3 | Center **(56,70)** mm, 2.7 mm NPTH |
| U6 radio | Placement origin **(65,7)** mm, rotation 0° |
| U6 antenna | Overhang approximately **6.1 mm above y=0 top Edge.Cuts** |
| J1 USB | Origin (3,40) mm, 270°; preserve connector entry/shell clearance |
| J2 battery | Origin (7,14) mm, 270°; cable access at board edge |
| J3 microSD | Origin (68,62) mm, 0°; insertion/ejection clearance |
| J4 I²C | Origin (76,38) mm, 90°; horizontal cable access |

The U6 antenna region is outside the PCB copper envelope in the selected placement. Maintain the antenna's manufacturer all-layer copper/component keepout and verify its transformed geometry in the final board. Do not extend GND planes into it or add copper-bearing panel rails within that region. The antenna is **not** an extension of the FR-4 outline; the module overhangs the existing board edge.

Require panelization and assembly-fixture review for the radio overhang, edge USB/JST connectors and microSD opening. Panel rails, tabs, V-scores, clamps and tooling must not collide with overhanging parts or antenna clearance. Panel layout is not supplied here; obtain and approve the proposed panel arrangement before production. Preserve all three mounting-hole locations; no mounting screws/standoffs are included.

## Footprints, mask and stencil

U10 **TPS22919DCKR** adds a SC70-6 load-switch footprint; C45 adds its 1 µF VSYS input capacitor. U10 pins are 1 IN=VSYS, 2 GND, 3 ON=PWR_EN, 4 NC floating, 5 QOD=LED_VDD and 6 VOUT=LED_VDD. D1/C24/C36 connect to LED_VDD. Include both new SMT parts in final BOM, centroid/pin1 review and assembly; reconcile all final routing-via counts after this revision. [Primary TI datasheet](https://www.ti.com/lit/ds/symlink/tps22919.pdf).


**U10 schematic model:** local symbol pin5 QOD is typed **passive** to represent TI's explicitly permitted direct tie to VOUT/pin6 (LED_VDD). The stock `open_collector` type produces an ERC conflict with the power-output pin6 for this permitted connection. Only the schematic electrical type is changed: pin numbers, package pinout and footprint are unchanged. **No ERC exclusions are used.** [TI TPS22919 pin-functions table](https://www.ti.com/lit/ds/symlink/tps22919.pdf).

- U5 must use the custom exact **TPS63070 RNM0015A** land pattern. Enlarged power pads9=L2 and11=L1 are switch nodes; pad10 alone is PGND. There is no generic grounded center pad16. Review mask-defined power lands and TI's segmented stencil apertures against the actual custom footprint.
- U1/U4 exposed GND pads and U6 pad19 require correct thermal/ground connectivity and filled/capped via treatment. Do not connect an enlarged pad to GND merely because it looks thermal.
- U2 W25Q32JVSSIQ uses wide 5.3 mm SOIC8; U3 APS6404L-3SQR-SN uses narrow SOIC8. C32/C33 are **1206**, not the earlier smaller output-capacitor packages.
- L1 uses the stock **L_Coilcraft_XAL4020-XXX** pattern; pad centers ±1.185 mm, land dimensions 0.98×3.40 mm, checked against the primary Coilcraft drawing.
- J6 is **FTSH-105-01-L-D THT**, using the intentionally edited generic 2×5 1.27 mm pattern, not the -DV SMT variant. All ten holes are 0.70 mm finished PTH with 1.00 mm lands; keep all physical leads including pin7 and leave lead holes open.
- Retain Hirose DM3AT socket's manufacturer top-copper keepout. Its reference stencil thickness is 0.12 mm; TI RNM and other parts can have different aperture recommendations. The assembler must reconcile an actual stencil/profile without overriding either part's land requirements.
- Bare ENIG TP1–TP10 need exposed probe surfaces. They are fabricated lands, excluded from BOM; do not print paste or install a test-point component unless the released data explicitly changes their intended treatment.

Do not adjust pad geometry or package orientation for manufacturing convenience without owner review. A local-library name or automated import does not constitute footprint approval; package/drawing comparison is a final release gate.

## Final CAM delivery and release checks

Final CAM parsing passed for **10 Gerber files, 374 plated holes and 7 NPTH holes**; all **334 scheduled filled/capped holes** register to the drill data within **0.00051 mm**, the numerical comparison tolerance for export rounding. This tolerance is not a supplier drilling/registration accuracy specification. Use the final source/export hashes, verification reports and matching note copies as the package identity; physical manufacture, supplier DFM and first-article testing remain separate approvals/results.

The complete prototype delivery includes [fab/README.md](../fab/README.md), [fab/order-instructions.md](../fab/order-instructions.md), [fab/gerbers/](../fab/gerbers/), [fab/drill/](../fab/drill/), [fab/assembly/](../fab/assembly/), [fab/schematic.pdf](../fab/schematic.pdf), and the matching fabrication/assembly/test notes. Read the final package revision/hash and [checks/verification.json](../checks/verification.json) before manufacture. Saved final PCB and assembly exports override earlier design/placement coordinates.

Final release evidence and supplier review cover:

- Final netlist synchronization, ERC and routed-board DRC, including intentional NCs, exposed pads, unconnected copper, clearance, holes and zones. Document dispositions for any accepted exceptions.
- Final filled GND-pour connectivity, inner escape-corridor isolation, return paths, USB/QSPI branches and switch-current loops. No controlled-impedance or measured SI result is claimed.
- Finished-board outline, mechanical envelope, radio overhang, component-to-edge/cage keepouts and connector mating clearances.
- Final plated/NPTH drill classification, **all-routing-via TypeVII instruction**, and twelve radio thermal via holes.
- BOM, placement, assembly drawing and revision identity agreement, with all fitted SMT/THT parts and excluded bare features correctly distinguished.
- Fabricator and assembler capability/quote review for fill/cap, fine-pitch packages, THT operations, overhang fixture and thermal profile. **PCBWay exact-MPN stock/lead times cannot be guaranteed without a quote**; no customer-soldered/DNP components are planned.
- Manufacturing exports, drill/BOM/placement review and final-revision verification evidence must agree. Package completion is not supplier approval.

Assembly delivery includes [bom.csv](../fab/assembly/bom.csv), preferred [placement.csv](../fab/assembly/placement.csv), [kicad-native-position.csv](../fab/assembly/kicad-native-position.csv), [assembly-pinout.csv](../fab/assembly/assembly-pinout.csv) and assembly drawings. All **115 real SMT/THT references in 53 BOM groups** must be factory assembled; 128 footprints include 13 excluded bare H/TP features. Preferred placement is a saved footprint anchor in mm, X right/positive Y down; native export uses Y-negative. PCBWay must reconcile origin/rotation with actual pin1 positions, rather than treating either format as an unverified machine-ready centroid list.

The generated [pcbway-centroids.csv](../fab/assembly/pcbway-centroids.csv) contains **112 surface-mounted physical F.Fab body-box centers**, including U10/C45, hybrid SMT/THT J1 and surface-mounted U6 with thermal holes; pure THT J5/J6/J7 are excluded. The generated [centroid-source.csv](../fab/assembly/centroid-source.csv) retains **all 115 component centers** for review/manual THT placement. Centroid CSV coordinates are mm, X right and Cartesian Y=−boardY. These are body-box centers, not anchors, courtyards or centers of mass; reconcile rotation/origin with actual pin1 coordinates and assembly drawings. [PCBWay specifies surface-mounted parts only in the centroid file](https://www.pcbway.com/assembly-file-requirements.html).

Assembly drawing floorplan/clearance envelopes are **courtyards, not physical body edges**. They may include clearance margins/antenna keepouts and must not define a pick centroid or manufacturer body-fit result. Inspect the generated body-center data against actual pad/pin1 positions.

Release first articles for inspection and qualification before any mass-production decision. Electrical testing of a bare board, supplier DFM review and assembled-board functional qualification are separate outcomes; record each only after it actually occurs.
