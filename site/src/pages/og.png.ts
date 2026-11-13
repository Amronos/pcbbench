import sharp, { type OverlayOptions } from 'sharp';
import { runs } from '../data/runs';

const WIDTH = 1200;
const HEIGHT = 630;
const MARGIN = 56;
const GAP = 40;
const PER_ROW = 4;

// Every board's top render at one shared px per mm, in rank order, on KiCad's canvas color.
export async function GET() {
	const boards = runs.map((run) => {
		const { image, pxPerMm } = run.renders.top;

		return {
			file: `${process.cwd()}/src/generated/renders/${run.id}-top.png`,
			widthMm: image.width / pxPerMm,
			heightMm: image.height / pxPerMm
		};
	});

	const rows = Array.from({ length: Math.ceil(boards.length / PER_ROW) }, (_, index) =>
		boards.slice(index * PER_ROW, (index + 1) * PER_ROW)
	);

	const rowWidthMm = rows.map((row) => row.reduce((total, board) => total + board.widthMm, 0));
	const rowHeightMm = rows.map((row) => Math.max(...row.map((board) => board.heightMm)));

	const scale = Math.min(
		...rows.map((row, index) => (WIDTH - 2 * MARGIN - (row.length - 1) * GAP) / rowWidthMm[index]),
		(HEIGHT - 2 * MARGIN - (rows.length - 1) * GAP) /
			rowHeightMm.reduce((total, height) => total + height, 0)
	);

	const usedHeight =
		rowHeightMm.reduce((total, height) => total + height * scale, 0) + (rows.length - 1) * GAP;

	let top = (HEIGHT - usedHeight) / 2;
	const layers: OverlayOptions[] = [];

	for (const [index, row] of rows.entries()) {
		const rowHeight = rowHeightMm[index] * scale;
		let left = (WIDTH - rowWidthMm[index] * scale - (row.length - 1) * GAP) / 2;

		for (const board of row) {
			const width = Math.round(board.widthMm * scale);
			const height = Math.round(board.heightMm * scale);

			layers.push({
				input: await sharp(board.file).resize(width, height).toBuffer(),
				left: Math.round(left),
				top: Math.round(top + (rowHeight - height) / 2)
			});
			left += width + GAP;
		}

		top += rowHeight + GAP;
	}

	const png = await sharp({
		create: { width: WIDTH, height: HEIGHT, channels: 3, background: '#061423' }
	})
		.composite(layers)
		.png()
		.toBuffer();

	return new Response(new Uint8Array(png), { headers: { 'Content-Type': 'image/png' } });
}
