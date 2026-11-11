import json
import os
from pathlib import Path
import sys

from shapely.geometry import LineString, Point, box
from shapely.affinity import rotate

sys.path.insert(0, os.environ['SPROCKET_KICAD_ROUTING_TOOLS'] + '/py_router')
from kicad_parser import parse_kicad_pcb

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'scratch/core-repaired.kicad_pcb')
manifest = json.loads(path.with_suffix('.changes.json').read_text())
moved_refs = set(manifest['moves'])
board = parse_kicad_pcb(str(path))
original = parse_kicad_pcb(manifest['source'])
old = {t.uuid for t in original.segments} | {v.uuid for v in original.vias}
copper_layers = {'F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'}
clearance_mm = .1269
objects = []
for track in board.segments:
    objects.append((track.net_id, {track.layer},
                    LineString([(track.start_x, track.start_y),
                                (track.end_x, track.end_y)]).buffer(track.width / 2),
                    track.uuid not in old, f'track {track.start_x},{track.start_y}'))
for via in board.vias:
    objects.append((via.net_id, copper_layers, Point(via.x, via.y).buffer(via.size / 2),
                    via.uuid not in old, f'via {via.x},{via.y}'))
for ref, footprint in board.footprints.items():
    for pad in footprint.pads:
        if not pad.net_id:
            continue
        copper = box(pad.global_x - pad.size_x / 2, pad.global_y - pad.size_y / 2,
                     pad.global_x + pad.size_x / 2, pad.global_y + pad.size_y / 2)
        copper = rotate(copper, pad.rect_rotation, origin=(pad.global_x, pad.global_y))
        layers = set(pad.layers)
        if '*.Cu' in layers:
            layers |= copper_layers
        objects.append((pad.net_id, layers, copper, ref in moved_refs, f'{ref}.{pad.pad_number}'))
findings = []
for index, (net_a, layers_a, shape_a, changed_a, label_a) in enumerate(objects):
    for net_b, layers_b, shape_b, changed_b, label_b in objects[index + 1:]:
        if not (changed_a or changed_b) or net_a == net_b or not layers_a & layers_b:
            continue
        distance = shape_a.distance(shape_b)
        if distance < clearance_mm:
            findings.append({'a': label_a, 'b': label_b, 'distance_mm': round(distance, 5)})
print(json.dumps(findings, indent=2))
print('Local conservative copper geometry findings:', len(findings))
