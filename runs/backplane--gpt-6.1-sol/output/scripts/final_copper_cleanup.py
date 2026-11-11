from ipc_client import *
import json
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);updates=[];ids=[]
for o in objs:
 if isinstance(o,pcb.Zone) and o.type==pcb.ZT_COPPER and pcb.BL_F_Cu in o.layers:o.copper_settings.connection.zone_connection=pcb.ZCS_FULL;updates.append(o)
 if isinstance(o,pcb.Via) and o.id.value=='d3648ceb-d8f6-44b3-a425-5eb0799c31f0':ids.append(o.id)
j=json.loads((ROOT/'build/drc-current.json').read_text());byid={o.id.value:o for o in objs if hasattr(o,'id')}
for v in j['violations']:
 if v['type'] in ['via_dangling','track_dangling']:
  for i in v['items']:
   if isinstance(byid.get(i['uuid']),(pcb.Track,pcb.Via,pcb.Arc)):ids.append(base.KIID(value=i['uuid']))
ids={i.value:i for i in ids}
cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=list(ids.values())));c.update(d,updates);c.end(d,cid,'Remove redundant route stubs and join top ground islands directly to through-hole ground pads');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);print('Removed',len(ids),'redundant route items')
