from ipc_client import *
import json
c=Client();d=c.open(base.DOCTYPE_PCB);objs=c.get(d);ids=[]
for o in objs:
 if isinstance(o,pcb.Via) and (o.id.value in ['5e48ae3a-3901-4c50-a8f0-7b109ec2c381','a9c86ff0-8adb-443c-9322-1139aa62a698','1d025501-5679-49cc-92ff-2762e9d2b781','52a4a941-eb8a-436c-be8a-0a47631c0967']):ids.append(o.id)
 if isinstance(o,pcb.Track) and o.id.value in ['c0b2f3fb-de11-4878-bcd0-68bb55c2362d','32752bbd-7f15-468d-ba57-aee66315cc23']:ids.append(o.id)
cid=c.begin(d);c.call(editor.DeleteItems(header=base.ItemHeader(document=d),item_ids=ids));c.end(d,cid,'Remove trial escape and stitches that fail independent all-layer clearance checks');c.save(d);c.call(pcbcmd.RefillZones(board=d));c.save(d)
