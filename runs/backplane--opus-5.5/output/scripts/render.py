"""Render board layers to a composite PNG for quick visual review."""
import sys, os, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
K = '/home/ubuntu/pcbbench-hub/bin/kicad-cli'
def strip_pours(pcb):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from sexp import parse, dumps, find
    t = parse(open(pcb).read())
    keep = [t[0]]
    for e in t[1:]:
        if isinstance(e, list) and e and e[0] == 'zone':
            nm = find(e, 'name')
            if nm and nm[1] in ('GND_F', 'GND_B', 'GND_In1', '3V3_In2'):
                continue
        keep.append(e)
    d = tempfile.mkdtemp()
    p = os.path.join(d, os.path.basename(pcb))
    open(p, 'w').write(dumps(keep))
    return p


def render(pcb, out, layers, box=None, dpi=400, scale_out=1.0, grid=True, nopour=False):
    if nopour:
        pcb = strip_pours(pcb)
    tmp = tempfile.mkdtemp()
    names = [l for l, c in layers]
    subprocess.run([K, 'pcb', 'export', 'png', '-o', tmp + '/', '--layers', ','.join(names), '--dpi', str(dpi),
                    '--drill-shape-opt', '1', pcb], check=True, capture_output=True)
    s = dpi / 25.4
    x0, y0, x1, y1 = box or (98, 98, 182, 138)
    bx = (int(x0 * s), int(y0 * s), int(x1 * s), int(y1 * s))
    W, H = bx[2] - bx[0], bx[3] - bx[1]
    o = np.zeros((H, W, 3), dtype=float) + 20
    base = os.path.splitext(os.path.basename(pcb))[0]
    for l, (col, al) in layers:
        alias = {'F.CrtYd': 'F_Courtyard', 'B.CrtYd': 'B_Courtyard', 'F.SilkS': 'F_Silkscreen', 'B.SilkS': 'B_Silkscreen'}
        f = os.path.join(tmp, '%s-%s.png' % (base, alias.get(l, l.replace('.', '_'))))
        if not os.path.exists(f):
            print('missing', f); continue
        a = np.array(Image.open(f).convert('RGBA').crop(bx)).astype(float)
        m = a[:, :, 3] > 0
        o[m] = o[m] * (1 - al) + np.array(col) * al
    im = Image.fromarray(o.astype('uint8'))
    if grid:
        d = ImageDraw.Draw(im)
        for mm in range(int(x0), int(x1) + 1):
            if (mm - 100) % 5 == 0:
                x = (mm - x0) * s
                d.line([(x, 0), (x, 6)], fill=(255, 255, 255)); d.text((x + 1, 6), str(mm - 100), fill=(255, 255, 255))
        for mm in range(int(y0), int(y1) + 1):
            if (mm - 100) % 5 == 0:
                y = (mm - y0) * s
                d.line([(0, y), (6, y)], fill=(255, 255, 255)); d.text((7, y), str(mm - 100), fill=(255, 255, 255))
    if scale_out != 1.0:
        im = im.resize((int(W * scale_out), int(H * scale_out)), Image.LANCZOS)
    im.save(out)
    return out
if __name__ == '__main__':
    pcb = sys.argv[1]; out = sys.argv[2]; mode = sys.argv[3] if len(sys.argv) > 3 else 'place'
    box = tuple(float(v) for v in sys.argv[4].split(',')) if len(sys.argv) > 4 else None
    dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 300
    if mode == 'place':
        L = [('B.CrtYd', ((80, 80, 200), 0.6)), ('F.Cu', ((200, 60, 60), 0.8)), ('F.CrtYd', ((230, 230, 230), 1.0)),
             ('F.Fab', ((240, 200, 60), 1.0)), ('Edge.Cuts', ((60, 220, 60), 1.0))]
    elif mode == 'copper':
        L = [('B.Cu', ((60, 100, 230), 0.6)), ('F.Cu', ((220, 60, 60), 0.6)), ('Edge.Cuts', ((60, 220, 60), 1.0))]
    elif mode == 'top':
        L = [('F.Cu', ((220, 60, 60), 0.85)), ('F.SilkS', ((240, 240, 240), 1.0)), ('Edge.Cuts', ((60, 220, 60), 1.0))]
    elif mode == 'bottom':
        L = [('B.Cu', ((60, 100, 230), 0.85)), ('B.SilkS', ((240, 240, 240), 1.0)), ('Edge.Cuts', ((60, 220, 60), 1.0))]
    elif mode in ('In1', 'In2'):
        L = [(mode + '.Cu', ((200, 160, 60), 0.85)), ('Edge.Cuts', ((60, 220, 60), 1.0))]
    render(pcb, out, L, box, dpi, nopour=('np' in sys.argv[6:]))
