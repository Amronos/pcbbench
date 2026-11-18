#!/usr/bin/env python3
"""Export the netlist from the schematic with kicad-cli and compare it with design.py.
Writes build/netlist.json = {ref: {pad: netname}} using KiCad's net names."""
import os, sys, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexpr import parse, find, findall
import design as D
K = '/home/ubuntu/pcbbench-hub/bin/kicad-cli'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sch = os.path.join(ROOT, 'boards', D.NAME, D.NAME + '.kicad_sch')
out = os.path.join(ROOT, 'build', 'netlist.net')
subprocess.run([K, 'sch', 'export', 'netlist', '--format', 'kicadsexpr', '-o', out, sch], check=True, capture_output=True)
e = parse(open(out).read())
got = {}
for n in findall(find(e, 'nets'), 'net'):
    name = find(n, 'name')[1]
    for nd in findall(n, 'node'):
        got.setdefault(find(nd, 'ref')[1], {})[find(nd, 'pin')[1]] = name
bad = 0
for p in D.P:
    for pin, net in p['nets'].items():
        g = got.get(p['ref'], {}).get(pin)
        if net is None:
            ok = g is None or g.startswith('unconnected-')
        elif net in D.PWR:
            ok = g == net
        else:
            ok = g == '/' + net
        if not ok:
            bad += 1; print('MISMATCH', p['ref'], pin, 'want', net, 'got', g)
# every net must have >= 2 nodes unless unconnected
cnt = {}
for r, pins in got.items():
    for pin, n in pins.items(): cnt.setdefault(n, []).append(r + '.' + pin)
for n, nodes in cnt.items():
    if len(nodes) < 2 and not n.startswith('unconnected-'):
        bad += 1; print('SINGLE-NODE NET', n, nodes)
comps = {find(c, 'ref')[1] for c in findall(find(e, 'components'), 'comp')}
want = {p['ref'] for p in D.P}
if comps != want: bad += 1; print('component set differs', comps ^ want)
json.dump(got, open(os.path.join(ROOT, 'build', 'netlist.json'), 'w'), indent=1, sort_keys=True)
print('netlist check:', 'OK' if not bad else '%d problems' % bad, '-', len(cnt), 'nets,', len(comps), 'components')
sys.exit(1 if bad else 0)
