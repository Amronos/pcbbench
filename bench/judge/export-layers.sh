#!/usr/bin/env bash
# Exports one PNG per layer, each with the board outline, from ~/package/board.kicad_pcb with the run's KiCad.
# Usage: export-layers.sh <comma-separated layers>
set -euo pipefail
cd ~/package
/opt/kicad-run/bin/kicad-cli pcb export svg --mode-multi --check-zones --exclude-drawing-sheet --page-size-mode 2 \
	--layers "$1" --common-layers Edge.Cuts -o layers board.kicad_pcb >/dev/null
for svg in layers/*.svg; do
	rsvg-convert -w 2400 -b white -o "${svg%.svg}.png" "$svg"
	rm "$svg"
done
rm -f board.kicad_prl
