from ipc_client import *
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);ids=[];updates=[]
for o in objs:
 if isinstance(o,(pcb.Track,pcb.Via,pcb.Arc)) and o.net.name=='/USB_EN2':
  if isinstance(o,pcb.Via):ps=[o.position]
  else:ps=[o.start,o.end]
  if min(p.x_nm/1e6 for p in ps)<116 and max(p.x_nm/1e6 for p in ps)>113.5 and min(p.y_nm/1e6 for p in ps)<128 and max(p.y_nm/1e6 for p in ps)>125.5:ids.append(o.id)
 if isinstance(o,pcb.Via) and o.id.value=='e975895d-8300-4616-b493-25301e8755e7':o.position.CopyFrom(xy(114.75,127));updates.append(o)
 if isinstance(o,pcb.Track) and o.id.value=='c76958c0-0264-4a8d-a0f4-1461bfddc2d2':o.end.CopyFrom(xy(114.75,127));updates.append(o)
cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=ids));c.update(d,updates);c.end(d,cid,'Keep charger enable escape clear of adjacent control and ISET resistor');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);print('Cleared',len(ids),'charger control routes')
