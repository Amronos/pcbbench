import type { Copper, Point } from './board.ts';

// Tolerance for copper that only touches an edge.
export const EDGE_MM = 0.005;

export const sub = (a: Point, b: Point) => ({ x: a.x - b.x, y: a.y - b.y });
export const cross = (a: Point, b: Point) => a.x * b.y - a.y * b.x;
export const dot = (a: Point, b: Point) => a.x * b.x + a.y * b.y;
export const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.y - b.y);

// Maps points given relative to origin and rotated by degrees onto the board. KiCad's y axis points down, so positive
// angles turn counterclockwise on screen.
export const frame = (origin: Point, degrees: number) => {
	const [cos, sin] = [Math.cos((degrees * Math.PI) / 180), Math.sin((degrees * Math.PI) / 180)];

	return ({ x: dx, y: dy }: Point) => ({
		x: origin.x + dx * cos + dy * sin,
		y: origin.y - dx * sin + dy * cos
	});
};

const edges = (polygon: Point[]) =>
	polygon.map((vertex, i) => [vertex, polygon[(i + 1) % polygon.length]!] as const);

export const isInside = (point: Point, polygon: Point[]) =>
	edges(polygon).filter(
		([a, b]) =>
			a.y > point.y !== b.y > point.y &&
			point.x < a.x + ((point.y - a.y) * (b.x - a.x)) / (b.y - a.y)
	).length %
		2 ===
	1;

const pointToSegment = (point: Point, a: Point, b: Point) => {
	const along = sub(b, a);
	const t = Math.max(0, Math.min(1, dot(sub(point, a), along) / (dot(along, along) || 1)));

	return distance(point, { x: a.x + t * along.x, y: a.y + t * along.y });
};

const segmentsCross = (a: Point, b: Point, c: Point, d: Point) =>
	cross(sub(b, a), sub(c, a)) * cross(sub(b, a), sub(d, a)) < 0 &&
	cross(sub(d, c), sub(a, c)) * cross(sub(d, c), sub(b, c)) < 0;

// How far a segment, or a point when a equals b, is from a polygon; 0 when it crosses into it.
export const segmentToPolygon = (a: Point, b: Point, polygon: Point[]) =>
	isInside(a, polygon) || edges(polygon).some(([c, d]) => segmentsCross(a, b, c, d))
		? 0
		: Math.min(
				...edges(polygon).flatMap(([c, d]) => [
					pointToSegment(c, a, b),
					pointToSegment(a, c, d),
					pointToSegment(b, c, d)
				])
			);

export const isDeepInside = (point: Point, polygon: Point[]) =>
	isInside(point, polygon) &&
	edges(polygon).every(([a, b]) => pointToSegment(point, a, b) > EDGE_MM);

export const polygonsOverlap = (p: Point[], q: Point[]) =>
	p.some((vertex) => isDeepInside(vertex, q)) ||
	q.some((vertex) => isDeepInside(vertex, p)) ||
	edges(p).some(([a, b]) => edges(q).some(([c, d]) => segmentsCross(a, b, c, d)));

export const boundingBox = (points: Point[]) => {
	const xs = points.map((point) => point.x);
	const ys = points.map((point) => point.y);

	const [left, right, top, bottom] = [
		Math.min(...xs),
		Math.max(...xs),
		Math.min(...ys),
		Math.max(...ys)
	];

	return [
		{ x: left, y: top },
		{ x: right, y: top },
		{ x: right, y: bottom },
		{ x: left, y: bottom }
	];
};

export const arc = (center: Point, radius: number, from: number, sweep: number, steps = 16) =>
	Array.from({ length: steps + 1 }, (_, i) => ({
		x: center.x + radius * Math.cos(from + (sweep * i) / steps),
		y: center.y + radius * Math.sin(from + (sweep * i) / steps)
	}));

// The circle through three points, walked from start through mid to end.
export function arcThrough(start: Point, mid: Point, end: Point) {
	const d = 2 * (start.x * (mid.y - end.y) + mid.x * (end.y - start.y) + end.x * (start.y - mid.y));

	if (!d) return [start, end];
	const sq = ({ x, y }: Point) => x * x + y * y;

	const center = {
		x:
			(sq(start) * (mid.y - end.y) + sq(mid) * (end.y - start.y) + sq(end) * (start.y - mid.y)) / d,
		y: (sq(start) * (end.x - mid.x) + sq(mid) * (start.x - end.x) + sq(end) * (mid.x - start.x)) / d
	};

	const angle = ({ x, y }: Point) => Math.atan2(y - center.y, x - center.x);
	const turn = (to: Point) => (angle(to) - angle(start) + 4 * Math.PI) % (2 * Math.PI);
	const sweep = turn(mid) <= turn(end) ? turn(end) : turn(end) - 2 * Math.PI;

	return arc(center, distance(start, center), angle(start), sweep);
}

// An arc's radius is that of the circle through its three points.
export const trackLength = ({ start, mid, end }: Copper['tracks'][number]) => {
	if (!mid) return distance(start, end);
	const [a, b, c] = [distance(start, mid), distance(mid, end), distance(start, end)];
	const radius = (a * b * c) / Math.abs(2 * cross(sub(mid, start), sub(end, start)));

	return Number.isFinite(radius)
		? 2 *
				radius *
				(Math.asin(Math.min(1, a / (2 * radius))) + Math.asin(Math.min(1, b / (2 * radius))))
		: c;
};
