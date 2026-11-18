from ipc_client import *
import json
c=Client();c.call(project.CloseAllDocuments(force=False))
p=DESIGN/'rp2350-connect.kicad_pro';j=json.loads(p.read_text());r=j['board']['design_settings']['rules'];r.update(min_clearance=0.127,min_via_diameter=0.45,min_through_hole_diameter=0.2,min_via_annular_width=0.125)
for cl in j['net_settings']['classes']:
 cl['clearance']=0.127;cl['via_diameter']=0.45;cl['via_drill']=0.2
 if cl['name']=='Power':cl['track_width']=0.25
 elif cl['name'] in ['Default','Memory']:cl['track_width']=0.15
p.write_text(json.dumps(j,indent=2)+'\n');doc=c.open(base.DOCTYPE_PCB)
objects=c.get(doc);bad=[o.id for o in objects if isinstance(o,pcb.Via) and abs(o.position.x_nm/1e6-175)<.001 and abs(o.position.y_nm/1e6-155)<.001]
if bad:
 cid=c.begin(doc);c.call(editor.DeleteItems(header=base.ItemHeader(document=doc),item_ids=bad));c.end(doc,cid,'Remove ground stitch inside microSD mechanical keepout');c.save(doc)
print('Updated 5mil spacing, 6mil signal routes, 0.2mm drill / 0.45mm routing vias')
