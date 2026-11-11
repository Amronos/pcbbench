from ipc_client import *
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
import math,numpy as np
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);pads=[];ob=[];dr=[]
for f in objs:
 if isinstance(f,pcb.FootprintInstance):
  pads.extend(unpack(a) for a in f.definition.items if a.Is(pcb.Pad.DESCRIPTOR))
for layer in [pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_In3_Cu,pcb.BL_In4_Cu,pcb.BL_B_Cu]:
 resp=c.call(pcbcmd.GetPadShapeAsPolygon(board=d,pads=[p.id for p in pads],layer=layer))
 for p,shape in zip(pads,resp.polygons):
  if p.net.name=='/GND':continue
  for poly in [shape]:
   pts=[(n.point.x_nm/1e6,n.point.y_nm/1e6) for n in poly.outline.nodes if n.HasField('point')]
   if len(pts)>2:ob.append(Polygon(pts).buffer(0))
for p in pads:
 dia=p.pad_stack.drill.diameter.x_nm/1e6
 if dia:dr.append(Point(p.position.x_nm/1e6,p.position.y_nm/1e6).buffer(dia/2+.1+.15+.012))
for o in objs:
 if isinstance(o,pcb.Via):
  if o.net.name!='/GND':ob.append(Point(o.position.x_nm/1e6,o.position.y_nm/1e6).buffer(o.pad_stack.copper_layers[0].size.x_nm/2e6))
  dr.append(Point(o.position.x_nm/1e6,o.position.y_nm/1e6).buffer(o.pad_stack.drill.diameter.x_nm/2e6+.1+.15+.012))
 elif isinstance(o,pcb.Track) and o.net.name!='/GND':ob.append(LineString([(o.start.x_nm/1e6,o.start.y_nm/1e6),(o.end.x_nm/1e6,o.end.y_nm/1e6)]).buffer(o.width.value_nm/2e6))
 elif isinstance(o,pcb.Arc) and o.net.name!='/GND':
  a=np.array([o.start.x_nm/1e6,o.start.y_nm/1e6]);b=np.array([o.mid.x_nm/1e6,o.mid.y_nm/1e6]);e=np.array([o.end.x_nm/1e6,o.end.y_nm/1e6]);mat=np.stack([2*(b-a),2*(e-a)])
  if abs(np.linalg.det(mat))<1e-8:continue
  cent=np.linalg.solve(mat,np.array([np.dot(b,b)-np.dot(a,a),np.dot(e,e)-np.dot(a,a)]));r=np.linalg.norm(a-cent);sa,ma,ea=[math.atan2(*(p-cent)[::-1]) for p in [a,b,e]];sweep=(ea-sa)%(2*math.pi)
  if (ma-sa)%(2*math.pi)>sweep:sweep-=2*math.pi
  pts=[cent+r*np.array([math.cos(sa+t*sweep),math.sin(sa+t*sweep)]) for t in np.linspace(0,1,max(3,int(r*abs(sweep)/.01)))];ob.append(LineString(pts).buffer(o.width.value_nm/2e6))
block=unary_union(ob).buffer(.225+.1+.012).union(unary_union(dr));ground=next(n for n in c.call(pcbcmd.GetNets(board=d)).nets if n.name=='/GND');new=[]
for z in objs:
 if isinstance(z,pcb.Zone) and z.type==pcb.ZT_COPPER and pcb.BL_F_Cu in z.layers:
  for fp in z.filled_polygons:
   for pp in fp.shapes.polygons:
    a=Polygon([(n.point.x_nm/1e6,n.point.y_nm/1e6) for n in pp.outline.nodes if n.HasField('point')]).buffer(0)
    if not(144<a.bounds[0]<145 and 1<a.area<3):continue
    good=a.buffer(-.24).difference(block)
    print('Ground island',a.bounds,'available via area',good.area,flush=True)
    if good.is_empty:continue
    pt=good.representative_point();v=pcb.Via(id=uid(),position=xy(pt.x,pt.y),type=pcb.VT_THROUGH,net=ground);v.pad_stack.type=pcb.PST_NORMAL;v.pad_stack.layers.extend([pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_In3_Cu,pcb.BL_In4_Cu,pcb.BL_B_Cu]);v.pad_stack.drill.CopyFrom(pcb.DrillProperties(start_layer=pcb.BL_F_Cu,end_layer=pcb.BL_B_Cu,diameter=xy(.2,.2),shape=pcb.DS_CIRCLE,capped=pcb.VDCM_CAPPED,filled=pcb.VDFM_FILLED));v.pad_stack.copper_layers.add(layer=pcb.BL_F_Cu,shape=pcb.PSS_CIRCLE,size=xy(.45,.45));new.append(v);print('via',pt.x,pt.y,flush=True)
if new:
 cid=c.begin(d);c.create(d,new);c.end(d,cid,'Connect core-regulator ground island with all-layer clearance-checked stitch');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d)
