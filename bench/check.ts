import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Effect, FileSystem, Layer, Record, Schema } from 'effect';
import { Command } from 'effect/cli';
import {
	byRef,
	readMetrics,
	readRun,
	updateMetrics,
	type Copper,
	type Footprint,
	type Point
} from './board.ts';
import { isSamePart, parseCsv, readBom, refsMatching, splitRefs } from './bom.ts';
import { Digikey, type DigikeyError } from './digikey.ts';
import { checkGates } from './gates.ts';
import {
	boundingBox,
	cross,
	distance,
	dot,
	EDGE_MM,
	isDeepInside,
	polygonsOverlap,
	segmentToPolygon,
	sub,
	trackLength
} from './geometry.ts';
import { Jlcpcb } from './jlcpcb.ts';
import { checkLayout } from './layout-checks.ts';
import { Lcsc, type LcscError } from './lcsc.ts';
import {
	isGround,
	isResistor,
	isTwoTerminal,
	onNet,
	otherNet,
	rp2350Pin,
	terminals
} from './netlist.ts';
import { Fix } from './price.ts';
import { BATCH_BOARDS, runIdArgument } from './runs.ts';

const PLACEMENT_TOLERANCE_MM = 0.5;

const SUPPLIERS: {
	name: string;
	column: RegExp;
	isNumberFor: (
		number: string,
		mpn: string
	) => Effect.Effect<boolean, LcscError | DigikeyError, Lcsc | Digikey>;
}[] = [
	{
		name: 'LCSC',
		column: /lcsc/i,
		isNumberFor: Effect.fnUntraced(function* (number: string, mpn: string) {
			const code = number.match(/\bC\d+\b/)?.[0];
			const product = code ? yield* Lcsc.use((lcsc) => lcsc.productByCode(code)) : null;

			return !!product && isSamePart(mpn, product.productModel);
		})
	},
	{
		name: 'Digi-Key',
		column: /digi-?key/i,
		isNumberFor: (number, mpn) => Digikey.use((digikey) => digikey.isNumberFor(number, mpn))
	},
	// There's no Mouser lookup, so any Mouser number counts.
	{ name: 'Mouser', column: /mouser/i, isNumberFor: () => Effect.succeed(true) }
];

// Matched against MPNs. Raspberry Pi also sells its chips under SC order codes.
const FEATURES = {
	rp2350: /\b(RP235[04]|SC151[0-2]|SC1509)/i,
	qspiFlash: /\b(W25Q|GD25|IS25[LW]P|AT25SF|MX25|S25FL|PY25|ZB25|BY25)/i,
	psram: /\b(APS6404|APS1604|LY68L|IPS6404|ESP-PSRAM)/i,
	usbC: /\b(TYPE-C|USB4105|USB4085|USB4110|GCT-USB4)/i,
	wifiBle: /\b(RMC20452|SC1169|CYW43439|ESP32-(C3|C5|C6|C61|S3)|ESP32-WROOM-32|NINA-W1)/i,
	microSd: /\b(104031|DM3AT|MEM2051|MEM2067|TF-01A)/i,
	qwiic: /\b[SB]M04B-SRSS/i,
	rgbLed: /\b(WS281[0-9]|SK6812|SK6805|APA102|SK9822|XL-\d+RGBC-WS|LC8812|IN-PI)/i
};

const POWER_PATH_CHARGERS =
	/\b(BQ2407[2-9]|BQ2423[0-2]|BQ2510[01]|BQ2512|BQ2515|BQ2518|BQ2560|BQ2561|BQ2562|BQ2589|BQ2429[5-7]|BQ2419|BQ21080|MCP73871|LTC4085|LTC4067|LTC4089|LTC4155|SGM4151)/i;

const FUEL_GAUGES = /\b(MAX1704|MAX1720|BQ27\d|LC709203|STC3100|CW201)/i;
const BATTERY_NET = /BAT|LIPO|CELL/i;

const POWER_PINS = [
	'IOVDD',
	'DVDD',
	'QSPI_IOVDD',
	'USB_OTP_VDD',
	'ADC_AVDD',
	'VREG_VIN',
	'VREG_AVDD'
];

// Hardware design with RP2350 only asks for decoupling "close to the power pins". Its Minimal board, whose capacitors it
// calls "slightly further away from the chip than is optimal", has one within 3.2 mm of every power pin, pad center to pad center.
const DECOUPLING_MAX_MM = 3.2;
const BATTERY_FULL_VOLTS = 4.2;

// D+ and D- segments further apart than this don't count as running side by side.
const PAIR_GAP_MAX_MM = 2;

const CheckedMetrics = Schema.Struct({
	fixes: Schema.Array(Fix),
	drc: Schema.Struct({ errors: Schema.Number, unconnectedItems: Schema.Number }),
	fab: Schema.Struct({
		layersDiffering: Schema.Array(Schema.String),
		layersMissing: Schema.Array(Schema.String)
	})
});

const PricedLines = Schema.fromJsonString(
	Schema.Array(
		Schema.Struct({
			refs: Schema.String,
			qty: Schema.Number,
			mpn: Schema.String,
			source: Schema.String
		})
	)
);

class CheckError extends Schema.TaggedError<CheckError>()('CheckError', {
	message: Schema.String
}) {}

const percent = (count: number, total: number) => Math.round((count / total) * 1000) / 10;
const round = (value: number, places = 2) => Math.round(value * 10 ** places) / 10 ** places;
const hasValue = (cell = '') => /\w/.test(cell) && !/^(n\/?a|none|-)$/i.test(cell);

const readCheckedRun = Effect.fn('readCheckedRun')(function* (runId: string) {
	const run = yield* readRun(runId);

	const { fixes, drc, fab } = yield* readMetrics(runId, CheckedMetrics).pipe(
		Effect.catchTag('SchemaError', () =>
			Effect.fail(new CheckError({ message: `Run inspect.ts and price.ts on ${runId} first` }))
		)
	);

	const output = `${run.runDir}/output`;
	const bom = yield* readBom(`${output}/${run.info.bom}`);
	const byReference = new Map(run.footprints.map((footprint) => [footprint.ref, footprint]));

	const rp2350s = refsMatching(bom.lines, FEATURES.rp2350).flatMap(
		(ref) => byReference.get(ref) ?? []
	);

	const adcPinNets = new Set(
		run.footprints.flatMap((footprint) =>
			footprint.pads.flatMap((pad) =>
				/ADC\d/i.test(rp2350s.includes(footprint) ? rp2350Pin(pad) : pad.pinFunction)
					? [pad.net]
					: []
			)
		)
	);

	// Some boards isolate the ADC pin from the divider with a transistor, so its non-gate pads also carry the midpoint.
	const adcNets = new Set([
		...adcPinNets,
		...run.footprints.flatMap((footprint) =>
			/^Q\d/.test(footprint.ref) && footprint.pads.some((pad) => adcPinNets.has(pad.net))
				? footprint.pads.filter((pad) => !/^G/i.test(pad.pinFunction)).map((pad) => pad.net)
				: []
		)
	]);

	return {
		...run,
		output,
		bom,
		fittedLines: bom.lines.filter((line) => line.fitted),
		byReference,
		fixes,
		fixedBomLines: new Set(fixes.flatMap((fix) => (fix.area === 'bom' ? [fix.refs] : []))),
		drc,
		fab,
		rp2350s,
		adcNets
	};
});

export type CheckedRun = Effect.Success<ReturnType<typeof readCheckedRun>>;

function checkBom({ bom, parts, byReference, fixedBomLines }: CheckedRun) {
	const bomRefs = new Set(bom.lines.flatMap((line) => splitRefs(line.refs)));

	return {
		lines: bom.lines.length,
		partsNotInBom: parts.map((part) => part.ref).filter((ref) => !bomRefs.has(ref)),
		refsNotOnBoard: [...bomRefs].filter((ref) => !byReference.has(ref)).sort(byRef),
		qtyMismatchLines: bom.lines
			.filter((line) => line.qty !== splitRefs(line.refs).length)
			.map((line) => line.refs),
		linesWithoutMpn: bom.lines.filter((line) => line.fitted && !line.mpn).length,
		linesFixed: fixedBomLines.size
	};
}

const checkSuppliers = Effect.fn('checkSuppliers')(function* ({ bom, fittedLines }: CheckedRun) {
	const validBySupplier: Record<string, number> = Object.fromEntries(
		SUPPLIERS.map(({ name }) => [name, 0])
	);

	const invalid = [];
	let linesWithValidNumber = 0;

	for (const line of fittedLines) {
		let hasValid = false;

		for (const { name, column, isNumberFor } of SUPPLIERS) {
			const number = line.row[bom.column(column)] ?? '';

			if (!hasValue(number)) continue;

			if (yield* isNumberFor(number, line.mpn)) {
				hasValid = true;
				validBySupplier[name] = (validBySupplier[name] ?? 0) + 1;
			} else invalid.push({ refs: line.refs, mpn: line.mpn, supplier: name, number });
		}

		if (hasValid) linesWithValidNumber++;
	}

	return {
		lines: fittedLines.length,
		validPercent: Object.fromEntries(
			Object.entries(validBySupplier).map(([name, count]) => [
				name,
				percent(count, fittedLines.length)
			])
		),
		linesWithValidNumber,
		invalid
	};
});

type Placed = { ref: string; x: number; y: number; rotation: number; side: 'top' | 'bottom' };

const readPlacement = Effect.fn('readPlacement')(function* ({ output, info }: CheckedRun) {
	const [header = [], ...rows] = parseCsv(
		yield* (yield* FileSystem.FileSystem).readFileString(`${output}/${info.placement}`)
	);

	const column = (pattern: RegExp) => header.findIndex((name) => pattern.test(name));

	const columns = {
		ref: column(/designator|^ref(erence)?$/i),
		x: column(/^(mid|pos|center|centre)?[ _-]?x(\b|_)/i),
		y: column(/^(mid|pos|center|centre)?[ _-]?y(\b|_)/i),
		rotation: column(/^rot/i),
		side: column(/layer|side|^tb$/i)
	};

	if (Object.values(columns).some((index) => index < 0))
		return yield* new CheckError({
			message: `Unrecognized placement columns in ${info.placement}: ${header.join(',')}`
		});

	const mmPer = /mil/i.test(header[columns.x]!)
		? 0.0254
		: /\bin(ch)?\b/i.test(header[columns.x]!)
			? 25.4
			: 1;

	const number = (cell = '') => parseFloat(cell.replace(/[^\d.eE+-]/g, ''));

	return rows.map((row): Placed => ({
		ref: row[columns.ref]!,
		x: number(row[columns.x]) * (/mil/i.test(row[columns.x] ?? '') ? 0.0254 : mmPer),
		y: number(row[columns.y]) * (/mil/i.test(row[columns.y] ?? '') ? 0.0254 : mmPer),
		rotation: number(row[columns.rotation]),
		side: /^(b|bot|bottom|back)$/i.test(row[columns.side] ?? '') ? 'bottom' : 'top'
	}));
});

const median = (values: number[]) =>
	values.toSorted((a, b) => a - b)[Math.floor(values.length / 2)] ?? 0;

// Where the part's pads are centered; placement files may use this instead of the footprint origin.
const padCenter = ({ pads, x, y }: Footprint) => {
	if (!pads.length) return { x, y };
	const xs = pads.map((pad) => pad.x);
	const ys = pads.map((pad) => pad.y);

	return { x: (Math.min(...xs) + Math.max(...xs)) / 2, y: (Math.min(...ys) + Math.max(...ys)) / 2 };
};

// Placement files use their own origin and axis directions, so each side gets the axis signs and offset that fit best.
function fitSide(pairs: { placed: Placed; footprint: Footprint }[]) {
	let best = { deviations: new Map<string, number>(), score: Infinity };

	for (const xSign of [1, -1]) {
		for (const ySign of [1, -1]) {
			const dx = median(pairs.map(({ placed, footprint }) => placed.x - xSign * footprint.x));
			const dy = median(pairs.map(({ placed, footprint }) => placed.y - ySign * footprint.y));

			const deviations = new Map(
				pairs.map(({ placed, footprint }) => {
					const distance = (point: { x: number; y: number }) =>
						Math.hypot(placed.x - (xSign * point.x + dx), placed.y - (ySign * point.y + dy));

					return [placed.ref, Math.min(distance(footprint), distance(padCenter(footprint)))];
				})
			);

			const score = median([...deviations.values()]);

			if (score < best.score) best = { deviations, score };
		}
	}

	return best.deviations;
}

const checkPlacement = Effect.fn('checkPlacement')(function* (run: CheckedRun) {
	const { parts, byReference } = run;
	const placed = yield* readPlacement(run);
	const placedRefs = placed.map((entry) => entry.ref);

	const pairs = placed.flatMap((entry) => {
		const footprint = byReference.get(entry.ref);

		return footprint ? [{ placed: entry, footprint }] : [];
	});

	const deviations = new Map([
		...fitSide(pairs.filter((pair) => pair.footprint.side === 'top')),
		...fitSide(pairs.filter((pair) => pair.footprint.side === 'bottom'))
	]);

	const normalize = (degrees: number) => ((round(degrees, 1) % 360) + 360) % 360;

	return {
		// PCBWay only needs surface-mount parts in the placement file.
		smdPartsMissing: parts
			.filter((part) => part.smd && !placedRefs.includes(part.ref))
			.map((part) => part.ref),
		refsNotOnBoard: placedRefs.filter((ref) => !byReference.has(ref)).sort(byRef),
		duplicateRefs: [
			...new Set(placedRefs.filter((ref, index) => placedRefs.indexOf(ref) !== index))
		].sort(byRef),
		wrongSide: pairs
			.filter(({ placed, footprint }) => placed.side !== footprint.side)
			.map(({ placed }) => placed.ref),
		positionOffByMoreThanHalfMm: [...deviations].flatMap(([ref, mm]) =>
			mm > PLACEMENT_TOLERANCE_MM ? [{ ref, mm: round(mm) }] : []
		),
		rotationDiffersFromBoard: pairs
			.filter(
				({ placed, footprint }) => normalize(placed.rotation) !== normalize(footprint.rotation)
			)
			.map(({ placed }) => placed.ref)
	};
});

// Libraries differ in whether repeated contacts share a number and whether thermal vias count as pads, so either count may match.
const padCounts = (numbers: string[]) => ({ total: numbers.length, unique: new Set(numbers).size });

const checkParts = Effect.fn('checkParts')(function* ({ runDir, byReference }: CheckedRun) {
	const [lcsc, jlcpcb, digikey] = [yield* Lcsc, yield* Jlcpcb, yield* Digikey];

	const priced = yield* Schema.decodeEffect(PricedLines)(
		yield* (yield* FileSystem.FileSystem).readFileString(`${runDir}/components-pricing.json`)
	);

	const notStocked = [];
	const discontinued = [];
	const padCountMismatches = [];

	for (const line of priced) {
		const needed = line.qty * BATCH_BOARDS;
		const code = line.source.match(/^LCSC (C\d+)$/)?.[1] ?? null;
		const product = code ? yield* lcsc.productByCode(code) : null;

		if (code && !product) return yield* new CheckError({ message: `LCSC has no ${code}` });
		const lcscStock = product?.stockNumber ?? 0;
		const jlcpcbStock = yield* jlcpcb.stock(line.mpn, code);
		const digikeyPart = yield* digikey.part(line.mpn);

		if (Math.max(lcscStock, jlcpcbStock, digikeyPart.stock) < needed)
			notStocked.push({
				refs: line.refs,
				mpn: line.mpn,
				lcsc: code,
				lcscStock,
				jlcpcbStock,
				digikeyStock: digikeyPart.stock,
				needed
			});

		const discontinuedAt = [
			...(product?.productCycle === 'stop_product' ? ['LCSC'] : []),
			...(digikeyPart.discontinued ? ['Digi-Key'] : [])
		];

		if (discontinuedAt.length)
			discontinued.push({ refs: line.refs, mpn: line.mpn, lcsc: code, discontinuedAt });

		if (!product) continue;
		const supplierNumbers = yield* lcsc.footprintPadNumbers(product);

		if (!supplierNumbers.length) continue;
		const supplierPads = padCounts(supplierNumbers);

		// Connector libraries disagree on whether shield tabs and doubled contacts are separate pads.
		for (const ref of splitRefs(line.refs).filter((ref) => !ref.startsWith('J'))) {
			const footprintPads = padCounts(
				byReference
					.get(ref)
					?.pads.map((pad) => pad.number)
					.filter(Boolean) ?? []
			);

			if (
				footprintPads.total !== supplierPads.total &&
				footprintPads.unique !== supplierPads.unique
			) {
				padCountMismatches.push({
					ref,
					mpn: line.mpn,
					lcsc: code,
					package: product.encapStandard,
					footprintPads,
					supplierFootprintPads: supplierPads
				});
			}
		}
	}

	return {
		lines: priced.length,
		inStockPercent: percent(priced.length - notStocked.length, priced.length),
		notStocked,
		discontinued,
		padCountMismatches
	};
});

type Checks = {
	bom: ReturnType<typeof checkBom>;
	placement: Effect.Success<ReturnType<typeof checkPlacement>>;
	parts: Effect.Success<ReturnType<typeof checkParts>>;
};

function needsFixes(
	{ bom, fittedLines, fixes, fixedBomLines, drc, fab }: CheckedRun,
	{ bom: bomCheck, placement, parts: partsCheck }: Checks
) {
	const fixesIn = (...areas: Fix['area'][]) =>
		fixes.flatMap((fix) =>
			areas.includes(fix.area) ? [fix.refs ? `${fix.refs}: ${fix.problem}` : fix.problem] : []
		);

	const listed = (label: string, refs: ReadonlyArray<string>) =>
		refs.length ? [`${label}: ${refs.join('; ')}`] : [];

	const placementRefs = {
		...placement,
		positionOffByMoreThanHalfMm: placement.positionOffByMoreThanHalfMm.map(({ ref }) => ref)
	};

	const refsNeedingFixes = new Set([
		...[...fixedBomLines].flatMap((refs) => splitRefs(refs ?? '')),
		...partsCheck.notStocked.flatMap((line) => splitRefs(line.refs)),
		...partsCheck.padCountMismatches.map((mismatch) => mismatch.ref),
		...bom.lines
			.filter((line) => !line.mpn || bomCheck.qtyMismatchLines.includes(line.refs))
			.flatMap((line) => splitRefs(line.refs))
	]);

	return {
		fabNotes: fixesIn('fabSpec'),
		board: [
			...fixesIn('pcb'),
			...(drc.errors ? [`${drc.errors} DRC errors`] : []),
			...(drc.unconnectedItems ? [`${drc.unconnectedItems} unconnected items`] : []),
			...listed('fab layers differing from the board', fab.layersDiffering),
			...listed('fab layers missing', fab.layersMissing)
		],
		assembly: [
			...fixesIn('bom'),
			// Fixed lines are checked by their delivered MPN, which the fix replaces.
			...listed(
				`not stocked for ${BATCH_BOARDS} boards`,
				partsCheck.notStocked
					.filter((line) => !fixedBomLines.has(line.refs))
					.map((line) => line.refs)
			),
			...listed(
				'pad count differs from the part',
				partsCheck.padCountMismatches.map((mismatch) => mismatch.ref)
			),
			...listed('parts not in the BOM', bomCheck.partsNotInBom),
			...(bomCheck.linesWithoutMpn ? [`${bomCheck.linesWithoutMpn} BOM lines without an MPN`] : []),
			...listed('BOM lines with the wrong Qty', bomCheck.qtyMismatchLines),
			...Object.entries(placementRefs).flatMap(([problem, refs]) =>
				listed(`placement ${problem}`, refs)
			)
		],
		bomLines: {
			total: fittedLines.length,
			needingFixes: fittedLines
				.filter((line) => splitRefs(line.refs).some((ref) => refsNeedingFixes.has(ref)))
				.map((line) => line.refs)
		}
	};
}

function checkFeatures({ bom, footprints, adcNets }: CheckedRun) {
	const status = (refs: string[]) => ({ status: refs.length ? 'found' : 'needsReview', refs });

	// A divider: a resistor from a battery net to an ADC input.
	const dividers = footprints.filter(
		(footprint) =>
			/^R\d/.test(footprint.ref) &&
			footprint.pads.some((pad) => adcNets.has(pad.net)) &&
			footprint.pads.some((pad) => !adcNets.has(pad.net) && BATTERY_NET.test(pad.net))
	);

	return {
		...Record.map(FEATURES, (pattern) => status(refsMatching(bom.lines, pattern))),
		chargerWithPowerPath: status(refsMatching(bom.lines, POWER_PATH_CHARGERS)),
		batteryMonitoring: status(
			[...refsMatching(bom.lines, FUEL_GAUGES), ...dividers.map((divider) => divider.ref)].sort(
				byRef
			)
		)
	};
}

export type Features = ReturnType<typeof checkFeatures>;

function checkDecoupling({ footprints }: CheckedRun, rp2350: Footprint) {
	const capacitors = footprints.filter(
		(footprint) => isTwoTerminal(footprint, 'C') && footprint.pads.some((pad) => isGround(pad.net))
	);

	const pins = rp2350.pads
		.filter((pad) => POWER_PINS.includes(rp2350Pin(pad)))
		.map((pin) => {
			const [nearest] = capacitors
				.filter((capacitor) => onNet(capacitor, pin.net))
				.map((capacitor) => ({
					capacitor: capacitor.ref,
					mm: Math.min(...terminals(capacitor).map((pad) => distance(pad, pin)))
				}))
				.sort((a, b) => a.mm - b.mm);

			return {
				pin: rp2350Pin(pin),
				pad: pin.number,
				net: pin.net,
				capacitor: nearest?.capacitor ?? null,
				mm: nearest ? round(nearest.mm) : null
			};
		});

	return {
		maxMm: DECOUPLING_MAX_MM,
		pinsWithin: pins.filter((pin) => pin.mm !== null && pin.mm <= DECOUPLING_MAX_MM).length,
		powerPins: pins.length,
		pins
	};
}

const parseOhms = Effect.fnUntraced(function* (value: string) {
	const match = value.match(/^([\d.]+)\s*([RkKM]?)(\d*)/);

	if (!match) return yield* new CheckError({ message: `Can't read a resistance from "${value}"` });
	const [, whole, unit = '', fraction] = match;

	return (
		Number(fraction ? `${whole}.${fraction}` : whole) * ({ k: 1e3, K: 1e3, M: 1e6 }[unit] ?? 1)
	);
});

const checkBatteryDivider = Effect.fnUntraced(function* (
	{ footprints, byReference, adcNets }: CheckedRun,
	features: Features
) {
	const [gauges, found] = [
		features.batteryMonitoring.refs.filter((ref) => !/^R\d/.test(ref)),
		features.batteryMonitoring.refs.filter((ref) => /^R\d/.test(ref))
	];

	const chargers = features.chargerWithPowerPath.refs.flatMap((ref) => byReference.get(ref) ?? []);

	const batteryNets = new Set(
		chargers
			.flatMap((charger) => charger.pads.map((pad) => pad.net))
			.filter((net) => BATTERY_NET.test(net))
	);

	// A transistor or load switch between a battery net and the divider.
	const switchOf = (net: string) =>
		footprints.find(
			(footprint) =>
				/^[QU]\d/.test(footprint.ref) &&
				!chargers.includes(footprint) &&
				onNet(footprint, net) &&
				footprint.pads.some((pad) => batteryNets.has(pad.net))
		)?.ref ?? null;

	const dividerAt = (midpoint: string) => {
		const resistors = footprints.filter(
			(footprint) => isResistor(footprint) && onNet(footprint, midpoint)
		);

		const bottom = resistors.find((resistor) => isGround(otherNet(resistor, midpoint)));

		const top = resistors.find(
			(resistor) =>
				resistor !== bottom &&
				(batteryNets.has(otherNet(resistor, midpoint)) || switchOf(otherNet(resistor, midpoint)))
		);

		return top && bottom ? { top, bottom, source: otherNet(top, midpoint) } : null;
	};

	const dividers = yield* Effect.forEach(found, (ref) =>
		Effect.gen(function* () {
			const resistor = byReference.get(ref)!;
			const adcNet = resistor.pads.find((pad) => adcNets.has(pad.net))?.net ?? '';
			const direct = dividerAt(adcNet);

			// Some boards buffer the divider with an op-amp, and the resistor checkFeatures finds is on its output.
			const buffer = direct
				? null
				: footprints.find(
						(footprint) =>
							/^U\d/.test(footprint.ref) && onNet(footprint, otherNet(resistor, adcNet))
					);

			const divider =
				direct ??
				buffer?.pads.map((pad) => (isGround(pad.net) ? null : dividerAt(pad.net))).find(Boolean);

			if (!divider)
				return yield* new CheckError({ message: `No battery divider found around ${ref}` });

			const [topOhms, bottomOhms] = yield* Effect.all([
				parseOhms(divider.top.value),
				parseOhms(divider.bottom.value)
			]);

			return {
				top: divider.top.ref,
				bottom: divider.bottom.ref,
				topOhms,
				bottomOhms,
				bufferedBy: buffer?.ref ?? null,
				microampsAtFullCharge: round((BATTERY_FULL_VOLTS / (topOhms + bottomOhms)) * 1e6),
				switchedBy: batteryNets.has(divider.source) ? null : switchOf(divider.source)
			};
		})
	);

	return { fuelGauges: gauges, dividers };
});

// Edge-coupled differential impedance from the IPC-2141 closed forms, with h the dielectric to the nearest plane:
// microstrip Z0 = 87/√(εr+1.41)·ln(5.98h/(0.8w+t)) and Zdiff = 2·Z0·(1−0.48·e^(−0.96s/h)); stripline, between planes b apart,
// Z0 = 60/√εr·ln(4b/(0.67π(0.8w+t))) and Zdiff = 2·Z0·(1−0.347·e^(−2.9s/b)).
function differentialImpedance(
	stackup: Copper['stackup'],
	layer: string,
	width: number,
	gap: number
) {
	const index = stackup.findIndex((entry) => entry.name === layer);

	if (index < 0) return null;
	const thickness = stackup[index]!.thickness;

	const dielectricToPlane = (step: number) => {
		let h = 0;
		let hTimesEr = 0;

		for (let i = index + step; stackup[i]; i += step) {
			const entry = stackup[i]!;

			if (entry.type === 'copper') return { h, er: hTimesEr / h };

			if (['core', 'prepreg'].includes(entry.type)) {
				h += entry.thickness;
				hTimesEr += entry.thickness * entry.epsilonR;
			}
		}

		return null;
	};

	const [above, below] = [dielectricToPlane(-1), dielectricToPlane(1)];
	const effectiveWidth = 0.8 * width + thickness;

	if (above && below) {
		const b = above.h + below.h + thickness;
		const er = (above.er * above.h + below.er * below.h) / (above.h + below.h);

		return round(
			2 *
				(60 / Math.sqrt(er)) *
				Math.log((4 * b) / (0.67 * Math.PI * effectiveWidth)) *
				(1 - 0.347 * Math.exp((-2.9 * gap) / b)),
			1
		);
	}

	const plane = above ?? below;

	if (!plane) return null;

	return round(
		2 *
			(87 / Math.sqrt(plane.er + 1.41)) *
			Math.log((5.98 * plane.h) / effectiveWidth) *
			(1 - 0.48 * Math.exp((-0.96 * gap) / plane.h)),
		1
	);
}

const checkUsb = Effect.fnUntraced(function* (
	{ footprints, copper }: CheckedRun,
	rp2350: Footprint,
	connector: Footprint
) {
	const onConnector = (net: string) => onNet(connector, net);

	// The nets from the RP2350 pin to the connector, through a series resistor if there is one.
	const line = Effect.fnUntraced(function* (pin: string) {
		const net = rp2350.pads.find((pad) => rp2350Pin(pad) === pin)?.net ?? '';

		if (onConnector(net)) return [net];

		const series = footprints.find(
			(footprint) =>
				isResistor(footprint) && onNet(footprint, net) && onConnector(otherNet(footprint, net))
		);

		if (!series)
			return yield* new CheckError({
				message: `No series resistor from ${net} to ${connector.ref}`
			});

		return [otherNet(series, net), net];
	});

	const [plus, minus] = yield* Effect.all([line('USB_DP'), line('USB_DM')]);
	const tracksOn = (nets: string[]) => copper.tracks.filter((track) => nets.includes(track.net));

	const length = (nets: string[]) =>
		round(tracksOn(nets).reduce((sum, track) => sum + trackLength(track), 0));

	// Straight D+ and D- segments that run side by side, grouped by layer, width and gap.
	const coupled = new Map<
		string,
		{ layer: string; widthMm: number; gapMm: number; lengthMm: number }
	>();

	for (const a of tracksOn(plus).filter((track) => !track.mid)) {
		const direction = sub(a.end, a.start);
		const aLength = Math.hypot(direction.x, direction.y);

		if (!aLength) continue;
		const unit = { x: direction.x / aLength, y: direction.y / aLength };

		for (const b of tracksOn(minus).filter((track) => !track.mid && track.layer === a.layer)) {
			const bLength = distance(b.start, b.end);

			if (!bLength || Math.abs(cross(unit, sub(b.end, b.start))) / bLength > 0.02) continue;
			const gap = round(Math.abs(cross(unit, sub(b.start, a.start))) - (a.width + b.width) / 2);
			const along = [dot(unit, sub(b.start, a.start)), dot(unit, sub(b.end, a.start))];
			const overlap = Math.min(aLength, Math.max(...along)) - Math.max(0, Math.min(...along));

			if (gap > PAIR_GAP_MAX_MM || overlap <= 0) continue;
			const widthMm = round((a.width + b.width) / 2, 3);
			const key = `${a.layer} ${widthMm} ${gap}`;
			const run = coupled.get(key) ?? { layer: a.layer, widthMm, gapMm: gap, lengthMm: 0 };
			coupled.set(key, { ...run, lengthMm: run.lengthMm + overlap });
		}
	}

	const [pair] = [...coupled.values()].sort((a, b) => b.lengthMm - a.lengthMm);
	const [plusMm, minusMm] = [length(plus), length(minus)];

	const onBoth = (footprint: Footprint) =>
		[plus, minus].every((nets) => footprint.pads.some((pad) => nets.includes(pad.net)));

	return {
		dPlusNets: plus,
		dMinusNets: minus,
		dPlusMm: plusMm,
		dMinusMm: minusMm,
		mismatchMm: round(Math.abs(plusMm - minusMm)),
		vias: copper.vias.filter((via) => [...plus, ...minus].includes(via.net)).length,
		pair: pair ? { ...pair, lengthMm: round(pair.lengthMm) } : null,
		differentialOhms: pair
			? differentialImpedance(copper.stackup, pair.layer, pair.widthMm, pair.gapMm)
			: null,
		esd: footprints
			.filter((footprint) => footprint !== rp2350 && footprint !== connector && onBoth(footprint))
			.map((footprint) => footprint.ref)
	};
});

function checkAntennaKeepout({ footprints, copper }: CheckedRun, module: Footprint) {
	const moduleArea = boundingBox(module.courtyard);

	const keepouts = [
		...module.zones.map((zone) => ({ owner: module.ref, zone })),
		...copper.zones.map((zone) => ({ owner: 'board', zone }))
	].filter(
		({ zone }) =>
			zone.notAllowed.some((item) => item !== 'footprints') &&
			polygonsOverlap(zone.outline, moduleArea)
	);

	return {
		module: module.ref,
		keepouts: keepouts.map(({ owner, zone }) => {
			const enters = (a: Point, b: Point, width: number) =>
				segmentToPolygon(a, b, zone.outline) < width / 2 - EDGE_MM;

			return {
				owner,
				name: zone.name,
				layers: zone.layers,
				notAllowed: zone.notAllowed,
				copperInside: {
					tracks: copper.tracks.filter((track) => enters(track.start, track.end, track.width))
						.length,
					vias: copper.vias.filter((via) => enters(via, via, via.size)).length,
					zoneFills: [
						...new Set(
							copper.zones.flatMap((other) =>
								other.fills
									.filter((fill) => polygonsOverlap(fill.outline, zone.outline))
									.map((fill) => `${other.net || 'no net'} on ${fill.layer}`)
							)
						)
					],
					pads: footprints
						.filter((footprint) => footprint !== module)
						.flatMap((footprint) =>
							footprint.pads
								.filter((pad) => pad.type !== 'np_thru_hole' && isDeepInside(pad, zone.outline))
								.map((pad) => `${footprint.ref}.${pad.number}`)
						)
				}
			};
		})
	};
}

const checkDesign = Effect.fn('checkDesign')(function* (run: CheckedRun, features: Features) {
	const [rp2350, connector, module] = [
		run.rp2350s[0],
		...[FEATURES.usbC, FEATURES.wifiBle].map((pattern) =>
			run.byReference.get(refsMatching(run.bom.lines, pattern)[0] ?? '')
		)
	];

	if (!rp2350 || !connector || !module)
		return yield* new CheckError({
			message: 'The design checks need the RP2350, USB-C connector and Wi-Fi module'
		});

	if (
		!rp2350.pads.some((pad) => pad.pinFunction) &&
		rp2350.pads.some((pad) => Number(pad.number) > 61)
	)
		return yield* new CheckError({
			message: `${rp2350.ref} names no pin functions and isn't an RP2350A`
		});

	return {
		decoupling: checkDecoupling(run, rp2350),
		battery: yield* checkBatteryDivider(run, features),
		usb: yield* checkUsb(run, rp2350, connector),
		antennaKeepout: checkAntennaKeepout(run, module)
	};
});

const checkDeliverables = Effect.fn('checkDeliverables')(function* ({ board, output }: CheckedRun) {
	const fs = yield* FileSystem.FileSystem;
	const project = board.replace(/\.kicad_pcb$/, '');
	const fabDir = `${output}/fab`;

	return {
		readme: yield* fs.exists(`${output}/README.md`),
		schematic: yield* fs.exists(`${project}.kicad_sch`),
		projectFile: yield* fs.exists(`${project}.kicad_pro`),
		fabFolder:
			(yield* fs.exists(fabDir)) &&
			(yield* fs.readDirectory(fabDir, { recursive: true })).length > 0
	};
});

const command = Command.make('check', { runId: runIdArgument }, ({ runId }) =>
	Effect.gen(function* () {
		const run = yield* readCheckedRun(runId);

		const checks = {
			bom: checkBom(run),
			placement: yield* checkPlacement(run),
			parts: yield* checkParts(run)
		};

		const features = checkFeatures(run);
		const design = yield* checkDesign(run, features);

		yield* updateMetrics(runId, {
			...checks,
			suppliers: yield* checkSuppliers(run),
			needsFixes: needsFixes(run, checks),
			features,
			design,
			gates: checkGates(run, features),
			layout: checkLayout(run, features, [...design.usb.dPlusNets, ...design.usb.dMinusNets]),
			deliverables: yield* checkDeliverables(run)
		});
	})
);

command.pipe(
	Command.run({ version: '0.0.0' }),
	Effect.provide(Layer.mergeAll(BunServices.layer, Lcsc.layer, Jlcpcb.layer, Digikey.layer)),
	BunRuntime.runMain
);
