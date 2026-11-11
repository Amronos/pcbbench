from ipc_client import *
from shapely.geometry import Point,LineString,Polygon
from shapely.ops import unary_union
import math
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);pads=[];ob=[];hardB=[];dr=[]
for f in objs:
 if isinstance(f,pcb.FootprintInstance):pads.extend(unpack(a) for a in f.definition.items if a.Is(pcb.Pad.DESCRIPTOR))
for layer in [pcb.BL_F_Cu,pcb.BL_In2_Cu,pcb.BL_In3_Cu,pcb.BL_B_Cu]:
 resp=c.call(pcbcmd.GetPadShapeAsPolygon(board=d,pads=[p.id for p in pads],layer=layer))
 for p,sh in zip(pads,resp.polygons):
  if p.net.name=='/SD_CLK_DRV':continue
  for poly in [sh]:
   pts=[(n.point.x_nm/1e6,n.point.y_nm/1e6) for n in poly.outline.nodes if n.HasField('point')]
   if len(pts)>2:
    a=Polygon(pts).buffer(0);ob.append(a)
    if layer==pcb.BL_B_Cu and (layer in p.pad_stack.layers or p.type in [pcb.PT_PTH,pcb.PT_NPTH]):hardB.append(a)
for o in objs:
 if isinstance(o,pcb.Via):
  if o.net.name!='/SD_CLK_DRV':
   a=Point(o.position.x_nm/1e6,o.position.y_nm/1e6).buffer(o.pad_stack.copper_layers[0].size.x_nm/2e6);ob.append(a);hardB.append(a)
  dr.append(Point(o.position.x_nm/1e6,o.position.y_nm/1e6).buffer(o.pad_stack.drill.diameter.x_nm/2e6+.1+.15+.015))
 elif isinstance(o,pcb.Track) and o.net.name!='/SD_CLK_DRV':ob.append(LineString([(o.start.x_nm/1e6,o.start.y_nm/1e6),(o.end.x_nm/1e6,o.end.y_nm/1e6)]).buffer(o.width.value_nm/2e6))
block=unary_union(ob).buffer(.225+.1+.015).union(unary_union(dr));hard=unary_union(hardB).buffer(.0635+.1+.015);cands=[]
for ix in range(12700,13301,5):
 for iy in range(13400,14201,5):
  x=ix/100;y=iy/100;pt=Point(x,y);line=LineString([(131.75,136.4),(x,y)])
  if not block.covers(pt) and not hard.intersects(line):cands.append(((x-130.3)**2+(y-137.8)**2,x,y,line))
assert cands,'No all-layer-safe outward via found'
_,x,y,line=min(cands,key=lambda p:p[0]);print('Outward SD via',x,y,flush=True);ids=[]
for o in objs:
 if isinstance(o,pcb.Track) and o.layer==pcb.BL_B_Cu and o.net.name!='/SD_CLK_DRV':
  a=LineString([(o.start.x_nm/1e6,o.start.y_nm/1e6),(o.end.x_nm/1e6,o.end.y_nm/1e6)]).buffer(o.width.value_nm/2e6+.0635+.1+.015)
  if line.intersects(a):ids.append(o.id);print('Local ripup',o.net.name,flush=True)
net=next(n for n in c.call(pcbcmd.GetNets(board=d)).nets if n.name=='/SD_CLK_DRV');v=pcb.Via(id=uid(),position=xy(x,y),type=pcb.VT_THROUGH,net=net);v.pad_stack.type=pcb.PST_NORMAL;v.pad_stack.layers.extend([pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_In3_Cu,pcb.BL_In4_Cu,pcb.BL_B_Cu]);v.pad_stack.drill.CopyFrom(pcb.DrillProperties(start_layer=pcb.BL_F_Cu,end_layer=pcb.BL_B_Cu,diameter=xy(.2,.2),shape=pcb.DS_CIRCLE,capped=pcb.VDCM_CAPPED,filled=pcb.VDFM_FILLED));v.pad_stack.copper_layers.add(layer=pcb.BL_F_Cu,shape=pcb.PSS_CIRCLE,size=xy(.45,.45));t=pcb.Track(id=uid(),start=xy(131.75,136.4),end=xy(x,y),width=base.Distance(value_nm=127000),layer=pcb.BL_B_Cu,net=net)
cid=c.begin(d)
if ids:c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=ids))
c.create(d,[v,t]);c.end(d,cid,'Escape SD clock outside the dense via field with exact all-layer clearance');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d)
