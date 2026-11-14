import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Console, Effect, Schema } from 'effect';
import { Command } from 'effect/cli';
import { readMetrics, readRun, updateMetrics } from './board.ts';
import { RUNS } from './runs.ts';

// Each item scores its points times a fraction from 0 to 1.
const ITEMS = [
	{ group: 'designReview', name: 'layout', points: 10 },
	{ group: 'designReview', name: 'routing', points: 10 },
	{ group: 'circuitChecks', name: 'decoupling', points: 5 },
	{ group: 'circuitChecks', name: 'usbProtection', points: 5 },
	{ group: 'circuitChecks', name: 'antennaKeepout', points: 5 },
	{ group: 'circuitChecks', name: 'batteryDrain', points: 5 },
	{ group: 'layoutChecks', name: 'thermal', points: 10 },
	{ group: 'layoutChecks', name: 'grounding', points: 10 },
	{ group: 'layoutChecks', name: 'silkscreen', points: 5 },
	{ group: 'layoutChecks', name: 'boardSize', points: 5 },
	{ group: 'orderable', name: 'fabNotesWithoutFixes', points: 5 },
	{ group: 'orderable', name: 'boardWithoutRework', points: 5 },
	{ group: 'orderable', name: 'bomLinesWithoutFixes', points: 10 },
	{ group: 'partsData', name: 'models3d', points: 5 },
	{ group: 'partsData', name: 'supplierNumbers', points: 5 }
] as const;

type Item = {
	group: (typeof ITEMS)[number]['group'];
	name: (typeof ITEMS)[number]['name'];
	points: number;
};

type Items = ReadonlyArray<Item>;

const GROUPS = [...new Set(ITEMS.map((item) => item.group))];
const GATE_PENALTY = 20;

// Adafruit's Feather RP2350 (50.8 × 22.8 mm) fits all of the brief but Wi-Fi and microSD.
const FULL_SIZE_MM2 = 50.8 * 22.8;
const ZERO_SIZE_MM2 = 5 * FULL_SIZE_MM2;

// A review area starts at 10 and loses these points per finding.
const MINOR_COST = 1;
const MAJOR_COST = 2;

// Battery current drawn by unswitched monitor dividers: full points at or below the first, none at the second.
const DRAIN_FULL_UA = 5;
const DRAIN_NONE_UA = 25;
const WEIGHT_SHIFT = 10;

// Each BOM line needing a fix costs this share of the BOM lines item, whatever the BOM's size.
const BOM_LINE_FIX_COST = 0.2;

const clamp = (value: number) => Math.min(1, Math.max(0, value));
const round = (value: number) => Math.round(value * 10) / 10;
const sum = (values: number[]) => values.reduce((total, value) => total + value, 0);

const Findings = Schema.Struct({ minor: Schema.Number, major: Schema.Number });
const Fraction = Schema.Struct({ fraction: Schema.Number });

const ScoredMetrics = Schema.Struct({
	review: Schema.Struct({
		findings: Schema.Struct({
			layout: Findings,
			routing: Findings,
			fatal: Schema.Number
		})
	}),
	boardSizeMm: Schema.Struct({ width: Schema.Number, height: Schema.Number }),
	gates: Schema.Record(Schema.String, Schema.Struct({ pass: Schema.Boolean })),
	layout: Schema.Struct({
		thermal: Fraction,
		grounding: Fraction,
		silkscreen: Fraction
	}),
	design: Schema.Struct({
		decoupling: Schema.Struct({ pinsWithin: Schema.Number, powerPins: Schema.Number }),
		usb: Schema.Struct({
			dPlusNets: Schema.Array(Schema.String),
			dMinusNets: Schema.Array(Schema.String),
			esd: Schema.Array(Schema.String)
		}),
		battery: Schema.Struct({
			dividers: Schema.Array(
				Schema.Struct({
					microampsAtFullCharge: Schema.Number,
					switchedBy: Schema.NullOr(Schema.String)
				})
			)
		}),
		antennaKeepout: Schema.Struct({
			keepouts: Schema.Array(
				Schema.Struct({
					copperInside: Schema.Struct({
						tracks: Schema.Number,
						vias: Schema.Number,
						zoneFills: Schema.Array(Schema.String),
						pads: Schema.Array(Schema.String)
					})
				})
			)
		})
	}),
	needsFixes: Schema.Struct({
		fabNotes: Schema.Array(Schema.String),
		board: Schema.Array(Schema.String),
		bomLines: Schema.Struct({ total: Schema.Number, needingFixes: Schema.Array(Schema.String) })
	}),
	suppliers: Schema.Struct({
		lines: Schema.Number,
		linesWithValidNumber: Schema.Number
	}),
	missing3dModels: Schema.Struct({ count: Schema.Number }),
	features: Schema.Record(Schema.String, Schema.Struct({ status: Schema.String }))
});

class UncheckedRunError extends Schema.TaggedError<UncheckedRunError>()('UncheckedRunError', {
	message: Schema.String,
	cause: Schema.Defect()
}) {}

const readFractions = Effect.fn('readFractions')(function* (runId: string) {
	const { parts } = yield* readRun(runId);

	const {
		review,
		boardSizeMm,
		gates,
		layout,
		design,
		needsFixes,
		suppliers,
		missing3dModels,
		features
	} = yield* readMetrics(runId, ScoredMetrics).pipe(
		Effect.catchTag('SchemaError', (cause) =>
			Effect.fail(
				new UncheckedRunError({
					message: `Run judge/judge.ts and check.ts on ${runId} first`,
					cause
				})
			)
		)
	);

	const reviewed = ({ minor, major }: typeof Findings.Type) =>
		clamp(1 - (MINOR_COST * minor + MAJOR_COST * major) / 10);

	const { usb } = design;
	// check.ts lists a line's nets from the connector side; a series resistor adds the RP2350-side net.
	const hasSeriesResistor = (nets: readonly string[]) => nets.length > 1;

	const drainMicroamps = sum(
		design.battery.dividers.flatMap(({ microampsAtFullCharge, switchedBy }) =>
			switchedBy ? [] : [microampsAtFullCharge]
		)
	);

	const { keepouts } = design.antennaKeepout;

	const keepoutClear =
		keepouts.length > 0 &&
		keepouts.every(
			({ copperInside: c }) => !c.tracks && !c.vias && !c.zoneFills.length && !c.pads.length
		);

	const fractions = {
		layout: reviewed(review.findings.layout),
		routing: reviewed(review.findings.routing),
		decoupling: design.decoupling.pinsWithin / design.decoupling.powerPins,
		usbProtection:
			(usb.esd.length ? 0.5 : 0) +
			0.25 * [usb.dPlusNets, usb.dMinusNets].filter(hasSeriesResistor).length,
		antennaKeepout: keepoutClear ? 1 : 0,
		batteryDrain: clamp((DRAIN_NONE_UA - drainMicroamps) / (DRAIN_NONE_UA - DRAIN_FULL_UA)),
		thermal: layout.thermal.fraction,
		grounding: layout.grounding.fraction,
		silkscreen: layout.silkscreen.fraction,
		boardSize: clamp(
			(ZERO_SIZE_MM2 - boardSizeMm.width * boardSizeMm.height) / (ZERO_SIZE_MM2 - FULL_SIZE_MM2)
		),
		fabNotesWithoutFixes: needsFixes.fabNotes.length ? 0 : 1,
		boardWithoutRework: needsFixes.board.length ? 0 : 1,
		bomLinesWithoutFixes: clamp(1 - BOM_LINE_FIX_COST * needsFixes.bomLines.needingFixes.length),
		models3d: 1 - missing3dModels.count / parts.length,
		supplierNumbers: suppliers.linesWithValidNumber / suppliers.lines
	} satisfies Record<Item['name'], number>;

	return {
		id: runId,
		fractions,
		failedGates: [
			...Object.entries(features).flatMap(([name, { status }]) =>
				status === 'found' ? [] : [`missing ${name}`]
			),
			...Object.entries(gates).flatMap(([name, { pass }]) => (pass ? [] : [name])),
			...(review.findings.fatal ? [`${review.findings.fatal} fatal review findings`] : [])
		]
	};
});

function score(
	{ fractions, failedGates }: Effect.Success<ReturnType<typeof readFractions>>,
	items: Items
) {
	const groups = Object.fromEntries(
		GROUPS.map((group) => [
			group,
			sum(
				items.flatMap((item) => (item.group === group ? [item.points * fractions[item.name]] : []))
			)
		])
	);

	const total = sum(Object.values(groups));

	return { total: failedGates.length ? Math.max(0, total - GATE_PENALTY) : total, groups };
}

// WEIGHT_SHIFT points moved from one group to another, scaling each group's items in proportion.
function shiftedItems(from: string, to: string): Items {
	const groupPoints = (group: string) =>
		sum(ITEMS.flatMap((item) => (item.group === group ? [item.points] : [])));

	const factor = (group: string) =>
		group === from
			? (groupPoints(from) - WEIGHT_SHIFT) / groupPoints(from)
			: group === to
				? (groupPoints(to) + WEIGHT_SHIFT) / groupPoints(to)
				: 1;

	return ITEMS.map((item) => ({ ...item, points: item.points * factor(item.group) }));
}

const command = Command.make('score', {}, () =>
	Effect.gen(function* () {
		const runs = yield* Effect.forEach(RUNS, ({ id }) => readFractions(id), {
			concurrency: 'unbounded'
		});

		const ranking = (items: Items) =>
			runs.toSorted((a, b) => score(b, items).total - score(a, items).total).map((run) => run.id);

		for (const run of runs) {
			const { total, groups } = score(run, ITEMS);

			yield* updateMetrics(run.id, {
				score: {
					total: round(total),
					groups: Object.fromEntries(
						Object.entries(groups).map(([group, points]) => [group, round(points)])
					),
					failedGates: run.failedGates
				}
			});
		}

		const baseline = ranking(ITEMS);

		yield* Console.log(`Ranking: ${baseline.join(' > ')}`);

		for (const from of GROUPS) {
			for (const to of GROUPS.filter((group) => group !== from)) {
				const moves = ranking(shiftedItems(from, to)).flatMap((id, place) =>
					place === baseline.indexOf(id) ? [] : [`${id} ${baseline.indexOf(id) + 1}→${place + 1}`]
				);

				yield* Console.log(
					`${WEIGHT_SHIFT} points ${from} → ${to}: ${moves.length ? moves.join(', ') : 'same ranking'}`
				);
			}
		}
	})
);

command.pipe(
	Command.run({ version: '0.0.0' }),
	Effect.provide(BunServices.layer),
	BunRuntime.runMain
);
