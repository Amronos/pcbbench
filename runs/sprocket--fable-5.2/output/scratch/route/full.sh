#!/bin/bash
# full.sh <tag> [fix rounds]: power nets first, then everything else, then rounds that reroute only the nets
# still open (rip-up of router copper allowed, hand-drawn copper is locked). Best board: <tag>_best.kicad_pcb
cd /home/ubuntu/pcbbench-run/scratch/route
tag=$1; rounds=${2:-6}
export IN2COST=${IN2COST:-1.5}
open() { grep -a JSON_SUMMARY_MIN "$1" | tail -1 | kicad-python -c "
import sys, json
d = json.loads(sys.stdin.read().split('JSON_SUMMARY_MIN: ')[1])
print(' '.join(d['pad_pairs_open']['nets']))"; }
./route.sh ../../rp2350-devboard.kicad_pcb ${tag}_p.kicad_pcb --nets VBUS +BATT /VSYS \
  --power-nets VBUS /VSYS --power-nets-widths 0.5 0.5
./route.sh ${tag}_p.kicad_pcb ${tag}_0.kicad_pcb --max-ripup 6
cur=${tag}_0; nets=$(open $cur.log); echo "round 0: $nets"
for i in $(seq 1 $rounds); do
  [ -z "$nets" ] && break
  extra=("" "--ordering inside_out" "--via-cost 40" "--direction backward" "--via-cost 40 --ordering inside_out" "--turn-cost 300")
  ./fix.sh $cur.kicad_pcb ${tag}_$i.kicad_pcb $nets --max-ripup 6 ${extra[$(( (i - 1) % 6 ))]} > /dev/null
  new=$(open ${tag}_$i.log); echo "round $i: $new"
  if grep -aq '"improvement_gate": "reverted"' ${tag}_$i.log; then continue; fi
  cur=${tag}_$i; nets=$new
done
for e in kicad_pcb kicad_pro kicad_dru; do cp $cur.$e ${tag}_best.$e; done
echo "best: $cur open: $nets"
