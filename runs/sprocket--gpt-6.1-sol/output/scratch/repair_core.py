import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from kipy import KiCad
from kipy.board_types import FootprintInstance, Track, Via
from kipy.geometry import Angle, Vector2
from kipy.proto.board import board_types_pb2 as bt
from kipy.proto.common.types.base_types_pb2 import DocumentType

sys.path.insert(0, os.environ['SPROCKET_KICAD_ROUTING_TOOLS'] + '/py_router')
from kicad_parser import parse_kicad_pcb

os.environ['KICAD10_FOOTPRINT_DIR'] = os.environ['SPROCKET_KICAD_LIBRARIES'] + '/footprints'
os.environ['KICAD10_SYMBOL_DIR'] = os.environ['SPROCKET_KICAD_LIBRARIES'] + '/symbols'

parser = argparse.ArgumentParser()
parser.add_argument('--source', default='scratch/clean.kicad_pcb')
parser.add_argument('--output', default='scratch/core-repaired.kicad_pcb')
parser.add_argument('--replace-own-copy', action='store_true')
args = parser.parse_args()
source, output = Path(args.source).resolve(), Path(args.output).resolve()
if source == output or (output.exists() and not args.replace_own_copy):
    raise SystemExit('Output must be a new board, distinct from source.')
subprocess.run([sys.executable, os.environ['SPROCKET_KICAD_ROUTING_TOOLS'] +
                '/py_router/copy_board.py', str(source), str(output)], check=True)

parsed = parse_kicad_pcb(str(source))
remove = set()
for track in parsed.segments:
    name = parsed.nets[track.net_id].name
    if name in {'/VREG_AVDD', '/VREG_LX'}:
        remove.add(track.uuid)
    if name == '/CORE_1V1' and min(track.start_x, track.end_x) >= 63.2:
        remove.add(track.uuid)
    if name == '/GND' and track.layer == 'F.Cu' and min(track.start_x, track.end_x) >= 64.4 and max(track.start_y, track.end_y) >= 53.5:
        remove.add(track.uuid)
remove.update({
    '2647a2d2-48ce-434a-b23e-86f105dcd83b',
    '70ef35ff-d874-41d1-8194-26a9c76a6446',
    'da50e127-4ebd-44f3-8d49-565d12cb366c',
    '1ffe2a86-4d6a-45ea-938c-176427c82d77',
    'bb7ee283-84fb-42df-82e9-5c350d20c41e',
    '7bb650b7-c5fb-430a-8aa9-446298f4c729',
    'fb7b1f0f-1570-4507-bb1f-68612d821d2f',
    'b6054768-efb3-4a16-97fd-2ceccdaec6a7',
    '79015407-8222-4b37-ba02-808bfd50317d',
    '547515e5-e02e-4b27-90dd-5c35cd7752aa',
    'dbfdb601-6d0e-4c02-b646-a49738ad2aa0',
    '4fb28cf7-5e21-4e57-b2d4-f8c302c46adc',
    '5ffaa099-e7f7-48d9-831f-a881cf8778cc',
    '157d51e8-310f-4d40-8d41-085229b36ccf',
    '62a2234c-3597-4491-9745-2a210106448c',
    '1e62065f-9562-404a-be21-767e9482a097',
    '3e87ccf3-c5bd-480f-815c-87e7f477ef70',
    '411b3e6d-c30f-4143-8858-e1a7e6d36482',
    'fca087f0-4c8a-4600-aa55-53829e65529d',
    'fda344a3-3e07-401a-a699-aadfc0dd79d7',
    '90b34d5a-bb8e-4152-acb7-d929b8535709',
    '93070135-046f-4575-b64b-aecb7d0ea423',
    '12e82001-460a-4380-af5d-1ff0bce2e3f0',
    'ed54cf0c-0515-4cb2-a1cb-a18e7af690de',
    '032cf1a4-7428-429c-a2ff-de72db44c8cf',
    '76cc77c6-fc09-44a1-85f2-77f900b91f09',
    '3eadf308-7ff4-42f1-b5da-60af0a44e5e8',
    'a6be7751-a555-4627-8daa-7eef1c352450',
    'a5b8167d-1bc3-4cf9-843c-33718fc5fd8c',
    'f8480f5f-5ba8-47ba-a166-7d70849c7419',
})

routes = [
    ('/VREG_AVDD', 'F.Cu', .127,
     [(57.8, 49.55), (57.8, 49.15), (58, 48.95), (58.8, 48.95),
      (59.7, 48.05), (60.2, 47.55), (60.2, 47.15)]),
    ('/VREG_AVDD', 'F.Cu', .2,
     [(62, 45.175), (61.3, 45.175), (61.3, 46.2), (60.2, 47.15)]),
    ('/VREG_LX', 'F.Cu', .127,
     [(57, 49.55), (57, 49.1), (57.15, 48.95), (57.4, 48.95), (57.8, 48.55),
      (58.1, 48.55), (58.5, 48.15), (58.5, 47.75)]),
    ('/+3V3', 'F.Cu', .127,
     [(56.6, 49.55), (56.6, 50.2)]),
    ('/+3V3', 'B.Cu', .2, [(56.6, 50.2), (57.025, 49.1)]),
    ('/GND', 'F.Cu', .127,
     [(57.4, 49.55), (57.4, 50.2)]),
    ('/GND', 'B.Cu', .2, [(57.4, 50.2), (58, 49.6), (58.575, 49.1)]),
    ('/CORE_1V1', 'B.Cu', .127, [(57.5, 52.6), (57.58, 52.75)]),
    ('/GND', 'B.Cu', .127, [(58.22, 52.75), (58.22, 53.05), (57.1, 53.05)]),
    ('/+3V3', 'B.Cu', .127, [(57.05, 52.425), (56.6, 52.875), (56.6, 53.925), (57.05, 54.375)]),
    ('/GPIO25', 'F.Cu', .127, [(58.45, 53.4), (57.8, 53.4), (57.5, 53.6)]),
    ('/GPIO25', 'B.Cu', .127, [(57.5, 53.6), (57.65, 53.75), (57.85, 53.75)]),
    ('/CORE_1V1', 'In2.Cu', .25, [(58.5, 46.9), (57.8, 47.6), (57.8, 49.5), (56, 50.75)]),
]
vias = [('/+3V3', 56.6, 50.2), ('/GND', 57.4, 50.2), ('/GND', 60.2, 45.25),
        ('/GND', 57.1, 53.05), ('/GPIO25', 57.5, 53.6)]
moves = {'C5': (60.2, 46.2, 90), 'C6': (57.8, 49.1, 0), 'C20': (57.9, 52.75, 0)}
manifest = {'source': str(source), 'output': str(output),
            'removed_ids': sorted(remove), 'moves': moves,
            'routes': routes, 'vias': vias,
            'package_changes': {'C6': {'footprint': 'Capacitor_SMD:C_0603_1608Metric', 'value': '4.7 µF', 'MPN': 'TBD, verify DC bias at 3.3 V'},
                                'C20': {'footprint': 'Capacitor_SMD:C_0201_0603Metric', 'value': '100 nF', 'MPN': 'TBD, verify at 1.1 V'}}}

with KiCad(headless=True, timeout_ms=120000, file_path=str(output)) as k:
    board = k.get_board()
    k.load_all_libraries()
    nets = {net.name: net for net in board.get_nets()}
    layers = {'F.Cu': bt.BL_F_Cu, 'B.Cu': bt.BL_B_Cu, 'In2.Cu': bt.BL_In2_Cu}
    items = board.get_tracks() + board.get_vias()
    victims = [item for item in items if item.id.value in remove]
    board.remove_items(victims)
    for ref, package in {'C6': 'C_0603_1608Metric', 'C20': 'C_0201_0603Metric'}.items():
        footprint = next(f for f in board.get_footprints() if f.reference_field.text.value == ref)
        replacement = board.place_footprint_from_library('Capacitor_SMD:' + package, footprint.position)
        old_nets = {p.number: p.net for p in footprint.definition.pads if p.number}
        proto = footprint.proto
        proto.definition.CopyFrom(replacement.proto.definition)
        proto.orientation.CopyFrom(Angle.from_degrees(0).proto)
        footprint = FootprintInstance(proto)
        for pad in footprint.definition.pads:
            if pad.number in old_nets:
                pad.net = old_nets[pad.number]
        board.remove_items([footprint, replacement])
        board.create_items([footprint])
    for footprint in board.get_footprints():
        ref = footprint.reference_field.text.value
        if ref not in moves:
            continue
        if ref in {'C6', 'C20'}:
            board.flip_items(footprint)
            footprint = next(f for f in board.get_footprints()
                             if f.reference_field.text.value == ref)
        x, y, angle = moves[ref]
        footprint.position = Vector2.from_xy_mm(x, y)
        footprint.orientation = Angle.from_degrees(angle)
        board.update_items(footprint)
    created = []
    for net, layer, width, points in routes:
        for start, end in zip(points, points[1:]):
            track = Track()
            track.net = nets[net]
            track.layer = layers[layer]
            track.width = round(width * 1e6)
            track.start = Vector2.from_xy_mm(*start)
            track.end = Vector2.from_xy_mm(*end)
            created.append(track)
    for net, x, y in vias:
        via = Via()
        via.net = nets[net]
        via.position = Vector2.from_xy_mm(x, y)
        via.diameter = 450000
        via.drill_diameter = 150000
        via.proto.pad_stack.drill.start_layer = bt.BL_F_Cu
        via.proto.pad_stack.drill.end_layer = bt.BL_B_Cu
        created.append(via)
    board.create_items(created)
    board.save()
output.with_suffix('.changes.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(output)
