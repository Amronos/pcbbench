"""Compare KiCad-exported netlist against design.py."""
import sys
from sexp import parse, find, findall
import design
t = parse(open(sys.argv[1]).read())
kn = {}
for n in findall(find(t, 'nets'), 'net'):
    name = find(n, 'name')[1]
    nodes = frozenset((find(x, 'ref')[1], find(x, 'pin')[1]) for x in findall(n, 'node'))
    kn[name] = nodes
dn = {k: frozenset(v) for k, v in design.nets().items()}
# map by node sets
bad = 0
for name, nodes in dn.items():
    k = kn.get(name) or kn.get('/' + name)
    if k is None:
        # find by membership
        cand = [kk for kk, vv in kn.items() if nodes & vv]
        print('MISSING net', name, 'candidates', cand); bad += 1
        continue
    if k != nodes:
        print('DIFF', name, 'extra', sorted(k - nodes), 'missing', sorted(nodes - k)); bad += 1
for name, nodes in kn.items():
    nm = name.lstrip('/')
    if nm not in dn and not name.startswith('unconnected-') and not name.startswith('Net-('):
        print('EXTRA kicad net', name, sorted(nodes)); bad += 1
    if name.startswith('Net-(') or name.startswith('unconnected-'):
        real = [x for x in nodes if not x[0].startswith('#')]
        if real and not name.startswith('unconnected-'):
            print('UNNAMED', name, sorted(nodes)); bad += 1
comps = {find(c, 'ref')[1] for c in findall(find(t, 'components'), 'comp')}
dcomps = {c['ref'] for c in design.COMPONENTS}
print('components kicad', len(comps), 'design', len(dcomps), 'missing', dcomps - comps, 'extra', comps - dcomps)
print('BAD' if bad else 'NETLIST OK', bad)
