from ipc_client import *
import json
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);straight={v['track'] for v in json.loads((ROOT/'build/straight-fanout.json').read_text())};ids=[]
for o in objs:
 if isinstance(o,(pcb.Track,pcb.Arc)):
  if o.layer==pcb.BL_In1_Cu and o.net.name!='/GND' or o.layer==pcb.BL_In4_Cu and o.net.name!='/3V3':ids.append(o.id)
  elif isinstance(o,pcb.Track) and o.net.name=='/GP14' and o.width.value_nm==127000 and o.id.value not in straight:ids.append(o.id)
# Straight charger EN1 escape to a via: voltage logic only, no power route.
nets={n.name:n for n in c.call(pcbcmd.GetNets(board=d)).nets};net=nets['/USB_EN1']
t=pcb.Track(id=uid(),start=xy(114.75,126.4375),end=xy(114.75,127.5),width=base.Distance(value_nm=127000),layer=pcb.BL_F_Cu,net=net)
v=pcb.Via(id=uid(),position=xy(114.75,127.5),type=pcb.VT_THROUGH,net=net)
v.pad_stack.type=pcb.PST_NORMAL;v.pad_stack.layers.extend([pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_In3_Cu,pcb.BL_In4_Cu,pcb.BL_B_Cu]);v.pad_stack.drill.CopyFrom(pcb.DrillProperties(start_layer=pcb.BL_F_Cu,end_layer=pcb.BL_B_Cu,diameter=xy(.2,.2),shape=pcb.DS_CIRCLE,capped=pcb.VDCM_CAPPED,filled=pcb.VDFM_FILLED));v.pad_stack.copper_layers.add(layer=pcb.BL_F_Cu,shape=pcb.PSS_CIRCLE,size=xy(.45,.45))
cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=ids));c.create(d,[t,v]);c.end(d,cid,'Clear obsolete routes from power planes and escape charger control');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);print('Removed',len(ids),'route items, added charger control escape')
