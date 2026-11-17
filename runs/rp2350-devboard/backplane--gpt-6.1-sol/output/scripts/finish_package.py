from pathlib import Path
import pymupdf as fitz,csv,json,shutil,hashlib,zipfile
R=Path(__file__).resolve().parents[1];F=R/'fab';D=R/'boards/rp2350-connect'
# Retain actual native source separately from the compatibility conversion.
src=F/'source-native';src.mkdir(exist_ok=True)
for n in ['rp2350-connect.kicad_pro','rp2350-connect.kicad_pcb','rp2350-connect.kicad_sch','connect.pretty','connect.kicad_sym','fp-lib-table','sym-lib-table','component-spec.json','library-provenance.json']:
 a=D/n;b=src/n
 if a.is_dir():shutil.copytree(a,b,dirs_exist_ok=True)
 else:shutil.copy2(a,b)
# Crop vector assembly drawings to all plotted content, after verifying it fits the original page.
for name in ['assembly-top','assembly-bottom']:
 path=F/(name+'.pdf');d=fitz.open(path);p=d[0];rr=[x['rect'] for x in p.get_drawings()]+[fitz.Rect(x[:4]) for x in p.get_text('blocks') if str(x[4]).strip()];box=fitz.Rect(rr[0])
 for x in rr[1:]:box|=x
 assert p.rect.contains(box),(name,p.rect,box)
 box+=(-8,-8,8,8);box&=p.rect;p.set_cropbox(box);tmp=R/'build'/(name+'-cropped.pdf');d.save(tmp);d.close();shutil.copy2(tmp,path)
 dd=fitz.open(path);dd[0].get_pixmap(matrix=fitz.Matrix(3,3),alpha=False).save(F/(name+'.png'))
# Fabrication specification with dimensions and verified NPTH locations.
doc=fitz.open();p=doc.new_page(width=595,height=842);p.insert_text((40,38),'RP2350 CONNECT — REV A',fontsize=17);p.insert_text((40,60),'PCB fabrication specification — first article',fontsize=11)
mm=72/25.4;ox=80;oy=105;w=85*mm;h=70*mm;p.draw_rect(fitz.Rect(ox,oy,ox+w,oy+h),color=(0,0,0),width=.8);p.insert_text((ox+w/2-22,oy-12),'85.00 mm',fontsize=10);p.insert_text((ox-48,oy+h/2),'70.00 mm',fontsize=10)
rows=list(csv.DictReader((F/'PCB-features.csv').open()))
for a in rows:
 x=ox+(float(a['X mm native'])-100)*mm;y=oy+(float(a['Y mm native'])-100)*mm
 if a['Type']=='NPTH':p.draw_circle((x,y),2.7*mm/2,color=(0,0,0),width=.7);p.insert_text((x+5,y+3),a['Reference'],fontsize=8)
p.insert_text((ox+60.5*mm,oy-24),'ESP PCB antenna overhang; no copper under antenna',fontsize=8);p.draw_rect(fitz.Rect(ox+60.5*mm,oy-5*mm,ox+81.5*mm,oy),color=(.5,.5,.5),width=.5)
y=335
lines=['Finished board: 85 x 70 mm; 1.6 mm FR-4, Tg >=150 C; ENIG, lead-free.', 'Green solder mask; white silkscreen; nominal 35 um copper on all six layers.', 'Layer order: F.Cu / In1.Cu GND / In2.Cu signal / In3.Cu signal / In4.Cu 3V3 / B.Cu.', 'PCBWay to finalize a symmetric 1.6 mm stack; closely couple outer/reference layers.', 'Minimum track: 0.127 mm. Minimum copper clearance: 0.10 mm.', 'Routing vias: 0.45/0.20 mm; power/thermal vias also 0.55/0.25 mm.', 'Minimum drill: 0.20 mm. Hole-to-hole clearance >=0.25 mm.', 'Copper-to-edge clearance >=0.30 mm. Four 2.7 mm NPTH mounting holes.', 'Resin fill + copper cap vias (type VII), including solder-pad and module thermal vias.', 'Do not fill connector PTH holes. Follow supplied mask/paste and drill files.', 'All 118 components fitted on top, including TH sockets and connectors.', 'USB/card/Qwiic openings and antenna overhang must stay clear of panel rails.', 'Bare-board electrical test against supplied IPC-D-356 netlist.', 'See PCBWAY-INSTRUCTIONS.md for procurement, polarity, panelization and assembly.', 'See TEST-PLAN.md for first-article rail, USB, battery, memory, radio and SD tests.']
for s in lines:p.insert_text((40,y),s,fontsize=9);y+=18
p.insert_text((40,815),'Diagram: board outline and mounting holes, 1:1; coordinates in PCB-features.csv.',fontsize=8);doc.save(F/'FABRICATION-SPEC.pdf')
# Refresh verification outputs only after saved canonical source validation.
for n in ['drc-final.json','erc-final.json','netlist-intent-check.json','pcb-intent-check.json','final-footprint-freeze.json']:
 shutil.copy2(R/'build'/n,F/'verification'/n)
# Validate every content file and then build a self-contained ZIP.
manifest=[]
for a in sorted(F.rglob('*')):
 if a.is_file() and a.name not in ['SHA256SUMS','rp2350-connect-pcbway.zip','package-sha256.txt']:
  assert a.stat().st_size>0,a;manifest.append(hashlib.sha256(a.read_bytes()).hexdigest()+'  '+str(a.relative_to(F)))
(F/'SHA256SUMS').write_text('\n'.join(manifest)+'\n');zip_path=F/'rp2350-connect-pcbway.zip'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for a in sorted(F.rglob('*')):
  if a.is_file() and a.name not in ['rp2350-connect-pcbway.zip','package-sha256.txt']:z.write(a,str(a.relative_to(F)))
assert zipfile.ZipFile(zip_path).testzip() is None
(F/'package-sha256.txt').write_text(hashlib.sha256(zip_path.read_bytes()).hexdigest()+'  '+zip_path.name+'\n');print('Packaged',len(manifest),'files; ZIP',zip_path.stat().st_size,'bytes')
