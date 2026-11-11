"""Net classes, written to the .kicad_pro JSON because kipy's project API fails in headless mode
("the requested project is not open"). Run with no KiCad session holding the project."""
import json
from pcblib import ROOT

path = f'{ROOT}/rp2350-devboard.kicad_pro'
pro = json.load(open(path))
ns = pro['net_settings']
default = next(c for c in ns['classes'] if c['name'] == 'Default')
default.update(clearance=0.15, track_width=0.15, via_diameter=0.55, via_drill=0.25, diff_pair_width=0.22, diff_pair_gap=0.15)
power = dict(default, name='Power', track_width=0.3, priority=0)
usb = dict(default, name='USB', track_width=0.22, priority=1)
ns['classes'] = [default, power, usb]
ns['netclass_patterns'] = [{'netclass': c, 'pattern': p} for p, c in (
    ('GND', 'Power'), ('+3V3', 'Power'), ('VBUS', 'Power'), ('+BATT', 'Power'), ('/VSYS', 'Power'), ('+1V1', 'Power'),
    ('/USB_*', 'USB'))]
json.dump(pro, open(path, 'w'), indent=2)
print('net classes written')
