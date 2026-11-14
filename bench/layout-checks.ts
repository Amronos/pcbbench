import { Match, Record } from 'effect';
import type { Copper, Footprint, Point } from './board.ts';
import { refsMatching } from './bom.ts';
import type { CheckedRun, Features } from './check.ts';
import {
	arcThrough,
	boundingBox,
	distance,
	isInside,
	polygonsOverlap,
	segmentToPolygon
} from './geometry.ts';
import {
	isGround,
	isResistor,
	isTwoTerminal,
	onNet,
	otherNet,
	rp2350Pin,
	terminals
} from './netlist.ts';

// Raspberry Pi's RP2350A Minimal reference design (RP-010328) puts a 3×3 grid of vias in the pad; neither RP2350 PDF gives a count.
const RP2350_THERMAL_VIAS = 9;

// Vias drawn in the thermal pad of each package's TI land pattern: RGT0016C, DRC0010J and DSC0010.
const THERMAL_VIAS: [RegExp, number][] = [
	[/\bBQ2407\d\w*RGT/i, 5],
	[/\bTPS6300[0-2]DRC/i, 4],
	[/\bTPS6306[0-2]DSC/i, 5]
];

const QSPI_PIN = /^QSPI_(SCLK|SS|SD[0-3])$/;
const SAMPLE_MM = 0.1;

// PCBWay capabilities: "Minimum Character Height (Legend) 0.8mm".
const MIN_TEXT_HEIGHT_MM = 0.8;

const fraction = (count: number, total: number) =>
	total ? Math.round((count / total) * 1000) / 1000 : 0;

const mm = (value: number) => Math.round(value * 10) / 10;

const center = (points: Point[]) => {
	const [topLeft, , bottomRight] = boundingBox(points);

	return { x: (topLeft!.x + bottomRight!.x) / 2, y: (topLeft!.y + bottomRight!.y) / 2 };
};

const partSide = (part: Footprint) => (part.side === 'top' ? 'F' : 'B');

// The copper pads under the middle of the package, which is where an exposed pad sits.
function exposedPad(part: Footprint) {
	const numbered = terminals(part);
	const middle = center(numbered);

	const copper = numbered.filter(
		(pad) => pad.type === 'smd' && pad.layers.some((layer) => layer.endsWith('.Cu'))
	);

	const pad = copper.find((candidate) => isInside(middle, candidate.outline));

	return pad ? copper.filter((other) => other.number === pad.number && other.net === pad.net) : [];
}

function checkThermal({ rp2350s, fittedLines, byReference, copper }: CheckedRun) {
	const rated = [
		...rp2350s.map((part) => ({ part, minVias: RP2350_THERMAL_VIAS })),
		...THERMAL_VIAS.flatMap(([pattern, minVias]) =>
			refsMatching(fittedLines, pattern)
				.flatMap((ref) => byReference.get(ref) ?? [])
				.map((part) => ({ part, minVias }))
		)
	];

	const pads = rated.flatMap(({ part, minVias }) => {
		const pieces = exposedPad(part);

		if (!pieces.length) return [];
		const { net } = pieces[0]!;
		const layer = `${partSide(part)}.Cu`;

		const touches = (point: Point, radius: number) =>
			pieces.some((piece) => segmentToPolygon(point, point, piece.outline) <= radius);

		const vias =
			copper.vias.filter((via) => via.net === net && touches(via, via.size / 2)).length +
			part.pads.filter(
				(other) => other.type === 'thru_hole' && other.net === net && touches(other, 0)
			).length;

		const planeOnOtherLayer = copper.zones.some(
			(zone) =>
				zone.net === net &&
				zone.fills.some(
					(fill) =>
						fill.layer !== layer &&
						pieces.some((piece) => polygonsOverlap(fill.outline, piece.outline))
				)
		);

		return [
			{
				ref: part.ref,
				net,
				vias,
				minVias,
				planeOnOtherLayer,
				share: planeOnOtherLayer ? Math.min(1, vias / minVias) : 0
			}
		];
	});

	return {
		fraction: fraction(
			pads.reduce((sum, pad) => sum + pad.share, 0),
			pads.length
		),
		pads
	};
}

// Physical order from the top: F.Cu, In1.Cu, In2.Cu, ..., B.Cu.
const depth = (layer: string) =>
	Match.value(layer).pipe(
		Match.when('F.Cu', () => 0),
		Match.when('B.Cu', () => Infinity),
		Match.orElse(() => Number(layer.match(/\d+/)?.[0]))
	);

function samples({ start, mid, end }: Copper['tracks'][number]) {
	const path = mid ? arcThrough(start, mid, end) : [start, end];

	return path.slice(1).flatMap((to, i) => {
		const from = path[i]!;
		const steps = Math.max(1, Math.ceil(distance(from, to) / SAMPLE_MM));

		return Array.from({ length: steps }, (_, step) => ({
			x: from.x + ((to.x - from.x) * (step + 0.5)) / steps,
			y: from.y + ((to.y - from.y) * (step + 0.5)) / steps,
			mm: distance(from, to) / steps
		}));
	});
}

function checkGrounding(
	{ footprints, copper, copperLayers, rp2350s, byReference }: CheckedRun,
	features: Features,
	usbNets: string[]
) {
	const stack = copperLayers.toSorted((a, b) => depth(a) - depth(b));

	// An outer layer's return current runs on the next layer in; an inner layer's on whichever neighbor is ground.
	const references = (layer: string) => {
		const index = stack.indexOf(layer);

		return [stack[index - 1], stack[index + 1]].filter((neighbor) => neighbor !== undefined);
	};

	const isPower = (net: string) =>
		isGround(net) ||
		footprints.some(
			(footprint) =>
				isTwoTerminal(footprint, 'C') &&
				onNet(footprint, net) &&
				footprint.pads.some((pad) => isGround(pad.net))
		);

	const onChip = (net: string) =>
		footprints.some((footprint) => /^U\d/.test(footprint.ref) && onNet(footprint, net));

	// Signal nets plus the far side of any series resistor that leads on to another chip.
	const signals = (nets: string[]) => {
		const own = nets.filter((net) => net && !isPower(net));

		const beyond = own.flatMap((net) =>
			footprints
				.filter((footprint) => isResistor(footprint) && onNet(footprint, net))
				.map((resistor) => otherNet(resistor, net))
				.filter((other) => onChip(other) && !isPower(other))
		);

		return [...new Set([...own, ...beyond])];
	};

	const buses = {
		usb: usbNets,
		qspi: signals(
			rp2350s.flatMap((part) =>
				part.pads.filter((pad) => QSPI_PIN.test(rp2350Pin(pad))).map((pad) => pad.net)
			)
		),
		microSd: signals(
			features.microSd.refs.flatMap((ref) => byReference.get(ref)?.pads.map((pad) => pad.net) ?? [])
		)
	};

	const groundFills = copper.zones
		.filter((zone) => isGround(zone.net))
		.flatMap((zone) => zone.fills)
		.map((fill) => ({ ...fill, box: boundingBox(fill.outline) }));

	const overGround = (point: Point, layers: string[]) =>
		groundFills.some(
			({ layer: fillLayer, box: [topLeft, , bottomRight], outline }) =>
				layers.includes(fillLayer) &&
				point.x >= topLeft!.x &&
				point.x <= bottomRight!.x &&
				point.y >= topLeft!.y &&
				point.y <= bottomRight!.y &&
				isInside(point, outline)
		);

	const measured = Record.map(buses, (nets) => {
		let [total, grounded] = [0, 0];

		for (const track of copper.tracks.filter((track) => nets.includes(track.net))) {
			const layers = references(track.layer);

			for (const sample of samples(track)) {
				total += sample.mm;

				if (overGround(sample, layers)) grounded += sample.mm;
			}
		}

		return { nets, mm: mm(total), groundedMm: mm(grounded) };
	});

	const sum = (key: 'mm' | 'groundedMm') =>
		Object.values(measured).reduce((total, bus) => total + bus[key], 0);

	return { fraction: fraction(sum('groundedMm'), sum('mm')), ...measured };
}

// Only text height is checked: PCBWay clips the legend off exposed copper, and reference designators are left off on purpose.
function checkSilkscreen({ footprints, silkscreen }: CheckedRun) {
	const texts = [...silkscreen, ...footprints.flatMap((footprint) => footprint.silkscreen)];
	const legible = texts.filter((text) => text.height >= MIN_TEXT_HEIGHT_MM);

	return {
		fraction: fraction(legible.length, texts.length),
		minTextHeightMm: MIN_TEXT_HEIGHT_MM,
		texts: texts.length,
		textsBelowMin: texts.length - legible.length,
		smallestTextMm: texts.length ? Math.min(...texts.map((text) => text.height)) : null
	};
}

export function checkLayout(run: CheckedRun, features: Features, usbNets: string[]) {
	return {
		thermal: checkThermal(run),
		grounding: checkGrounding(run, features, usbNets),
		silkscreen: checkSilkscreen(run)
	};
}
