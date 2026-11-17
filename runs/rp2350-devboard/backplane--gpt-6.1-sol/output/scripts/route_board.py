from ipc_client import *
import json,sys,time
c=Client();doc=c.open(base.DOCTYPE_PCB)
objs=c.get(doc);fps=[f for f in objs if isinstance(f,pcb.FootprintInstance)]
assert len(fps)==125
pads=[]
for f in fps:
 for a in f.definition.items:
  if a.Is(pcb.Pad.DESCRIPTOR):pads.append(unpack(a))
reports=[]
groups=[('core and switch loops',['/CORE_SW','/1V1','/CORE_FB','/BB_L1','/BB_L2','/MAIN_FB','/BB_VAUX','/LED_SW','/LED_FB'],False),('QSPI memory',['/QSPI_D0','/QSPI_D1','/QSPI_D2','/QSPI_D3','/QSPI_CLK','/FLASH_CS','/PSRAM_CS'],True),('USB data',['/USB_DP','/USB_DM','/USB_DP_MCU','/USB_DM_MCU'],False)]
if '--remaining' in sys.argv:groups=[('remaining nets',None,False)]
for title,names,no_vias in groups:
 ids=[p.id for p in pads if names is None or p.net.name in names]
 if '--all-items' in sys.argv:ids += [o.id for o in c.get(doc) if isinstance(o,(pcb.Track,pcb.Via,pcb.Arc))]
 cid=c.begin(doc)
 result=c.call(route.SketchRoute(board=doc,items=ids,preferred_layer=pcb.BL_In2_Cu if '--inner2' in sys.argv else pcb.BL_In3_Cu if '--inner3' in sys.argv else pcb.BL_B_Cu if '--bottom' in sys.argv else pcb.BL_F_Cu,corner_mode=route.SRCM_MITERED_45,disallow_vias=no_vias,time_limit_ms=45000))
 c.end(doc,cid,'Route '+title);c.save(doc)
 data={'stage':title,'connections':result.connections,'routed':result.routed,'failed':result.failed,'vias':result.vias,'length_mm':result.length_nm/1e6,'timed_out':result.timed_out,'elapsed_ms':result.elapsed_ms};reports.append(data)
 print(json.dumps(data),flush=True)
 c.call(pcbcmd.RefillZones(board=doc));c.save(doc)
assert len([f for f in c.get(doc) if isinstance(f,pcb.FootprintInstance)])==125
path=ROOT/'build'/('route-remaining.json' if '--remaining' in sys.argv else 'route-critical.json');path.write_text(json.dumps(reports,indent=2)+'\n')
