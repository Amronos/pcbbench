import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Console, Effect, Schema } from 'effect';
import { Command } from 'effect/cli';
import { readMetrics, readRun, updateMetrics } from './board.ts';
import { RUNS } from './runs.ts';

// Each item scores its points times a fraction from 0 to 1.
const ITEMS = [
	{ group: 'designReview', name: 'yesNo', points: 15 },
	{ group: 'designReview', name: 'judgeScores', points: 35 },
	{ group: 'circuitChecks', name: 'decoupling', points: 7 },
	{ group: 'circuitChecks', name: 'usbImpedance', points: 7 },
	{ group: 'circuitChecks', name: 'antennaKeepout', points: 6 },
	{ group: 'orderable', name: 'pcbWithoutFixes', points: 10 },
	{ group: 'orderable', name: 'bomLinesWithoutFixes', points: 10 },
	{ group: 'partsData', name: 'models3d', points: 5 },
	{ group: 'partsData', name: 'supplierFromOne', points: 3 },
	{ group: 'partsData', name: 'supplierFromTwo', points: 1.5 },
	{ group: 'partsData', name: 'supplierFromAllThree', points: 0.5 }
] as const;

type Item = {
	group: (typeof ITEMS)[number]['group'];
	name: (typeof ITEMS)[number]['name'];
	points: number;
};

type Items = ReadonlyArray<Item>;

const GROUPS = [...new Set(ITEMS.map((item) => item.group))];
const MISSING_FEATURE_CAP = 50;
const USB_TARGET_OHMS = 90;
const USB_FULL_WITHIN = 0.1;
const USB_NONE_BEYOND = 0.35;
const WEIGHT_SHIFT = 10;

const clamp = (value: number) => Math.min(1, Math.max(0, value));
const round = (value: number) => Math.round(value * 10) / 10;
const sum = (values: number[]) => values.reduce((total, value) => total + value, 0);

const ScoredMetrics = Schema.Struct({
	review: Schema.Struct({
		judges: Schema.Array(Schema.String),
		yesVotes: Schema.Record(Schema.String, Schema.Number),
		meanScores: Schema.Record(Schema.String, Schema.Number)
	}),
	design: Schema.Struct({
		decoupling: Schema.Struct({ pinsWithin: Schema.Number, powerPins: Schema.Number }),
		usb: Schema.Struct({ differentialOhms: Schema.NullOr(Schema.Number) }),
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
		pcbManufacturing: Schema.Array(Schema.String),
		bomLines: Schema.Struct({ total: Schema.Number, needingFixes: Schema.Array(Schema.String) })
	}),
	suppliers: Schema.Struct({
		lines: Schema.Number,
		linesWithValidNumbers: Schema.Struct({
			fromOne: Schema.Number,
			fromTwo: Schema.Number,
			fromAllThree: Schema.Number
		})
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

	const { review, design, needsFixes, suppliers, missing3dModels, features } = yield* readMetrics(
		runId,
		ScoredMetrics
	).pipe(
		Effect.catchTag('SchemaError', (cause) =>
			Effect.fail(
				new UncheckedRunError({
					message: `Run judge/judge.ts and check.ts on ${runId} first`,
					cause
				})
			)
		)
	);

	const yesVotes = Object.values(review.yesVotes);
	const meanScores = Object.values(review.meanScores);
	const ohms = design.usb.differentialOhms;
	const usbError = ohms === null ? Infinity : Math.abs(ohms - USB_TARGET_OHMS) / USB_TARGET_OHMS;
	const { keepouts } = design.antennaKeepout;

	const keepoutClear =
		keepouts.length > 0 &&
		keepouts.every(
			({ copperInside: c }) => !c.tracks && !c.vias && !c.zoneFills.length && !c.pads.length
		);

	const supplierLines = (count: number) => count / suppliers.lines;

	const fractions = {
		yesNo: sum(yesVotes) / (yesVotes.length * review.judges.length),
		judgeScores: sum(meanScores) / (meanScores.length * 10),
		decoupling: design.decoupling.pinsWithin / design.decoupling.powerPins,
		usbImpedance: clamp((USB_NONE_BEYOND - usbError) / (USB_NONE_BEYOND - USB_FULL_WITHIN)),
		antennaKeepout: keepoutClear ? 1 : 0,
		pcbWithoutFixes: needsFixes.pcbManufacturing.length ? 0 : 1,
		bomLinesWithoutFixes: 1 - needsFixes.bomLines.needingFixes.length / needsFixes.bomLines.total,
		models3d: 1 - missing3dModels.count / parts.length,
		supplierFromOne: supplierLines(suppliers.linesWithValidNumbers.fromOne),
		supplierFromTwo: supplierLines(suppliers.linesWithValidNumbers.fromTwo),
		supplierFromAllThree: supplierLines(suppliers.linesWithValidNumbers.fromAllThree)
	} satisfies Record<Item['name'], number>;

	return {
		id: runId,
		fractions,
		missingFeatures: Object.entries(features).flatMap(([name, { status }]) =>
			status === 'found' ? [] : [name]
		)
	};
});

function score(
	{ fractions, missingFeatures }: Effect.Success<ReturnType<typeof readFractions>>,
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

	return { total: missingFeatures.length ? Math.min(total, MISSING_FEATURE_CAP) : total, groups };
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
					missingFeatures: run.missingFeatures
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
