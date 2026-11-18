import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from sexpr import *
S='/home/ubuntu/.local/share/backplane/kicad/10.99.0-bp.4/share/kicad'
def sym(lib, name):
    e = parse(open(f'{S}/symbols/{lib}.kicad_symdir/{name}.kicad_sym').read())
    for s in findall(e, 'symbol'):
        if s[1] == name: return s
def pins(s, acc=None):
    acc = [] if acc is None else acc
    for u in findall(s, 'symbol'):
        for p in findall(u, 'pin'):
            acc.append((find(p,'number')[1], find(p,'name')[1], p[1], find(p,'at')[1:], find(p,'length')[1], u[1]))
    return acc
def fp(lib, name):
    return parse(open(f'{S}/footprints/{lib}.pretty/{name}.kicad_mod').read())
def fpinfo(f):
    pads=[]
    for p in findall(f,'pad'):
        pads.append((p[1],p[2],p[3],find(p,'at')[1:],find(p,'size')[1:]))
    xs=[];ys=[]
    for t in ('fp_line','fp_rect','fp_poly','fp_circle'):
        for l in findall(f,t):
            if find(l,'layer')[1]=='F.CrtYd':
                for k in ('start','end','center'):
                    if find(l,k): xs.append(float(find(l,k)[1])); ys.append(float(find(l,k)[2]))
                if find(l,'pts'):
                    for q in findall(find(l,'pts'),'xy'): xs.append(float(q[1])); ys.append(float(q[2]))
    return pads,(min(xs),min(ys),max(xs),max(ys)) if xs else None
if __name__=='__main__':
    for a in sys.argv[1:]:
        lib,name=a.split(':')
        if os.path.exists(f'{S}/symbols/{lib}.kicad_symdir/{name}.kicad_sym'):
            s=sym(lib,name); print('SYM',a, 'extends' , find(s,'extends'))
            for p in sorted(pins(s), key=lambda p:(len(p[0]),p[0])): print('  ',p)
        else:
            pads,bb=fpinfo(fp(lib,name)); print('FP',a,'crtyd',bb)
            for p in pads: print('  ',p)
