import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
board_dir = HERE / os.environ.get('RENDER_CASE', 'fixed')
local_lib = board_dir / 'lib'
if not local_lib.exists():
    local_lib.symlink_to(ROOT / 'lib', target_is_directory=True)
env = dict(os.environ,
           KICAD_CONFIG_HOME=os.environ.get('RENDER_CONFIG_HOME',
               str(ROOT / 'scratch/render-investigation/config-exact')),
           KICAD10_3DMODEL_DIR=str(ROOT / 'scratch/render-investigation/models'))
subprocess.run(['kicad-cli', 'pcb', 'render', '--width', '1400', '--height', '1100',
                '--quality', os.environ.get('RENDER_QUALITY', 'user'),
                '--preset', 'follow_plot_settings',
                '--background', 'opaque', '--zoom', '0.9', *sys.argv[1:],
                str(board_dir / 'sprocket2350.kicad_pcb')], env=env, check=True)
