from ipc_client import *
c=Client();d=c.open(base.DOCTYPE_PCB);n=next(n for n in c.call(pcbcmd.GetNets(board=d)).nets if n.name=='/CORE_FB');new=[]
for x,y in [(145.275,135.75),(150.175,139)]:
 v=pcb.Via(id=uid(),position=xy(x,y),type=pcb.VT_THROUGH,net=n);v.pad_stack.type=pcb.PST_NORMAL;v.pad_stack.layers.extend([pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_In3_Cu,pcb.BL_In4_Cu,pcb.BL_B_Cu]);v.pad_stack.drill.CopyFrom(pcb.DrillProperties(start_layer=pcb.BL_F_Cu,end_layer=pcb.BL_B_Cu,diameter=xy(.2,.2),shape=pcb.DS_CIRCLE,capped=pcb.VDCM_CAPPED,filled=pcb.VDFM_FILLED));v.pad_stack.copper_layers.add(layer=pcb.BL_F_Cu,shape=pcb.PSS_CIRCLE,size=xy(.45,.45));new.append(v)
cid=c.begin(d);c.create(d,new);c.end(d,cid,'Provide capped via transitions on core-feedback lands');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d)
