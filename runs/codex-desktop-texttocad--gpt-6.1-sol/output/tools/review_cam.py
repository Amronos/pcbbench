from pathlib import Path
from datetime import datetime, timezone
import csv
import hashlib
import json
import shutil
import warnings
from gerbonara import GerberFile, ExcellonFile
from gerbonara.layers import LayerStack

ROOT = Path(__file__).resolve().parents[1]
FAB = ROOT / 'fab'
verification = json.loads((ROOT / 'checks/verification.json').read_text())
parsed = []
captured = []
with warnings.catch_warnings(record=True) as notices:
    warnings.simplefilter('always')
    for path in sorted((FAB / 'gerbers').glob('*.gbr')):
        image = GerberFile.open(path)
        parsed.append({'file': str(path.relative_to(FAB)), 'objects': len(image.objects),
                       'bounds_mm': image.bounding_box(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    plated = ExcellonFile.open(FAB / 'drill/Atlas2350-PTH.drl')
    unplated = ExcellonFile.open(FAB / 'drill/Atlas2350-NPTH.drl')
    with (FAB / 'drill/filled-capped-hole-schedule.csv').open() as schedule:
        fill = list(csv.DictReader(schedule))
    missing = []
    for hole in fill:
        x, y, diameter = float(hole['x_mm']), -float(hole['y_mm']), float(hole['finished_hole_mm'])
        if not any(abs(getattr(item, 'x', 1e9) - x) <= 0.00051 and
                   abs(getattr(item, 'y', 1e9) - y) <= 0.00051 and
                   abs(item.aperture.diameter - diameter) < 0.00001 for item in plated.objects):
            missing.append(hole)
    staging = ROOT / 'checks/cam'
    staging.mkdir(exist_ok=True)
    for path in list((FAB / 'gerbers').glob('*.gbr')) + list((FAB / 'drill').glob('*.drl')):
        shutil.copy2(path, staging / path.name)
    stack = LayerStack.open(staging)
    for side in ['top', 'bottom']:
        (ROOT / f'checks/cam-{side}-drill.svg').write_text(str(stack.to_pretty_svg(side=side, margin=2)))
    captured = sorted({str(item.message) for item in notices})
expected_plated = verification['routing_vias'] + 12 + 40
errors = []
if len(parsed) != 10:
    errors.append('Expected ten Gerber layers')
if len(plated.objects) != expected_plated or len(unplated.objects) != 7:
    errors.append('Unexpected drill object counts')
if missing:
    errors.append('Fill/cap schedule holes do not match plated drill data')
result = {'reviewed_utc': datetime.now(timezone.utc).isoformat(),
          'status': 'PASS' if not errors else 'FAIL', 'errors': errors,
          'gerbers': parsed, 'plated_drill_objects': len(plated.objects),
          'nonplated_drill_objects': len(unplated.objects),
          'fill_cap_registration_matches': len(fill) - len(missing),
          'drill_coordinate_tolerance_mm': 0.00051,
          'parser_notices': captured,
          'notice_disposition': 'KiCad aperture macro unused-parameter notices and Excellon G90 header ordering are accepted by the parser; bottom paste is absent because all assembled parts are top-side. Gerber job is metadata, not a plotted layer.',
          'limits': 'CAM parsing and registration checks do not establish electrical performance, impedance, supplier DFM approval or physical first-article acceptance.'}
(ROOT / 'checks/cam-review.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
if errors:
    raise SystemExit(1)
