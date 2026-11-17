#!/bin/sh
# ERC + per-sheet PNG renders into $1 (default /tmp/work/sch)
set -e
cd "$(dirname "$0")/.."
OUT=${1:-/tmp/work/sch}
rm -rf "$OUT"; mkdir -p "$OUT"
kicad-cli sch erc --severity-all --format json -o "$OUT/erc.json" rp2350-devboard.kicad_sch | head -1
kicad-cli sch export svg -o "$OUT/" rp2350-devboard.kicad_sch >/dev/null
for f in "$OUT"/*.svg; do rsvg-convert -w 2800 -b white "$f" -o "${f%.svg}.png"; done
