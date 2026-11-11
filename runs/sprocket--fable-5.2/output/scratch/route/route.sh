#!/bin/bash
# route.sh <in.kicad_pcb> <out.kicad_pcb> [extra kicad-route args]: route with the project's standing options.
# Existing copper is kept and never ripped up. Log goes to <out>.log.
in=$1; out=$2; shift 2
KICAD_RIP_PREEXISTING=0 KICAD_FINALIZE_RIP=0 kicad-route "$in" "$out" \
  --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 ${IN2COST:-3.0} 1.1 \
  --escalation off --strict-sizes --keep-input-copper "$@" > "${out%.kicad_pcb}.log" 2>&1
echo "EXIT=$?" >> "${out%.kicad_pcb}.log"
