"""Extract footprints from the Raspberry Pi RP2350A minimal design (MIT) into the project library."""
import os, sys
from sexp import parse, dumps, find, findall, Sym
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'third_party', 'RPi-RP2350A-Minimal', 'RPI-RP2350A-MINIMAL_R4-S1.kicad_pcb')
OUT = os.path.join(HERE, '..', 'boards', 'rp2350-dev', 'lib', 'RP2350_Dev.pretty')

PICK = {  # their ref -> our footprint name
    'U1': 'RP2350A_QFN60_RPi',
    'C14': 'C_0402_RPi',
    'C6': 'C_0402_RPi_Wide',
    'R10': 'R_0402_RPi',
    'L1': 'L_Abracon_AOTA-B201610',
    'X1': 'Crystal_3225_RPi',
    'U3': 'SOIC-8_5.3mm_RPi',
}

def ref_of(fp):
    for p in findall(fp, 'property'):
        if p[1] == 'Reference':
            return p[2]

def main():
    t = parse(open(SRC).read())
    for fp in findall(t, 'footprint'):
        r = ref_of(fp)
        if r not in PICK:
            continue
        at = find(fp, 'at')
        assert len(at) < 4 or float(at[3]) == 0, r
        name = PICK[r]
        out = [Sym('footprint'), name, [Sym('version'), Sym('20260206')], [Sym('generator'), 'rp2350dev_extract']]
        for e in fp[2:]:
            if isinstance(e, list) and e and e[0] in ('at', 'path', 'sheetname', 'sheetfile', 'uuid', 'locked'):
                continue
            if isinstance(e, list) and e and e[0] == 'pad':
                e = [x for x in e if not (isinstance(x, list) and x and x[0] in ('net', 'uuid'))]
            if isinstance(e, list) and e and e[0] == 'property':
                if e[1] == 'Reference':
                    e[2] = 'REF**'
                elif e[1] == 'Value':
                    e[2] = name
            out.append(e)
        # embed the referenced 3D model(s) from the board-level embedded files
        emb = find(t, 'embedded_files')
        files = {find(f, 'name')[1]: f for f in findall(emb, 'file')} if emb else {}
        need = []
        for m in findall(out, 'model'):
            if m[1].startswith('kicad-embed://'):
                need.append(m[1][len('kicad-embed://'):])
        if need:
            efs = [Sym('embedded_files')] + [files[n] for n in need if n in files]
            mi = next(i for i, e in enumerate(out) if isinstance(e, list) and e and e[0] == 'model')
            out.insert(mi, efs)
        # description
        out.insert(4, [Sym('descr'), 'From Raspberry Pi RP2350A Minimal design R4 (MIT licence), ref ' + r])
        open(os.path.join(OUT, name + '.kicad_mod'), 'w').write(dumps(out) + '\n')
        print('wrote', name)

if __name__ == '__main__':
    main()
