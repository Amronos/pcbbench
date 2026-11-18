"""Write every non-fixed segment/via of the board into routes.sexp (so gen_pcb can rebuild it)."""
import os, sys, json
from sexp import parse, dumps, find, findall, Sym
HERE = os.path.dirname(os.path.abspath(__file__))
pcb = sys.argv[1]
out = sys.argv[2]
fixed = set(json.load(open(os.path.join(HERE, 'fixed_uuids.json'))))
t = parse(open(pcb).read())
items = []
for e in t[1:]:
    if isinstance(e, list) and e and e[0] in ('segment', 'via', 'arc') and find(e, 'uuid')[1] not in fixed:
        keep = [e[0]]
        for k in e[1:]:
            if isinstance(k, list) and k and k[0] in ('start', 'mid', 'end', 'at', 'size', 'drill', 'width', 'layer', 'layers', 'net', 'uuid'):
                keep.append(k)
        items.append(keep)
open(out, 'w').write('\n'.join(dumps(x) for x in items) + '\n')
print('harvested', len(items), 'items')
