#!/bin/bash
# regenerate the schematic in the workspace root, run ERC, export the netlist and docs/
set -e
cd /home/ubuntu/pcbbench-run
kicad-python scratch/sch/gen_sch.py /home/ubuntu/pcbbench-run/rp2350-devboard.kicad_sch
kicad-cli sch erc --severity-all --format json -o scratch/erc.json rp2350-devboard.kicad_sch
kicad-cli sch export netlist -o scratch/rp2350-devboard.net rp2350-devboard.kicad_sch
kicad-cli sch export png --dpi 150 -o docs rp2350-devboard.kicad_sch
kicad-cli sch export pdf -o docs/schematic.pdf rp2350-devboard.kicad_sch
grep -c '"severity"' scratch/erc.json || true
