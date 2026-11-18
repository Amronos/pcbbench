from pathlib import Path
import sexpdata as sx

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'Atlas2350.kicad_pcb'
board = sx.load(source.open())
def tag(node):
    return str(node[0]) if isinstance(node, list) and node else ''
setup = next(node for node in board if tag(node) == 'setup')
setup[:] = [node for node in setup if tag(node) != 'stackup']
stackup = sx.loads('''(stackup
    (layer "F.SilkS" (type "Top Silk Screen"))
    (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01) (color "Green"))
    (layer "F.Cu" (type "copper") (thickness 0.035))
    (layer "dielectric 1" (type "prepreg") (thickness 0.12) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
    (layer "In1.Cu" (type "copper") (thickness 0.0175))
    (layer "dielectric 2" (type "core") (thickness 1.255) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
    (layer "In2.Cu" (type "copper") (thickness 0.0175))
    (layer "dielectric 3" (type "prepreg") (thickness 0.12) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
    (layer "B.Cu" (type "copper") (thickness 0.035))
    (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01) (color "Green"))
    (layer "B.SilkS" (type "Bottom Silk Screen"))
    (copper_finish "ENIG") (dielectric_constraints no))''')
setup.insert(1, stackup)
board[:] = [node for node in board if tag(node) != 'title_block']
board.insert(5, sx.loads('(title_block (title "Atlas2350 connected LiPo development board") (date "2026-11-10") (rev "A") (company "Atlas2350"))'))
temporary = source.with_suffix('.tmp')
temporary.write_text(sx.dumps(board) + '\n')
sx.load(temporary.open())
temporary.replace(source)
print('Set ENIG, outer35um/inner17.5um copper and nominal 0.12/1.255/0.12mm dielectrics')
