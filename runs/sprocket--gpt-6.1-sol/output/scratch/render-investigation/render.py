import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BOARD = HERE / os.environ.get('RENDER_BOARD', 'sprocket2350.kicad_pcb')
STOCK = Path(os.environ['SPROCKET_KICAD_LIBRARIES']) / '3dmodels'
OVERLAY = HERE / 'models'
local_lib = BOARD.parent / 'lib'
if not local_lib.exists():
    local_lib.symlink_to(ROOT / 'lib', target_is_directory=True)

references = sorted(set(re.findall(
    r'\(model "\$\{KICAD10_3DMODEL_DIR\}/([^"\n]+)"', BOARD.read_text())))
for relative in references:
    installed = STOCK / relative
    selected = installed if installed.is_file() else ROOT / 'lib/3d' / relative
    if selected.is_file():
        target = OVERLAY / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.symlink_to(selected)
    else:
        print(f'Missing model: {relative}', flush=True)

env = dict(os.environ, KICAD_CONFIG_HOME=str(HERE / os.environ.get('RENDER_CONFIG', 'config')),
           KICAD10_3DMODEL_DIR=str(OVERLAY))
subprocess.run([
    'kicad-cli', 'pcb', 'render', '--width', '1400', '--height', '1100',
    '--quality', os.environ.get('RENDER_QUALITY', 'user'),
    '--preset', os.environ.get('RENDER_PRESET', 'follow_plot_settings'),
    *sys.argv[1:], str(BOARD),
], env=env, check=True)
