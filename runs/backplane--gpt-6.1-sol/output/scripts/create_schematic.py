from ipc_client import *
import json,math,collections
from common.commands import library_commands_pb2 as libcmd
from common.types import library_types_pb2 as lt
COMPS=json.loads((DESIGN/'component-spec.json').read_text())
c=Client()
c.call(project.CloseAllDocuments(force=False))
doc=c.open(base.DOCTYPE_SCHEMATIC)
# get library definitions after the project tables were reloaded.
cache={}
for p in COMPS:
 if p['localsym'] not in cache:cache[p['localsym']]=c.lib(base.LT_SYMBOL,p['localsym'])
print('Resolved',len(cache),'self-contained symbols',flush=True)
# All positions stay on the 1.27mm schematic grid.
blocks={'memory':(133.35,60.96,27.94,17.78,3),'core':(128.27,109.22,25.4,17.78,3),'decoupling':(25.4,152.4,22.86,20.32,5),'clock':(25.4,132.08,22.86,17.78,4),'controls':(124.46,147.32,22.86,17.78,4),'usb':(322.58,81.28,25.4,17.78,3),'charger':(25.4,241.3,24.13,17.78,4),'mainpower':(127,241.3,25.4,17.78,4),'batteryadc':(190.5,147.32,25.4,17.78,3),'radio':(226.06,83.82,24.13,17.78,3),'sd':(228.6,160.02,24.13,17.78,3),'qwiic':(350.52,147.32,25.4,17.78,2),'rgb':(302.26,246.38,25.4,17.78,4),'expansion':(215.9,210.82,44.45,17.78,2),'debug':(297.18,180.34,25.4,17.78,3)}
fixed={'R30':(302.26,104.14),'J2':(96.52,213.36),'J3':(294.64,85.09),'J5':(325.12,152.4),'J6':(224.79,210.82),'J7':(270.51,210.82),'J8':(294.64,180.34),'U5':(381,104.14),'U10':(373.38,213.36),'D2':(375.92,181.61)}
counts=collections.Counter();items=[];created={};positions={}
# Recreate the blank schematic if requested only; never erase authored progress by default.
existing=c.get(doc)
if existing:
 assert '--rebuild' in sys.argv, 'Schematic already contains items; use --rebuild for this generated design'
 cid=c.begin(doc)
 c.call(editor.DeleteItems(header=base.ItemHeader(document=doc),item_ids=[i.id for i in existing]))
 c.end(doc,cid,'Rebuild generated schematic with expanded spacing');c.save(doc)
cid=c.begin(doc)
for p in COMPS:
 definition=cache[p['localsym']]
 pos=p.get('schpos') or fixed.get(p['ref'])
 if not pos:
  x,y,dx,dy,n=blocks[p['group']];i=counts[p['group']];counts[p['group']]+=1;pos=(x+(i%n)*dx,y+(i//n)*dy)
 x,y=[round(v*1.4/1.27)*1.27 for v in pos];positions[p['ref']]=[x,y]
 units=definition.unit_count or 1
 for unit in range(1,units+1):
  uy=y+17.78*(unit-1);sid=uid()
  inst=sch.SchematicSymbolInstance(id=sid,position=xy(x,uy),definition=definition,unit=sch.SchematicSymbolUnit(unit=unit),transform=sch.SchematicSymbolTransform(orientation=sch.SSO_0),attributes=sch.SchematicSymbolAttributes())
  inst.reference_field.CopyFrom(sch.SchematicField(name='Reference',text=txt(p['ref'],x+2.54,uy-3.81,1.0),visible=True))
  inst.value_field.CopyFrom(sch.SchematicField(name='Value',text=txt(p['value'],x+2.54,uy-1.27,1.0),visible=True))
  if p['ref'].startswith(('U','J')) and unit==1:
   # Library field coordinates keep names clear of the pin rows.
   for field,name,t in [(inst.reference_field,'Reference',p['ref']),(inst.value_field,'Value',p['value'])]:
    df=definition.reference_field if name=='Reference' else definition.value_field
    field.text.position.CopyFrom(xy(x+df.text.position.x_nm/1e6,uy+df.text.position.y_nm/1e6));field.text.text=t
  inst.footprint_field.CopyFrom(sch.SchematicField(name='Footprint',text=txt(p['localfp'],x,uy),visible=False))
  inst.datasheet_field.CopyFrom(definition.datasheet_field);inst.datasheet_field.visible=False
  inst.description_field.CopyFrom(definition.description_field);inst.description_field.visible=False
  for name,value in [('Manufacturer',p['mfr']),('MPN',p['mpn']),('Assembly','FIT'),('Notes',p['note'])]:
   inst.user_fields.add().CopyFrom(sch.SchematicField(name=name,text=txt(value,x,uy),visible=False))
  items.append(inst)
  if unit==1:created[p['ref']]=sid.value
  seen={}
  for ch in definition.items:
   if ch.HasField('unit') and ch.unit.unit not in (0,unit):continue
   if not ch.item.Is(sch.SchematicPin.DESCRIPTOR):continue
   pin=unpack(ch.item);num=pin.number
   assert num in p['pins'],(p['ref'],num,pin.name)
   net=p['pins'][num];px=x+pin.position.x_nm/1e6;py=uy+pin.position.y_nm/1e6
   loc=(px,py)
   if loc in seen:
    assert seen[loc]==net,(p['ref'],num,net,seen[loc]);continue
   seen[loc]=net
   if net is None:
    items.append(sch.NoConnectMarker(id=uid(),position=xy(px,py)));continue
   # Pin orientation points into the symbol; wire extends away.
   outward={sch.SPO_RIGHT:(-1,0),sch.SPO_LEFT:(1,0),sch.SPO_UP:(0,1),sch.SPO_DOWN:(0,-1)}[pin.orientation]
   ex=px+outward[0]*3.81;ey=py+outward[1]*3.81
   items.append(sch.SchematicLine(id=uid(),type=sch.SLT_WIRE,start=xy(px,py),end=xy(ex,ey)))
   spin={(-1,0):sch.SLSS_LEFT,(1,0):sch.SLSS_RIGHT,(0,1):sch.SLSS_BOTTOM,(0,-1):sch.SLSS_UP}[outward]
   items.append(sch.LocalLabel(id=uid(),position=xy(ex,ey),text=txt(net,ex,ey,0.85),spin_style=spin))
 # Save in manageable batches without ending commit (atomic section).
 if len(items)>100:
  c.create(doc,items);items=[]
if items:c.create(doc,items)
# True power-output flags for connector-fed rails and filtered supply, giving meaningful ERC.
for i,net in enumerate(['GND','VBUS','VBUS_RAW','1V1','ADC_3V3']):
 x=22.86+i*35.56;y=274.32
 df=c.lib(base.LT_SYMBOL,'connect:PWR_FLAG')
 inst=sch.SchematicSymbolInstance(id=uid(),position=xy(x,y),definition=df,attributes=df.attributes,unit=sch.SchematicSymbolUnit(unit=1))
 inst.reference_field.CopyFrom(sch.SchematicField(name='Reference',text=txt('#FLG'+str(i+1),x,y),visible=False))
 inst.value_field.CopyFrom(sch.SchematicField(name='Value',text=txt('PWR_FLAG',x,y),visible=False))
 c.create(doc,[inst,sch.LocalLabel(id=uid(),position=xy(x,y),text=txt(net,x,y,0.85),spin_style=sch.SLSS_LEFT)])
# Sheet block headings and actionable notes.
notes=[(15,12,'RP2350 CONNECT — REV A — 85 x 70 mm, 4-layer PCB'),(120,14,'16MB flash + 8MB PSRAM (shared QMI bus, GPIO0 CS1)'),(216,14,'Wi-Fi / BLE: ESP32-C3-WROOM-02-N4'),(316,14,'USB-C: USB 2.0 FS sink, independent 5.1k CC resistors'),(16,124,'12MHz crystal + per-pin supply bypass'),(120,71,'External 1.1V core; VREG_FB=GND, VREG_LX=NC'),(223,107,'microSD SPI1, switched rail; enable after USB enumeration'),(306,133,'Qwiic / STEMMA QT: 3.3V I2C'),(16,178,'USB_EN1/2 reset LOW: USB100; radio and SD reset OFF'),(16,185,'Firmware: USB500 after enumeration, handle USB suspend; set VREG.HIZ'),(15,200,'LiPo 4.2V, protected pack +10k NTC; pin1=BAT+, 2=GND, 3=NTC'),(120,200,'3.3V buck-boost; nominal 66uF output'),(298,200,'RGB: dedicated 5V boost + AHCT level buffer'),(208,234,'Sockets expose user GPIO and power-control signals'),(15,284,'All fitted parts assembled by PCBWay. Battery, microSD media and cables are external. See README and fab instructions.')]
for x,y,t in notes:c.create(doc,[sch.SchematicText(id=uid(),text=txt(t,x*1.4,y*1.4,1.3))])
c.end(doc,cid,'Complete annotated RP2350 Connect schematic');c.save(doc)
(DESIGN/'symbol-ids.json').write_text(json.dumps(created,indent=2)+'\n')
(DESIGN/'schematic-positions.json').write_text(json.dumps(positions,indent=2)+'\n')
print('Saved canonical schematic',DESIGN/'rp2350-connect.kicad_sch',flush=True)
