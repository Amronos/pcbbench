from ipc_client import *
c=Client();doc=c.open(base.DOCTYPE_PCB)
fps={f.reference_field.text.text.text:f for f in c.get(doc) if isinstance(f,pcb.FootprintInstance)}
assert len(fps)==125
cid=c.begin(doc)
changes=[]
for ref,x,y in [('H2',145,104),('H4',181,161),('FID2',181,137),('FID3',110,166)]:
 changes.append(pcb.FootprintInstance(id=fps[ref].id,position=xy(x,y),layer=pcb.BL_F_Cu))
c.update(doc,changes);c.end(doc,cid,'Clear connector mounting holes and fiducials');c.save(doc)
got=[f for f in c.get(doc) if isinstance(f,pcb.FootprintInstance)]
print('IPC placement readback',len(got),'footprints',len({f.id.value for f in got}),'unique IDs')
assert len(got)==125,'IPC update created duplicate footprints again'
