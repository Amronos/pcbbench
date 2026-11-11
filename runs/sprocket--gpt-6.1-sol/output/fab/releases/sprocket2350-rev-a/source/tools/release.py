import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
NAME = 'sprocket2350'
SOURCE_FILES = (
    f'{NAME}.kicad_pcb', f'{NAME}.kicad_sch', f'{NAME}.kicad_pro', f'{NAME}.net',
    'fp-lib-table', 'sym-lib-table', 'README.md',
    'fab/FABRICATION.md', 'fab/ASSEMBLY.md',
)
LIB_SUFFIXES = {'.kicad_sym', '.kicad_mod', '.md', '.txt', '.json'}
MODEL_SUFFIXES = {'.step', '.stp', '.wrl'}


def run(*args, cwd, env=None):
    subprocess.run([str(arg) for arg in args], cwd=cwd, env=env, check=True)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot_sources(destination):
    files = [ROOT / name for name in SOURCE_FILES]
    files += sorted(ROOT.glob('*.kicad_dru'))
    files += sorted((ROOT / 'tools').glob('*.py'))
    files += sorted(path for path in (ROOT / 'lib').rglob('*')
                    if path.is_file() and (path.suffix.lower() in LIB_SUFFIXES | MODEL_SUFFIXES
                                          or path.name.upper().startswith(('LICENSE', 'COPYING'))))
    hashes = {}
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f'Source must be a local regular file: {path}')
        relative = path.relative_to(ROOT)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        if path.suffix.lower() not in MODEL_SUFFIXES:
            hashes[str(relative)] = digest(target)
    return hashes


def check_design(source, output):
    checks = output / 'checks'
    checks.mkdir()
    for kind, command, filename in [('sch', 'erc', 'ERC.json'), ('pcb', 'drc', 'DRC.json')]:
        parity = ['--schematic-parity', '--refill-zones', '--save-board'] if kind == 'pcb' else []
        extension = 'kicad_sch' if kind == 'sch' else 'kicad_pcb'
        run('kicad-cli', kind, command, *parity, '--severity-all', '--format', 'json',
            '-o', checks / filename, source / f'{NAME}.{extension}', cwd=source)
    erc = json.loads((checks / 'ERC.json').read_text())
    drc = json.loads((checks / 'DRC.json').read_text())
    findings = sum(len(sheet['violations']) for sheet in erc['sheets'])
    findings += sum(len(drc[key]) for key in ('violations', 'unconnected_items', 'schematic_parity'))
    if findings:
        raise ValueError(f'Release blocked: {findings} ERC/DRC findings, including exclusions')


def export_manufacturing(source, output):
    board = source / f'{NAME}.kicad_pcb'
    schematic = source / f'{NAME}.kicad_sch'
    for directory in ('gerbers', 'drills', 'assembly'):
        (output / directory).mkdir()
    run('kicad-python', source / 'tools/export_package.py', '--status', 'FIRST_ARTICLE',
        '--board', board, '--output', output / 'assembly', cwd=source)
    run('kicad-python', source / 'tools/export_via_treatment.py',
        '--board', board, '--output', output / 'fabrication', cwd=source)
    audit = Path(os.environ['SPROCKET_KICAD_ROUTING_TOOLS']) / 'py_tools/check_impedance.py'
    run('kicad-python', audit, board, '--nets', '/USB_D_P', '/USB_D_N',
        '/MCU_USB_P', '/MCU_USB_N', '--coplanar-gap', '0.3', '--exit-zero',
        '--json', output / 'checks/USB-diagnostic.json', cwd=source)
    run('kicad-cli', 'pcb', 'export', 'gerbers', '--layers',
        'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts',
        '--exclude-value', '--subtract-soldermask', '-o', str(output / 'gerbers') + '/', board,
        cwd=source)
    run('kicad-cli', 'pcb', 'export', 'drill', '--excellon-separate-th',
        '--excellon-oval-format', 'route', '--generate-map', '--generate-report',
        '--map-format', 'pdf', '--report-path', output / 'drills/drill-report.txt',
        '-o', str(output / 'drills') + '/', board, cwd=source)
    run('kicad-cli', 'pcb', 'export', 'ipcd356', '-o', output / f'{NAME}.d356', board, cwd=source)
    for side, layer in [('top', 'F.Fab'), ('bottom', 'B.Fab')]:
        mirror = ['--mirror'] if side == 'bottom' else []
        run('kicad-cli', 'pcb', 'export', 'pdf', '--layers', f'{layer},Edge.Cuts',
            '--sketch-pads-on-fab-layers', '--black-and-white', *mirror,
            '--mode-single', '-o', output / 'assembly' / f'{side}-assembly.pdf', board, cwd=source)
        with tempfile.TemporaryDirectory(prefix=f'.{side}-png-', dir=output) as temporary:
            sheet = Path(temporary) / 'empty.kicad_wks'
            sheet.write_text('(kicad_wks (version 20231120) (generator "pl_editor"))\n',
                             encoding='utf-8')
            run('kicad-cli', 'pcb', 'export', 'png', '--layers', layer,
                '--common-layers', 'Edge.Cuts', '--sketch-pads-on-fab-layers',
                '--black-and-white', '--drawing-sheet', sheet, '--dpi', '450', *mirror,
                '-o', temporary + '/', board, cwd=source)
            images = list(Path(temporary).glob('*.png'))
            if len(images) != 1:
                raise ValueError(f'Expected one {side} assembly PNG, got {len(images)}')
            with Image.open(images[0]) as image:
                image = image.convert('RGBA')
                bounds = image.getbbox()
                if bounds is None:
                    raise ValueError(f'Empty {side} assembly PNG')
                image = image.crop(bounds)
                background = Image.new('RGBA', image.size, 'white')
                background.alpha_composite(image)
                background.convert('RGB').save(output / 'assembly' / f'{side}-assembly.png')
    run('kicad-cli', 'sch', 'export', 'pdf', '-o', output / 'assembly/schematic.pdf', schematic,
        cwd=source)
    run('kicad-cli', 'pcb', 'export', 'stackup', '--format', 'json',
        '-o', output / 'stackup.json', board, cwd=source)
    with (output / 'assembly/placement.csv').open(encoding='utf-8', newline='') as stream:
        has_bottom = any(row['Side'] == 'Bottom' for row in csv.DictReader(stream))
    render_board(source, output, has_bottom)


def render_board(source, output, has_bottom):
    board = source / f'{NAME}.kicad_pcb'
    stock = os.environ.get('KICAD10_3DMODEL_DIR')
    if not stock and os.environ.get('SPROCKET_KICAD_LIBRARIES'):
        stock = str(Path(os.environ['SPROCKET_KICAD_LIBRARIES']) / '3dmodels')
    references = sorted(set(re.findall(
        r'\(model "\$\{KICAD10_3DMODEL_DIR\}/([^"\n]+)"', board.read_text())))
    models = []
    with tempfile.TemporaryDirectory(prefix='.render-models-', dir=output.parent) as temporary:
        overlay = Path(temporary)
        for relative in references:
            path = Path(relative)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError(f'Unsafe model path: {relative}')
            installed = Path(stock) / path if stock else None
            local = source / 'lib/3d' / path
            selected = installed if installed and installed.is_file() else local
            origin = 'installed' if selected == installed else 'local visualization substitute'
            if selected.is_file():
                target = overlay / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.symlink_to(selected.resolve())
            else:
                origin = 'missing'
            models.append({'reference': relative, 'source': origin})
        config = overlay / 'config'
        viewer = config / '10.99/3d_viewer.json'
        viewer.parent.mkdir(parents=True)
        viewer.write_text(json.dumps({
            'meta': {'version': 5},
            'current_layer_preset': 'legacy_preset_flag',
            'render': {
                'show_board_body': True,
                'show_copper_top': True, 'show_copper_bottom': True,
                'show_copper_inner1': False, 'show_copper_inner2': False,
                'show_zones': True,
                'show_soldermask_top': True, 'show_soldermask_bottom': True,
                'show_silkscreen_top': True, 'show_silkscreen_bottom': True,
                'raytrace_anti_aliasing': True, 'raytrace_shadows': True,
                'raytrace_reflections': False, 'raytrace_refractions': False,
                'raytrace_post_processing': True, 'raytrace_procedural_textures': False,
            },
        }), encoding='utf-8')
        env = dict(os.environ, KICAD10_3DMODEL_DIR=str(overlay), KICAD_CONFIG_HOME=str(config))
        views = [('top-3d.png', []), ('isometric.png', ['--rotate', '325,0,25'])]
        if has_bottom:
            views.append(('bottom-3d.png', ['--side', 'bottom']))
        for filename, view in views:
            run('kicad-cli', 'pcb', 'render', '--width', '1400', '--height', '1100',
                '--quality', 'user', '--preset', 'follow_plot_settings',
                '--background', 'opaque', '--zoom', '0.9', *view,
                '-o', output / 'assembly' / filename,
                board, cwd=source, env=env)
    (output / 'checks/render-models.json').write_text(json.dumps({
        'models': models,
        'limitations': 'Saved model transforms are unchanged during release. Local model '
                       'substitutes are visualization only. Renders are not mechanical validation.',
    }, indent=2) + '\n', encoding='utf-8')


def write_archive(output, source_files):
    source = output / 'source'
    files = sorted([source / relative for relative in source_files] +
                   [path for path in output.rglob('*')
                    if path.is_file() and not path.is_relative_to(source)])
    sums = output / 'SHA256SUMS'
    sums.write_text(''.join(f'{digest(path)}  {path.relative_to(output).as_posix()}\n'
                            for path in files), encoding='utf-8')
    archive_path = output / f'{NAME}-FIRST_ARTICLE.zip'
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in files + [sums]:
            archive.write(path, path.relative_to(output))


def main():
    parser = argparse.ArgumentParser(
        description='Generate an unapproved, physically untested FIRST_ARTICLE candidate. '
                    'Refills and saves only a staged PCB snapshot, then exports that checked board. '
                    'ERC/DRC success is not approval to manufacture.')
    parser.add_argument('--output', type=Path,
                        default=ROOT / 'fab/releases' / f'{NAME}-first-article',
                        help='New package directory. Existing destinations are never overwritten.')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        parser.error(f'Output already exists: {output}')
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / 'fab/releases'):
        parser.error('In-workspace releases must be under fab/releases, outside source directories.')
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix='.release-', dir=output.parent) as temporary:
            staging = Path(temporary) / 'package'
            source = staging / 'source'
            hashes = snapshot_sources(source)
            check_design(source, staging)
            checked_hashes = dict(hashes)
            checked_hashes[f'{NAME}.kicad_pcb'] = digest(source / f'{NAME}.kicad_pcb')
            export_manufacturing(source, staging)
            for relative, expected in hashes.items():
                if (digest(ROOT / relative) != expected
                        or digest(source / relative) != checked_hashes[relative]):
                    raise ValueError(f'Source changed during release: {relative}; retry on stable saved inputs')
            for path in source.rglob('*'):
                if path.is_file() and str(path.relative_to(source)) not in hashes:
                    path.unlink()
            (staging / 'release.json').write_text(json.dumps({
                'status': 'FIRST_ARTICLE',
                'physically_tested': False,
                'production_qualified': False,
                'approved_for_manufacture': False,
                'remaining_review': 'Resolve USB controlled impedance and supplier stackup, drill '
                                    'and Type VII process requirements before ordering. Test core '
                                    'power, ESD and other first-article behavior before production.',
                'checks': 'Zero reported ERC/DRC findings, including exclusions and schematic parity, '
                          'on the staged source snapshot after refilling and saving its PCB zones.',
                'placement_coordinates': 'Absolute KiCad footprint anchors in mm, +Y down; '
                                         'bottom coordinates not mirrored. Verify assembler rotations.',
                'assembly_views': 'Top and bottom assembly PDFs/PNGs include references. Bottom '
                                  'drawings are mirrored bottom views; placement coordinates are not.',
                'usb_diagnostic': 'checks/USB-diagnostic.json analyzes this checked snapshot. '
                                  'Reference-plane continuity and side-gap measurements do not '
                                  'verify 90 ohm impedance. Diagnostic findings do not gate candidates.',
                'input_source_sha256': hashes,
                'checked_source_sha256': checked_hashes,
                'source_omissions': 'Optional 3D model binaries are omitted because redistribution '
                                    'rights and package substitutions are unresolved. Model manifest, '
                                    'licenses and documentation are included. Install KiCad libraries '
                                    'and configure their paths separately.',
                'render_limitations': 'See checks/render-models.json for missing and local models. '
                                      'Saved model transforms are unchanged. Missing or substituted '
                                      'models are not mechanical validation.',
            }, indent=2) + '\n', encoding='utf-8')
            write_archive(staging, hashes)
            staging.rename(output)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f'Release failed; no new package published: {error}') from error
    print(f'FIRST_ARTICLE candidate: {output}. Not approved for manufacture; physically untested.')


if __name__ == '__main__':
    main()
