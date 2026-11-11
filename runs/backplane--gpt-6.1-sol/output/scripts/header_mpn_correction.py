from ipc_client import *
import json
old='FTSH-105-01-L-DV-K';mpn='FTSH-105-01-L-D-K';note='Through-hole D termination, 1.27mm pitch, keyed position; fits installed PTH SWD footprint.'
c=Client();d=c.open(base.DOCTYPE_PCB);f=next(o for o in c.get(d) if isinstance(o,pcb.FootprintInstance) and o.reference_field.text.text.text=='J8')
for a in f.definition.items:
 z=unpack(a)
 if isinstance(z,pcb.Field) and z.name in ['MPN','Notes']:
  z.text.text.text=mpn if z.name=='MPN' else note;a.Pack(z)
cid=c.begin(d);c.update(d,[f]);c.end(d,cid,'Specify through-hole Samtec SWD header termination');c.save(d);c.call(project.CloseAllDocuments(force=False));s=c.open(base.DOCTYPE_SCHEMATIC);o=next(o for o in c.get(s) if isinstance(o,sch.SchematicSymbolInstance) and o.reference_field.text.text=='J8')
for a in o.user_fields:
 if a.name=='MPN':a.text.text=mpn
 if a.name=='Notes':a.text.text=note
cid=c.begin(s);c.update(s,[o]);c.end(s,cid,'Match through-hole SWD header MPN and procurement note');c.save(s);c.call(project.CloseAllDocuments(force=False))
p=DESIGN/'component-spec.json';j=json.loads(p.read_text())
for a in j:
 if a['ref']=='J8':a['mpn']=mpn;a['note']=note
p.write_text(json.dumps(j,indent=2)+'\n');p=ROOT/'scripts/design_spec.py';p.write_text(p.read_text().replace(old,mpn))
p=ROOT/'README.md';p.write_text(p.read_text().replace('Hirose push-push microSD slot','Hirose microSD slot'))
p=ROOT/'fab/PCBWAY-INSTRUCTIONS.md';t=p.read_text().replace('Fit the SWD header as specified.','Fit J8 as the through-hole Samtec FTSH-105-01-L-D-K with its keyed position.');p.write_text(t)
