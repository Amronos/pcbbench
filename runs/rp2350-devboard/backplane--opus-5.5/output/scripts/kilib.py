"""KiCad library helpers: load + flatten symbols, load footprints."""
import os, copy
from sexp import parse, find, findall, Sym

KSHARE = os.path.expanduser('~/.local/share/backplane/kicad/10.99.0-bp.4/share/kicad')
SYMDIR = KSHARE + '/symbols'
FPDIR = KSHARE + '/footprints'
HERE = os.path.dirname(os.path.abspath(__file__))
PROJ_LIB = os.path.join(HERE, '..', 'boards', 'rp2350-dev', 'lib')

_symcache = {}

def _load_raw_symbol(lib, name):
    p = os.path.join(SYMDIR, lib + '.kicad_symdir', name + '.kicad_sym')
    t = parse(open(p).read())
    for e in findall(t, 'symbol'):
        if e[1] == name:
            return e
    raise KeyError(name)

def _rename_units(sym, old, new):
    for e in sym:
        if isinstance(e, list) and e and e[0] == 'symbol':
            u = e[1]
            if u.startswith(old + '_'):
                e[1] = new + u[len(old):]

def load_symbol(libid):
    """Return flattened symbol s-expr named 'Lib:Name' suitable for lib_symbols."""
    if libid in _symcache:
        return copy.deepcopy(_symcache[libid])
    lib, name = libid.split(':')
    raw = _load_raw_symbol(lib, name)
    ext = find(raw, 'extends')
    if ext:
        parent = load_symbol(lib + ':' + ext[1])
        pname = ext[1]
        sym = parent
        sym[1] = name
        _rename_units(sym, pname, name)
        # override properties
        childprops = {p[1]: p for p in findall(raw, 'property')}
        newl = []
        for e in sym:
            if isinstance(e, list) and e and e[0] == 'property' and e[1] in childprops:
                newl.append(childprops.pop(e[1]))
            else:
                newl.append(e)
        # insert remaining child props after last property
        idx = max(i for i, e in enumerate(newl) if isinstance(e, list) and e and e[0] == 'property')
        for p in childprops.values():
            idx += 1
            newl.insert(idx, p)
        sym = newl
        sym[1] = name
    else:
        sym = copy.deepcopy(raw)
    _symcache[libid] = copy.deepcopy(sym)
    return copy.deepcopy(sym)

def lib_symbol_for_sch(libid):
    s = load_symbol(libid)
    s[1] = libid
    return s

def symbol_pins(libid):
    """List of dicts: number, name, type, x, y, angle, length, unit."""
    s = load_symbol(libid)
    name = s[1]
    pins = []
    for u in findall(s, 'symbol'):
        # unit index from name suffix Name_U_B
        parts = u[1].rsplit('_', 2)
        unit = int(parts[-2]) if len(parts) >= 3 else 0
        for p in findall(u, 'pin'):
            at = find(p, 'at')
            pins.append(dict(number=find(p, 'number')[1], name=find(p, 'name')[1],
                             type=str(p[1]), x=float(at[1]), y=float(at[2]),
                             angle=float(at[3]) if len(at) > 3 else 0.0,
                             length=float(find(p, 'length')[1]), unit=unit,
                             hidden=any(isinstance(z, list) and z and z[0] == 'hide' for z in p) or (Sym('hide') in p)))
    return pins

def symbol_prop(libid, key):
    s = load_symbol(libid)
    for p in findall(s, 'property'):
        if p[1] == key:
            return p[2]
    return None

def load_footprint(fpid):
    lib, name = fpid.split(':')
    if lib == 'RP2350_Dev':
        p = os.path.join(PROJ_LIB, 'RP2350_Dev.pretty', name + '.kicad_mod')
    else:
        p = os.path.join(FPDIR, lib + '.pretty', name + '.kicad_mod')
    return parse(open(p).read())

def footprint_pads(fpid):
    t = load_footprint(fpid)
    out = []
    for p in findall(t, 'pad'):
        at = find(p, 'at')
        out.append(dict(num=p[1], type=str(p[2]), shape=str(p[3]), x=float(at[1]), y=float(at[2]),
                        rot=float(at[3]) if len(at) > 3 else 0.0,
                        w=float(find(p, 'size')[1]), h=float(find(p, 'size')[2])))
    return out
