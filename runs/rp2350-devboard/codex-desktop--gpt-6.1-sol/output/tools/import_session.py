from pathlib import Path
import sys
import uuid
import sexpdata as sx

ROOT = Path(__file__).resolve().parent.parent
S = sx.Symbol


def tags(data, name):
    return [item for item in data if isinstance(item, list) and item and str(item[0]) == name]


def tag(data, name):
    return tags(data, name)[0]


def node(name, *values):
    return [S(name), *values]


def main():
    session_path = Path(sys.argv[1])
    board_path = ROOT / 'Aster2350.kicad_pcb'
    board = sx.loads(board_path.read_text())
    session = sx.loads(session_path.read_text().replace('[', '_').replace(']', '_'))
    routes = tag(session, 'routes')
    resolution = tag(routes, 'resolution')
    if str(resolution[1]) != 'um':
        raise ValueError('Session coordinate unit must be um')
    multiplier = 0.001 / float(resolution[2])
    nets = {item[2]: item[1] for item in tags(board, 'net')}
    named_nets = not bool(nets)
    imported = []
    for net in tags(tag(routes, 'network_out'), 'net'):
        net_name = str(net[1])
        for wire in tags(net, 'wire'):
            if not tags(wire, 'path'):
                continue
            path = tag(wire, 'path')
            layer = str(path[1])
            width = float(path[2]) * multiplier
            points = [(round(float(path[index]) * multiplier, 6), round(-float(path[index + 1]) * multiplier, 6)) for index in range(3, len(path), 2)]
            for first, second in zip(points, points[1:]):
                if first == second:
                    continue
                imported.append(node('segment', node('start', *first), node('end', *second), node('width', width), node('layer', layer), node('net', net_name if named_nets else nets[net_name]), node('uuid', str(uuid.uuid4()))))
        for via in tags(net, 'via'):
            position = (round(float(via[2]) * multiplier, 6), round(-float(via[3]) * multiplier, 6))
            imported.append(node('via', node('at', *position), node('size', 0.6), node('drill', 0.3), node('layers', 'F.Cu', 'B.Cu'), node('net', net_name if named_nets else nets[net_name]), node('uuid', str(uuid.uuid4()))))
    board[:] = [item for item in board if not (isinstance(item, list) and str(item[0]) in ['segment', 'via'])]
    board.extend(imported)
    board_path.write_text(sx.dumps(board) + '\n')
    print(f'Imported {len(imported)} routed copper items from {session_path.name}')


if __name__ == '__main__':
    main()
