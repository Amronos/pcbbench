from ipc_client import *
import json
c=Client();d=c.open(base.DOCTYPE_PCB);j=json.loads((ROOT/'build/drc-current.json').read_text());objs=c.get(d);byid={o.id.value:o for o in objs if hasattr(o,'id')};ids=set()
for v in j['violations']:
 if v['type'] in ['clearance','shorting_items','hole_clearance'] and any('of R13' in i['description'] for i in v['items']):
  for i in v['items']:
   if isinstance(byid.get(i['uuid']),(pcb.Track,pcb.Via,pcb.Arc)):ids.add(i['uuid'])
cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=[base.KIID(value=i) for i in ids]));c.end(d,cid,'Remove old routes crossing relocated USB series resistor');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);print('Removed',len(ids),'obstructing route items')
