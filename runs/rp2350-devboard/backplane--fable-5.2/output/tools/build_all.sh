#!/bin/bash
# Regenerate everything from tools/design.py:  schematic -> netlist check -> placed board with the hand-made
# fan-out -> maze router for the remaining connections -> ground pours -> DRC -> fab outputs.
set -e
cd "$(dirname "$0")"
python3 make_lib.py && python3 make_pro.py
python3 build_sch.py && python3 check_netlist.py
if [ "$1" = "--reroute" ]; then
  python3 build_pcb.py --drop-routes
  python3 maze.py | tail -3
fi
python3 build_pcb.py --pours
python3 drc.py --refill | tail -3
python3 export_fab.py
