"""drcsum.py [drc.json] [-v [type]]: count DRC findings by type; -v lists them (optionally one type)."""
import json, sys, collections
args = [a for a in sys.argv[1:] if not a.startswith('-')]
d = json.load(open(args[0] if args else '/home/ubuntu/pcbbench-run/scratch/drc.json'))
only = args[1] if len(args) > 1 else None
cnt = collections.Counter()
for key in ('violations', 'unconnected_items', 'schematic_parity'):
    for v in d.get(key, []):
        cnt[(v['severity'], v['type'])] += 1
        if '-v' in sys.argv and (only is None or v['type'] == only):
            its = '; '.join(f"{i['description'][:70]} @({i['pos']['x'] - 100:.2f},{i['pos']['y'] - 100:.2f})" for i in v['items'])
            print(v['type'], '|', v['description'][:90], '|', its)
for (s, t), n in sorted(cnt.items()):
    print(f'{n:5d} {s:8s} {t}')
