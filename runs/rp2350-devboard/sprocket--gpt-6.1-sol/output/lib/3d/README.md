# Component models for visualization

`tools/models.py` attaches all six models below by default. U1, U4, and U5 use manufacturer geometry. J1, J3, and D2 use body approximations. These attachments are for visualization, not mechanical signoff or land-pattern validation. They do not change the BOM or footprints.

| Ref | BOM part | Selected file | Status |
|---|---|---|---|
| U1 | Raspberry Pi RP2350A | `rpi_rp2350a.step` | Manufacturer reference-design model. |
| U4 | TI BQ24074RGTR | `RGT0016C.stp` | Manufacturer's exact package model. |
| U5 | TI TPS63001DRCR | `DRC0010J.stp` | Manufacturer's exact package model. |
| J1 | HRO TYPE-C-31-M-12 | `TYPE-C-31-M-12.3dshapes/USB-C_SMD-TYPE-C-31-M-12_1.step` | Visualization-only body approximation; outer solder tails are merged. |
| J3 | JST S3B-PH-SM4-TB(LF)(SN) | `S3B-PH-SM4-TB.3dshapes/CONN-SMD_PH2.00-WS-3P.step` | Visualization-only body approximation; STEP and WRL differ. |
| D2 | Worldsemi WS2812C-2020-V6 | `WS2812C-2020-V6.3dshapes/LED-SMD_4P-L2.2-W2.0-P1.00_WS2815C-2020-4P.wrl` | Visualization-only matching envelope; filename identifies WS2815C, not the BOM device. STEP unavailable. |

See [dimension checks and registration evidence](dimensions.md). EasyEDA downloads remain unchanged in their original `.3dshapes` directories.

## Sources

Downloaded 2026-11-13:

- U1: [Raspberry Pi reference design](https://pip.raspberrypi.com/documents/RP-010328-CA-RP2350A%20Minimal%20KiCAD.zip), `RPI-RP2350A-MINIMAL_R4-S1_public/RPI-RP2350A-MINIMAL_R4-S1.kicad_pcb`. The embedded `rpi_rp2350a.step` was base64-decoded and Zstandard-decompressed without further changes. License: [LICENSE-Raspberry-Pi.txt](LICENSE-Raspberry-Pi.txt).
- U4: [TI RGT0016C](https://webench.ti.com/cad/dlbxl.cgi/newstep/RGT0016C.stp).
- U5: [TI DRC0010J](https://webench.ti.com/cad/dlbxl.cgi/newstep/DRC0010J.stp).
- EasyEDA candidates: `uvx easyeda2kicad --3d --lcsc_id CODE --output lib/3d/NAME`, version 1.0.1. Codes: U1 C42411118, U4 C54313, U5 C28060, J1 C165948, J3 C265101, D2 C55109522.

TI and EasyEDA downloads did not include a redistribution license. Their source terms still apply.

## Attach without changing the root board

Run with the connector's Python, on a board copy:

```sh
kicad-python tools/models.py /absolute/path/to/copy.kicad_pcb
# Optional subset:
kicad-python tools/models.py /absolute/path/to/copy.kicad_pcb --refs J1 J3 D2
```

The script rejects the root board and checks model files and footprint names before updating. It replaces only the requested footprints' model lists through kipy. Re-running it does not duplicate models. Other footprints keep their existing models.

Saved model paths are `${KIPRJMOD}/lib/3d/…`. To render a copy outside the project root, copy `lib/3d` beside that board. The script does not copy assets.

All models use unit scale. See [visualization registration](dimensions.md#visualization-registration) for offsets and rotations. Model offsets in this kipy API are millimeters despite `Vector3D`'s generic `x_nm` field names.

The [top render](../../scratch/models-top.png) and [left-side render](../../scratch/models-side.png) show the attached bodies and pad registration on `scratch/models-visualization.kicad_pcb`.
