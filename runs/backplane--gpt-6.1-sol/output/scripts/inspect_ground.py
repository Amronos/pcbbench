from ipc_client import *
from shapely.geometry import Polygon,Point
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);via=[o for o in objs if isinstance(o,pcb.Via) and o.net.name=='/GND']
for z in objs:
 if isinstance(z,pcb.Zone) and z.type==pcb.ZT_COPPER and pcb.BL_F_Cu in z.layers:
  for fp in z.filled_polygons:
   for p in fp.shapes.polygons:
    a=Polygon([(n.point.x_nm/1e6,n.point.y_nm/1e6) for n in p.outline.nodes if n.HasField('point')]);vs=[o for o in via if a.buffer(.001).covers(Point(o.position.x_nm/1e6,o.position.y_nm/1e6))]
    if not vs:print('NO VIA',a.area,a.bounds,'center',a.representative_point().x,a.representative_point().y)
