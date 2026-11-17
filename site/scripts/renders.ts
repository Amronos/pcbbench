// Cuts the drop shadow out of each run's KiCad renders and measures where the board sits in
// the top and bottom views and layer images, so the site can draw boards at true scale.
import { mkdir, readdir } from 'node:fs/promises';
import { RUNS } from '@pcbbench/bench/runs';
import sharp from 'sharp';

const RUNS_DIR = new URL('../../runs/', import.meta.url);
const OUT_DIR = new URL('../src/generated/renders/', import.meta.url);
const VIEWS = ['top', 'bottom', 'iso'] as const;

export type View = (typeof VIEWS)[number];

// The renders have a transparent background, and the shadow is translucent black.
const SHADOW_MAX_ALPHA = 230;

// Every board has green soldermask; the connectors and modules that overhang its edge aren't green.
const MASK_MIN_GREEN_LEAD = 8;

export type Box = { x: number; y: number; width: number; height: number };

export type RenderInfo = {
	width: number;
	height: number;
	board?: Box;
};

export type LayerInfo = RenderInfo & { name: string; file: string };

export type RunRenders = Record<View, RenderInfo> & { layers: ReadonlyArray<LayerInfo> };

// The judge's layer images are KiCad SVG plots on white. The Edge.Cuts outline plots as a slightly
// green gray (208,210,205), and thin outlines blend with the white, so only the tint is checked.
const OUTLINE_MAX_TINT = 10;
const PLOT_WHITE_MIN = 250;

// Layer images keep this much around the outline, as a fraction of the board's longer side, so
// overhanging parts show but text placed far off the board doesn't.
const LAYER_MARGIN = 0.03;

// KiCad's PCB editor background, so light layers like silkscreen stay readable.
const SUBSTRATE_RGB = [0, 16, 35];

const LAYER_KINDS = ['Cu', 'Silkscreen', 'Mask', 'Fab'];

function clearShadow(pixels: Uint8Array, width: number, height: number) {
	const background = new Uint8Array(width * height);
	const queue = new Uint32Array(width * height);
	let head = 0;
	let tail = 0;

	const visit = (index: number) => {
		if (background[index] || pixels[index * 4 + 3] > SHADOW_MAX_ALPHA) return;

		background[index] = 1;
		queue[tail++] = index;
	};

	for (let x = 0; x < width; x++) {
		visit(x);
		visit((height - 1) * width + x);
	}

	for (let y = 0; y < height; y++) {
		visit(y * width);
		visit(y * width + width - 1);
	}

	while (head < tail) {
		const index = queue[head++];
		const x = index % width;

		if (x > 0) visit(index - 1);

		if (x < width - 1) visit(index + 1);

		if (index >= width) visit(index - width);

		if (index < width * (height - 1)) visit(index + width);
	}

	for (let index = 0; index < width * height; index++) {
		if (background[index]) pixels[index * 4 + 3] = 0;
	}

	return background;
}

function boundingBox(width: number, height: number, include: (index: number) => boolean): Box {
	let left = width;
	let right = -1;
	let top = height;
	let bottom = -1;

	for (let y = 0; y < height; y++) {
		for (let x = 0; x < width; x++) {
			if (!include(y * width + x)) continue;

			left = Math.min(left, x);
			right = Math.max(right, x);
			top = Math.min(top, y);
			bottom = Math.max(bottom, y);
		}
	}

	return { x: left, y: top, width: right - left + 1, height: bottom - top + 1 };
}

async function cutOut(source: URL, target: URL, measureBoard: boolean): Promise<RenderInfo> {
	const { data, info } = await sharp(source.pathname)
		.ensureAlpha()
		.raw()
		.toBuffer({ resolveWithObject: true });

	const pixels = new Uint8Array(data.buffer, data.byteOffset, data.byteLength);
	const background = clearShadow(pixels, info.width, info.height);
	const crop = boundingBox(info.width, info.height, (index) => !background[index]);

	await sharp(pixels, { raw: { width: info.width, height: info.height, channels: 4 } })
		.extract({ left: crop.x, top: crop.y, width: crop.width, height: crop.height })
		.png()
		.toFile(target.pathname);

	if (!measureBoard) return { width: crop.width, height: crop.height };

	const board = boundingBox(info.width, info.height, (index) => {
		const offset = index * 4;
		const [red, green, blue] = [pixels[offset], pixels[offset + 1], pixels[offset + 2]];

		return (
			!background[index] &&
			green - red >= MASK_MIN_GREEN_LEAD &&
			green - blue >= MASK_MIN_GREEN_LEAD
		);
	});

	return {
		width: crop.width,
		height: crop.height,
		board: { ...board, x: board.x - crop.x, y: board.y - crop.y }
	};
}

// Names come from KiCad's plot file names, like board-In1_Cu.png or board-f_silkscreen.png.
function parseLayer(file: string) {
	const match = file.match(/^board-(F|B|In(\d+))_([a-z]+)\.png$/i);
	const kind = LAYER_KINDS.find((known) => known.toLowerCase() === match?.[3].toLowerCase());

	if (!match || !kind) throw new Error(`Unknown layer image ${file}`);

	const side = match[2] ? `In${match[2]}` : match[1].toUpperCase();
	const depth = match[2] ? Number(match[2]) : side === 'F' ? 0 : Number.MAX_SAFE_INTEGER;

	return { name: `${side}.${kind}`, rank: [LAYER_KINDS.indexOf(kind), depth] };
}

async function plotLayer(source: URL, target: URL): Promise<RenderInfo> {
	const { data, info } = await sharp(source.pathname)
		.removeAlpha()
		.raw()
		.toBuffer({ resolveWithObject: true });

	const { width, height } = info;

	const isWhite = (index: number) =>
		data[index * 3] >= PLOT_WHITE_MIN &&
		data[index * 3 + 1] >= PLOT_WHITE_MIN &&
		data[index * 3 + 2] >= PLOT_WHITE_MIN;

	const board = boundingBox(width, height, (index) => {
		const [red, green, blue] = data.subarray(index * 3, index * 3 + 3);

		return green < PLOT_WHITE_MIN && green >= red && red > blue && green - blue <= OUTLINE_MAX_TINT;
	});

	const margin = Math.round(Math.max(board.width, board.height) * LAYER_MARGIN);
	const left = Math.max(0, board.x - margin);
	const top = Math.max(0, board.y - margin);

	const crop = {
		x: left,
		y: top,
		width: Math.min(width, board.x + board.width + margin) - left,
		height: Math.min(height, board.y + board.height + margin) - top
	};

	for (let index = 0; index < width * height; index++) {
		if (isWhite(index)) data.set(SUBSTRATE_RGB, index * 3);
	}

	await sharp(data, { raw: { width, height, channels: 3 } })
		.extract({ left: crop.x, top: crop.y, width: crop.width, height: crop.height })
		.png()
		.toFile(target.pathname);

	return {
		width: crop.width,
		height: crop.height,
		board: { ...board, x: board.x - crop.x, y: board.y - crop.y }
	};
}

async function plotLayers(runId: string, runOut: URL): Promise<ReadonlyArray<LayerInfo>> {
	const source = new URL(`${runId}/renders/layers/`, RUNS_DIR);
	const target = new URL('layers/', runOut);
	await mkdir(target, { recursive: true });

	const layers = (await readdir(source))
		.map((file) => ({ source: file, ...parseLayer(file) }))
		.toSorted((a, b) => a.rank[0] - b.rank[0] || a.rank[1] - b.rank[1]);

	return Promise.all(
		layers.map(async ({ source: file, name }) => {
			const out = name.replace('.', '_');

			return {
				name,
				file: out,
				...(await plotLayer(new URL(file, source), new URL(`${out}.png`, target)))
			};
		})
	);
}

const renders: Record<string, RunRenders> = Object.fromEntries(
	await Promise.all(
		RUNS.map(async ({ id: runId }) => {
			const runOut = new URL(`${runId}/`, OUT_DIR);
			await mkdir(runOut, { recursive: true });

			return [
				runId,
				{
					...Object.fromEntries(
						await Promise.all(
							VIEWS.map(async (view) => [
								view,
								await cutOut(
									new URL(`${runId}/renders/${view}.png`, RUNS_DIR),
									new URL(`${view}.png`, runOut),
									view !== 'iso'
								)
							])
						)
					),
					layers: await plotLayers(runId, runOut)
				}
			];
		})
	)
);

await Bun.write(new URL('../renders.json', OUT_DIR), `${JSON.stringify(renders, null, '\t')}\n`);

console.log(`Cut out ${RUNS.length * VIEWS.length} renders and plotted layer images`);
