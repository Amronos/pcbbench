from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import shutil
import zipfile
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
FAB = ROOT / 'fab'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


verification = json.loads((ROOT / 'checks/verification.json').read_text())
cam = json.loads((ROOT / 'checks/cam-review.json').read_text())
assert verification['status'] == cam['status'] == 'PASS'
for filename, expected in verification['source_sha256'].items():
    assert digest(ROOT / filename) == expected, filename
for name in ['erc', 'drc']:
    assert not json.loads((ROOT / f'checks/{name}-final.json').read_text())['findings']
bom = rows(FAB / 'assembly/bom.csv')
assert len(bom) == 53 and sum(int(row['quantity']) for row in bom) == 115
assert len(rows(FAB / 'assembly/pcbway-centroids.csv')) == 112
assert len(rows(FAB / 'assembly/parts.csv')) == 115
assert len(rows(FAB / 'assembly/centroid-source.csv')) == 115
assembly = json.loads((FAB / 'assembly/manifest.json').read_text())
assert assembly['board_sha256'] == digest(ROOT / 'Atlas2350.kicad_pcb')
assert assembly['design_sha256'] == digest(ROOT / 'design.json')
for gerber in cam['gerbers']:
    assert digest(FAB / gerber['file']) == gerber['sha256']
for name in ['fabrication-notes', 'assembly-notes', 'test-plan']:
    shutil.copy2(ROOT / f'docs/{name}.md', FAB / f'{name}.md')
for name in ['verification.json', 'erc-final.json', 'drc-final.json', 'cam-review.json']:
    shutil.copy2(ROOT / f'checks/{name}', FAB / name)
pdf_pages = {}
for path in sorted(FAB.rglob('*.pdf')):
    with pymupdf.open(path) as document:
        assert len(document) > 0, path
        pdf_pages[str(path.relative_to(FAB))] = len(document)
assert pdf_pages['schematic.pdf'] == 6
assert pdf_pages['assembly/assembly-orientation.pdf'] == 4
assert pdf_pages['fabrication-and-assembly.pdf'] == 1
files = [path for path in sorted(FAB.rglob('*')) if path.is_file() and
         path not in {FAB / 'manifest.json', FAB / 'SHA256SUMS.txt'} and path.suffix != '.zip']
assert all(path.stat().st_size > 0 for path in files)
source_files = sorted(list(ROOT.glob('*.kicad_*')) +
                      [ROOT / 'sym-lib-table', ROOT / 'fp-lib-table', ROOT / 'design.json'] +
                      list((ROOT / 'libraries').rglob('*.kicad_sym')) +
                      list((ROOT / 'libraries').rglob('*.kicad_mod')))
source_files = [path for path in source_files if path.suffix != '.kicad_prl']
manifest = {'release': 'Atlas2350 Rev A', 'packaged_utc': datetime.now(timezone.utc).isoformat(),
            'status': 'Prototype manufacturing and complete-population assembly package; supplier quote/DFM and physical qualification pending',
            'assembled_components_per_board': 115, 'bom_groups': 53, 'surface_centroids': 112,
            'schematic_pin_assignments_checked': 432, 'erc_findings': 0, 'drc_findings': 0,
            'native_pcb_format': '20261031; compatible KiCad11 development/nightly required',
            'pdf_pages': pdf_pages,
            'source_sha256': {str(path.relative_to(ROOT)): digest(path) for path in source_files},
            'files': {str(path.relative_to(FAB)): {'bytes': path.stat().st_size, 'sha256': digest(path)} for path in files}}
(FAB / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
checksummed = files + [FAB / 'manifest.json']
(FAB / 'SHA256SUMS.txt').write_text(''.join(f'{digest(path)}  {path.relative_to(FAB)}\n' for path in sorted(checksummed)))
upload = FAB / 'Atlas2350-PCBWay.zip'
with zipfile.ZipFile(upload, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(FAB.rglob('*')):
        if path.is_file() and path.suffix != '.zip':
            archive.write(path, str(path.relative_to(FAB)))
with zipfile.ZipFile(upload) as archive:
    assert archive.testzip() is None
project_files = source_files + [ROOT / 'README.md', ROOT / 'research.md'] + list((ROOT / 'docs').glob('*.md')) + list((ROOT / 'tools').glob('*.py'))
project_files += [path for path in FAB.rglob('*') if path.is_file() and path.suffix != '.zip']
project_files += [ROOT / f'checks/{name}' for name in ['verification.json', 'erc-final.json', 'drc-final.json', 'cam-review.json', 'Atlas2350-final.xml', 'final-top.png', 'cam-final-top.png']]
project_zip = ROOT / 'Atlas2350-project.zip'
with zipfile.ZipFile(project_zip, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(set(project_files)):
        archive.write(path, str(path.relative_to(ROOT)))
with zipfile.ZipFile(project_zip) as archive:
    assert archive.testzip() is None
report = {'status': 'PASS', 'upload_zip': str(upload), 'upload_sha256': digest(upload),
          'project_zip': str(project_zip), 'project_sha256': digest(project_zip),
          'manufacturing_files': len(checksummed) + 1, 'pdf_pages': pdf_pages}
(ROOT / 'checks/release-package.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
