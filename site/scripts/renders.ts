// Cuts the drop shadow out of each run's KiCad renders and measures where the board sits in
// the top and bottom views, so the site can draw boards at true scale.
import { mkdir, readdir } from 'node:fs/promises';
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

await mkdir(OUT_DIR, { recursive: true });

const runIds = (await readdir(RUNS_DIR, { withFileTypes: true }))
	.filter((entry) => entry.isDirectory())
	.map((entry) => entry.name);

const renders = Object.fromEntries(
	await Promise.all(
		runIds.map(async (runId) => [
			runId,
			Object.fromEntries(
				await Promise.all(
					VIEWS.map(async (view) => [
						view,
						await cutOut(
							new URL(`${runId}/renders/${view}.png`, RUNS_DIR),
							new URL(`${runId}-${view}.png`, OUT_DIR),
							view !== 'iso'
						)
					])
				)
			)
		])
	)
);

await Bun.write(new URL('../renders.json', OUT_DIR), `${JSON.stringify(renders, null, '\t')}\n`);

console.log(`Cut out ${runIds.length * VIEWS.length} renders`);
