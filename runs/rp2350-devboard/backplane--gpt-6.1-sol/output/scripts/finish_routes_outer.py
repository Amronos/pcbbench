"""Connect explicit saved DRC endpoint pairs with a clearance-aware outer-layer grid search.
Every route is saved through IPC, then KiCad DRC is the independent acceptance check.
"""
from ipc_client import *
import cv2,numpy as np,heapq,math,json,time,sys
G=.025; X0=100.35;Y0=100.35; W=3374;H=2774
c=Client();doc=c.open(base.DOCTYPE_PCB);objects=c.get(doc)
nets={n.name:n for n in c.call(pcbcmd.GetNets(board=doc)).nets};names={n:i+2 for i,n in enumerate(nets)};names['']=1
owners=np.zeros((2,H,W),np.int16);holes=np.ones((H,W),np.uint8)*255;via_forbidden=np.zeros((H,W),np.uint8)
pads=[];idobjects={o.id.value:o for o in objects if hasattr(o,'id')};existingvias=[]
def pix(v):return (round((v.x_nm/1e6-X0)/G),round((v.y_nm/1e6-Y0)/G))
for f in objects:
 if isinstance(f,pcb.FootprintInstance):
  for a in f.definition.items:
   p=unpack(a)
   if hasattr(p,'id') and isinstance(p.id,base.KIID):idobjects[p.id.value]=p
   if isinstance(p,pcb.Pad):pads.append(p)
   if isinstance(p,pcb.Zone) and p.type==pcb.ZT_RULE_AREA and p.rule_area_settings.keepout_vias:
    for poly in p.outline.polygons:cv2.fillPoly(via_forbidden,[np.array([pix(n.point) for n in poly.outline.nodes if n.HasField('point')],np.int32)],1)
def pix(v):return (round((v.x_nm/1e6-X0)/G),round((v.y_nm/1e6-Y0)/G))
def point(v):return (v.x_nm/1e6,v.y_nm/1e6)
def drawpoly(layer,net,poly):
 pts=[pix(n.point) for n in poly.outline.nodes if n.HasField('point')]
 if len(pts)>=3:cv2.fillPoly(owners[layer],[np.array(pts,np.int32)],names.get(net,1))
def drawitem(o):
 net=o.net.name if hasattr(o,'net') else ''
 if isinstance(o,pcb.Track):
  if o.layer not in [pcb.BL_F_Cu,pcb.BL_B_Cu]:return
  layer=0 if o.layer==pcb.BL_F_Cu else 1
  cv2.line(owners[layer],pix(o.start),pix(o.end),names[net],max(1,math.ceil(o.width.value_nm/1e6/G)),cv2.LINE_8)
  for p in [pix(o.start),pix(o.end)]:cv2.circle(owners[layer],p,math.ceil(o.width.value_nm/1e6/G/2),names[net],-1)
 elif isinstance(o,pcb.Via):
  size=o.pad_stack.copper_layers[0].size.x_nm/1e6
  for layer in [0,1]:cv2.circle(owners[layer],pix(o.position),math.ceil(size/G/2),names[net],-1)
  cv2.circle(holes,pix(o.position),math.ceil(o.pad_stack.drill.diameter.x_nm/1e6/G/2),0,-1)
  existingvias.append((o.position.x_nm/1e6,o.position.y_nm/1e6,net))
 elif isinstance(o,pcb.Arc):
  # Recover the circle through its three points, then rasterize the full actual swept arc.
  a=np.array(point(o.start));b=np.array(point(o.mid));d=np.array(point(o.end))
  mat=np.stack([2*(b-a),2*(d-a)]);rhs=np.array([np.dot(b,b)-np.dot(a,a),np.dot(d,d)-np.dot(a,a)])
  if abs(np.linalg.det(mat))<1e-8:return
  center=np.linalg.solve(mat,rhs);radius=np.linalg.norm(a-center)
  angles=[math.atan2(*(p-center)[::-1]) for p in [a,b,d]];start,mid,end=angles
  ccw=(end-start)%(2*math.pi);mm=(mid-start)%(2*math.pi);sweep=ccw if mm<=ccw else ccw-2*math.pi
  pts=[(round((center[0]+radius*math.cos(start+sweep*t)-X0)/G),round((center[1]+radius*math.sin(start+sweep*t)-Y0)/G)) for t in np.linspace(0,1,max(3,round(radius*abs(sweep)/G*2)))]
  layer=0 if o.layer==pcb.BL_F_Cu else 1
  cv2.polylines(owners[layer],[np.array(pts,np.int32)],False,names[net],max(1,math.ceil(o.width.value_nm/1e6/G)),cv2.LINE_8)
# Footprint pads, exact native polygon representations on each outer layer.
for layer,ki in [(0,pcb.BL_F_Cu),(1,pcb.BL_B_Cu)]:
 resp=c.call(pcbcmd.GetPadShapeAsPolygon(board=doc,pads=[p.id for p in pads],layer=ki))
 for p,poly in zip(pads,resp.polygons):
  if ki in p.pad_stack.layers or p.type in [pcb.PT_PTH,pcb.PT_NPTH]:drawpoly(layer,p.net.name,poly)
for p in pads:
 dr=p.pad_stack.drill.diameter.x_nm/1e6
 if dr>0:cv2.circle(holes,pix(p.position),math.ceil(dr/G/2),0,-1)
for o in objects:
 if isinstance(o,(pcb.Track,pcb.Via,pcb.Arc)):drawitem(o)
 if isinstance(o,pcb.Zone) and o.type==pcb.ZT_RULE_AREA:
  for poly in o.outline.polygons:
   pts=np.array([pix(n.point) for n in poly.outline.nodes if n.HasField('point')],np.int32)
   if o.rule_area_settings.keepout_vias:cv2.fillPoly(via_forbidden,[pts],1)
   if o.rule_area_settings.keepout_tracks:
    for l in [0,1]:cv2.fillPoly(owners[l],[pts],1)
# Edge margin, keep drill bodies at least 0.3mm from Edge.Cuts.
for l in [0,1]:
 owners[l,:3,:]=1;owners[l,-3:,:]=1;owners[l,:,:3]=1;owners[l,:,-3:]=1
HD=cv2.distanceTransform(holes,cv2.DIST_L2,5)*G

def endpoint(item):
 o=idobjects.get(item['uuid']);x=item['pos']['x'];y=item['pos']['y'];layers=[0]
 if isinstance(o,(pcb.Via,)):layers=[0,1]
 elif isinstance(o,pcb.Pad) and o.type==pcb.PT_PTH:layers=[0,1]
 elif isinstance(o,(pcb.Track,pcb.Arc)):layers=[0 if o.layer==pcb.BL_F_Cu else 1]
 return round((x-X0)/G),round((y-Y0)/G),layers,(x,y),o

def astar(sx,sy,sl,gx,gy,gl,free,vm,timeout=12):
 # Restrict to the board; the search expands in both directions and changes layer only at a legal via location.
 xmin=max(0,min(sx,gx)-320);xmax=min(W-1,max(sx,gx)+320);ymin=max(0,min(sy,gy)-320);ymax=min(H-1,max(sy,gy)+320)
 def heur(x,y):
  dx=abs(gx-x);dy=abs(gy-y);return 2.2*(max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy))
 queue=[];cost={};prev={};targets={l*H*W+gy*W+gx for l in gl};deadline=time.monotonic()+timeout
 for l in sl:
  key=l*H*W+sy*W+sx;cost[key]=0;heapq.heappush(queue,(heur(sx,sy),0,key))
 moves=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414213562),(-1,1,1.414213562),(1,-1,1.414213562),(-1,-1,1.414213562)]
 iterations=0
 while queue:
  f,dist,key=heapq.heappop(queue)
  if cost.get(key,math.inf)!=dist:continue
  if key in targets:
   out=[key]
   while key in prev:key=prev[key];out.append(key)
   return out[::-1]
  l=key//(H*W);r=key%(H*W);y=r//W;x=r%W
  iterations+=1
  if iterations%20000==0 and time.monotonic()>deadline:return None
  for dx,dy,d in moves:
   nx=x+dx;ny=y+dy
   if nx<xmin or nx>xmax or ny<ymin or ny>ymax or not free[l,ny,nx]:continue
   nk=l*H*W+ny*W+nx;nd=dist+d*(1.0 if l==1 else 1.008)
   if nd<cost.get(nk,math.inf):cost[nk]=nd;prev[nk]=key;heapq.heappush(queue,(nd+heur(nx,ny),nd,nk))
  if vm[y,x] and free[1-l,y,x]:
   nk=(1-l)*H*W+y*W+x;nd=dist+35
   if nd<cost.get(nk,math.inf):cost[nk]=nd;prev[nk]=key;heapq.heappush(queue,(nd+heur(x,y),nd,nk))
 return None

def makevia(x,y,net):
 v=pcb.Via(id=uid(),position=xy(x,y),type=pcb.VT_THROUGH,net=nets[net])
 v.pad_stack.type=pcb.PST_NORMAL;v.pad_stack.layers.extend([pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_B_Cu])
 v.pad_stack.drill.CopyFrom(pcb.DrillProperties(start_layer=pcb.BL_F_Cu,end_layer=pcb.BL_B_Cu,diameter=xy(.2,.2),shape=pcb.DS_CIRCLE,capped=pcb.VDCM_CAPPED,filled=pcb.VDFM_FILLED))
 v.pad_stack.copper_layers.add(layer=pcb.BL_F_Cu,shape=pcb.PSS_CIRCLE,size=xy(.45,.45))
 return v

if '--fanout' in sys.argv:
 f=next(f for f in objects if isinstance(f,pcb.FootprintInstance) and f.reference_field.text.text.text=='U1')
 pp=[unpack(a) for a in f.definition.items if a.Is(pcb.Pad.DESCRIPTOR)]
 results=[]
 for p in sorted(pp,key=lambda p:int(p.number or 0)):
  net=p.net.name
  if net.startswith('unconnected-') or net=='/GND' or not p.number:continue
  nid=names[net];sx,sy=pix(p.position);sp=point(p.position)
  D=np.array([cv2.distanceTransform(((owners[l]==0)|(owners[l]==nid)).astype(np.uint8)*255,cv2.DIST_L2,5)*G for l in [0,1]])
  free=D>=.127/2+.1+.002;free[1]=False;free[0,sy,sx]=True
  vm=(np.minimum(D[0],D[1])>=.225+.1+.01)&(HD>=.1+.25+.025)&(via_forbidden==0)
  candidates=[]
  for gy in range(max(0,sy-130),min(H,sy+131)):
   for gx in range(max(0,sx-130),min(W,sx+131)):
    if not vm[gy,gx]:continue
    wx=X0+gx*G;wy=Y0+gy*G
    outward=(wx<sp[0]-.75 if abs(sp[0]-133.55)<.01 else wx>sp[0]+.75 if abs(sp[0]-140.45)<.01 else wy<sp[1]-.75 if abs(sp[1]-130.55)<.01 else wy>sp[1]+.75)
    if outward:candidates.append(((gx-sx)**2+(gy-sy)**2,gx,gy))
  candidates.sort();path=None
  for dist,gx,gy in candidates[:40]:
   path=astar(sx,sy,[0],gx,gy,[0],free,np.zeros_like(vm),timeout=1)
   if path:break
  if not path:
   print('FANOUT FAILED',p.number,net,flush=True);results.append({'pin':p.number,'net':net,'success':False});continue
  pts=[]
  for key in path:
   r=key%(H*W);y=r//W;x=r%W;pts.append((round(X0+x*G,5),round(Y0+y*G,5)))
  simple=[sp,pts[0]]
  for i in range(1,len(pts)-1):
   a,b,d=pts[i-1:i+2]
   if abs((b[0]-a[0])*(d[1]-b[1])-(b[1]-a[1])*(d[0]-b[0]))>1e-7:simple.append(b)
  simple.append(pts[-1]);new=[]
  for a,b in zip(simple,simple[1:]):
   if math.hypot(a[0]-b[0],a[1]-b[1])>.00001:new.append(pcb.Track(id=uid(),start=xy(*a),end=xy(*b),width=base.Distance(value_nm=127000),layer=pcb.BL_F_Cu,net=nets[net]))
  new.append(makevia(*pts[-1],net))
  cid=c.begin(doc);c.create(doc,new);c.end(doc,cid,'Fan out MCU pin '+p.number);c.save(doc)
  for o in new:drawitem(o)
  HD=cv2.distanceTransform(holes,cv2.DIST_L2,5)*G
  print('FANOUT',p.number,net,pts[-1],flush=True);results.append({'pin':p.number,'net':net,'success':True})
 c.call(pcbcmd.RefillZones(board=doc));c.save(doc)
 (ROOT/'build/mcu-fanout.json').write_text(json.dumps(results,indent=2)+'\n');exit()

report=json.loads((ROOT/'build/drc-current.json').read_text());results=[]
for index,v in enumerate(report['unconnected_items']):
 a,b=v['items']
 if a['description'].startswith('Zone') or b['description'].startswith('Zone'):continue
 sx,sy,sl,sp,so=endpoint(a);gx,gy,gl,gp,go=endpoint(b)
 net=(so.net.name if hasattr(so,'net') else go.net.name);nid=names[net]
 D=np.array([cv2.distanceTransform(((owners[l]==0)|(owners[l]==nid)).astype(np.uint8)*255,cv2.DIST_L2,5)*G for l in [0,1]])
 free=D>=.127/2+.1+.002
 vm=(np.minimum(D[0],D[1])>=.225+.1+.01)&(HD>=.1+.25+.025)&(via_forbidden==0)
 for x,y,n in existingvias:
  if n==net:
   px=round((x-X0)/G);py=round((y-Y0)/G)
   if 0<=px<W and 0<=py<H:vm[py,px]=True
 for l in sl:free[l,sy,sx]=True
 for l in gl:free[l,gy,gx]=True
 if '--debug' in sys.argv:
  print(net,'start',sp,'goal',gp,'Dstart',D[:,sy,sx],'Dgoal',D[:,gy,gx]);print('near source\n',np.round(D[0,sy-4:sy+5,sx-12:sx+4],2));print('ownsource\n',owners[0,sy-4:sy+5,sx-12:sx+4]);print('netid',nid,'freecells',int(free.sum()),'viacells',int(vm.sum()));exit()
 path=astar(sx,sy,sl,gx,gy,gl,free,vm)
 if path is None:
  print('UNRESOLVED',index,net,a['description'],b['description'],flush=True);results.append({'net':net,'success':False,'pair':index});continue
 pts=[]
 for key in path:
  l=key//(H*W);r=key%(H*W);y=r//W;x=r%W;pts.append((l,round(X0+x*G,5),round(Y0+y*G,5)))
 # Retain only bends and via transitions; exact saved endpoint positions bridge grid quantization.
 simple=[pts[0]]
 for i in range(1,len(pts)-1):
  aa,bb,cc=pts[i-1:i+2]
  if aa[0]!=bb[0] or bb[0]!=cc[0] or abs((bb[1]-aa[1])*(cc[2]-bb[2])-(bb[2]-aa[2])*(cc[1]-bb[1]))>1e-7:simple.append(bb)
 simple.append(pts[-1]);simple=[(simple[0][0],*sp)]+simple+[(simple[-1][0],*gp)]
 new=[];nv=0
 for aa,bb in zip(simple,simple[1:]):
  if aa[0]!=bb[0]:
   if not any(n==net and math.hypot(aa[1]-x,aa[2]-y)<.075 for x,y,n in existingvias):new.append(makevia(aa[1],aa[2],net));nv+=1
  elif math.hypot(aa[1]-bb[1],aa[2]-bb[2])>.00001:
   new.append(pcb.Track(id=uid(),start=xy(aa[1],aa[2]),end=xy(bb[1],bb[2]),width=base.Distance(value_nm=127000),layer=pcb.BL_F_Cu if aa[0]==0 else pcb.BL_B_Cu,net=nets[net]))
 cid=c.begin(doc);c.create(doc,new);c.end(doc,cid,'Finish explicit connection '+net);c.save(doc)
 for o in new:drawitem(o)
 HD=cv2.distanceTransform(holes,cv2.DIST_L2,5)*G
 print('CONNECTED',index,net,len(new),'items',nv,'vias',flush=True);results.append({'net':net,'success':True,'pair':index,'items':len(new),'vias':nv})
c.call(pcbcmd.RefillZones(board=doc));c.save(doc)
(ROOT/'build/finish-routing.json').write_text(json.dumps(results,indent=2)+'\n')
print('Saved routed canonical PCB; failed',sum(not r['success'] for r in results),flush=True)
