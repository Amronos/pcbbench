from ipc_client import *
import shutil
c=Client();d=c.open(base.DOCTYPE_PCB);c.save(d);shutil.copy2(DESIGN/'rp2350-connect.kicad_pcb',ROOT/'build/backups/before-six-layers.kicad_pcb')
objs=c.get(d);layers=c.call(pcbcmd.GetBoardEnabledLayers(board=d));changes=[]
for o in objs:
 if isinstance(o,pcb.Zone):
  if o.type==pcb.ZT_COPPER and pcb.BL_In2_Cu in o.layers:
   o.layers[:]=[pcb.BL_In4_Cu];o.name='/3V3 plane BL_In4_Cu';changes.append(o)
  elif o.type==pcb.ZT_RULE_AREA and pcb.BL_In1_Cu in o.layers:
   o.layers.extend([pcb.BL_In3_Cu,pcb.BL_In4_Cu]);changes.append(o)
 if isinstance(o,pcb.Via):o.pad_stack.layers.extend([pcb.BL_In3_Cu,pcb.BL_In4_Cu]);changes.append(o)
cid=c.begin(d);c.call(pcbcmd.SetBoardEnabledLayers(board=d,copper_layer_count=6,layers=list(layers.layers)+[pcb.BL_F_Paste,pcb.BL_B_Paste]));c.update(d,changes);c.end(d,cid,'Use six layers with two internal signal layers and dedicated GND and 3V3 planes');c.save(d)
c.call(pcbcmd.RefillZones(board=d));c.save(d);print(c.call(pcbcmd.GetBoardEnabledLayers(board=d)))
