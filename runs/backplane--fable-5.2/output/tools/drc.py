#!/usr/bin/env python3
"""run DRC and print a compact summary. usage: drc.py [--refill] [--all]"""
import sys, os, subprocess, json, re
from collections import Counter
import design as D
K = '/home/ubuntu/pcbbench-hub/bin/kicad-cli'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PCB = os.path.join(ROOT, 'boards', D.NAME, D.NAME + '.kicad_pcb')
cmd = [K, 'pcb', 'drc', '--format', 'json', '--severity-all', '--schematic-parity', '-o', '/tmp/drc.json']
if '--refill' in sys.argv: cmd += ['--refill-zones', '--save-board']
subprocess.run(cmd + [PCB], capture_output=True)
j = json.load(open('/tmp/drc.json'))
def loc(it):
    p = it.get('pos', {}); return '(%.2f,%.2f)' % (p.get('x', 0) - D.OX, p.get('y', 0) - D.OY)
c = Counter()
for v in j.get('violations', []):
    c[v['type'] + '/' + v['severity']] += 1
    if '--all' in sys.argv or v['severity'] == 'error':
        print(v['type'], '|', v['description'][:90], '|', ' ; '.join(i['description'][:60] + loc(i) for i in v['items']))
print('--- unconnected')
for v in j.get('unconnected_items', []):
    print('  ', ' <-> '.join(i['description'][:70] + loc(i) for i in v['items']))
for v in j.get('schematic_parity', []):
    c['parity'] += 1; print('PARITY', v['description'][:100], [i['description'][:60] for i in v['items']])
print(dict(c), 'unconnected:', len(j.get('unconnected_items', [])))
