import json
import math
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Track, Via
from kipy.proto.board import board_types_pb2 as bt


def check(path):
    report = path.with_name(path.stem + '-drc.json')
    subprocess.run(
        [
            'kicad-cli', 'pcb', 'drc', '--refill-zones', '--severity-all',
            '--format', 'json', '-o', str(report), str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return json.loads(report.read_text())


def error_count(report):
    return sum(
        v['severity'] == 'error' for v in report['violations']
    )


def safe(report):
    return not report['unconnected_items'] and error_count(report) == 0


def center_joins(board, via):
    nearby = {}
    for track in board.get_tracks():
        if not isinstance(track, Track) or track.net != via.net:
            continue
        if track.layer == bt.BL_In1_Cu:
            continue
        for point in (track.start, track.end):
            distance = math.hypot(point.x - via.position.x, point.y - via.position.y)
            if distance <= (via.diameter + track.width) / 2:
                nearby.setdefault(track.layer, {})[(point.x, point.y)] = (point, track.width)
    joins = []
    for layer, endpoints in nearby.items():
        if len(endpoints) < 2:
            continue
        for point, width in endpoints.values():
            if point == via.position:
                continue
            track = Track()
            track.net, track.layer, track.width = via.net, layer, width
            track.start, track.end = point, via.position
            joins.append(track)
    return joins


def main():
    path = Path(sys.argv[1]).resolve()
    if path.parent.name != 'scratch' or path.name != 'copper-clean.kicad_pcb':
        raise ValueError('Only scratch/copper-clean.kicad_pcb may be edited')
    deadline = time.monotonic() + 180
    report = check(path)
    if not safe(report):
        raise ValueError('Input has errors or opens')
    rejected = set()
    accepted = Counter()
    with KiCad(headless=True, file_path=str(path), timeout_ms=60000) as k:
        board = k.get_board()
        while time.monotonic() < deadline:
            candidate = next(
                (
                    (v['type'], item['uuid'])
                    for v in report['violations']
                    if v['type'] in ('via_dangling', 'track_dangling')
                    for item in v['items']
                    if item['uuid'] not in rejected
                ),
                None,
            )
            if candidate is None:
                break
            kind, uuid = candidate
            items = {
                item.id.value: item
                for item in [*board.get_tracks(), *board.get_vias()]
            }
            item = items.get(uuid)
            if item is None:
                rejected.add(uuid)
                continue
            if 'USB' in item.net.name.upper() or item.net.name == '/VBUS':
                rejected.add(uuid)
                print('PROTECTED', item.net.name, uuid, flush=True)
                continue
            joins = center_joins(board, item) if isinstance(item, Via) else []
            created = board.create_items(joins) if joins else []
            board.remove_items([item])
            board.save()
            trial = check(path)
            if safe(trial):
                report = trial
                accepted[kind] += 1
                print('ACCEPT', kind, item.net.name, uuid, flush=True)
            else:
                if created:
                    board.remove_items(created)
                board.create_items([item])
                board.save()
                rejected.add(uuid)
                print(
                    'RETAIN', kind, item.net.name, uuid,
                    'opens', len(trial['unconnected_items']),
                    'errors', error_count(trial),
                    flush=True,
                )
        report = check(path)
    print('ACCEPTED', dict(accepted))
    print('FINAL', dict(Counter(v['type'] for v in report['violations'])))
    print('OPENS', len(report['unconnected_items']))
    if not safe(report):
        raise RuntimeError('Final DRC failed')


if __name__ == '__main__':
    main()
