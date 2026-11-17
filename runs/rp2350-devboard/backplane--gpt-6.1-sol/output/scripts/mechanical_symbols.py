from ipc_client import *
from library_build import sym
import sexpdata as sx,json
p=DESIGN/'connect.kicad_sym';root=sx.loads(p.read_text())
for name in ['MountingHole','Fiducial']:
 if not any(isinstance(a,list) and str(a[0])=='symbol' and a[1]==name for a in root):root.append(sym('Mechanical',name))
p.write_text(sx.dumps(root)+'\n')
c=Client();c.call(project.CloseAllDocuments(force=False));board=c.open(base.DOCTYPE_PCB);fps={f.reference_field.text.text.text:f for f in c.get(board) if isinstance(f,pcb.FootprintInstance)};d=c.open(base.DOCTYPE_SCHEMATIC);existing=c.get(d);new=[];updates=[];ids={}
for o in existing:
 if isinstance(o,sch.SchematicText) and '4-layer PCB' in o.text.text:o.text.text=o.text.text.replace('4-layer PCB','6-layer PCB');updates.append(o)
for i,ref in enumerate(['H1','H2','H3','H4','FID1','FID2','FID3']):
 f=fps[ref];name='MountingHole' if ref[0]=='H' else 'Fiducial';definition=c.lib(base.LT_SYMBOL,'connect:'+name);x=210+i*25.4;y=380.0;id=uid();ids[ref]=id.value
 inst=sch.SchematicSymbolInstance(id=id,position=xy(x,y),definition=definition,unit=sch.SchematicSymbolUnit(unit=1),transform=sch.SchematicSymbolTransform(orientation=sch.SSO_0),attributes=sch.SchematicSymbolAttributes(exclude_from_bill_of_materials=True,exclude_from_position_files=True))
 inst.reference_field.CopyFrom(sch.SchematicField(name='Reference',text=txt(ref,x+2.54,y-3.81,1.0),visible=True));inst.value_field.CopyFrom(sch.SchematicField(name='Value',text=txt('M2.5' if ref[0]=='H' else 'Fiducial',x+2.54,y-1.27,.85),visible=True));inst.footprint_field.CopyFrom(sch.SchematicField(name='Footprint',text=txt('connect:'+f.definition.id.entry_name,x,y),visible=False));new.append(inst)
new.append(sch.SchematicText(id=uid(),text=txt('PCB features: four 2.7mm mounting holes and three 1mm fiducials; no purchased parts',210,367.5,1.0)))
cid=c.begin(d);c.create(d,new);c.update(d,updates);c.end(d,cid,'Document mechanical PCB features and final six-layer stack');c.save(d)
changes=[]
for ref,id in ids.items():
 f=fps[ref];u=pcb.FootprintInstance(id=f.id,symbol_path=base.SheetPath(path=[base.KIID(value=id)]),symbol_sheet_name='/',symbol_sheet_filename='rp2350-connect.kicad_sch');u.value_field.CopyFrom(f.value_field);u.value_field.text.text.text='M2.5' if ref[0]=='H' else 'Fiducial';changes.append(u)
cid=c.begin(board);c.update(board,changes);c.end(board,cid,'Associate holes and fiducials with excluded schematic symbols');c.save(board)
(ROOT/'build/mechanical-symbol-ids.json').write_text(json.dumps(ids,indent=2)+'\n');print('Saved seven non-purchased PCB symbols')
