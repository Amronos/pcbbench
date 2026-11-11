# Render investigation

Superseded by [the J2 isolation result](../render-isolation/RESULT.md).
The culprit and fully populated recipe are now confirmed.

Root CAD and tools/release.py were not edited. No DRC or router was run.

The clean isometric image is `/tmp/sprocket-no-local.png`. Top and bottom
diagnostic images are `top-partial.png` and `bottom-partial.png` here.
These are actual KiCad renders, but omit the six `${KIPRJMOD}/lib/3d` model
references. They are not complete package illustrations.

With the same config-exact settings and stock-model overlay, the snapshot
without a local lib directory renders cleanly. The snapshot with its lib
symlink renders corrupted polygons across the board. The snapshot PCB bytes
are identical. This implicates local model loading or renderer interaction;
the individual model and precise bug were not isolated.

Recipe from the workspace root:

```sh
KICAD_CONFIG_HOME="$PWD/scratch/render-investigation/config-exact" \
KICAD10_3DMODEL_DIR="$PWD/scratch/render-investigation/models" \
kicad-cli pcb render --quality user --preset follow_plot_settings \
  --width 1400 --height 1100 --background opaque --zoom 0.9 \
  --rotate 325,0,25 -o /tmp/sprocket-no-local.png \
  scratch/render-investigation/partial/sprocket2350.kicad_pcb
```

Omit rotation for top; replace it with `--side bottom` for bottom.
The model overlay follows the existing release.py fallback choices.
Disabling inner copper alone did not fix the original configuration.
The GUI fallback was unavailable because agent-desktop reported no AT-SPI access.

Recommended next investigation: load the six project-local STEP references
one at a time in scratch, preserving the working config and board snapshot.
Do not solve this by changing the authoritative copper or via treatments.
