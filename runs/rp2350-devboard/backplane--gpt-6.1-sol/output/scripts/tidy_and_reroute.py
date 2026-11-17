from ipc_client import *
import sexpdata as sx,shutil
c=Client();d=c.open(base.DOCTYPE_PCB);c.save(d);shutil.copy2(DESIGN/'rp2350-connect.kicad_pcb',ROOT/'build/backups/before-routing-margin-fix.kicad_pcb');objs=c.get(d)
a=sx.load(open(ROOT/'build/backups/before-six-layers.kicad_pcb'))
old={str(z[1]) for o in a if isinstance(o,list) and str(o[0]) in ['segment','arc','via'] for z in o if isinstance(z,list) and str(z[0])=='uuid'}
changes=[];ids=[]
for o in objs:
 if isinstance(o,pcb.Track) and o.width.value_nm==127000 and o.id.value not in old:ids.append(o.id)
 if isinstance(o,pcb.Via) and o.id.value not in old:ids.append(o.id)
 if isinstance(o,pcb.Zone) and o.type==pcb.ZT_COPPER and pcb.BL_B_Cu in o.layers:
  o.copper_settings.connection.zone_connection=pcb.ZCS_FULL;changes.append(o)
 if isinstance(o,pcb.BoardText):
  if o.text.text=='QWIIC 3V3':o.text.position.CopyFrom(xy(103,153));changes.append(o)
  if o.text.text=='BOOT':o.text.position.CopyFrom(xy(128,150));changes.append(o)
  if o.text.text=='MICRO SD':o.text.position.CopyFrom(xy(170,159));changes.append(o)
 if isinstance(o,pcb.FootprintInstance):
  r=o.reference_field.text.text.text
  for a in o.definition.items:
   sh=unpack(a)
   if r=='D2' and isinstance(sh,pcb.BoardText) and sh.text.text=='1':ids.append(sh.id)
   if r=='U9' and isinstance(sh,pcb.BoardGraphicShape) and sh.layer==pcb.BL_F_SilkS and sh.shape.HasField('polygon'):ids.append(sh.id)
   if r=='U8' and isinstance(sh,pcb.BoardGraphicShape) and sh.layer==pcb.BL_F_SilkS and sh.shape.HasField('segment'):
    seg=sh.shape.segment
    if seg.start.y_nm<100300000 and seg.end.y_nm<100300000:ids.append(sh.id);continue
    if seg.start.y_nm<100300000:seg.start.y_nm=100300000;changes.append(sh)
    elif seg.end.y_nm<100300000:seg.end.y_nm=100300000;changes.append(sh)
cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=ids));c.update(d,changes);c.end(d,cid,'Increase numerical routing safety margin and clean assembly artwork and ground connections');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);print('Removed',len(ids),'items and saved artwork milestone')
