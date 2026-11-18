from pathlib import Path
from collections import defaultdict
import argparse
import heapq
import json
import math
import uuid
import numpy as np
import sexpdata as sx
from shapely.geometry import Point, LineString, Polygon, box
from shapely.affinity import rotate, translate
from shapely.ops import unary_union
from shapely import contains_xy

ROOT = Path(__file__).resolve().parent.parent
S = sx.Symbol
LAYERS = ['F.Cu', 'B.Cu', 'In2.Cu']


def node(name, *values):
    return [S(name), *values]


def tags(data, name):
    return [item for item in data if isinstance(item, list) and item and str(item[0]) == name]


def tag(data, name, default=None):
    result = next(iter(tags(data, name)), None)
    if result is None and name == 'at':
        transform = next(iter(tags(data, 'transform')), None)
        if transform is not None:
            translation = next(iter(tags(transform, 'translate')))
            rotation = next(iter(tags(transform, 'rotate')))
            return node('at', *translation[1:3], rotation[1])
    return result if result is not None else default


def replace(data, name, value):
    data[:] = [item for item in data if not (isinstance(item, list) and str(item[0]) == name)]
    data.append(value)


def pad_shape(pad, footprint):
    width, height = tag(pad, 'size')[1:3]
    shape_name = str(pad[3])
    if shape_name == 'circle':
        shape = Point(0, 0).buffer(width / 2)
    elif shape_name == 'oval':
        if width >= height:
            shape = LineString([(-(width-height)/2, 0), ((width-height)/2, 0)]).buffer(height/2)
        else:
            shape = LineString([(0, -(height-width)/2), (0, (height-width)/2)]).buffer(width/2)
    else:
        shape = box(-width/2, -height/2, width/2, height/2)
        if shape_name == 'roundrect':
            radius = min(width, height) * tag(pad, 'roundrect_rratio', [None, 0.25])[1]
            shape = box(-width/2+radius, -height/2+radius, width/2-radius, height/2-radius).buffer(radius)
        elif shape_name == 'custom':
            primitives = tag(pad, 'primitives', [])
            polygons = [shape]
            for primitive in tags(primitives, 'gr_poly'):
                polygons.append(Polygon([point[1:3] for point in tag(primitive, 'pts')[1:]]))
            shape = unary_union(polygons)
    pad_at = tag(pad, 'at')
    pad_angle = pad_at[3] if len(pad_at) > 3 else 0
    footprint_at = tag(footprint, 'at')
    footprint_angle = footprint_at[3] if len(footprint_at) > 3 else 0
    shape = translate(rotate(shape, -(pad_angle-footprint_angle), origin=(0, 0)), *pad_at[1:3])
    return translate(rotate(shape, -footprint_angle, origin=(0, 0)), *footprint_at[1:3])


def copper_items(board):
    for footprint in tags(board, 'footprint'):
        for pad in tags(footprint, 'pad'):
            layer_names = tag(pad, 'layers')[1:]
            if not any('Cu' in str(layer) for layer in layer_names):
                continue
            net = tag(pad, 'net', [None, None])[1]
            shape = pad_shape(pad, footprint)
            yield dict(shape=shape, layers=LAYERS if '*.Cu' in layer_names else [str(layer) for layer in layer_names if str(layer) in LAYERS], net=net, kind='pad', object=pad)
    for track in tags(board, 'segment'):
        shape = LineString([tag(track, 'start')[1:3], tag(track, 'end')[1:3]]).buffer(tag(track, 'width')[1]/2)
        yield dict(shape=shape, layers=[tag(track, 'layer')[1]], net=tag(track, 'net')[1], kind='track', object=track)
    for via in tags(board, 'via'):
        yield dict(shape=Point(*tag(via, 'at')[1:3]).buffer(tag(via, 'size')[1]/2), layers=LAYERS, net=tag(via, 'net')[1], kind='via', object=via)


def add_track(board, net, points, layer='F.Cu', width=0.15):
    for first, second in zip(points, points[1:]):
        if math.dist(first, second) < 0.00001:
            continue
        board.append(node('segment', node('start', *first), node('end', *second), node('width', width), node('layer', layer), node('net', net), node('uuid', str(uuid.uuid4()))))


def add_via(board, net, position):
    for existing in tags(board, 'via'):
        center = tag(existing, 'at')[1:3]
        if tag(existing, 'net')[1] == net and math.dist(center, position) < 0.2:
            for layer in LAYERS:
                add_track(board, net, [center, position], layer, width=0.1)
            return
    board.append(node('via', node('at', *position), node('size', 0.6), node('drill', 0.3), node('layers', 'F.Cu', 'B.Cu'), node('net', net), node('uuid', str(uuid.uuid4()))))


def basic_cleanup(board):
    for segment in tags(board, 'segment'):
        if tag(segment, 'layer')[1] == 'In1.Cu' and tag(segment, 'net')[1] != 'GND':
            replace(segment, 'layer', node('layer', 'B.Cu'))
        if tag(segment, 'width')[1] < 0.1:
            replace(segment, 'width', node('width', 0.1))
    for footprint in tags(board, 'footprint'):
        props = {item[1]: item[2] for item in tags(footprint, 'property')}
        if props.get('Reference', '').startswith('TP'):
            replace(footprint, 'attr', node('attr', S('board_only'), S('exclude_from_pos_files'), S('exclude_from_bom')))
        if footprint[1] == 'Aster:Fiducial':
            for pad in tags(footprint, 'pad'):
                replace(pad, 'clearance', node('clearance', 0.65))
        if props.get('Reference') == 'C42':
            for pad in tags(footprint, 'pad'):
                if tag(pad, 'net', [None, None])[1] == 'GND':
                    replace(pad, 'zone_connect', node('zone_connect', 2))
    positions = {'LiPo 1S + NTC': None, '+ N -': None, 'ESP BOOT': (153, 132.5), 'BOOT': (129, 153.2), 'QWIIC / QT': (170, 154.4)}
    for text in list(tags(board, 'gr_text')):
        if text[1] in positions:
            if positions[text[1]] is None:
                board.remove(text)
            else:
                replace(text, 'at', node('at', *positions[text[1]], 0))
    if not any(text[1] == '1+' for text in tags(board, 'gr_text')):
        for text_value, position, layer in [('1+', (104.5, 139), 'F.SilkS'), ('BATT  1:+  2:NTC  3:GND', (111, 141.9), 'B.SilkS')]:
            effects = node('effects', node('font', node('size', 0.7, 0.7), node('thickness', 0.12)))
            if layer.startswith('B.'):
                effects.append(node('justify', S('mirror')))
            board.append(node('gr_text', text_value, node('at', *position, 0), node('layer', layer), node('uuid', str(uuid.uuid4())), effects))


def obstacles(board, net, radius):
    per_layer = defaultdict(list)
    for item in copper_items(board):
        if item['net'] == net:
            continue
        shape = item['shape'].buffer(radius + 0.112)
        for layer in item['layers']:
            per_layer[layer].append(shape)
    antenna = box(150.85, 99, 179.15, 111.15)
    return [unary_union(per_layer[layer] + [antenna]) for layer in LAYERS]


def via_obstacle(board, net):
    shapes = []
    for item in copper_items(board):
        if item['net'] != net:
            shapes.append(item['shape'].buffer(0.415))
        elif item['kind'] == 'pad' and 'F.Cu' in item['layers']:
            shapes.append(item['shape'].buffer(0.21))
        elif item['kind'] == 'via':
            center = item['shape'].centroid
            shapes.append(center.buffer(0.56).difference(center.buffer(0.04)))
        if item['kind'] == 'via' and item['net'] != net:
            position = tag(item['object'], 'at')[1:3]
            drill = tag(item['object'], 'drill')[1]
            shapes.append(Point(*position).buffer(drill/2+0.15+0.26))
    for footprint in tags(board, 'footprint'):
        for pad in tags(footprint, 'pad'):
            drill = tag(pad, 'drill')
            if not drill:
                continue
            shape = pad_shape(pad, footprint)
            size = tag(pad, 'size')[1:3]
            drill_dimension = float(drill[1]) if isinstance(drill[1], (int, float)) else max(float(value) for value in drill[2:])
            shapes.append(shape.centroid.buffer(drill_dimension/2+0.15+0.26))
    shapes.append(box(150.6, 99, 179.4, 111.4))
    return unary_union(shapes)


def add_supply_via(board, point):
    net = '+3V3'
    blocked = via_obstacle(board, net)
    route_blocked = obstacles(board, net, 0.075)[0]
    xcoord, ycoord = point
    candidates = []
    for radius_index in range(0, 41):
        radius = radius_index * 0.05
        for angle_index in range(48):
            angle = angle_index * math.pi/24
            candidate = (round(xcoord+radius*math.cos(angle), 5), round(ycoord+radius*math.sin(angle), 5))
            if not (101 < candidate[0] < 179 and 112 < candidate[1] < 164):
                continue
            if blocked.intersects(Point(*candidate)):
                continue
            segment = LineString([point, candidate])
            if not route_blocked.intersects(segment):
                candidates.append(candidate)
        if candidates:
            break
    if not candidates:
        raise RuntimeError('No supply via candidate near '+str(point))
    candidate = min(candidates, key=lambda item: math.dist(item, point))
    add_track(board, net, [point, candidate], width=0.2)
    add_via(board, net, candidate)
    print('Connected 3V3 to plane at', candidate)


def astar_route(board, net, start, end, start_layer='F.Cu', end_layer='F.Cu', step=0.1):
    origin_x, origin_y = 100.5, 111.5
    width = round((179.5-origin_x)/step)+1
    height = round((164.5-origin_y)/step)+1
    xvalues = origin_x+np.arange(width)*step
    yvalues = origin_y+np.arange(height)*step
    xgrid, ygrid = np.meshgrid(xvalues, yvalues)
    geom = obstacles(board, net, 0.05)
    blocked = np.stack([contains_xy(shape, xgrid, ygrid) for shape in geom])
    via_blocked = contains_xy(via_obstacle(board, net), xgrid, ygrid)

    def grid_point(point, layer):
        return (LAYERS.index(layer), int(round((point[1]-origin_y)/step)), int(round((point[0]-origin_x)/step)))

    source = grid_point(start, start_layer)
    target = grid_point(end, end_layer)
    for via in tags(board, 'via'):
        if tag(via, 'net')[1] == net:
            via_position = grid_point(tag(via, 'at')[1:3], 'F.Cu')
            _, via_row, via_column = via_position
            if 0 <= via_row < height and 0 <= via_column < width:
                blocked[:, via_row, via_column] = False
                via_blocked[via_row, via_column] = False
    if not (0 <= source[1] < height and 0 <= source[2] < width and 0 <= target[1] < height and 0 <= target[2] < width):
        raise RuntimeError('Route point outside routing bounds')
    blocked[source] = False
    blocked[target] = False

    def heuristic(position):
        dx = abs(position[2]-target[2])
        dy = abs(position[1]-target[1])
        return max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy)+(30 if position[0]!=target[0] else 0)

    pending = [(heuristic(source), 0, source)]
    cost = {source: 0}
    parent = {}
    directions = [(0,1,1),(0,-1,1),(1,0,1),(-1,0,1),(1,1,math.sqrt(2)),(1,-1,math.sqrt(2)),(-1,1,math.sqrt(2)),(-1,-1,math.sqrt(2))]
    visited = 0
    while pending:
        _, score, position = heapq.heappop(pending)
        if score > cost.get(position, math.inf)+0.00001:
            continue
        if position == target:
            break
        visited += 1
        layer, row, column = position
        adjacent = []
        for dy, dx, increment in directions:
            next_row, next_column = row+dy, column+dx
            if not (0 <= next_row < height and 0 <= next_column < width) or blocked[layer,next_row,next_column]:
                continue
            if dx and dy and (blocked[layer,row,next_column] or blocked[layer,next_row,column]):
                continue
            adjacent.append(((layer,next_row,next_column),increment))
        if not via_blocked[row,column]:
            adjacent.extend(((next_layer,row,column),30) for next_layer in range(3) if next_layer!=layer and not blocked[next_layer,row,column])
        for destination, increment in adjacent:
            next_cost = score+increment
            if next_cost+0.00001 < cost.get(destination, math.inf):
                cost[destination] = next_cost
                parent[destination] = position
                heapq.heappush(pending,(next_cost+heuristic(destination),next_cost,destination))
    else:
        raise RuntimeError(f'No route for {net} after {visited} visited states')
    path = [target]
    while path[-1]!=source:
        path.append(parent[path[-1]])
    path.reverse()
    runs = []
    current_layer = path[0][0]
    points = [start]
    vias = []
    for position in path:
        physical = (round(origin_x+position[2]*step,5),round(origin_y+position[1]*step,5))
        if position[0]!=current_layer:
            points.append(physical)
            runs.append((current_layer,points))
            vias.append(physical)
            current_layer=position[0]
            points=[physical]
        elif points[-1]!=physical:
            points.append(physical)
    points.append(end)
    runs.append((current_layer,points))
    for layer, points in runs:
        simplified=[points[0]]
        index=0
        while index<len(points)-1:
            furthest=index+1
            for test in range(index+2,len(points)):
                first,second=points[index],points[test]
                dx=abs(second[0]-first[0]);dy=abs(second[1]-first[1])
                if min(dx,dy)>0.00001 and abs(dx-dy)>0.00001:
                    continue
                if not geom[layer].intersects(LineString([first,second])):
                    furthest=test
            simplified.append(points[furthest]);index=furthest
        add_track(board,net,simplified,LAYERS[layer],width=0.1)
    for position in vias:
        add_via(board,net,position)
    print(f'Routed {net}: {len(path)} grid steps, {len(vias)} vias, {visited} searched states')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['cleanup','supply','route'])
    parser.add_argument('--point',nargs=2,type=float)
    parser.add_argument('--start',nargs=2,type=float)
    parser.add_argument('--end',nargs=2,type=float)
    parser.add_argument('--net')
    parser.add_argument('--start-layer',default='F.Cu')
    parser.add_argument('--end-layer',default='F.Cu')
    parser.add_argument('--step',type=float,default=0.1)
    args=parser.parse_args()
    path=ROOT/'Aster2350.kicad_pcb'
    board=sx.loads(path.read_text())
    if args.action=='cleanup':
        basic_cleanup(board)
    elif args.action=='supply':
        add_supply_via(board,tuple(args.point))
    else:
        astar_route(board,args.net,tuple(args.start),tuple(args.end),args.start_layer,args.end_layer,args.step)
    path.write_text(sx.dumps(board)+'\n')


if __name__=='__main__':
    main()
