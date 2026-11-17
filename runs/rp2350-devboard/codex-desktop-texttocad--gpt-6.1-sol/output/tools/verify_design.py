from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from cad import kicad_pcb

ROOT = Path(__file__).resolve().parents[1]
design = json.loads((ROOT / 'design.json').read_text())
board = kicad_pcb.read(ROOT / 'Atlas2350.kicad_pcb')
xml = ET.parse(ROOT / 'checks/Atlas2350-final.xml')
schematic_nets = {(node.attrib['ref'], node.attrib['pin']): net.attrib['name']
                  for net in xml.findall('./nets/net') for node in net.findall('node')}
pcb = {part.ref: part for part in board.parts}
errors = []
checked_pins = 0
for part in design:
    for number, expected in part['nets'].items():
        checked_pins += 1
        actual = schematic_nets.get((part['ref'], number))
        if expected is not None and actual != expected:
            errors.append(f'Schematic {part["ref"]}.{number}: {actual} != {expected}')
        if expected is None and actual is not None and not actual.startswith('unconnected-'):
            errors.append(f'Schematic NC connected: {part["ref"]}.{number}')
        pads = [pad for pad in pcb[part['ref']].pads if pad.number == number]
        if not pads:
            errors.append(f'Missing physical pad: {part["ref"]}.{number}')
        for pad in pads:
            if expected is not None and pad.net != expected:
                errors.append(f'PCB {part["ref"]}.{number}: {pad.net} != {expected}')
            if expected is None and pad.net and not pad.net.startswith('unconnected-'):
                errors.append(f'PCB NC connected: {part["ref"]}.{number}')
real = [part for part in design if not part['ref'].startswith(('TP', 'H'))]
for part in real:
    if pcb[part['ref']].side != 'top' or pcb[part['ref']].dnp or not pcb[part['ref']].in_bom:
        errors.append(f'Assembly population/side: {part["ref"]}')
reports = {}
for name in ['erc', 'drc']:
    report = json.loads((ROOT / f'checks/{name}-final.json').read_text())
    reports[name] = dict(Counter(finding['severity'] for finding in report['findings']))
    if report['findings']:
        errors.append(f'{name.upper()} not clean: {len(report["findings"])} findings')
project = json.loads((ROOT / 'Atlas2350.kicad_pro').read_text())
for key, excluded in [('DRC', project['board']['design_settings'].get('drc_exclusions', [])),
                      ('ERC', project.get('erc', {}).get('erc_exclusions', []))]:
    if excluded:
        errors.append(f'{key} contains excluded findings')
totals = Counter()
via_totals = Counter(via.net for via in board.vias)
for track in board.tracks:
    totals[track.net] += track.length
fast_nets = ['QSPI_CLK_SRC', 'QSPI_CLK', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2', 'QSPI_IO3', 'FLASH_CS', 'PSRAM_CS',
             'USB_D+', 'USB_D-', 'USB_PHY_D+', 'USB_PHY_D-', 'XIN', 'XOUT', 'XTAL_OUT']
layers = {name: sorted({track.layer for track in board.tracks if track.net == name}) for name in fast_nets}
for name in fast_nets:
    if any(layer not in {'F.Cu', 'B.Cu'} for layer in layers[name]):
        errors.append(f'Fast net leaves planned outer layers: {name}')
via_rows = [{'feature': 'routing_via', 'reference': '', 'pad': '', 'net': via.net,
             'x_mm': f'{via.at[0]:.6f}', 'y_mm': f'{via.at[1]:.6f}', 'finished_hole_mm': f'{via.drill:.3f}',
             'process': 'IPC4761 TypeVII resin filled and copper capped; no open holes'} for via in board.vias]
for pad in pcb['U6'].pads:
    if pad.number == '19' and pad.drill:
        via_rows.append({'feature': 'module_thermal_PTH', 'reference': 'U6', 'pad': '19', 'net': pad.net,
                         'x_mm': f'{pad.at[0]:.6f}', 'y_mm': f'{pad.at[1]:.6f}', 'finished_hole_mm': f'{pad.drill:.3f}',
                         'process': 'IPC4761 TypeVII resin filled and copper capped; not a component lead hole'})
output = ROOT / 'fab/drill'
output.mkdir(parents=True, exist_ok=True)
with (output / 'filled-capped-hole-schedule.csv').open('w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=list(via_rows[0]))
    writer.writeheader()
    writer.writerows(via_rows)
result = {
    'verified_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'PASS' if not errors else 'FAIL', 'errors': errors,
    'schematic_pin_assignments_checked': checked_pins, 'pcb_footprints': len(board.parts),
    'assembled_components': len(real), 'bare_features_excluded': len(design) - len(real),
    'tracks': len(board.tracks), 'routing_vias': len(board.vias),
    'fill_cap_holes_total': len(via_rows), 'reports': reports,
    'fast_net_copper_length_totals_mm_not_point_to_point': {name: round(totals[name], 3) for name in fast_nets},
    'fast_net_vias': {name: via_totals[name] for name in fast_nets}, 'fast_net_layers': layers,
    'signal_layer_track_counts': dict(Counter(track.layer for track in board.tracks)),
    'unperformed': ['physical prototype tests', 'PCBWay quote/DFM approval', 'USB compliance testing',
                    'RF certification', 'controlled-impedance simulation or measurement', 'first-article signal-integrity qualification'],
    'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                      for name in ['Atlas2350.kicad_pcb', 'Atlas2350.kicad_pro', 'Atlas2350.kicad_sch', 'design.json']},
}
(ROOT / 'checks/verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
if errors:
    raise SystemExit(1)
