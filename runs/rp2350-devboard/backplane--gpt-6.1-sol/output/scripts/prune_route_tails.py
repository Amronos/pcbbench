from ipc_client import *
import subprocess,json,shutil
c=Client();d=c.open(base.DOCTYPE_PCB);K='/home/ubuntu/pcbbench-hub/bin/kicad-cli';b=str(DESIGN/'rp2350-connect.kicad_pcb');rep=ROOT/'build/drc-current.json'
def drc():
 subprocess.run([K,'pcb','drc','--refill-zones','--format','json','--schematic-parity','-o',str(rep),b],check=True,capture_output=True);return json.loads(rep.read_text())
j=drc();assert not [v for v in j['violations'] if v['severity']=='error'];assert not j['unconnected_items'],j['unconnected_items']
seen=set()
for step in range(20):
 ids={i['uuid'] for v in j['violations'] if v['type']=='track_dangling' for i in v['items']}
 if not ids or frozenset(ids) in seen:break
 seen.add(frozenset(ids))
 objs=[o for o in c.get(d) if hasattr(o,'id') and o.id.value in ids];cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=[o.id for o in objs]));c.end(d,cid,'Prune unused copper tails pass '+str(step+1));c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);after=drc()
 if after['unconnected_items']:
  cid=c.begin(d);c.create(d,objs);c.end(d,cid,'Retain copper tails necessary for checked connectivity');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d);j=drc();print('Retained tail group to preserve connectivity',flush=True);break
 j=after;print('Pruned',len(objs),'tails; remaining warnings',len(j['violations']),flush=True)
assert not j['unconnected_items'];assert not j['schematic_parity'];assert not [v for v in j['violations'] if v['severity']=='error'],j['violations']
print('Zero DRC errors, zero unrouted, zero schematic parity issues',flush=True)
