from ipc_client import *
c=Client();d=c.open(base.DOCTYPE_PCB);nets={n.name:n for n in c.call(pcbcmd.GetNets(board=d)).nets};new=[]
for net,x,y in [('/SD_CLK_DRV',141.55,130.275),('/USB_EN2',114.25,127.4)]:
 v=pcb.Via(id=uid(),position=xy(x,y),type=pcb.VT_THROUGH,net=nets[net]);v.pad_stack.type=pcb.PST_NORMAL;v.pad_stack.layers.extend([pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_In3_Cu,pcb.BL_In4_Cu,pcb.BL_B_Cu]);v.pad_stack.drill.CopyFrom(pcb.DrillProperties(start_layer=pcb.BL_F_Cu,end_layer=pcb.BL_B_Cu,diameter=xy(.2,.2),shape=pcb.DS_CIRCLE,capped=pcb.VDCM_CAPPED,filled=pcb.VDFM_FILLED));v.pad_stack.copper_layers.add(layer=pcb.BL_F_Cu,shape=pcb.PSS_CIRCLE,size=xy(.45,.45));new.append(v)
new.append(pcb.Track(id=uid(),start=xy(114.25,126.4375),end=xy(114.25,127.4),width=base.Distance(value_nm=127000),layer=pcb.BL_F_Cu,net=nets['/USB_EN2']))
cid=c.begin(d);c.create(d,new);c.end(d,cid,'Complete SD clock and charger enable escapes');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d)
