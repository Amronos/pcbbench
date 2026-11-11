#!/usr/bin/env python3
"""render board layers to PNG for inspection: render.py out.png [layers] [x0 y0 x1 y1] [dpi]"""
import sys, os, subprocess, glob
sys.path.append('/home/ubuntu/.local/lib/python3.12/site-packages')
import pymupdf
import design as D
K = '/home/ubuntu/pcbbench-hub/bin/kicad-cli'
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
pcb = os.path.join(ROOT, 'boards', D.NAME, D.NAME + '.kicad_pcb')
out = sys.argv[1]
layers = sys.argv[2] if len(sys.argv) > 2 else 'F.Cu,F.Fab,Edge.Cuts,F.CrtYd'
box = [float(v) for v in sys.argv[3:7]] if len(sys.argv) > 6 else [-1, -1, D.W + 1, D.H + 1]
dpi = int(sys.argv[7]) if len(sys.argv) > 7 else 500
svg = '/tmp/render_tmp.svg'
subprocess.run([K, 'pcb', 'export', 'svg', '--layers', layers, '--mode-single', '--page-size-mode', '0',
                '--exclude-drawing-sheet', '-o', svg, pcb], check=True, capture_output=True)
d = pymupdf.open(svg); pg = d[0]
s = 72 / 25.4
clip = pymupdf.Rect((D.OX + box[0]) * s, (D.OY + box[1]) * s, (D.OX + box[2]) * s, (D.OY + box[3]) * s)
pg.get_pixmap(dpi=dpi, clip=clip).save(out)
print(out)
