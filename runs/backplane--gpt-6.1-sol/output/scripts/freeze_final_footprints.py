from pathlib import Path
import sexpdata as sx,copy,json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'boards/rp2350-connect';S=sx.Symbol
r=sx.loads((D/'rp2350-connect.kicad_pcb').read_text());selected={'U7','U8','U9','J4','FID1'};manifest=[]
for f in r:
 if not isinstance(f,list) or str(f[0])!='footprint':continue
 ref=next((p[2] for p in f if isinstance(p,list) and str(p[0])=='property' and p[1]=='Reference'),'')
 if ref not in selected:continue
 name=f[1].split(':')[-1];rot=next((z[1] for x in f if isinstance(x,list) and str(x[0])=='transform' for z in x[1:] if isinstance(z,list) and str(z[0])=='rotate'),0)
 a=copy.deepcopy(f);a[1]=name
 a=[v for v in a if not(isinstance(v,list) and str(v[0]) in ['transform','at','uuid','path','sheetname','sheetfile'])]
 a.insert(2,[S('version'),20260206]);a.insert(3,[S('generator'),'pcbnew']);a.insert(4,[S('generator_version'),'10.99'])
 for v in a:
  if not isinstance(v,list):continue
  if str(v[0])=='property':
   if v[1]=='Reference':v[2]='REF**'
   elif v[1]=='Value':v[2]=name
  if str(v[0]) in ['property','pad','fp_text']:
   for q in v:
    if isinstance(q,list) and str(q[0])=='at':
     angle=(q[3] if len(q)>3 else 0)-rot
     if len(q)>3:q[3]=angle
     elif angle:q.append(angle)
  if str(v[0])=='pad':v[:]=[q for q in v if not(isinstance(q,list) and str(q[0]) in ['net','pinfunction','pintype'])]
 out=D/'connect.pretty'/(name+'.kicad_mod');shutil.copy2(out,ROOT/'build/backups'/(name+'-before-freeze.kicad_mod'));data=sx.dumps(a)+'\n';out.write_text(data);manifest.append({'footprint':name,'source_reference':ref,'sha256':hashlib.sha256(data.encode()).hexdigest(),'changes':'Final saved copper, pad, courtyard and artwork geometry; board transform and electrical net assignments removed.'})
(ROOT/'build/final-footprint-freeze.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Froze',len(manifest),'final footprint definitions')
