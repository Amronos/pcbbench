# Atlas2350 Rev A — PCBWay turnkey package

Request an initial quote for **five fully assembled boards**. PCBWay supplies and assembles every real component, including through-hole headers and USB shell stakes. There are **115 populated components / 53 BOM groups per board**, no DNP options and no customer-soldered parts. Battery, microSD card, cables and mounting screws are external accessories, not BOM components.

## Upload / manufacturing inputs

- `gerbers/`: ten Gerber X2 plots: four copper layers, both masks, both silkscreens, top paste and the closed board outline; `.gbrjob` is the job index.
- `drill/`: separate plated and non-plated Excellon files, PDF drill maps, drill report and `filled-capped-hole-schedule.csv`.
- `Atlas2350.ipc`: IPC-D-356 netlist for bare-board electrical test.
- `assembly/bom.csv`: grouped, exact manufacturer/MPN BOM; `parts.csv` expands every reference individually.
- `assembly/pcbway-centroids.csv`: component-body centroids for placement. Read its companion source/methodology files before machine setup.
- `assembly/kicad-native-position.csv`: native KiCad **footprint-anchor**, not computed body-centroid, output. Do not treat it as an interchangeable centroid file.
- `assembly/placement.csv`: richly annotated CAD-anchor output, **X right / Y down**, mm. Native KiCad CSV and PCBWay centroid CSV use **Cartesian Y up**; their Y values are negative below the origin.
- `assembly/assembly-pinout.csv`, `assembly-orientation.pdf`, `top-assembly-kicad.pdf` and `top-assembly-orientation.svg`: actual pin numbering, pin1/orientation, connector and population references.
- `schematic.pdf`, `fabrication-and-assembly.pdf`, `fabrication-notes.md`, `assembly-notes.md`, `test-plan.md`: circuit, process requirements and first-article qualification.
- `verification.json`, `erc-final.json`, `drc-final.json`: design-check evidence. `manifest.json` and `SHA256SUMS.txt` identify the released files.

All CAD/plot coordinates use the same **absolute KiCad origin (0,0)**, at the top-left extent of the 80×75 mm outline; the chamfer means (0,0) itself is outside the board. Do not independently recenter copper, drills, paste, placement or drawings. Apply panelization offsets together. Placement rotation is saved KiCad degrees, CCW viewed from the top; PCBWay must reconcile reel and machine zero angles against the physical pad1 references.

## Mandatory process requirements

Four layers, 1.6 mm FR-4, ENIG, green mask, white silk, outer 1 oz / inner 0.5 oz copper. Requested nominal dielectrics are **0.12 mm / 1.255 mm / 0.12 mm**, from top to bottom; quote the actual cured stackup/materials. This is not an impedance-certified design. Routing vias are 0.60/0.30 mm. **Every hole in the filled/capped schedule requires IPC-4761 Type VII resin fill and copper cap**, including the twelve U6 thermal holes. Do not fill component lead holes. Standard open/tented-via fabrication is not a substitute. The schedule is the geometric authority for selective hole treatment.

All components are top-side. U6's antenna overhangs the top board edge by approximately 6.1 mm; panel rails and fixtures must clear it and its keepout. U5 uses the exact irregular RNM0015A footprint—pads9/11 are switch nodes, and no pad16 exists. U2 is wide SOIC8; U3 is narrow SOIC8. J6 is the THT FTSH-105-01-L-D variant, with 0.70 mm finished holes. D1 must be the V6 LED variant. No silent footprint, pinout or part substitutions.

PCBWay determines sourcing lead times, panelization, stencil/profile and DFM acceptance in its quote. This package does not assert current stock availability or supplier approval. Do not order a cheaper open-via process or accept a part substitution to bypass those checks.

## Prototype status

ERC, DRC and explicit schematic-to-PCB pin checks are complete in the included reports. Physical first articles have **not** been manufactured or tested. This is an electrically complete prototype CAM/assembly package, not mass-production, RF, USB or safety certification. A clean DRC is not a guarantee of circuit performance.

No firmware binary is included. Supply/program qualified RP2350 and ESP-AT images before functional acceptance; the test plan records commissioning obligations. J2 is a **custom three-wire protected LiPo interface: 1 BAT+, 2 GND, 3 cell-mounted 10k NTC**. RGB is not guaranteed when VSYS falls below 3.3 V; firmware should blank it around 3.6 V battery voltage under load. Read the main project README for all operating limitations.
