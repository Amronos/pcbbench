# Saved-board assembly orientation guide

Generated UTC: 2026-11-10T02:12:01.626690+00:00

Board: `/Users/ec2-user/pcbbench-run/Atlas2350.kicad_pcb`
Board SHA-256: `d566adf81f6cd3687b7653f3ec31e04d1cb71c4ed3aec2fcd21980b33ea612a8`

This package records saved geometry; it does not run or certify ERC, DRC, DFM, firmware testing or production release.

All coordinates are millimetres in the absolute KiCad board/page frame: (0,0) is the saved board coordinate origin, X increases right and Y increases down in the top view. No auxiliary-origin subtraction, bottom-view mirroring or placement centroid correction is applied. Placement X/Y is the saved footprint anchor, not a calculated package centroid. Pad X/Y is the actual transformed pad center (hole center for plated pads).

Rotation is the saved KiCad footprint angle in degrees, counter-clockwise as viewed from the top. The normalized column is modulo360. Machine zero-angle/reel orientation must be reconciled by the assembler; these exports do not invent an IPC or pick-and-place rotation conversion. Bottom-side parts retain the same top-view coordinates; convert for a machine only after its convention is established.

The SVG includes every real component, including THT and mixed packages. Envelope polygons are footprint courtyards, including the RF antenna keepout, not physical package edges. Red squares are all occurrences of literal pad1; USB-C without literal pad1 uses contact A1, explicitly labeled in the tables. Pin1 is a numbering/orientation reference, not a universal polarity mark. Nonpolar parts still have numbered pads. Repeated shell, switch and thermal pad numbers are retained as separate occurrences in assembly-pinout.csv. Unnumbered NPTH features belonging to real components have separate non-electrical rows; H*/TP* features are excluded.

Assembly all real components in parts.csv/bom.csv, including through-hole connectors and mixed SMT/THT shell stakes. SMT modules with plated thermal features are identified separately from THT lead-mounted components. Consult assembly-pinout.csv for actual pad geometry/net assignments; do not infer lead holes from component category alone.

Package is the actual saved footprint library identifier. Manufacturer/full MPN/value are validated against design.json and saved fields where present. H*/TP* features are excluded, not DNP; real parts marked DNP/excluded, missing parts, conflicting values/fields or declared-net mismatches stop packaging rather than silently omitting them.

## Complete component orientation table

| Ref | Full MPN | Side / mounting | X mm | Y mm | KiCad angle ° | Pin1/contact reference positions mm |
|---|---|---|---:|---:|---:|---|
| C1 | GRM155R71C104KA88D | top / SMT | 29.000000 | 48.300000 | 0.000000 | 1[1]=(28.520000,48.300000) |
| C2 | GRM155R71C104KA88D | top / SMT | 33.000000 | 48.300000 | 0.000000 | 1[1]=(32.520000,48.300000) |
| C3 | GRM155R71C104KA88D | top / SMT | 35.000000 | 46.000000 | 90.000000 | 1[1]=(35.000000,46.480000) |
| C4 | GRM155R71C104KA88D | top / SMT | 34.700000 | 38.300000 | 0.000000 | 1[1]=(34.220000,38.300000) |
| C5 | GRM155R71C104KA88D | top / SMT | 31.400000 | 35.500000 | 90.000000 | 1[1]=(31.400000,35.980000) |
| C6 | GRM155R71C104KA88D | top / SMT | 27.200000 | 36.000000 | 90.000000 | 1[1]=(27.200000,36.480000) |
| C7 | GRM155R71C104KA88D | top / SMT | 24.200000 | 38.900000 | 180.000000 | 1[1]=(24.680000,38.900000) |
| C8 | GRM155R71C104KA88D | top / SMT | 24.200000 | 42.800000 | 180.000000 | 1[1]=(24.680000,42.800000) |
| C9 | GRM155R71C104KA88D | top / SMT | 24.200000 | 44.000000 | 180.000000 | 1[1]=(24.680000,44.000000) |
| C10 | GRM155R71C104KA88D | top / SMT | 25.500000 | 36.800000 | 90.000000 | 1[1]=(25.500000,37.280000) |
| C11 | GRM155R71C104KA88D | top / SMT | 31.000000 | 48.300000 | 0.000000 | 1[1]=(30.520000,48.300000) |
| C12 | GRM155R71C104KA88D | top / SMT | 29.600000 | 35.500000 | 90.000000 | 1[1]=(29.600000,35.980000) |
| C13 | GRM155R71C104KA88D | top / SMT | 35.400000 | 42.000000 | 0.000000 | 1[1]=(34.920000,42.000000) |
| C14 | GRM155R71C104KA88D | top / SMT | 16.000000 | 52.000000 | 90.000000 | 1[1]=(16.000000,52.480000) |
| C15 | GRM155R71C104KA88D | top / SMT | 25.000000 | 56.000000 | 90.000000 | 1[1]=(25.000000,56.480000) |
| C16 | GRM155R71C104KA88D | top / SMT | 17.000000 | 15.000000 | 90.000000 | 1[1]=(17.000000,15.480000) |
| C17 | GRM155R71C104KA88D | top / SMT | 19.500000 | 33.500000 | 0.000000 | 1[1]=(19.020000,33.500000) |
| C18 | GRM155R71C104KA88D | top / SMT | 12.500000 | 21.500000 | 0.000000 | 1[1]=(12.020000,21.500000) |
| C19 | GRM155R71C104KA88D | top / SMT | 39.000000 | 19.000000 | 90.000000 | 1[1]=(39.000000,19.480000) |
| C20 | GRM155R71C104KA88D | top / SMT | 39.000000 | 22.000000 | 90.000000 | 1[1]=(39.000000,22.480000) |
| C21 | GRM155R71C104KA88D | top / SMT | 51.000000 | 8.000000 | 0.000000 | 1[1]=(50.520000,8.000000) |
| C22 | GRM155R71C104KA88D | top / SMT | 54.000000 | 4.500000 | 180.000000 | 1[1]=(54.480000,4.500000) |
| C23 | GRM155R71C104KA88D | top / SMT | 68.000000 | 51.000000 | 0.000000 | 1[1]=(67.520000,51.000000) |
| C24 | GRM155R71C104KA88D | top / SMT | 75.000000 | 31.000000 | 90.000000 | 1[1]=(75.000000,31.480000) |
| C25 | GRM188R60J475KE19D | top / SMT | 23.000000 | 37.500000 | 180.000000 | 1[1]=(23.775000,37.500000) |
| C26 | GRM188R61A225KE15D | top / SMT | 24.500000 | 30.000000 | 90.000000 | 1[1]=(24.500000,30.775000) |
| C27 | GRM188R61A225KE15D | top / SMT | 31.000000 | 31.000000 | 90.000000 | 1[1]=(31.000000,31.775000) |
| C28 | GRM21BR61A106KE19L | top / SMT | 12.500000 | 19.500000 | 180.000000 | 1[1]=(13.450000,19.500000) |
| C29 | GRM21BR61A475KA73L | top / SMT | 15.000000 | 15.000000 | 90.000000 | 1[1]=(15.000000,15.950000) |
| C30 | GRM21BR61A106KE19L | top / SMT | 21.000000 | 20.000000 | 0.000000 | 1[1]=(20.050000,20.000000) |
| C31 | GRM21BR61A106KE19L | top / SMT | 17.000000 | 35.000000 | 270.000000 | 1[1]=(17.000000,34.050000) |
| C32 | GRM31CR61C226KE15L | top / SMT | 16.000000 | 26.100000 | 90.000000 | 1[1]=(16.000000,27.575000) |
| C33 | GRM31CR61C226KE15L | top / SMT | 19.000000 | 26.100000 | 90.000000 | 1[1]=(19.000000,27.575000) |
| C34 | GRM21BR60J226ME39L | top / SMT | 51.000000 | 5.500000 | 0.000000 | 1[1]=(50.050000,5.500000) |
| C35 | GRM21BR61A106KE19L | top / SMT | 70.000000 | 49.000000 | 0.000000 | 1[1]=(69.050000,49.000000) |
| C36 | GRM155R61A105KE15D | top / SMT | 77.000000 | 31.000000 | 90.000000 | 1[1]=(77.000000,31.480000) |
| C37 | GRM155R61A105KE15D | top / SMT | 25.500000 | 34.800000 | 90.000000 | 1[1]=(25.500000,35.280000) |
| C38 | GRM1555C1H150JA01D | top / SMT | 38.000000 | 46.000000 | 0.000000 | 1[1]=(37.520000,46.000000) |
| C39 | GRM1555C1H150JA01D | top / SMT | 42.000000 | 41.000000 | 90.000000 | 1[1]=(42.000000,41.480000) |
| C40 | GRM155R71C104KA88D | top / SMT | 33.000000 | 16.000000 | 90.000000 | 1[1]=(33.000000,16.480000) |
| C41 | GRM1555C1H102JA01D | top / SMT | 42.000000 | 16.000000 | 0.000000 | 1[1]=(41.520000,16.000000) |
| C42 | GRM155R71C104KA88D | top / SMT | 21.000000 | 31.500000 | 0.000000 | 1[1]=(20.520000,31.500000) |
| C43 | GRM155R61A105KE15D | top / SMT | 33.000000 | 56.000000 | 90.000000 | 1[1]=(33.000000,56.480000) |
| C44 | GRM21BR61A106KE19L | top / SMT | 54.000000 | 2.000000 | 270.000000 | 1[1]=(54.000000,1.050000) |
| C45 | GRM155R61A105KE15D | top / SMT | 77.000000 | 20.000000 | 90.000000 | 1[1]=(77.000000,20.480000) |
| D1 | WS2812B-2020-V6 | top / SMT | 75.000000 | 27.000000 | 0.000000 | 1[1]=(74.085000,26.450000) |
| F1 | MF-MSMF050-2 | top / SMT | 6.500000 | 25.500000 | 0.000000 | 1[1]=(4.362500,25.500000) |
| FB1 | BLM15AG601SN1D | top / SMT | 27.600000 | 33.800000 | 90.000000 | 1[1]=(27.600000,34.285000) |
| J1 | USB4105-GF-A | top / SMT+THT | 3.000000 | 40.000000 | 270.000000 | A1[1]=(6.680000,36.800000) |
| J2 | S3B-PH-SM4-TB(LF)(SN) | top / SMT | 7.000000 | 14.000000 | 270.000000 | 1[1]=(9.850000,12.000000) |
| J3 | DM3AT-SF-PEJM5 | top / SMT | 68.000000 | 62.000000 | 0.000000 | 1[1]=(70.775000,54.275000) |
| J4 | SM04B-SRSS-TB(LF)(SN) | top / SMT | 76.000000 | 38.000000 | 90.000000 | 1[1]=(74.000000,39.500000) |
| J5 | TSW-110-07-G-D | top / THT | 48.000000 | 49.000000 | 0.000000 | 1[1]=(48.000000,49.000000) |
| J6 | FTSH-105-01-L-D | top / THT | 42.000000 | 28.000000 | 0.000000 | 1[1]=(42.000000,28.000000) |
| J7 | TSW-106-07-G-S | top / THT | 57.000000 | 24.000000 | 90.000000 | 1[1]=(57.000000,24.000000) |
| L1 | XAL4020-102MEC | top / SMT | 12.500000 | 31.000000 | 90.000000 | 1[1]=(12.500000,32.185000) |
| R1 | RC0402FR-075K1L | top / SMT | 10.000000 | 46.000000 | 0.000000 | 1[1]=(9.490000,46.000000) |
| R2 | RC0402FR-075K1L | top / SMT | 10.000000 | 48.000000 | 0.000000 | 1[1]=(9.490000,48.000000) |
| R3 | RC0402FR-0727RL | top / SMT | 24.300000 | 41.600000 | 0.000000 | 1[1]=(23.790000,41.600000) |
| R4 | RC0402FR-0727RL | top / SMT | 24.300000 | 40.400000 | 0.000000 | 1[1]=(23.790000,40.400000) |
| R5 | RC0402FR-073K57L | top / SMT | 15.000000 | 22.000000 | 90.000000 | 1[1]=(15.000000,22.510000) |
| R6 | RC0402FR-073K24L | top / SMT | 19.000000 | 23.000000 | 0.000000 | 1[1]=(18.490000,23.000000) |
| R7 | RC0402FR-07100KL | top / SMT | 21.000000 | 16.000000 | 0.000000 | 1[1]=(20.490000,16.000000) |
| R8 | RC0402FR-0710KL | top / SMT | 21.000000 | 23.000000 | 0.000000 | 1[1]=(20.490000,23.000000) |
| R9 | RC0402FR-0710KL | top / SMT | 21.000000 | 21.800000 | 0.000000 | 1[1]=(20.490000,21.800000) |
| R10 | RC0402FR-07470KL | top / SMT | 35.000000 | 19.000000 | 90.000000 | 1[1]=(35.000000,19.510000) |
| R11 | RC0402FR-07470KL | top / SMT | 37.000000 | 19.000000 | 90.000000 | 1[1]=(37.000000,19.510000) |
| R12 | RC0402FR-071ML | top / SMT | 35.000000 | 22.000000 | 90.000000 | 1[1]=(35.000000,22.510000) |
| R13 | RC0402FR-07330KL | top / SMT | 37.000000 | 22.000000 | 90.000000 | 1[1]=(37.000000,22.510000) |
| R14 | RC0402FR-0710KL | top / SMT | 16.000000 | 47.000000 | 0.000000 | 1[1]=(15.490000,47.000000) |
| R15 | RC0402FR-0710KL | top / SMT | 29.000000 | 51.000000 | 0.000000 | 1[1]=(28.490000,51.000000) |
| R16 | RC0402FR-0733RL | top / SMT | 24.500000 | 46.500000 | 0.000000 | 1[1]=(23.990000,46.500000) |
| R17 | RC0402FR-071KL | top / SMT | 37.200000 | 40.000000 | 0.000000 | 1[1]=(36.690000,40.000000) |
| R18 | RC0402FR-0710KL | top / SMT | 37.000000 | 48.000000 | 90.000000 | 1[1]=(37.000000,48.510000) |
| R19 | RC0402FR-071KL | top / SMT | 34.000000 | 62.000000 | 90.000000 | 1[1]=(34.000000,62.510000) |
| R20 | RC0402FR-0710KL | top / SMT | 53.000000 | 8.000000 | 0.000000 | 1[1]=(52.490000,8.000000) |
| R21 | RC0402FR-0710KL | top / SMT | 54.000000 | 12.000000 | 90.000000 | 1[1]=(54.000000,12.510000) |
| R22 | RC0402FR-071KL | top / SMT | 53.000000 | 16.000000 | 90.000000 | 1[1]=(53.000000,16.510000) |
| R23 | RC0402FR-071KL | top / SMT | 54.000000 | 18.000000 | 90.000000 | 1[1]=(54.000000,18.510000) |
| R24 | RC0402FR-074K7L | top / SMT | 70.000000 | 36.000000 | 90.000000 | 1[1]=(70.000000,36.510000) |
| R25 | RC0402FR-074K7L | top / SMT | 70.000000 | 40.000000 | 90.000000 | 1[1]=(70.000000,40.510000) |
| R26 | RC0402FR-0747KL | top / SMT | 58.000000 | 57.000000 | 90.000000 | 1[1]=(58.000000,57.510000) |
| R27 | RC0402FR-0747KL | top / SMT | 58.000000 | 60.000000 | 90.000000 | 1[1]=(58.000000,60.510000) |
| R28 | RC0402FR-0747KL | top / SMT | 58.000000 | 63.000000 | 90.000000 | 1[1]=(58.000000,63.510000) |
| R29 | RC0402FR-0747KL | top / SMT | 64.000000 | 49.000000 | 0.000000 | 1[1]=(63.490000,49.000000) |
| R30 | RC0402FR-0747KL | top / SMT | 66.000000 | 49.000000 | 0.000000 | 1[1]=(65.490000,49.000000) |
| R31 | RC0402FR-0710KL | top / SMT | 73.000000 | 49.500000 | 0.000000 | 1[1]=(72.490000,49.500000) |
| R32 | RC0402FR-07330RL | top / SMT | 71.000000 | 28.000000 | 0.000000 | 1[1]=(70.490000,28.000000) |
| R33 | RC0402FR-07100KL | top / SMT | 73.000000 | 33.000000 | 90.000000 | 1[1]=(73.000000,33.510000) |
| R34 | RT0402BRD0710KL | top / SMT | 30.000000 | 28.000000 | 90.000000 | 1[1]=(30.000000,28.510000) |
| R35 | RT0402BRD0710KL | top / SMT | 30.000000 | 26.000000 | 90.000000 | 1[1]=(30.000000,26.510000) |
| R36 | RC0402FR-0710KL | top / SMT | 54.000000 | 14.000000 | 90.000000 | 1[1]=(54.000000,14.510000) |
| R37 | RC0402FR-0710KL | top / SMT | 77.000000 | 3.000000 | 90.000000 | 1[1]=(77.000000,3.510000) |
| R38 | RC0402FR-07100RL | top / SMT | 40.000000 | 16.000000 | 0.000000 | 1[1]=(39.490000,16.000000) |
| R39 | RC0402FR-071KL | top / SMT | 15.000000 | 38.000000 | 0.000000 | 1[1]=(14.490000,38.000000) |
| R40 | RC0402FR-0710KL | top / SMT | 21.000000 | 35.500000 | 0.000000 | 1[1]=(20.490000,35.500000) |
| R41 | RC0402FR-07100KL | top / SMT | 21.000000 | 14.000000 | 0.000000 | 1[1]=(20.490000,14.000000) |
| R42 | RT0402BRD07312KL | top / SMT | 22.000000 | 29.000000 | 90.000000 | 1[1]=(22.000000,29.510000) |
| R43 | RT0402BRD07100KL | top / SMT | 22.000000 | 27.000000 | 90.000000 | 1[1]=(22.000000,27.510000) |
| SW1 | TL3342F160QG | top / SMT | 40.000000 | 55.000000 | 0.000000 | 1[1]=(36.850000,53.100000); 1[2]=(43.150000,53.100000) |
| SW2 | TL3342F160QG | top / SMT | 40.000000 | 63.000000 | 0.000000 | 1[1]=(36.850000,61.100000); 1[2]=(43.150000,61.100000) |
| SW3 | TL3342F160QG | top / SMT | 68.000000 | 32.000000 | 0.000000 | 1[1]=(64.850000,30.100000); 1[2]=(71.150000,30.100000) |
| SW4 | TL3342F160QG | top / SMT | 56.000000 | 32.000000 | 0.000000 | 1[1]=(52.850000,30.100000); 1[2]=(59.150000,30.100000) |
| SW5 | JS102011SAQN | top / SMT | 8.000000 | 63.000000 | 270.000000 | 1[1]=(10.750000,60.500000) |
| U1 | RP2350A | top / SMT | 30.000000 | 42.000000 | 90.000000 | 1[1]=(27.200000,45.450000) |
| U2 | W25Q32JVSSIQ | top / SMT | 20.000000 | 52.000000 | 90.000000 | 1[1]=(18.095000,55.587500) |
| U3 | APS6404L-3SQR-SN | top / SMT | 29.000000 | 56.000000 | 90.000000 | 1[1]=(27.095000,58.475000) |
| U4 | BQ24074RGTR | top / SMT | 17.000000 | 19.000000 | 0.000000 | 1[1]=(15.562500,18.250000) |
| U5 | TPS63070RNMR | top / SMT | 17.000000 | 31.000000 | 180.000000 | 1[1]=(18.150000,31.750000) |
| U6 | ESP32-C3-WROOM-02-N4 | top / SMT with plated thermal features | 65.000000 | 7.000000 | 0.000000 | 1[1]=(56.250000,1.000000) |
| U7 | TLV75801PDBVR | top / SMT | 28.000000 | 31.000000 | 0.000000 | 1[1]=(26.862500,30.050000) |
| U8 | USBLC6-2SC6 | top / SMT | 11.500000 | 40.000000 | 0.000000 | 1[1]=(10.362500,39.050000) |
| U9 | TLV9001IDBVR | top / SMT | 36.000000 | 16.000000 | 0.000000 | 1[1]=(34.862500,15.050000) |
| U10 | TPS22919DCKR | top / SMT | 77.000000 | 23.000000 | 0.000000 | 1[1]=(76.162500,22.350000) |
| Y1 | ABM8-272-T3 | top / SMT | 39.000000 | 43.000000 | 0.000000 | 1[1]=(37.900000,43.850000) |

## Files

- `parts.csv`
- `bom.csv`
- `placement.csv`
- `assembly-pinout.csv`
- `top-assembly-orientation.svg`
- `assembly-orientation.md`
- `manifest.json`

No application firmware, fabrication copper exports or bare-board drill files are generated by this script.
