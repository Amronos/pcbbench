# J2 model transform caused the broken renders

Six isolated renders used the same PCB snapshot, config, stock-model overlay,
camera and quality. Only one project-local model was available in each case.
Every output was inspected with parse_file.

| Case | Ref | Local model | Result |
|---|---|---|---|
| 0 | None | No project-local models | Clean, incomplete |
| 1 | J2 | JST_PH_S2B-PH-SM4-TB | Whole-board polygon corruption |
| 2 | L2 | L_Coilcraft_XxL4020 | Clean, body visible |
| 3 | U1 | QFN-60-1EP | Clean, body visible |
| 4 | U8 | TDFN-8-1EP | Clean, body visible |
| 5 | U5 | VQFN-16-1EP | Clean, body visible |
| 6 | U6 | Texas_DRC0010J | Clean, body visible |

J2's saved model offset was `(xyz 0 -3200000 0)`. Model offsets are mm,
so that placed it 3.2 km away. Its intended offset is -3.2 mm. The huge
scene extent likely causes float/depth precision loss, although the exact
renderer mechanism was not traced.

Correcting only the offset removes the corruption with all models loaded,
but the saved X rotation 90 places J2's housing below the board. X rotation
270 places the housing above the board. Offset +3.2 shifts it over U5;
offset -3.2 aligns the housing and visible leads with the footprint.

The final render-only copy at `oriented/sprocket2350.kicad_pcb` differs from
the frozen source in only these two J2 model-transform values:

```diff
- (offset (xyz 0 -3200000 0))
+ (offset (xyz 0 -3.2 0))
- (rotate (xyz 90 0 0))
+ (rotate (xyz 270 0 0))
```

All 92 model references resolve to existing files. No model geometry was
fabricated, replaced or repaired. Existing local substitutes and provenance
limits from lib/3d/manifest.json still apply. Visual alignment is not a
pin-1 or enclosure sign-off.

Verified full renders:

- `top-oriented.png`
- `isometric-oriented.png`
- `bottom-oriented.png`, including C6/C20 bodies

The same corrected copy also renders clean with a scoped copy of the original
3d_viewer.json, inner copper enabled, and quality basic. That output is
`isometric-original-config.png`. Hiding inner copper is not the required fix.

## Repeat from the workspace root

```sh
KICAD_CONFIG_HOME="$PWD/scratch/render-investigation/config-exact" \
KICAD10_3DMODEL_DIR="$PWD/scratch/render-investigation/models" \
kicad-cli pcb render --width 1400 --height 1100 --quality user \
  --preset follow_plot_settings --background opaque --zoom 0.9 \
  --rotate 325,0,25 -o /tmp/isometric.png \
  scratch/render-isolation/oriented/sprocket2350.kicad_pcb
```

Omit rotation for top. Use `--side bottom` instead for bottom.
The oriented directory's lib symlink makes the six KIPRJMOD models available.
The stock overlay uses the existing release.py model-selection policy.

## API warning for the parent

Installed kipy's Vector3D fields and parameter names say nm, but KiCad uses
the model offset vector directly in mm. The required assignments are:

```python
model.offset = Vector3D.from_xyz(0, -3.2, 0)
model.rotation = Vector3D.from_xyz(270, 0, 0)
```

At inspection, tools/finish_layout.py still assigned rotation 90. Running
that version again would restore the below-board orientation.

I did not edit root CAD, root scripts, global preferences or model files.
The parent changed the authoritative board during this investigation.
These images use the frozen 08:46 snapshot, SHA256
`9d7390b16ae54b51ec2efebaf51ee5de8b64767f4210945b384c9367e2fffda5`,
plus the two render-only J2 corrections. No DRC or router ran. All renders
were sequential. The scripts and case images are retained as evidence.
