# Board STEP models

Six real STEP files are stored at the board's requested relative paths. All six
stock filenames were absent from official KiCad packages3D master at commit
`afa6aab16f43a736cd062b8c853863e753653921`.

These files are for mechanical visualization only, not land-pattern design,
manufacturing clearance sign-off, or exact package-detail verification. Renaming
a substitute to the requested filename does not make it an exact stock model.
No board, schematic, footprint, project, or KiCad environment setting was edited.
The board still uses `${KICAD10_3DMODEL_DIR}`. Acquisition alone does not connect
these local files to that environment variable.

## Path mapping and dimensions

All destinations below are relative to `lib/3d/`. Dimensions are mm. Heights come
from the downloaded STEP coordinates. Cartesian-point extents in the manifest
are not a CAD-kernel bounding-box measurement and can include curve control points.

| Ref | Destination | Actual source model | Body and height | Status and limits |
|---|---|---|---|---|
| J2 | `Connector_JST.3dshapes/JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal.step` | ElectronicCats/BastWAN `S2B-PH-SM4-TB(LF)(SN).STEP` | Housing width 7.9, depth 7.6, height 5.5; tails extend 0.1 below seating plane | Same-part community/distributor-style model. Manufacturer origin and redistribution rights not independently confirmed. Raw Y-up orientation requires the transform below. |
| L2 | `Inductor_SMD.3dshapes/L_Coilcraft_XxL4020.step` | KiCad `L_Coilcraft_XAL4020-XXX.step` | Model 4.3 x 4.3 x 2.10 | XAL substitute for XFL4020-222MEC. XFL datasheet specifies 4.0 ±0.3 square and 2.10 max height. Matches maximum envelope, not nominal 4.0 square. Terminal details and markings differ. |
| U1 | `Package_DFN_QFN.3dshapes/QFN-60-1EP_7x7mm_P0.4mm_EP3.4x3.4mm.step` | Raspberry Pi `rpi_rp2350a.step` embedded in official Minimal KiCad archive | Nominal 7 x 7 x 0.85; model point extents 7.02 x 7.02 | Manufacturer same-part RP2350A model, extracted unchanged. 60 pins, 0.4 pitch, EP 3.4 x 3.4. |
| U5 | `Package_DFN_QFN.3dshapes/VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step` | KiCad `WQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm.step` | 3 x 3 x 0.90 | Generic 16-pin package substitute, pitch 0.5 and EP 1.6 x 1.6 match. Height is within TI RGT0016B 1.0 max. Not a manufacturer BQ24074 model. |
| U6 | `Package_SON.3dshapes/Texas_DRC0010J.step` | KiCad `VSON-10-1EP_3x3mm_P0.5mm_EP1.65x2.4mm.step` | 3 x 3 x 0.93 | Generic 10-pin SON substitute. Pitch 0.5 and EP 1.65 x 2.4 match DRC0010J. Height is within its 0.8-1.0 range. Special thermal-pad extensions are not reproduced. |
| U8 | `Package_DFN_QFN.3dshapes/TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm.step` | KiCad `VDFN-8-1EP_2x2mm_P0.5mm_EP0.9x1.7mm.step` | Nominal 2 x 2; point extents 2 x 1.98; height 0.78 | Generic 8-pin DFN substitute, pitch 0.5. Within Maxim T822 0.80 max height. EP is **0.9 x 1.7**, not requested **0.8 x 1.2**. |

## Orientation and offsets

Recommended model-local transforms, before the footprint's own board rotation:

| Ref | Rotation XYZ, degrees | Offset XYZ, mm | Scale XYZ |
|---|---|---|---|
| J2 | `(270, 0, 0)` | `(0, -3.2, 0)` | `(1, 1, 1)` |
| L2, U1, U5, U6, U8 | `(0, 0, 0)` | `(0, 0, 0)` | `(1, 1, 1)` |

J2's raw coordinates use X for width, Y for height, and negative Z for depth.
The recommended transform maps `(x, y, z)` to `(x, -z - 3.2, y)`. Housing depth
0 to 7.6 then maps to footprint Y -3.2 to 4.4, matching the existing F.Fab
outline. Raw X is already centered. The full point range after this transform
is X ±3.95, Y -3.2 to 5.454, Z -0.1 to 5.5; the depth range includes contacts
and curve control points. This transform is recommended from coordinate and
outline comparison, not a live 3D-viewer alignment check. It is **not baked into
the STEP file**. Pin-1/contact alignment and the other models' alignment should
be checked in the viewer before enclosure sign-off.

The official KiCad `JST_PH_S2B-PH-K` through-hole alternative was rejected:
its model is only 5.9 wide and 4.85 high, versus this SMD part's 7.9 and 5.5.
JST's same-part official download exists but requires license acceptance and
contact details. No personal data was supplied.

## Provenance

Full download URLs, model identities, SHA-256 hashes, byte counts, solid entity
counts, and point extents are in [manifest.json](manifest.json).

- KiCad alternatives: [official GitLab repository](https://gitlab.com/kicad/libraries/kicad-packages3D), pinned to the commit above. Original embedded license notices are retained. See [KiCad-LICENSE.md](KiCad-LICENSE.md).
- RP2350A: [official Minimal KiCad download](https://datasheets.raspberrypi.com/rp2350/Minimal-KiCAD.zip). The script downloads the redirected official asset, reads `RPI-RP2350A-MINIMAL_R4-S1.kicad_pcb` in memory, and decodes the base64/zstd embedded `rpi_rp2350a.step`. Archive hash is recorded. See [RaspberryPi-LICENSE.txt](RaspberryPi-LICENSE.txt).
- J2: [ElectronicCats/BastWAN source](https://github.com/ElectronicCats/BastWAN/blob/master/Hardware/bast-wan.pretty/packages3d/S2B-PH-SM4-TB(LF)(SN)--3DModel-STEP-56544.STEP). STEP header identifies the same part, dated 2018-11-06, SolidWorks 2017. This is not claimed to be an official JST download. Check redistribution rights before publishing it.

Dimension references:

- [Coilcraft XFL4020 datasheet](https://www.coilcraft.com/getmedia/50632d43-da1b-4cdb-8ab4-3029cab51df3/xfl4020.pdf), mechanical drawing on page 3.
- [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf), RP2350A package drawing.
- [TI RGT package reference](https://www.ti.com/lit/ds/symlink/cdclvp1102.pdf), RGT0016B outline used by the board's stock footprint.
- [TI TPS63000 datasheet](https://www.ti.com/lit/ds/symlink/tps63000.pdf), DRC0010J outline.
- [Maxim 21-0168 TDFN drawing](https://www.analog.com/media/en/package-pcb-resources/package/pkg_pdf/tdfn-ep/21-0168.pdf), T822 package.
- [JST PH series](https://www.jst-mfg.com/product/index.php?series=199&lang=2), S2B-PH-SM4-TB.

## Fetch and verify

From the workspace root, with Python 3 and `zstd` installed:

```sh
python tools/fetch_models.py
python tools/fetch_models.py --check
```

The script writes only under `lib/3d/`. It rejects HTML, LFS pointers, missing
STEP sections, incomplete terminators, missing solid entities, and missing mm
units. Offline `--check` also verifies hashes against the manifest. Files are
downloaded or extracted without geometry edits. No router, DRC, or CAD export
jobs are involved.
