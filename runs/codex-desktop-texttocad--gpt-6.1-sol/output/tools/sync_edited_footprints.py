from copy import deepcopy
from pathlib import Path
import sexpdata as sx

ROOT = Path(__file__).resolve().parents[1]
def tag(node):
    return str(node[0]) if isinstance(node, list) and node else ''
board = sx.load(open(ROOT / 'Atlas2350.kicad_pcb'))
for footprint in board:
    if tag(footprint) != 'footprint':
        continue
    ref = next((node[2] for node in footprint if tag(node) == 'property' and node[1] == 'Reference'), '')
    if ref not in {'U6', 'J3', 'J6'}:
        continue
    definition = deepcopy(footprint)
    name = definition[1].split(':')[-1]
    definition[1] = name
    definition = [node for node in definition if tag(node) not in {'transform', 'uuid', 'path', 'sheetname', 'sheetfile'}]
    definition.insert(2, [sx.Symbol('version'), 20261031])
    definition.insert(3, [sx.Symbol('generator'), 'pcbnew'])
    for node in definition:
        if tag(node) == 'property' and node[1] == 'Reference':
            node[2] = 'REF**'
        if tag(node) == 'property' and node[1] == 'Value':
            node[2] = name
        if tag(node) == 'pad':
            node[:] = [item for item in node if tag(item) not in {'net', 'pinfunction', 'pintype'}]
    output = ROOT / 'libraries' / 'Atlas.pretty' / (name + '.kicad_mod')
    output.write_text(sx.dumps(definition) + '\n')
    print(f'Synchronized intentional board edits in {output.name}')
