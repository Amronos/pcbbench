from ipc_client import *
import json,shutil
c=Client();doc=c.open(base.DOCTYPE_PCB);c.save(doc)
shutil.copy2(DESIGN/'rp2350-connect.kicad_pcb',ROOT/'build/backups/pcb-before-mcu-fanout.kicad_pcb')
planned={(round(x,5),round(y,5)) for x,y,d,n in json.loads((ROOT/'build/plane-vias.json').read_text())}
ids=[]
for o in c.get(doc):
 if isinstance(o,(pcb.Track,pcb.Arc)):
  ps=[o.start,o.end]
  if isinstance(o,pcb.Arc):ps.append(o.mid)
  xmin=min(p.x_nm/1e6 for p in ps);xmax=max(p.x_nm/1e6 for p in ps);ymin=min(p.y_nm/1e6 for p in ps);ymax=max(p.y_nm/1e6 for p in ps)
  if xmin<144 and xmax>130 and ymin<140 and ymax>128:ids.append(o.id)
 elif isinstance(o,pcb.Via):
  x=o.position.x_nm/1e6;y=o.position.y_nm/1e6
  if 130<x<144 and 128<y<140 and (round(x,5),round(y,5)) not in planned:ids.append(o.id)
cid=c.begin(doc);c.call(editor.DeleteItems(header=base.ItemHeader(document=doc),item_ids=ids));c.end(doc,cid,'Clear constrained MCU escape paths for deliberate fanout');c.save(doc)
c.call(pcbcmd.RefillZones(board=doc));c.save(doc)
print('Removed',len(ids),'route items around MCU; saved canonical board')
