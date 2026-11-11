"""Repair invalid saved IPC footprint duplicates, then enforce courtyard placement spacing.
Native-file fallback is needed for this corrupt milestone; a backup is retained.
"""
from ipc_client import *
from pathlib import Path
import sexpdata as sx,collections,copy,json,shutil,math
from shapely.geometry import box
S=sx.Symbol
BASE=Path('/home/ubuntu/.local/share/backplane/kicad/10.99.0-bp.4/share/kicad/footprints')
def tag(a,n):return isinstance(a,list) and a and str(a[0])==n
def child(a,n):return next((x for x in a if tag(x,n)),None)
def ref(f):return next(x[2] for x in f if tag(x,'property') and x[1]=='Reference')
def trans(f):
 t=child(f,'transform');p=child(t,'translate');r=child(t,'rotate');return float(p[1]),float(p[2]),float(r[1])
def bbox(f):
 pts=[]
 for a in f:
  if not isinstance(a,list):continue
  layer=child(a,'layer')
  if not layer or layer[1]!='F.CrtYd':continue
  for b in a:
   if isinstance(b,list) and str(b[0]) in ['start','end','center','mid'] and isinstance(b[1],(int,float)):pts.append(b[1:3])
  if str(a[0])=='fp_poly':
   pts.extend(z[1:] for z in child(a,'pts')[1:] if tag(z,'xy'))
 assert pts,(ref(f),'missing courtyard')
 x,y,r=trans(f);r=math.radians(r)
 p=[(a*math.cos(r)+b*math.sin(r),-a*math.sin(r)+b*math.cos(r)) for a,b in pts]
 return min(a for a,b in p),min(b for a,b in p),max(a for a,b in p),max(b for a,b in p)
c=Client();c.call(project.CloseAllDocuments(force=False))
p=DESIGN/'rp2350-connect.kicad_pcb';backup=ROOT/'build/backups';backup.mkdir(exist_ok=True)
shutil.copy2(p,backup/'pcb-invalid-ipc-placement.kicad_pcb')
j=sx.loads(p.read_text());fps=[x for x in j if tag(x,'footprint')]
chosen={}
for f in fps:
 x,y,r=trans(f)
 if ref(f) not in chosen or (x>=100 and y>=95):chosen[ref(f)]=f
assert len(chosen)==125,len(chosen)
for rr in ['H1','H2','H3','H4','FID1','FID2','FID3']:
 f=chosen[rr];libname='MountingHole' if rr.startswith('H') else 'Fiducial';name=f[1].split(':')[-1]
 raw=sx.loads((BASE/(libname+'.pretty')/(name+'.kicad_mod')).read_text())
 geom=[x for x in raw if isinstance(x,list) and str(x[0]) in ['fp_line','fp_rect','fp_circle','fp_arc','fp_poly','fp_text','pad','model']]
 keep=[x for x in f if not (isinstance(x,list) and str(x[0]) in ['fp_line','fp_rect','fp_circle','fp_arc','fp_poly','fp_text','pad','model'])]
 keep.extend(copy.deepcopy(geom));chosen[rr]=keep
 f=chosen[rr]
 # Freeze these drawing-only footprints as local resources too.
 (DESIGN/'connect.pretty'/(name+'.kicad_mod')).write_text(sx.dumps(raw)+'\n');f[1]='connect:'+name
# Specific large component moves, before the passive packing pass.
for rr,x,y in [('R30',158,119),('J1',102.4,143),('L2',125,114),('L1',149,132),('H1',104,104),('H2',151,104),('H3',104,166),('H4',181,166),('FID1',103,121),('FID2',181,141),('FID3',108,166)]:
 a=child(child(chosen[rr],'transform'),'translate');a[1:]=[x,y]
# All physical footprints except passives are fixed, respecting the major architectural placement.
fixed=[f for rr,f in chosen.items() if rr[0] not in ['R','C','F'] or rr.startswith('FID')]
occupied=[]
for f in fixed:
 x,y,r=trans(f);a,b,d,e=bbox(f);occupied.append((ref(f),box(x+a,y+b,x+d,y+e).buffer(0.02)))
# Move each passive by the smallest practical amount that clears all real courtyards.
changes=[]
for rr,f in chosen.items():
 if f in fixed:continue
 x,y,r=trans(f);a,b,d,e=bbox(f)
 candidates=[(0,0)]
 for ring in range(1,33):
  rad=ring*0.25
  for dx,dy in [(rad,t*0.25) for t in range(-ring,ring+1)]+[(-rad,t*0.25) for t in range(-ring,ring+1)]+[(t*0.25,rad) for t in range(-ring+1,ring)]+[(t*0.25,-rad) for t in range(-ring+1,ring)]:candidates.append((dx,dy))
 candidates.sort(key=lambda v:v[0]**2+v[1]**2)
 done=False
 for dx,dy in candidates:
  nx,ny=x+dx,y+dy;shape=box(nx+a,ny+b,nx+d,ny+e)
  if nx+a<100.7 or nx+d>184.3 or ny+b<101.7 or ny+e>169.3:continue
  if any(shape.intersects(poly) for ref2,poly in occupied):continue
  child(child(f,'transform'),'translate')[1:]=[nx,ny];occupied.append((rr,shape.buffer(0.02)))
  if dx or dy:changes.append((rr,round(dx,2),round(dy,2)))
  done=True;break
 assert done,rr
# Hide values, correct legible refs; native reference positions remain local to each footprint.
for f in chosen.values():
 for prop in [x for x in f if tag(x,'property')]:
  if prop[1]=='Value':
   if not child(prop,'hide'):prop.append([S('hide'),S('yes')])
  if prop[1]=='Reference':
   r=trans(f)[2];at=child(prop,'at')
   if len(at)>3:at[3]=r
   ef=child(prop,'effects');font=child(ef,'font');child(font,'size')[1:]=[0.8,0.8]
   th=child(font,'thickness')
   if th:th[1]=0.1
   else:font.append([S('thickness'),0.1])
j=[x for x in j if not tag(x,'footprint')]+list(chosen.values())
p.write_text(sx.dumps(j)+'\n')
# USB footprint's vendor-approved NPTH holes are 0.194mm from pads.
pro=DESIGN/'rp2350-connect.kicad_pro';pj=json.loads(pro.read_text());pj['board']['design_settings']['rules']['min_hole_clearance']=0.15;pro.write_text(json.dumps(pj,indent=2)+'\n')
check=sx.loads(p.read_text());assert len([x for x in check if tag(x,'footprint')])==125
(ROOT/'build/placement-adjustments.json').write_text(json.dumps(changes,indent=2)+'\n')
print('Repaired canonical board: 125 unique footprints; moved',len(changes),'passives to clear courtyards',changes,flush=True)
# Re-read canonical in KiCad. Further IPC reads must happen outside an open editing commit.
doc=c.open(base.DOCTYPE_PCB);got=[f for f in c.get(doc) if isinstance(f,pcb.FootprintInstance)]
assert len(got)==125;assert len({f.id.value for f in got})==125
c.save(doc);print('KiCad re-read and saved canonical PCB with 125 unique footprint IDs',flush=True)
