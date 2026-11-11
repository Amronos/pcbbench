from ipc_client import *
import json
c=Client();c.call(project.CloseAllDocuments(force=False));doc=c.open(base.DOCTYPE_PCB);objs=c.get(doc)
nets={n.name:n for n in c.call(pcbcmd.GetNets(board=doc)).nets}
f=next(f for f in objs if isinstance(f,pcb.FootprintInstance) and f.reference_field.text.text.text=='U1');new=[];report=[]
for a in f.definition.items:
 if not a.Is(pcb.Pad.DESCRIPTOR):continue
 p=unpack(a);n=int(p.number or 0);net=p.net.name
 if not n or net=='/GND' or net.startswith('unconnected-'):continue
 x=p.position.x_nm/1e6;y=p.position.y_nm/1e6;d=1.1 if n%2 else 1.8
 vx,vy=x,y
 if abs(x-133.55)<.01:vx-=d
 elif abs(x-140.45)<.01:vx+=d
 elif abs(y-130.55)<.01:vy-=d
 else:vy+=d
 t=pcb.Track(id=uid(),start=p.position,end=xy(vx,vy),width=base.Distance(value_nm=127000),layer=pcb.BL_F_Cu,net=p.net)
 v=pcb.Via(id=uid(),position=xy(vx,vy),type=pcb.VT_THROUGH,net=p.net)
 v.pad_stack.type=pcb.PST_NORMAL;v.pad_stack.layers.extend([pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_B_Cu])
 v.pad_stack.drill.CopyFrom(pcb.DrillProperties(start_layer=pcb.BL_F_Cu,end_layer=pcb.BL_B_Cu,diameter=xy(.2,.2),shape=pcb.DS_CIRCLE,capped=pcb.VDCM_CAPPED,filled=pcb.VDFM_FILLED))
 v.pad_stack.copper_layers.add(layer=pcb.BL_F_Cu,shape=pcb.PSS_CIRCLE,size=xy(.45,.45));new.extend([t,v]);report.append(dict(pin=n,net=net,track=t.id.value,via=v.id.value,pos=[vx,vy]))
cid=c.begin(doc);c.create(doc,new);c.end(doc,cid,'Add alternating straight MCU escapes for every signal and supply pad');c.save(doc);c.call(pcbcmd.RefillZones(board=doc));c.save(doc)
(ROOT/'build/straight-fanout.json').write_text(json.dumps(report,indent=2)+'\n');print('Saved',len(report),'MCU fanouts')
