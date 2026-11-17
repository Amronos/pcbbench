import json, sys
from collections import Counter
d = json.load(open(sys.argv[1]))
for key in ('violations', 'unconnected_items', 'schematic_parity'):
    v = d.get(key, [])
    c = Counter((x['type'], x['severity']) for x in v)
    print(key, len(v), dict(c))
    if '-v' in sys.argv:
        for x in v[:int(sys.argv[sys.argv.index('-v') + 1]) if len(sys.argv) > sys.argv.index('-v') + 1 else 50]:
            print('   ', x['type'], x['description'], [(i['description'], i['pos']) for i in x['items']])
