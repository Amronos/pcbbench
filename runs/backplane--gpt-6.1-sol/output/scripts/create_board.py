from ipc_client import *
import json,copy,math
COMPS=json.loads((DESIGN/'component-spec.json').read_text());byref={p['ref']:p for p in COMPS}
c=Client();c.call(project.CloseAllDocuments(force=False))
# Set manufacturable project rules before reloading the project.
p=DESIGN/'rp2350-connect.kicad_pro';j=json.loads(p.read_text());ds=j['board']['design_settings'];rules=ds['rules']
rules.update(min_clearance=0.15,min_track_width=0.127,min_via_diameter=0.55,min_through_hole_diameter=0.2,min_via_annular_width=0.125,min_hole_to_hole=0.25,min_copper_edge_clearance=0.3,min_silk_clearance=0.1,min_text_height=0.8,min_text_thickness=0.10)
ds['track_widths']=[0,0.15,0.18,0.22,0.3,0.5,0.8];ds['via_dimensions']=[{'diameter':0.55,'drill':0.25},{'diameter':0.6,'drill':0.3}]
cl=j['net_settings']['classes'][0];cl.update(clearance=0.15,track_width=0.18,via_diameter=0.55,via_drill=0.25,diff_pair_width=0.22,diff_pair_gap=0.15)
classes=[cl]
for name,width,nets in [('Power',0.5,['/VSYS','/VBAT','/VBUS','/VBUS_RAW','/LED_5V','/1V1']),('USB',0.22,['/USB_DP','/USB_DM','/USB_DP_MCU','/USB_DM_MCU']),('Memory',0.18,['/QSPI_D0','/QSPI_D1','/QSPI_D2','/QSPI_D3','/QSPI_CLK','/FLASH_CS','/PSRAM_CS'])]:
 nc=copy.deepcopy(cl);nc.update(name=name,track_width=width,priority=len(classes));classes.append(nc)
 for net in nets:j['net_settings']['netclass_assignments'][net]=[name]
j['net_settings']['classes']=classes
j['text_variables'].update({'REVISION':'A','BOARD_NAME':'RP2350 CONNECT'})
p.write_text(json.dumps(j,indent=2)+'\n')
doc=c.open(base.DOCTYPE_PCB)
assert not c.get(doc), 'Board already contains items'
cid=c.begin(doc)
report=c.call(pcbcmd.ImportNetlist(board=doc,netlist_path=str(ROOT/'build/rp2350-connect.net'),match_mode=pcbcmd.NMM_REFERENCE,update_footprints=True))
print(report.report[-3000:],flush=True);assert report.error_count==0
c.end(doc,cid,'Import checked schematic netlist');c.save(doc)
fps=[f for f in c.get(doc) if isinstance(f,pcb.FootprintInstance)]
assert len(fps)==len(COMPS),(len(fps),len(COMPS))
cid=c.begin(doc)
updates=[]
for f in fps:
 ref=f.reference_field.text.text.text;p=byref[ref];x,y,angle=p['pcbpos']
 updates.append(pcb.FootprintInstance(id=f.id,position=xy(x,y),orientation=base.Angle(value_degrees=angle),layer=pcb.BL_F_Cu))
c.update(doc,updates)
# Board outline, manufacture from this closed Edge.Cuts contour.
items=[]
for a,b in [((100,100),(185,100)),((185,100),(185,170)),((185,170),(100,170)),((100,170),(100,100))]:
 g=pcb.BoardGraphicShape(id=uid(),layer=pcb.BL_Edge_Cuts)
 g.shape.segment.start.CopyFrom(xy(*a));g.shape.segment.end.CopyFrom(xy(*b));g.shape.attributes.stroke.width.value_nm=50000;items.append(g)
# Origin is defined at lower-left for placement file and fab exports.
# Antenna keepout extends north beyond board; footprints may overhang, copper must not.
z=pcb.Zone(id=uid(),type=pcb.ZT_RULE_AREA,layers=[pcb.BL_F_Cu,pcb.BL_In1_Cu,pcb.BL_In2_Cu,pcb.BL_B_Cu],name='ESP32 antenna no copper')
p=z.outline.polygons.add();p.outline.closed=True
for x,y in [(160.5,95),(181.5,95),(181.5,101.6),(160.5,101.6)]:p.outline.nodes.add().point.CopyFrom(xy(x,y))
z.rule_area_settings.keepout_copper=True;z.rule_area_settings.keepout_vias=True;z.rule_area_settings.keepout_tracks=True;items.append(z)
# Mounting holes are native footprint instances excluded from assembly and BOM.
for ref,x,y in [('H1',104,104),('H2',151,104),('H3',104,166),('H4',181,166)]:
 definition=c.lib(base.LT_FOOTPRINT,'MountingHole:MountingHole_2.7mm_M2.5')
 f=pcb.FootprintInstance(id=uid(),position=xy(x,y),layer=pcb.BL_F_Cu,definition=definition)
 f.reference_field.CopyFrom(definition.reference_field);f.reference_field.text.text.text=ref
 f.value_field.CopyFrom(definition.value_field);f.value_field.text.text.text='M2.5';f.value_field.visible=False
 f.attributes.exclude_from_bill_of_materials=True;f.attributes.exclude_from_position_files=True
 items.append(f)
# Three copper fiducials with 2mm mask opening, excluded from assembly.
for ref,x,y in [('FID1',104,110),('FID2',181,140),('FID3',108,166)]:
 definition=c.lib(base.LT_FOOTPRINT,'Fiducial:Fiducial_1mm_Mask2mm')
 f=pcb.FootprintInstance(id=uid(),position=xy(x,y),layer=pcb.BL_F_Cu,definition=definition)
 f.reference_field.CopyFrom(definition.reference_field);f.reference_field.text.text.text=ref
 f.value_field.CopyFrom(definition.value_field);f.value_field.visible=False
 f.attributes.exclude_from_bill_of_materials=True;f.attributes.exclude_from_position_files=True;items.append(f)
# Silkscreen instructions near controls and connectors. Ref fields will be tidied after routing.
for x,y,t,size in [(114,108,'RP2350 CONNECT  REV A',1.2),(124,110,'16MB FLASH / 8MB PSRAM',0.85),(123,152,'RESET',0.85),(132,152,'BOOT',0.85),(154,154,'ESP BOOT',0.85),(106,110,'BAT+ GND NTC',0.85),(110,152,'QWIIC 3V3',0.85),(159,129,'WIFI / BLE',0.9),(174,160,'MICRO SD',0.85),(114,142,'SWD',0.85),(172,135,'ESP UART0',0.85)]:
 items.append(pcb.BoardText(id=uid(),text=txt(t,x,y,size),layer=pcb.BL_F_SilkS))
c.create(doc,items)
# Hide values, keep reference lettering small and horizontal.
updates=[]
for f in c.get(doc):
 if not isinstance(f,pcb.FootprintInstance):continue
 f.value_field.visible=False
 f.reference_field.text.text.attributes.size.CopyFrom(xy(0.8,0.8));f.reference_field.text.text.attributes.stroke_width.value_nm=100000
 f.reference_field.text.text.attributes.angle.value_degrees=0
 f.reference_field.text.text.attributes.keep_upright=True
 updates.append(f)
c.update(doc,updates)
c.end(doc,cid,'Place all fitted parts, holes, fiducials, edge cuts and RF keepout');c.save(doc)
print('Saved canonical PCB',DESIGN/'rp2350-connect.kicad_pcb',flush=True)
