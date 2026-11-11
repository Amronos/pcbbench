import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
models = sorted(set(re.findall(
    r'\(model "\$\{KIPRJMOD\}/lib/3d/([^"\n]+)"',
    (HERE / 'sprocket2350.kicad_pcb').read_text())))
index = int(sys.argv[1])
case = HERE / f'case-{index}'
case.mkdir(exist_ok=True)
for suffix in ('kicad_pcb', 'kicad_pro'):
    target = case / f'sprocket2350.{suffix}'
    if not target.exists():
        target.symlink_to(HERE / target.name)
selected = models if index == 7 else ([] if index == 0 else [models[index - 1]])
for relative in selected:
    target = case / 'lib/3d' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.symlink_to(ROOT / 'lib/3d' / relative)
print(f'Case {index}: {selected}', flush=True)
env = dict(os.environ,
           KICAD_CONFIG_HOME=str(ROOT / 'scratch/render-investigation/config-exact'),
           KICAD10_3DMODEL_DIR=str(ROOT / 'scratch/render-investigation/models'))
subprocess.run(['kicad-cli', 'pcb', 'render', '--width', '1100', '--height', '900',
                '--quality', 'user', '--preset', 'follow_plot_settings',
                '--background', 'opaque', '--rotate', '325,0,25', '--zoom', '0.9',
                '-o', str(HERE / f'case-{index}.png'),
                str(case / 'sprocket2350.kicad_pcb')], env=env, check=True)
