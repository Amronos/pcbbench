#!/bin/bash
# drc.sh [board]: run DRC into scratch/drc.json and print the summary
cd /home/ubuntu/pcbbench-run
kicad-cli pcb drc --refill-zones --schematic-parity --severity-all --format json -o scratch/drc.json "${1:-rp2350-devboard.kicad_pcb}" >/dev/null 2>&1
kicad-python scratch/pcb/drcsum.py scratch/drc.json
