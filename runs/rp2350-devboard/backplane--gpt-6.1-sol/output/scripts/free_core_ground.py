from ipc_client import *
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);ids=[]
for o in objs:
 if isinstance(o,pcb.Track) and o.net.name=='/CORE_FB' and min(o.start.x_nm,o.end.x_nm)<145500000 and max(o.start.x_nm,o.end.x_nm)>144000000 and min(o.start.y_nm,o.end.y_nm)<137600000 and max(o.start.y_nm,o.end.y_nm)>135000000:ids.append(o.id)
net=next(n for n in c.call(pcbcmd.GetNets(board=d)).nets if n.name=='/GND');t=pcb.Track(id=uid(),start=xy(145.275,136.25),end=xy(143,136.52),width=base.Distance(value_nm=127000),layer=pcb.BL_F_Cu,net=net)
cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=ids));c.create(d,[t]);c.end(d,cid,'Give core regulator ground a direct reference connection and reroute its feedback around it');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);print('Removed',len(ids),'feedback segments')
