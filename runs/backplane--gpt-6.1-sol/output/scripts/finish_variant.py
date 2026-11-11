from ipc_client import *
import json
c=Client();c.call(project.CloseAllDocuments(force=False));s=c.open(base.DOCTYPE_SCHEMATIC);sy=next(o for o in c.get(s) if isinstance(o,sch.SchematicSymbolInstance) and o.reference_field.text.text=='U9');sy.footprint_field.text.text='connect:SOT-23-6_LED';cid=c.begin(s);c.update(s,[sy]);c.end(s,cid,'Match separate LED-boost silk footprint in schematic');c.save(s);c.call(project.CloseAllDocuments(force=False))
p=DESIGN/'component-spec.json';j=json.loads(p.read_text())
for a in j:
 if a['ref']=='U9':a['localfp']='connect:SOT-23-6_LED'
p.write_text(json.dumps(j,indent=2)+'\n');d=c.open(base.DOCTYPE_PCB);f=[o for o in c.get(d) if isinstance(o,pcb.FootprintInstance)];assert len(f)==125 and len({o.id.value for o in f})==125;print('Canonical board retains 125 unique footprints')
