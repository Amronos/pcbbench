import { Console, Effect, FileSystem, Schema } from 'effect';
import { arc, boundingBox, frame } from './geometry.ts';

// The child lists of an s-expression, found by matching parentheses outside quoted strings.
function children(expr: string, head: string) {
	const found: string[] = [];
	let depth = 0;
	let start = 0;
	let quoted = false;

	for (let i = 1; i < expr.length; i++) {
		const char = expr[i];

		if (quoted) {
			if (char === '\\') i++;
			else if (char === '"') quoted = false;
		} else if (char === '"') quoted = true;
		else if (char === '(' && depth++ === 0) start = i;
		else if (
			char === ')' &&
			--depth === 0 &&
			expr.startsWith(`(${head}`, start) &&
			/\s/.test(expr[start + head.length + 1] ?? '')
		)
			found.push(expr.slice(start, i + 1));
	}

	return found;
}

export const byRef = (a: string, b: string) => a.localeCompare(b, 'en', { numeric: true });

export type Point = { x: number; y: number };

const point = (block: string, key: string): Point => {
	const [, x = 0, y = 0] =
		block.match(new RegExp(`\\(${key} ([-\\d.]+) ([-\\d.]+)`))?.map(Number) ?? [];

	return { x, y };
};

const points = (block: string) =>
	[...block.matchAll(/\((?:xy|start|mid|end|center) ([-\d.]+) ([-\d.]+)\)/g)].map(([, x, y]) => ({
		x: Number(x),
		y: Number(y)
	}));

const netOf = (block: string) => block.match(/\(net (?:\d+ )?"([^"]*)"/)?.[1] ?? '';

const layersOf = (block: string) =>
	block.match(/\(layers? ((?:"[^"]*"\s*)+)\)/)?.[1].match(/[^"\s]+/g) ?? [];

const numberOf = (block: string, key: string) =>
	Number(block.match(new RegExp(`\\(${key} ([-\\d.]+)`))?.[1]);

const angleOf = (block: string) =>
	Number(block.match(/\(at [-\d.]+ [-\d.]+ ([-\d.]+)\)/)?.[1] ?? 0);

function padOutline(kind: string, { x: width, y: height }: Point) {
	if (!['circle', 'oval'].includes(kind))
		return boundingBox([
			{ x: -width / 2, y: -height / 2 },
			{ x: width / 2, y: height / 2 }
		]);

	const radius = Math.min(width, height) / 2;
	const along = Math.max(width, height) / 2 - radius;

	const stadium = [
		...arc({ x: along, y: 0 }, radius, -Math.PI / 2, Math.PI, 8),
		...arc({ x: -along, y: 0 }, radius, Math.PI / 2, Math.PI, 8)
	];

	return width >= height ? stadium : stadium.map(({ x, y }) => ({ x: y, y: x }));
}

function parseText(block: string) {
	return {
		text: block.match(/^\((?:gr_text|fp_text \w+|property "[^"]*") "((?:\\.|[^"\\])*)"/)?.[1] ?? '',
		layer: layersOf(block)[0] ?? '',
		height: Number(block.match(/\(size ([-\d.]+) [-\d.]+\)/)?.[1] ?? 0)
	};
}

export type Text = ReturnType<typeof parseText>;

const SILKSCREEN = /^[FB]\.Silk/;

// The silkscreen texts a board or footprint shows.
function parseSilkscreen(block: string, prefix: 'gr' | 'fp') {
	return [
		...children(block, `${prefix}_text`),
		...(prefix === 'fp' ? children(block, 'property') : [])
	].flatMap((block) => {
		const text = parseText(block);

		return !block.includes('(hide yes)') && SILKSCREEN.test(text.layer) && text.text ? [text] : [];
	});
}

function parseZone(block: string, toBoard = (xy: Point) => xy) {
	return {
		name: block.match(/\(name "([^"]*)"/)?.[1] ?? '',
		net: netOf(block),
		layers: layersOf(block),
		notAllowed: [
			...(block
				.match(/\(keepout\s*((?:\(\w+ \w+\)\s*)+)\)/)?.[1]
				.matchAll(/\((\w+) not_allowed\)/g) ?? [])
		].map(([, item]) => item!),
		outline: points(children(block, 'polygon')[0] ?? '').map(toBoard),
		fills: children(block, 'filled_polygon').map((fill) => ({
			layer: layersOf(fill)[0] ?? '',
			outline: points(fill)
		}))
	};
}

export type Zone = ReturnType<typeof parseZone>;

// From this board file version on, zones inside footprints are stored in the footprint's frame rather than the board's.
const FIRST_FOOTPRINT_FRAME_ZONES = 20260616;

function parseFootprint(block: string, fileVersion: number) {
	const header = block.slice(0, block.search(/\(property |\(descr |\(pad /));

	const placement =
		header.match(/\(translate ([-\d.]+) ([-\d.]+)\)(?:\s*\(rotate ([-\d.]+)\))?/) ??
		header.match(/\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)/);

	const attrs = block.match(/\(attr ([^)]*)\)/)?.[1].split(' ') ?? [];
	const libId = block.match(/^\(footprint "([^"]*)"/)?.[1] ?? '';
	const x = Number(placement?.[1]);
	const y = Number(placement?.[2]);
	const rotation = Number(placement?.[3] ?? 0);

	// Child positions are stored unrotated, relative to the footprint.
	const toBoard = frame({ x, y }, rotation);

	const pads = [...block.matchAll(/\(pad "([^"]*)" (\w+) (\w+)[\s\S]*?(?=\(pad "|$)/g)].map(
		([pad, number = '', type = '', kind = '']) => {
			const at = toBoard(point(pad, 'at'));

			return {
				number,
				type,
				net: netOf(pad),
				pinFunction: pad.match(/\(pinfunction "([^"]*)"/)?.[1] ?? '',
				layers: layersOf(pad),
				// Pad angles are stored relative to the board, not the footprint.
				outline: padOutline(kind, point(pad, 'size')).map(frame(at, angleOf(pad))),
				...at
			};
		}
	);

	return {
		ref: block.match(/\(property "Reference" "([^"]*)"/)?.[1] ?? '',
		value: block.match(/\(property "Value" "([^"]*)"/)?.[1] ?? '',
		side: header.includes('(layer "B.Cu")') ? ('bottom' as const) : ('top' as const),
		x,
		y,
		rotation,
		smd: attrs.includes('smd'),
		// Bare test pads are copper only; PCBWay leaves them out of the BOM too.
		isPart:
			!/TestPoint/i.test(libId) &&
			!['board_only', 'exclude_from_bom', 'dnp'].some((attr) => attrs.includes(attr)),
		hasModel: block.includes('(model '),
		pads,
		courtyard: ['fp_line', 'fp_rect', 'fp_poly', 'fp_arc', 'fp_circle']
			.flatMap((kind) => children(block, kind))
			.filter((graphic) => /\(layer "[FB]\.CrtYd"\)/.test(graphic))
			.flatMap(points)
			.map(toBoard),
		zones: children(block, 'zone').map((zone) =>
			parseZone(zone, fileVersion >= FIRST_FOOTPRINT_FRAME_ZONES ? toBoard : undefined)
		),
		silkscreen: parseSilkscreen(block, 'fp')
	};
}

export type Footprint = ReturnType<typeof parseFootprint>;

function parseCopper(pcb: string) {
	const setup = children(pcb, 'setup')[0] ?? '';

	return {
		tracks: ['segment', 'arc'].flatMap((kind) =>
			children(pcb, kind).map((track) => ({
				start: point(track, 'start'),
				mid: kind === 'arc' ? point(track, 'mid') : null,
				end: point(track, 'end'),
				width: numberOf(track, 'width'),
				layer: layersOf(track)[0] ?? '',
				net: netOf(track)
			}))
		),
		vias: children(pcb, 'via').map((via) => ({
			...point(via, 'at'),
			size: numberOf(via, 'size'),
			net: netOf(via)
		})),
		zones: children(pcb, 'zone').map((zone) => parseZone(zone)),
		stackup: children(children(setup, 'stackup')[0] ?? '', 'layer').map((layer) => ({
			name: layer.match(/^\(layer "([^"]*)"/)?.[1] ?? '',
			type: layer.match(/\(type "([^"]*)"/)?.[1] ?? '',
			thickness: numberOf(layer, 'thickness'),
			epsilonR: numberOf(layer, 'epsilon_r')
		}))
	};
}

export type Copper = ReturnType<typeof parseCopper>;

export const runDirectory = (runId: string) => `${import.meta.dir}/../runs/${runId}`;

export const RENDERS = {
	top: ['--side', 'top'],
	bottom: ['--side', 'bottom'],
	iso: ['--rotate', '-40,0,30', '--perspective', '--floor', '--zoom', '0.7']
};

export const RENDER_SIZE = ['--quality', 'high', '--width', '1600', '--height', '1200'];

const RunInfo = Schema.fromJsonString(
	Schema.Struct({
		board: Schema.String,
		bom: Schema.String,
		placement: Schema.String,
		fabZip: Schema.String,
		versions: Schema.Struct({ kicad: Schema.String })
	})
);

export const readRunInfo = Effect.fn('readRunInfo')(function* (runId: string) {
	const text = yield* (yield* FileSystem.FileSystem).readFileString(
		`${runDirectory(runId)}/info.json`
	);

	return yield* Schema.decodeEffect(RunInfo)(text);
});

export const readRun = Effect.fn('readRun')(function* (runId: string) {
	const runDir = runDirectory(runId);
	const info = yield* readRunInfo(runId);
	const board = `${runDir}/output/${info.board}`;
	const pcb = yield* (yield* FileSystem.FileSystem).readFileString(board);
	const fileVersion = Number(pcb.match(/\(version (\d+)\)/)?.[1]);

	const footprints = children(pcb, 'footprint').map((footprint) =>
		parseFootprint(footprint, fileVersion)
	);

	const parts = footprints
		.filter((footprint) => footprint.isPart)
		.sort((a, b) => byRef(a.ref, b.ref));

	const copperLayers = [
		...(pcb.match(/\n\t\(layers\n([\s\S]*?)\n\t\)/)?.[1] ?? '').matchAll(
			/\(\d+ "([^"]+\.Cu)" (?:signal|power|mixed|jumper)/g
		)
	].map(([, name]) => name!);

	return {
		runDir,
		info,
		board,
		footprints,
		parts,
		copperLayers,
		copper: parseCopper(pcb),
		silkscreen: parseSilkscreen(pcb, 'gr')
	};
});

const metricsPath = (runId: string) => `${runDirectory(runId)}/metrics.json`;

// Each script decodes only the metrics.json sections it reads.
export const readMetrics = Effect.fn('readMetrics')(function* <
	S extends Schema.ConstraintDecoder<unknown>
>(runId: string, sections: S) {
	const text = yield* (yield* FileSystem.FileSystem).readFileString(metricsPath(runId));

	return yield* Schema.decodeUnknownEffect(Schema.fromJsonString(sections))(text);
});

// What JSON.stringify writes, which leaves out undefined fields.
export type JsonFields = { readonly [key: string]: JsonField };

type JsonField =
	string | number | boolean | null | undefined | ReadonlyArray<JsonField> | JsonFields;

export const updateMetrics = Effect.fn('updateMetrics')(function* (
	runId: string,
	fields: JsonFields
) {
	const metrics = yield* readMetrics(runId, Schema.JsonObject);

	yield* (yield* FileSystem.FileSystem).writeFileString(
		metricsPath(runId),
		`${JSON.stringify({ ...metrics, ...fields }, null, '\t')}\n`
	);
	yield* Console.log(JSON.stringify(fields, null, '\t'));
});
