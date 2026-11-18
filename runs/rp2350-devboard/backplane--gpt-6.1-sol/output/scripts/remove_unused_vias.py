from ipc_client import *
import subprocess,json
c=Client();d=c.open(base.DOCTYPE_PCB);K='/home/ubuntu/pcbbench-hub/bin/kicad-cli';rep=ROOT/'build/drc-current.json'
def drc():
 subprocess.run([K,'pcb','drc','--refill-zones','--schematic-parity','--format','json','-o',str(rep),str(DESIGN/'rp2350-connect.kicad_pcb')],check=True,capture_output=True);return json.loads(rep.read_text())
j=drc();assert not j['unconnected_items'];assert not [v for v in j['violations'] if v['severity']=='error'];ids=[i['uuid'] for v in j['violations'] if v['type']=='via_dangling' for i in v['items']]
for id in ids:
 obj=next((o for o in c.get(d) if isinstance(o,pcb.Via) and o.id.value==id),None)
 if obj is None:continue
 cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=[obj.id]));c.end(d,cid,'Remove unused single-layer via');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);after=drc()
 if after['unconnected_items'] or [v for v in after['violations'] if v['severity']=='error']:
  cid=c.begin(d);c.create(d,[obj]);c.end(d,cid,'Retain via needed by verified copper connectivity');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);j=drc();print('Retained connectivity junction',obj.net.name,flush=True)
 else:j=after;print('Removed unused via',obj.net.name,flush=True)
assert not j['unconnected_items'];assert not [v for v in j['violations'] if v['severity']=='error'];print('Remaining warnings',len(j['violations']),flush=True)
