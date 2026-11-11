#!/bin/bash
# fix.sh <in.kicad_pcb> <out.kicad_pcb> <nets...>: reroute the named nets and let the router rip up its own
# earlier copper to make room. Locked (hand-drawn) copper is never ripped.
in=$1; out=$2; shift 2
kicad-route "$in" "$out" --layers F.Cu In1.Cu In2.Cu B.Cu --layer-costs 1.0 -1 ${IN2COST:-1.5} 1.1 \
  ${ESC:---escalation off --strict-sizes} --nets "$@" > "${out%.kicad_pcb}.log" 2>&1
echo "EXIT=$?" >> "${out%.kicad_pcb}.log"
grep -a JSON_SUMMARY_MIN "${out%.kicad_pcb}.log" | tail -1 | cut -c1-500
