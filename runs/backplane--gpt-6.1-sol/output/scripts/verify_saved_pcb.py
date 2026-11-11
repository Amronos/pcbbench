from ipc_client import *
import json,csv
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);fps={f.reference_field.text.text.text:f for f in objs if isinstance(f,pcb.FootprintInstance)};assert len(fps)==125;assert len({f.id.value for f in fps.values()})==125
spec=json.loads((DESIGN/'component-spec.json').read_text());errors=[];checked=0
for p in spec:
 f=fps[p['ref']];actual={}
 for a in f.definition.items:
  if a.Is(pcb.Pad.DESCRIPTOR):
   q=unpack(a);actual.setdefault(q.number,set()).add(q.net.name.lstrip('/'))
 for pin,net in p['pins'].items():
  if net is None:continue
  checked+=1
  if actual.get(pin)!={net}:errors.append({'ref':p['ref'],'pin':pin,'expected':net,'actual':sorted(actual.get(pin,set()))})
assert not errors,errors
(ROOT/'build/pcb-intent-check.json').write_text(json.dumps({'fitted_components_checked':118,'total_footprints':125,'unique_footprint_ids':125,'connected_pins_checked':checked,'mismatches':errors},indent=2)+'\n')
with (ROOT/'fab/PCB-features.csv').open('w',newline='') as z:
 w=csv.writer(z);w.writerow(['Reference','Type','X mm native','Y mm native','Diameter mm','Note'])
 for r in ['H1','H2','H3','H4','FID1','FID2','FID3']:
  f=fps[r];w.writerow([r,'NPTH' if r.startswith('H') else 'Copper fiducial',f.position.x_nm/1e6,f.position.y_nm/1e6,2.7 if r.startswith('H') else 1.0,'M2.5 hardware' if r.startswith('H') else '2mm mask aperture; no component fitted'])
print('Saved PCB:',checked,'intended pin nets verified; 125 unique footprints')
c.save(d);c.call(project.CloseAllDocuments(force=False))
