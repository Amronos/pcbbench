from ipc_client import *
from shapely.geometry import Polygon,Point
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);nets={n.name:n for n in c.call(pcbcmd.GetNets(board=d)).nets};new=[]
def via(x,y,name):
 v=pcb.Via(id=uid(),position=xy(x,y),type=pcb.VT_THROUGH,net=nets[name]);v.pad_stack.type=pcb.PST_NORMAL;v.pad_stack.layers.extend([pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_In3_Cu,pcb.BL_In4_Cu,pcb.BL_B_Cu]);v.pad_stack.drill.CopyFrom(pcb.DrillProperties(start_layer=pcb.BL_F_Cu,end_layer=pcb.BL_B_Cu,diameter=xy(.2,.2),shape=pcb.DS_CIRCLE,capped=pcb.VDCM_CAPPED,filled=pcb.VDFM_FILLED));v.pad_stack.copper_layers.add(layer=pcb.BL_F_Cu,shape=pcb.PSS_CIRCLE,size=xy(.45,.45));new.append(v)
via(131.5,137.2,'/SD_CLK_DRV');new.append(pcb.Track(id=uid(),start=xy(131.75,136.4),end=xy(131.5,137.2),width=base.Distance(value_nm=127000),layer=pcb.BL_B_Cu,net=nets['/SD_CLK_DRV']))
for z in objs:
 if isinstance(z,pcb.Zone) and z.type==pcb.ZT_COPPER and pcb.BL_F_Cu in z.layers:
  for fp in z.filled_polygons:
   for p in fp.shapes.polygons:
    a=Polygon([(n.point.x_nm/1e6,n.point.y_nm/1e6) for n in p.outline.nodes if n.HasField('point')])
    if a.bounds[0]>140 and a.area<4 and a.area>1:
     q=a.buffer(-.26)
     if not q.is_empty:
      pt=q.representative_point();via(pt.x,pt.y,'/GND');print('Ground stitch',pt.x,pt.y,flush=True)
cid=c.begin(d);c.create(d,new);c.end(d,cid,'Stitch isolated regulator ground copper and clear the final SD clock escape');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d)
