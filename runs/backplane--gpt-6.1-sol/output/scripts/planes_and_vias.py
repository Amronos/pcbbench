from ipc_client import *
from shapely.geometry import Polygon,Point
import math,json
c=Client();c.call(project.CloseAllDocuments(force=True));doc=c.open(base.DOCTYPE_PCB)
objects=c.get(doc);fps=[f for f in objects if isinstance(f,pcb.FootprintInstance)]
assert len(fps)==125
# All reads precede BeginCommit; the runtime exposes staged clones during an open commit.
changes=[];deletes=[]
for f in fps:
 f.reference_field.visible=False;f.value_field.visible=False
 changes.append(f)
 if f.reference_field.text.text.text=='U8':
  for a in f.definition.items:
   if a.Is(pcb.BoardGraphicShape.DESCRIPTOR):
    sh=unpack(a)
    if sh.layer!=pcb.BL_F_SilkS or not sh.shape.HasField('segment'):continue
    seg=sh.shape.segment
    if seg.start.y_nm<100300000 and seg.end.y_nm<100300000:deletes.append(sh.id);continue
    if seg.start.y_nm<100300000:seg.start.y_nm=100300000;changes.append(sh)
    if seg.end.y_nm<100300000:seg.end.y_nm=100300000;changes.append(sh)
nets={n.name:n for n in c.call(pcbcmd.GetNets(board=doc)).nets}
pads=[]
for f in fps:
 for a in f.definition.items:
  if a.Is(pcb.Pad.DESCRIPTOR):pads.append(unpack(a))
response=c.call(pcbcmd.GetPadShapeAsPolygon(board=doc,pads=[p.id for p in pads],layer=pcb.BL_F_Cu))
obstacles=[]
for pad,poly in zip(pads,response.polygons):
 pts=[(n.point.x_nm/1e6,n.point.y_nm/1e6) for n in poly.outline.nodes if n.HasField('point')]
 if len(pts)>=3:obstacles.append((pad.net.name,Polygon(pts).buffer(0)))
placed=[]
def via_at(x,y,net,diam=.55,drill=.25):
 if any((x-a)**2+(y-b)**2<(diam/2+d/2+.25)**2 for a,b,d,n in placed):return None
 disk=Point(x,y).buffer(diam/2+.15)
 if any(n!=net and disk.intersects(shape) for n,shape in obstacles):return None
 # All existing PTH/NPTH drills also constrain distance, including same-net drills.
 for p in pads:
  dr=p.pad_stack.drill.diameter.x_nm/1e6
  if dr>0 and math.hypot(x-p.position.x_nm/1e6,y-p.position.y_nm/1e6)<(dr+drill)/2+.25:return None
 v=pcb.Via(id=uid(),position=xy(x,y),type=pcb.VT_THROUGH,net=nets[net])
 v.pad_stack.type=pcb.PST_NORMAL
 v.pad_stack.layers.extend([pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_B_Cu])
 v.pad_stack.drill.CopyFrom(pcb.DrillProperties(start_layer=pcb.BL_F_Cu,end_layer=pcb.BL_B_Cu,diameter=xy(drill,drill),shape=pcb.DS_CIRCLE,capped=pcb.VDCM_CAPPED,filled=pcb.VDFM_FILLED))
 v.pad_stack.unconnected_layer_removal=pcb.ULR_KEEP
 for layer in [pcb.BL_F_Cu]:
  v.pad_stack.copper_layers.add(layer=layer,shape=pcb.PSS_CIRCLE,size=xy(diam,diam))
 placed.append((x,y,diam,net));return v
new=[]
# Plane stitches directly in suitably large supply/ground solder pads. These are filled and capped.
for p in pads:
 if p.type!=pcb.PT_SMD or p.net.name not in ['/GND','/3V3']:continue
 layers=[a for a in p.pad_stack.copper_layers if a.layer==pcb.BL_F_Cu]
 if not layers or min(layers[0].size.x_nm,layers[0].size.y_nm)<550000:continue
 if pcb.BL_F_Cu not in p.pad_stack.layers:continue
 x=p.position.x_nm/1e6;y=p.position.y_nm/1e6
 if x<100.8 or x>184.2 or y<101.8 or y>169.2:continue
 v=via_at(x,y,p.net.name)
 if v:new.append(v)
# EP vias on MCU and main power regulator; 0.25mm, resin filled and copper capped.
for x,y in [(136.3,133.3),(137.7,133.3),(136.3,134.7),(137.7,134.7),(124.7,118.6),(125.3,119.4)]:
 v=via_at(x,y,'/GND')
 if v:new.append(v)
# Distributed ground stitches. Never place copper in the antenna area.
for x in range(105,181,10):
 for y in range(105,166,10):
  v=via_at(x,y,'/GND')
  if v:new.append(v)
# Multi-layer solid reference ground and 3V3 power plane, plus outer ground fills.
for layer,net in [(pcb.BL_F_Cu,'/GND'),(pcb.BL_In1_Cu,'/GND'),(pcb.BL_In2_Cu,'/3V3'),(pcb.BL_B_Cu,'/GND')]:
 z=pcb.Zone(id=uid(),type=pcb.ZT_COPPER,layers=[layer],name=net+' plane '+pcb.BoardLayer.Name(layer))
 p=z.outline.polygons.add();p.outline.closed=True
 for x,y in [(100.35,100.35),(184.65,100.35),(184.65,169.65),(100.35,169.65)]:p.outline.nodes.add().point.CopyFrom(xy(x,y))
 cs=z.copper_settings;cs.net.CopyFrom(nets[net]);cs.clearance.value_nm=150000;cs.min_thickness.value_nm=127000;cs.fill_mode=pcb.ZFM_SOLID;cs.island_mode=pcb.IRM_ALWAYS
 cs.connection.zone_connection=pcb.ZCS_PTH_THERMAL;cs.connection.thermal_spokes.gap.value_nm=200000;cs.connection.thermal_spokes.width.value_nm=250000
 z.border.style=pcb.ZBS_DIAGONAL_EDGE;z.border.pitch.value_nm=500000;new.append(z)
cid=c.begin(doc)
c.update(doc,changes)
if deletes:c.call(editor.DeleteItems(header=base.ItemHeader(document=doc),item_ids=deletes))
c.create(doc,new)
c.end(doc,cid,'Add GND and 3V3 planes, capped power stitches, and clean reference artwork');c.save(doc)
print('Created',len(placed),'filled/capped vias and four copper planes',flush=True)
c.call(pcbcmd.RefillZones(board=doc));c.save(doc)
got=[f for f in c.get(doc) if isinstance(f,pcb.FootprintInstance)];assert len(got)==125
(ROOT/'build/plane-vias.json').write_text(json.dumps(placed,indent=2)+'\n')
print('Filled and saved canonical PCB; 125 footprints remain',flush=True)
