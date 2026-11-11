from ipc_client import *
import json,shutil,sexpdata as sx
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);ids=[];j=json.loads((ROOT/'build/drc-current.json').read_text())
for o in objs:
 if isinstance(o,pcb.Track) and o.net.name=='/CORE_FB':ids.append(o.id)
 if isinstance(o,pcb.Via) and o.id.value=='1069fd03-d6df-4eb1-9754-5e0287bbe60b':ids.append(o.id)
for v in j['violations']:
 if v['type']=='track_dangling':ids.extend(base.KIID(value=i['uuid']) for i in v['items'])
ids={i.value:i for i in ids};cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=list(ids.values())));c.end(d,cid,'Remove redundant route tails and reroute core feedback clear of both ground pins');c.save(d)
objs=c.get(d);pads=[]
for f in objs:
 if isinstance(f,pcb.FootprintInstance):pads.extend(unpack(a).id for a in f.definition.items if a.Is(pcb.Pad.DESCRIPTOR) and unpack(a).net.name=='/CORE_FB')
cid=c.begin(d);r=c.call(route.SketchRoute(board=d,items=pads,preferred_layer=pcb.BL_F_Cu,corner_mode=route.SRCM_MITERED_45,disallow_vias=True,time_limit_ms=45000));c.end(d,cid,'Route core feedback on top around the regulator ground connection');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);print('Feedback routes',r.routed,'failed',r.failed,flush=True)
# U9 silk-only variant keeps U5 on the unchanged standard SOT-23-6.
mod=DESIGN/'connect.pretty/SOT-23-6.kicad_mod';newmod=DESIGN/'connect.pretty/SOT-23-6_LED.kicad_mod';a=sx.loads(mod.read_text());a[1]='SOT-23-6_LED';newmod.write_text(sx.dumps(a)+'\n');shutil.copy2(ROOT/'build/backups/SOT-23-6-before-freeze.kicad_mod',mod)
f=next(f for f in c.get(d) if isinstance(f,pcb.FootprintInstance) and f.reference_field.text.text.text=='U9');f.definition.id.entry_name='SOT-23-6_LED';cid=c.begin(d);c.update(d,[f]);c.end(d,cid,'Use a separate LED-boost footprint for its trimmed silk marker');c.save(d)
s=c.open(base.DOCTYPE_SCHEMATIC);sy=next(o for o in c.get(s) if isinstance(o,sch.SchematicSymbolInstance) and o.reference_field.text.text=='U9');sy.footprint_field.text.text='connect:SOT-23-6_LED';cid=c.begin(s);c.update(s,[sy]);c.end(s,cid,'Match the LED-boost footprint variant in the schematic');c.save(s)
p=DESIGN/'component-spec.json';spec=json.loads(p.read_text())
for a in spec:
 if a['ref']=='U9':a['localfp']='connect:SOT-23-6_LED'
p.write_text(json.dumps(spec,indent=2)+'\n')
