import { $ } from 'bun';
import { mkdir } from 'node:fs/promises';

// KiCad names each plotted file after its layer, as in board-F_Cu.gbr or board-PTH.drl.
const LAYER_IN_FILE_NAME = /[-_](F_Cu|B_Cu|In\d+_Cu|[FB]_Mask|[FB]_Paste|[FB]_Silkscreen|Edge_Cuts|N?PTH)\.\w+$/i;
const DPI = 1000;
// About 50 µm at 1000 dpi; absorbs the rounding when two exports place the same edge a pixel apart.
const TOLERANCE = 'Disk:2';
const MAX_DIFF_PERCENT = 0.1;

const layerName = (token: string) =>
	/^n?pth$/i.test(token)
		? token.toUpperCase()
		: token
				.toLowerCase()
				.split('_')
				.map((word) => word[0]!.toUpperCase() + word.slice(1))
				.join('.');

async function layerFiles(dir: string) {
	const files = await Array.fromAsync(new Bun.Glob('**/*').scan({ cwd: dir, absolute: true }));
	return new Map(
		files.flatMap((file) => {
			const token = file.match(LAYER_IN_FILE_NAME)?.[1];
			return token ? [[layerName(token), file] as const] : [];
		})
	);
}

const litPixels = async (...args: string[]) => Number(await $`convert ${args} -format ${'%[fx:mean*w*h]'} info:`.text());
// Pixels drawn in one image that the other doesn't cover, even after growing it by the tolerance.
const uncovered = (image: string, other: string) => litPixels(image, '(', other, '-morphology', 'Dilate', TOLERANCE, ')', '-compose', 'Minus_Src', '-composite');

// The layer is drawn green and the outline red, so each image is framed by its own board outline whatever origin the export used.
// gerbv's PNG export paints clear-polarity objects (as in --subtract-soldermask) in the ink color; its SVG paints them white.
// Pixels that are green but not red are the layer's ink.
async function renderLayer(layer: string, edgeCuts: string, out: string) {
	await $`gerbv -x svg -D ${DPI} -b ${'#000000'} -f ${'#00FF00FF'} -f ${'#FF0000FF'} -o ${out}.svg ${layer} ${edgeCuts}`.quiet();
	await $`rsvg-convert -b black -o ${out} ${out}.svg`.quiet();
	await $`convert ${out} -channel RG -separate +channel -compose Minus_Dst -composite -threshold 50% ${out}`.quiet();
	const [width = 0, height = 0] = (await $`identify -format "%w %h" ${out}`.text()).split(' ').map(Number);
	return { width, height };
}

export async function matchFab(kicadCli: string, board: string, fabZip: string, expectedLayers: string[], work: string) {
	const [delivered, reexported] = [`${work}/delivered`, `${work}/reexported`];
	await mkdir(reexported, { recursive: true });
	await $`unzip -q -o ${fabZip} -d ${delivered}`;
	const deliveredFiles = await layerFiles(delivered);
	const useAuxOrigin = (await Bun.file(board).text()).includes('(useauxorigin yes)');
	// The board's own plot settings, so options such as reference designators on silkscreen match the agent's export.
	// Zones are refilled because saved fills can be stale, and the delivered files should match the design.
	await $`${kicadCli} pcb export gerbers --board-plot-params --check-zones -o ${reexported}/ ${board}`.quiet();
	// gerbv draws routed slots and G85 slots differently, so slots use the delivered file's format.
	const deliveredPth = deliveredFiles.get('PTH');
	const ovalFormat = deliveredPth && /^M15$/m.test(await Bun.file(deliveredPth).text()) ? 'route' : 'alternate';
	await $`${kicadCli} pcb export drill --excellon-separate-th --excellon-oval-format ${ovalFormat} --drill-origin ${useAuxOrigin ? 'plot' : 'absolute'} -u mm -o ${reexported}/ ${board}`.quiet();
	let reexportedFiles = await layerFiles(reexported);
	const unplotted = [...new Set([...expectedLayers, ...deliveredFiles.keys()])].filter((layer) => !reexportedFiles.has(layer) && !layer.endsWith('PTH'));
	if (unplotted.length) {
		await $`${kicadCli} pcb export gerbers --check-zones ${useAuxOrigin ? ['--use-drill-file-origin'] : []} -l ${unplotted.join(',')} -o ${reexported}/ ${board}`.quiet();
		reexportedFiles = await layerFiles(reexported);
	}

	const diffPercentByLayer: Record<string, number> = {};
	const [a, b] = [`${work}/delivered.png`, `${work}/reexported.png`];
	for (const [layer, file] of deliveredFiles) {
		const reference = reexportedFiles.get(layer);
		if (!reference) continue;
		const sizes = [await renderLayer(file, deliveredFiles.get('Edge.Cuts')!, a), await renderLayer(reference, reexportedFiles.get('Edge.Cuts')!, b)];
		const extent = ['-background', 'black', '-gravity', 'NorthWest', '-extent', `${Math.max(...sizes.map((size) => size.width))}x${Math.max(...sizes.map((size) => size.height))}`];
		await $`convert ${a} ${extent} ${a}`.quiet();
		await $`convert ${b} ${extent} ${b}`.quiet();
		const drawn = await litPixels(a, b, '-compose', 'Lighten', '-composite');
		diffPercentByLayer[layer] = drawn ? Math.round((((await uncovered(a, b)) + (await uncovered(b, a))) / drawn) * 10000) / 100 : 0;
	}
	return {
		diffPercentByLayer,
		layersDiffering: Object.keys(diffPercentByLayer).filter((layer) => diffPercentByLayer[layer]! > MAX_DIFF_PERCENT),
		layersMissing: expectedLayers.filter((layer) => !deliveredFiles.has(layer))
	};
}
