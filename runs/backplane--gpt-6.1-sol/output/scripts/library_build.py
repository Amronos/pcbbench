"""Copy and flatten used KiCad library symbols and footprints into the project."""
from pathlib import Path
import sexpdata as sx,copy,hashlib,json
from design_spec import COMP
BASE=Path('/home/ubuntu/.local/share/backplane/kicad/10.99.0-bp.4/share/kicad')
DEST=Path(__file__).resolve().parents[1]/'boards/rp2350-connect'
S=sx.Symbol
def tag(a,n):return isinstance(a,list) and a and str(a[0])==n
def children(a,n):return [x for x in a if tag(x,n)]
def sym(lib,name):
 root=sx.loads((BASE/'symbols'/(lib+'.kicad_symdir')/(name+'.kicad_sym')).read_text());a=children(root,'symbol')[0]
 ext=children(a,'extends')
 if ext:
  parent=sym(lib,ext[0][1]);old=parent[1];parent[1]=name
  for b in children(parent,'symbol'):b[1]=name+b[1][len(old):]
  for b in a[2:]:
   if tag(b,'extends'):continue
   key=str(b[0]);ident=b[1] if key=='property' else None
   parent=[x for x in parent if not (isinstance(x,list) and str(x[0])==key and (ident is None or x[1]==ident))]
   parent.append(copy.deepcopy(b))
  a=parent
 return a

def write():
 (DEST/'connect.pretty').mkdir(exist_ok=True)
 allsym={};fps={};manifest=[]
 for c in COMP:
  lib,name=c['lib'].split(':');a=sym(lib,name)
  # Symbols with same base may carry different footprints; retain per-instance footprint override.
  allsym[name]=a
  f=c['footprint']
  if not f:
   props=children(a,'property');f=next(x[2] for x in props if x[1]=='Footprint')
  assert f,c['ref']
  l,n=f.split(':',1);src=BASE/'footprints'/(l+'.pretty')/(n+'.kicad_mod')
  assert src.exists(),str(src)
  data=src.read_text()
  # Reproducible local copies; omit generated private label on silk.
  obj=sx.loads(data)
  obj=[x for x in obj if not (tag(x,'property') and x[1]=='KiLib_Generator')]
  if l=='RF_Module' and n=='ESP32-C3-WROOM-02':
   # Keep the center solder pad and paste windows, but replace open via-in-pad with filled/capped process.
   # All original thermal vias are retained; PCBWay must resin fill and copper cap these PTHs.
   pass
  out=sx.dumps(obj)+'\n'
  (DEST/'connect.pretty'/(n+'.kicad_mod')).write_text(out)
  fps[n]=out;c['localfp']='connect:'+n;c['localsym']='connect:'+name
  manifest.append({'ref':c['ref'],'symbol_source':c['lib'],'footprint_source':f,'footprint_sha256':hashlib.sha256(out.encode()).hexdigest()})
 # Flatten all inherited definitions to keep project portable, with no external symbol dependency.
 allsym['PWR_FLAG']=sym('power','PWR_FLAG')
 text=sx.dumps([S('kicad_symbol_lib'),[S('version'),20251024],[S('generator'),'kicad_symbol_editor']]+list(allsym.values()))+'\n'
 (DEST/'connect.kicad_sym').write_text(text)
 (DEST/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "connect") (type "KiCad") (uri "${KIPRJMOD}/connect.kicad_sym") (options "") (descr "Self-contained flattened KiCad symbols")))\n')
 (DEST/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "connect") (type "KiCad") (uri "${KIPRJMOD}/connect.pretty") (options "") (descr "Frozen footprints for RP2350 Connect")))\n')
 (DEST/'library-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (DEST/'component-spec.json').write_text(json.dumps(COMP,indent=2)+'\n')
 print('Prepared',len(COMP),'components,',len(allsym),'symbols,',len(fps),'footprints')
if __name__=='__main__':write()
