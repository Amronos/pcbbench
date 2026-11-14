import argparse
from itertools import pairwise
from pathlib import Path

from kipy import KiCad
from kipy.board_types import Track, Via, Zone
from kipy.geometry import Angle, Vector2
from kipy.proto.board import board_types_pb2 as bt

V = Vector2.from_xy_mm
PLACEMENT = {
    'U4': (114, 121, 0),
    'U5': (127, 120, 0),
    'L1': (122.5, 120, 90),
    'C21': (116.5, 117.5, 90),
    'C22': (110.5, 121, 90),
    'C23': (118.1, 121, 90),
    'C24': (125.6, 124, 270),
    'C25': (130.3, 120, 0),
    'C26': (125.6, 116.3, 90),
    'C27': (129, 116.3, 90),
    'R13': (112.6, 117.7, 90),
    'R14': (119, 118.5, 0),
    'R15': (114.9, 117.7, 90),
    'R16': (113.75, 117.7, 90),
    'R17': (116.8, 124, 180),
    'R18': (115.2, 125, 90),
    'R19': (119.8, 124.8, 0),
    'R20': (119.8, 125.9, 0),
}
OWN_NETS = {
    'VBUS',
    'SYS',
    'BAT',
    'PWR_L1',
    'PWR_L2',
    'ISET',
    'ILIM',
    'TMR',
    'ITERM',
    'USB_LIMIT',
    'CHG',
    'PGOOD',
}
TAG = 'sprocket-power-layout'


def short(net):
    return net.name.rsplit('/', 1)[-1]


def revise(path):
    if path.resolve() == Path(__file__).resolve().parents[1] / 'sprocket2350.kicad_pcb':
        raise ValueError('Use copy_board.py to make a scratch board first')
    with KiCad(headless=True, file_path=str(path.resolve()), timeout_ms=60000) as k:
        board = k.get_board()
        footprints = {f.reference_field.text.value: f for f in board.get_footprints()}
        missing = PLACEMENT.keys() - footprints.keys()
        if missing:
            raise ValueError(f'Missing power components: {sorted(missing)}')
        owners = {footprints[r].id.value for r in PLACEMENT}
        old_pads = [
            p for p in board.get_pads() if p.parent.value in owners and p.net.name
        ]

        def at_pad(point, pad):
            return (
                abs(point.x - pad.position.x) < 500000
                and abs(point.y - pad.position.y) < 500000
            )

        def old_regulator_ground(point):
            return 122000000 < point.x < 126000000 and 118000000 < point.y < 122000000

        remove = []
        for item in board.get_items():
            if not isinstance(item, (Track, Via, Zone)):
                continue
            if short(item.net) == 'VBUS' and isinstance(item, (Track, Via)):
                points = (
                    [item.position] if isinstance(item, Via) else [item.start, item.end]
                )
                if all(p.x < 111000000 and p.y < 114000000 for p in points):
                    continue
            if (
                TAG in str(item.custom_properties)
                or short(item.net) in OWN_NETS
                or (
                    isinstance(item, (Track, Via))
                    and short(item.net) == 'GND'
                    and (
                        old_regulator_ground(item.position)
                        if isinstance(item, Via)
                        else old_regulator_ground(item.start)
                        and old_regulator_ground(item.end)
                    )
                )
                or (
                    isinstance(item, Track)
                    and short(item.net) in {'GND', '3V3'}
                    and any(
                        p.net == item.net
                        and (at_pad(item.start, p) or at_pad(item.end, p))
                        for p in old_pads
                    )
                )
            ):
                remove.append(item)
        board.remove_items(remove)
        for ref, (x, y, angle) in PLACEMENT.items():
            footprint = footprints[ref]
            footprint.position, footprint.orientation = (
                V(x, y),
                Angle.from_degrees(angle),
            )
            for pad in footprint.definition.pads:
                pad.teardrop.mode = bt.PTM_DISABLED
                if pad.net.name and short(pad.net) == 'GND':
                    pad.padstack.zone_settings.zone_connection = bt.ZCS_FULL
            board.update_items(footprint)
        pads = {
            (footprints_ref, p.number): p
            for p in board.get_pads()
            if p.net.name
            for footprints_ref in PLACEMENT
            if p.parent.value == footprints[footprints_ref].id.value
        }
        nets = {short(p.net): p.net for p in pads.values()}
        copper = []

        def track(net, points, width=0.5):
            for a, b in pairwise(points):
                t = Track()
                t.net, t.layer, t.width = nets[net], bt.BL_F_Cu, round(width * 1e6)
                t.start, t.end = V(*a), V(*b)
                t.proto.custom_properties.add(key=TAG, value='1')
                copper.append(t)

        def xy(ref, pin):
            p = pads[ref, str(pin)].position
            return p.x / 1e6, p.y / 1e6

        def ground_via(x, y, tag):
            via = Via()
            via.position, via.net, via.type = V(x, y), nets['GND'], bt.VT_THROUGH
            via.diameter, via.drill_diameter = 450000, 200000
            via.padstack.drill.start_layer = bt.BL_F_Cu
            via.padstack.drill.end_layer = bt.BL_B_Cu
            via.proto.custom_properties.add(key=TAG, value=tag)
            copper.append(via)
            return via

        # Fine-pitch power pins need a short 0.24 mm exit before widening.
        for pin, net, endpoint in [
            (1, '3V3', (125.1, 119)),
            (2, 'PWR_L2', (124.8, 119.5)),
            (4, 'PWR_L1', (124.8, 120.5)),
            (5, 'SYS', (125.1, 121)),
        ]:
            track(net, [xy('U5', pin), endpoint], 0.24)
        track(
            'PWR_L2', [(124.8, 119.5), (124.2, 118.9), (124.2, 117.8625), xy('L1', 2)]
        )
        track(
            'PWR_L1', [(124.8, 120.5), (124.2, 121.1), (124.2, 122.1375), xy('L1', 1)]
        )
        track('3V3', [(125.1, 119), (125.1, 118.5)], 0.24)
        track('3V3', [(125.1, 118.5), (125.1, 117.75), xy('C26', 1)], 0.5)
        track('SYS', [(125.1, 121), (125.1, 121.5)], 0.24)
        track('SYS', [(125.1, 121.5), (125.1, 122.25), xy('C24', 1)], 0.5)
        track('VBUS', [xy('U4', 13), (114.75, 119)], 0.25)
        track(
            'VBUS', [(114.75, 119), (115.5, 119), (116.225, 118.275), xy('C21', 1)], 0.5
        )
        for pin in (2, 3):
            track('BAT', [xy('U4', pin), (111.6, xy('U4', pin)[1])], 0.25)
        track(
            'BAT',
            [(111.6, 120.75), (111.6, 121.25), (111.075, 121.775), xy('C22', 1)],
            0.6,
        )
        for pin in (10, 11):
            track('SYS', [xy('U4', pin), (116.5, xy('U4', pin)[1])], 0.25)
        track(
            'SYS', [(116.5, 120.75), (116.5, 121.45), (117, 121.95), xy('C23', 1)], 0.6
        )
        track('TMR', [xy('U4', 14), (114.25, 118.86), xy('R15', 1)], 0.15)
        track('SYS', [xy('U5', 8), (129.2, 120)], 0.24)
        track('SYS', [(129.2, 120), xy('C25', 1)], 0.5)
        track('SYS', [xy('U5', 6), (129.2, 121)], 0.24)
        track('SYS', [(129.2, 121), (129.2, 120)], 0.5)
        track('3V3', [xy('C26', 1), xy('C27', 1)], 0.6)
        for ref in ('C21', 'C22', 'C23', 'C24', 'C25', 'C26', 'C27'):
            gx, gy = xy(ref, 2)
            vx = gx - 0.85 if ref == 'C22' else gx + 0.85
            track('GND', [(gx, gy), (vx, gy)], 0.5)
            ground_via(vx, gy, 'capacitor ground')
        for ref in ('U4', 'U5'):
            center = footprints[ref].position
            for dx in (-0.4, 0.4):
                for dy in (-0.4, 0.4):
                    via = ground_via(
                        center.x / 1e6 + dx,
                        center.y / 1e6 + dy,
                        'thermal IPC-4761 type VII',
                    )
                    via.padstack.drill.filled = bt.VDFM_FILLED
                    via.padstack.drill.capped = bt.VDCM_CAPPED
        board.create_items(copper)
        board.refill_zones(block=True, max_poll_seconds=120)
        switch_debris = [
            item
            for item in board.get_items()
            if isinstance(item, (Track, Via))
            and short(item.net) in {'PWR_L1', 'PWR_L2'}
            and not any(prop.key == TAG for prop in item.custom_properties)
        ]
        board.remove_items(switch_debris)
        board.refill_zones(block=True, max_poll_seconds=120)
        board.save()
        print(
            f'{path}: moved {len(PLACEMENT)} parts, removed {len(remove)} copper items, '
            f'created {len(copper)} items; route remaining owned nets and GND/3V3'
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('board', type=Path)
    revise(parser.parse_args().board)
