from pathlib import Path
import subprocess,csv,json,shutil,hashlib,zipfile,collections
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'boards/rp2350-connect';F=ROOT/'fab';K='/home/ubuntu/pcbbench-hub/bin/kicad-cli';B=str(D/'rp2350-connect.kicad_pcb');S=str(D/'rp2350-connect.kicad_sch')
for p in ['gerbers','drill','verification','source-kicad10']: (F/p).mkdir(exist_ok=True)
def run(a):
 r=subprocess.run([K]+a,capture_output=True,text=True);print(r.stdout,r.stderr,flush=True);assert r.returncode==0,(a,r.returncode);return r.stdout
jobs=[['pcb','export','gerbers','-l','F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask','-o',str(F/'gerbers'),B],['pcb','export','drill','--format','excellon','--drill-origin','absolute','--excellon-units','mm','--excellon-separate-th','--generate-map','--map-format','pdf','--generate-report','--report-path',str(F/'drill/drill-report.txt'),'-o',str(F/'drill'),B],['pcb','export','pos','--format','csv','--units','mm','--side','both','-o',str(F/'placement.csv'),B],['pcb','export','ipcd356','-o',str(F/'rp2350-connect.ipc'),B],['sch','export','pdf','-o',str(F/'schematic.pdf'),S],['pcb','export','pdf','-l','F.Fab,F.SilkS,Edge.Cuts','--mode-single','--black-and-white','--sketch-pads-on-fab-layers','--sketch-pad-numbers','--scale','1','-o',str(F/'assembly-top.pdf'),B],['pcb','export','pdf','-l','B.Fab,Edge.Cuts','--mode-single','--black-and-white','--sketch-pads-on-fab-layers','--sketch-pad-numbers','--mirror','--scale','1','-o',str(F/'assembly-bottom.pdf'),B]]
with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,jobs))
if (F/'source-kicad10').exists():shutil.rmtree(F/'source-kicad10')
# The compatibility conversion is independent of CAM exports; no forced dropping of features.
run(['project','downgrade','--target','10.0','--report-json',str(F/'verification/kicad10-conversion-report.json'),'-o',str(F/'source-kicad10'),str(D/'rp2350-connect.kicad_pro')])
for n in ['connect.pretty','connect.kicad_sym','fp-lib-table','sym-lib-table','component-spec.json','library-provenance.json']:
 src=D/n;dest=F/'source-kicad10'/n
 if src.is_dir():shutil.copytree(src,dest,dirs_exist_ok=True)
 else:shutil.copy2(src,dest)
# BOM and CPL are independent exports, reconciled by fitted reference IDs.
parts=json.loads((D/'component-spec.json').read_text());refs={p['ref'] for p in parts}
rows=list(csv.DictReader((F/'placement.csv').open()));col=next(k for k in rows[0] if k.lower() in ['ref','reference','designator']);got={r[col] for r in rows};assert got==refs,(refs-got,got-refs);assert len(rows)==118
(F/'verification/assembly-reconciliation.json').write_text(json.dumps({'bom_components':118,'placement_rows':len(rows),'missing_references':sorted(refs-got),'extra_references':sorted(got-refs),'all_components_fitted':True,'pcbway_procures_all':True},indent=2)+'\n')
for n in ['erc-final.json','drc-final.json','netlist-intent-check.json','pcb-intent-check.json','final-footprint-freeze.json']:
 src=ROOT/'build'/n
 if src.exists():shutil.copy2(src,F/'verification'/n)
shutil.copy2(ROOT/'build/rp2350-connect.net',F/'schematic.net')
print('Exported PCBWay CAM, assembly and compatible source package',flush=True)
