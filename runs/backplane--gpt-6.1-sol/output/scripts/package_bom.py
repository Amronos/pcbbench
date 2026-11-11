from pathlib import Path
import json,csv,collections
root=Path(__file__).resolve().parents[1];parts=json.loads((root/'boards/rp2350-connect/component-spec.json').read_text());assert len(parts)==118
out=root/'fab';out.mkdir(exist_ok=True)
groups=collections.defaultdict(list)
for p in parts:groups[(p['mfr'],p['mpn'],p['value'],p['localfp'],p['note'])].append(p['ref'])
with (out/'BOM.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['References','Quantity per board','Value','Manufacturer','Manufacturer part number','KiCad footprint','Fit','Procurement','Notes'])
 for (mfr,mpn,value,fp,note),refs in groups.items():w.writerow([' '.join(refs),len(refs),value,mfr,mpn,fp,'YES','PCBWay turnkey procurement',note])
with (out/'BOM-ungrouped.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','Manufacturer','Manufacturer part number','Footprint','Fit','Notes'])
 for p in parts:w.writerow([p['ref'],p['value'],p['mfr'],p['mpn'],p['localfp'],'YES',p['note']])
print('BOM:',len(parts),'fitted components;',len(groups),'procurement lines')
