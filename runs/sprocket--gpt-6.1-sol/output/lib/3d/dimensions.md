# 3D model dimension validation

All dimensions are millimeters. CadQuery/OpenCascade measurements use imported STEP geometry without placement transforms. Exposed-pad (EP) dimensions refer to the bottom seating face at Z = 0, not the larger upper leadframe. EasyEDA WRL vertices were converted using KiCad's 2.54 mm per coordinate unit.

## Selected manufacturer models

Manufacturer models represent the vendor's reference geometry, not every manufactured part at its tolerance extremes. Selection, usage, and visualization limits are in [README.md](README.md).

| Ref | Selected file | Molded body X × Y | Overall height | Terminals / pitch | Bottom EP | Status |
|---|---|---:|---:|---:|---:|---|
| U1 | `rpi_rp2350a.step` | 7.000 × 7.000 | 0.850 | 60 / 0.400 | 3.400 × 3.400 | Accept manufacturer RP2350A reference model. |
| U4 | `RGT0016C.stp` | 3.000 × 3.000 | 1.000 | 16 / 0.500 | 1.680 × 1.680 | Accept TI RGT0016C package model for BQ24074RGTR. |
| U5 | `DRC0010J.stp` | 3.000 × 3.000 | 1.000 | 10 / 0.500 | 1.650 × 2.400 main rectangle | Accept TI DRC0010J package model for TPS63001DRCR. |

### Datasheet comparison

Sources are the exact links in `fab/BOM.csv`, including current redirects and package appendices.

| Ref | Drawing source | Body / height limits | Terminal width × length | EP limits |
|---|---|---|---|---|
| U1 | [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf), section 14.1, Figure 147, printed p.1324 / PDF p.1325 in RP-008373-DS-3 | 7 × 7 BSC; height 0.800–0.900 | 0.130–0.230 × 0.350–0.450 | 3.350–3.450 square |
| U4 | [BQ24074 datasheet](https://www.ti.com/lit/ds/symlink/bq24074.pdf#page=52), PDF p.52, RGT0016C, 4222419/E, 07/2025 | 2.90–3.10 each; height 0.80–1.00 | 0.18–0.30 × 0.30–0.50 | 1.68 ± 0.07 square |
| U5 | [TPS63001 datasheet](https://www.ti.com/lit/ds/symlink/tps63001.pdf#page=23), PDF p.23, DRC0010J, 4218878/B, 07/2018 | 2.90–3.10 each; height 0.80–1.00 | 0.18–0.30 × 0.30–0.50 | 1.65 ± 0.10 × 2.40 ± 0.10, plus side tabs |

Measured terminal width × length is 0.180 × 0.410 for U1 and 0.240 × 0.400 for both TI models. All fit the drawing limits. U1's complete metal-inclusive bounds are 7.020 × 7.020 × 0.850; the 0.010 metal projection on each side is distinct from its 7.000 square molded body. Both TI models have complete bounds 3.000 × 3.000 × 1.000. Body undersides are Z = 0.010 for U1 and Z = 0.025 for U4/U5, within the drawings' 0–0.050 stand-off limits.

### Seating faces and orientation

| Ref | Bottom EP detail | Bottom-face area | Upper leadframe distinction |
|---|---|---:|---|
| U1 | Square bounds ±1.700; semicircular R0.200 indentation centered at (−1.700, +1.050) | 11.49717 mm² | Separate EP solid, Z = 0–0.010. |
| U4 | Square bounds ±0.840; upper-left corner cut with 0.350 legs | 2.76115 mm² | Whole EP solid bounds are 1.880 square. That is not the exposed bottom pad size. |
| U5 | Main rectangle X = ±0.825, Y = ±1.200; four 0.250-wide tabs project 0.300 to Y = ±1.500; upper-left cut has 0.300 legs | 4.21500 mm² | Bottom bounds including tabs are 1.650 × 3.000; whole leadframe solid bounds are 1.900 × 3.000. Neither is the main EP rectangle. |

Terminal centers confirm pitch independently of filenames: U1 has 15 per side from −2.800 to +2.800 in 0.400 increments; U4 has four per side at −0.750, −0.250, +0.250, +0.750; U5 has five per side at −1.000, −0.500, 0, +0.500, +1.000.

All three seat at Z = 0. Pin 1 is upper-left in Cartesian XY, (−X, +Y). U1's top index mark centers at (−2.800, +2.800); the TI bottom-pad corner cuts occupy the same upper-left quadrant. Use zero rotation and zero offset.

### Manufacturer provenance

- U1: [Raspberry Pi RP2350A Minimal KiCAD ZIP](https://pip.raspberrypi.com/documents/RP-010328-CA-RP2350A%20Minimal%20KiCAD.zip), embedded `rpi_rp2350a.step` in `RPI-RP2350A-MINIMAL_R4-S1_public/RPI-RP2350A-MINIMAL_R4-S1.kicad_pcb`. The local file identifies `rpi_rp2350a`, FreeCAD/OpenCascade, dated 2024-10-18. Source extraction and license are recorded in `README.md`.
- U4: [TI RGT0016C.stp](https://webench.ti.com/cad/dlbxl.cgi/newstep/RGT0016C.stp). Local STEP header identifies `RGT0016C_ASM`, dated 2025-07-31.
- U5: [TI DRC0010J.stp](https://webench.ti.com/cad/dlbxl.cgi/newstep/DRC0010J.stp). Local STEP header identifies `DRC0010J_ASM`, dated 2018-07-10.

## EasyEDA candidate limitations

Manufacturer models replace the U1/U4/U5 candidates. J1/J3 STEP and D2 WRL are selected for body visualization only. Exact product listings and matching envelopes do not prove exact terminal geometry or device identity.

| Ref | Candidate filename within its directory | Measured finding | Exact-model status |
|---|---|---|---|
| U1 | `QFN-60_L7.0-W7.0-P0.40-TL-EP3.4.{step,wrl}` | STEP bounds 7.002 × 7.002 × 0.861; 60 terminals, 0.400 pitch, 3.400 square bottom EP. Pad notch includes R0.20410 arc and R0.100 blends rather than the manufacturer's R0.200 semicircle. | Superseded by Raspberry Pi model; package-compatible approximation only. |
| U4 | `QFN-16_L3.0-W3.0-P0.50-EP1.7.{step,wrl}` | STEP height 0.76010; WRL 0.76022, below 0.80 minimum. 16 terminals, 0.500 pitch, 1.700 square bottom EP. | Reject height mismatch. EP1.7 itself is within tolerance. |
| U5 | `VSON-10_L3.0-W3.0-H0.6-P0.50_TPS.{step,wrl}` | STEP height 0.61100; WRL 0.61011, below 0.80 minimum. 10 terminals, 0.500 pitch; main bottom EP 2.380 × 1.650. | Reject height mismatch. Horizontal dimensions alone are insufficient. |
| J1 | `USB-C_SMD-TYPE-C-31-M-12_1.{step,wrl}` | STEP bounds 8.940 × 7.900 × 4.101 including below-board tabs. Shell 8.940 × 7.300 × 3.200; central pitch 0.500. Only 12 solder-tail shapes: eight 0.200-wide and four merged 0.400-wide tails, versus 16 separate 0.200 ± 0.050 terminals in drawing. | Reject exact solder-terminal geometry; approximate body only. |
| J3 | `CONN-SMD_PH2.00-WS-3P.{step,wrl}` | STEP bounds 10.000 × 8.500 × 5.501; WRL 10.000 × 9.050 × 5.500. Three terminals at 2.000 pitch. Drawing width 9.9, height 5.5; front-to-tail depth 8.6 derived from 6.0 + reference (2.6). | No exact model verified. STEP is approximate; WRL tails are 0.550 longer than STEP after housing alignment. |
| D2 | `LED-SMD_4P-L2.2-W2.0-P1.00_WS2815C-2020-4P.wrl` | WRL bounds 2.20015 × 2.00000 × 0.83998; four bottom terminals, 1.000 pitch, 1.13005 inner gap. Exact WS2812C drawing specifies 2.20 × 2.00 × 0.84, not 2.00 square. STEP absent. | Reject exact identity claim. Geometry is compatible, but filename identifies WS2815C. |

J1 STEP and WRL have matching envelope sizes but a +0.250 Y shift in WRL. J3 housing alignment requires approximately +2.000 X and −2.900 Y on STEP coordinates; the residual 0.550 tail-depth difference is geometry, not registration. Neither connector has a central EP. D2 also has no central thermal pad; its four bottom-terminal bounds are approximately 0.525 × 0.700, distinct from the suggested 0.700 square PCB lands.

Connector/LED drawing sources:

- J1: [BOM-linked LCSC C165948 listing](https://www.lcsc.com/product-detail/USB-Connectors_HRO-TYPE-C-31-M-12_C165948.html), [HRO TYPE-C-31-M-12 drawing](https://datasheet.lcsc.com/datasheet/pdf/9e56b777c022540fcce7c7f67825f55e.pdf?productCode=C165948), p.1/1, 2020-12-08. Shell depth 7.35 with general ±0.15 tolerance; shell height 3.20 ± 0.05. Approximate shell agreement does not fix merged tails.
- J3: [JST ePH.pdf](https://www.jst-mfg.com/product/pdf/eng/ePH.pdf), p.4 side-entry SMT header, p.2 separate PCB pattern. No general mechanical tolerance establishes the 10.0 versus 9.9 width as compliant or a proven tolerance failure. Undimensioned cavity/key details cannot be certified exact.
- D2: [Worldsemi WS2812C-2020-V6 PDF](https://www.world-semi.com/downloads/datasheets/en/ws2812c-2020-v6-2.1.pdf), p.2/10, retrieved document V1.1, drawing tolerance ±0.15. Matching size, tier height 0.280, pitch, and inner gap do not distinguish different LEDs sharing a package.

## Visualization registration

Transforms below apply before the footprint's board position and rotation. Offsets are millimeters in Cartesian model coordinates. A transformed model point `(x, y)` corresponds to footprint-local 2D `(x, -y)`. All scales are 1 and all Z offsets are 0. U1/U4/U5 use zero offset and rotation. No model geometry was changed.

| Ref | Z rotation | Offset X, Y, Z | Registration against footprint |
|---|---:|---|---|
| J1 STEP | 180° | 0, −1.05, 0 | Shell Y bounds −4.70…+2.60 become −3.65…+3.65, matching the fab body. Tail Y bounds −5.30…−4.25 become +3.20…+4.25, overlapping the pad row at local 2D Y = −4.045. Central tail X centers ±0.25, ±0.75, ±1.25, ±1.75 match the pad columns after rotation. |
| J3 STEP | 0° | +2.00, −2.90, 0 | Terminal X centers −4, −2, 0 become −2, 0, +2, matching pads 1–3. Mounting-tab centers (−6.125, 0), (+2.125, 0) become (−4.125, −2.9), (+4.125, −2.9), inside MP pads centered at local 2D (±4.35, +2.9). Signal tails reach model Y = +3.95 after translation and overlap lands spanning Cartesian Y = +1.10…+4.60. |
| D2 WRL | 0° | 0, 0, 0 | Four bottom-terminal centers are approximately (±0.8275, ±0.5000), inside the four lands centered at (±0.915, ±0.550) in footprint-local 2D. Body remains centered, 2.20 × 2.00 × 0.84. Device identity and polarity marking are not certified by this shared model. |

J1's shell bottom is Z = 0.05, its tails seat at Z = 0, and its mounting tabs extend to Z = −0.85. J3's mounting tabs and terminal seating faces are at Z = 0. D2's bottom terminals are at Z = 0. The side view confirms the bodies sit above the board, with J1 tabs entering the board rather than floating above it.

Verification on 2026-11-13: attached all six models through kipy on `scratch/models-visualization.kicad_pcb`, with the assets copied under `scratch/lib/3d` to check the saved portable paths. Compared the [top](../../scratch/models-top.png) and [left-side](../../scratch/models-side.png) renders against the pads. J1's existing board rotation is 180°, J3's is −90°, and D2's is 0°. These rotations were retained, not folded into the model transforms.
