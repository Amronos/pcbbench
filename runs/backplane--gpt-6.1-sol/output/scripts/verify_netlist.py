import json,sexpdata as sx,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=json.loads((ROOT/'boards/rp2350-connect/component-spec.json').read_text());j=sx.loads((ROOT/'build/rp2350-connect.net').read_text());actual={}
for a in j:
 if isinstance(a,list) and str(a[0])=='nets':
  for net in a[1:]:
   name=next(x[1] for x in net if isinstance(x,list) and str(x[0])=='name').lstrip('/')
   for node in net:
    if isinstance(node,list) and str(node[0])=='node':
     d={str(x[0]):x[1] for x in node[1:] if isinstance(x,list)};actual[(d['ref'],d['pin'])]=name
errors=[];tested=0
for c in spec:
 for pin,net in c['pins'].items():
  if net is not None:
   tested+=1
   if actual.get((c['ref'],pin))!=net:errors.append((c['ref'],pin,net,actual.get((c['ref'],pin))))
print('Netlist intent check:',tested,'connected pins,',len(errors),'mismatches')
for error in errors:print(error)
assert not errors
(ROOT/'build/netlist-intent-check.json').write_text(json.dumps({'connected_pins_checked':tested,'mismatches':errors},indent=2)+'\n')
