from ipc_client import *
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);fps={f.reference_field.text.text.text:f for f in objs if isinstance(f,pcb.FootprintInstance)}
deletes=[o.id for o in objs if isinstance(o,pcb.Via) and abs(o.position.x_nm/1e6-134)<.001 and abs(o.position.y_nm/1e6-138.77)<.001]
changes=[pcb.FootprintInstance(id=fps[r].id,position=xy(x,y),layer=pcb.BL_F_Cu) for r,x,y in [('R13',132,124.8),('C14',134,142.2)]]
cid=c.begin(d)
if deletes:c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=deletes))
c.update(d,changes);c.end(d,cid,'Clear QSPI and GPIO escapes with nearby resistor and capacitor relocation');c.save(d)
c.call(pcbcmd.RefillZones(board=d));c.save(d)
