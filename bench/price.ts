import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Console, DateTime, Effect, FileSystem, Layer, Schema } from 'effect';
import { Argument, Command } from 'effect/cli';
import { runDirectory, updateMetrics } from './board.ts';
import { readBom } from './bom.ts';
import { Lcsc, type LcscProduct } from './lcsc.ts';
import { BATCH_BOARDS } from './runs.ts';

const Tier = Schema.Struct({ ladder: Schema.Number, usd: Schema.Number });

type Tier = typeof Tier.Type;

export const Fix = Schema.Struct({
	area: Schema.Literals(['bom', 'pcb', 'fabSpec']),
	problem: Schema.String,
	fix: Schema.String,
	refs: Schema.optional(Schema.String),
	mpn: Schema.optional(Schema.String)
});

export type Fix = typeof Fix.Type;

const overrideFields = {
	buyMpn: Schema.optional(Schema.String),
	fixes: Schema.optional(Schema.Array(Fix))
};

const PriceOverride = Schema.Union([
	Schema.Struct({ ...overrideFields, lcsc: Schema.String }),
	Schema.Struct({
		...overrideFields,
		source: Schema.String,
		minBuy: Schema.Number,
		tiers: Schema.Array(Tier)
	})
]);

type PriceOverride = typeof PriceOverride.Type;

const PriceOverrides = Schema.fromJsonString(Schema.Record(Schema.String, PriceOverride));

const Quote = Schema.Struct({ pcbUsd: Schema.Number, assemblyUsd: Schema.Number });

type Quote = typeof Quote.Type;

const PcbwayQuote = Schema.fromJsonString(
	Schema.Struct({
		one: Schema.Struct({ ...Quote.fields, pcbQty: Schema.Number }),
		five: Quote,
		options: Schema.Struct({ size_mm: Schema.String }),
		fixes: Schema.optional(Schema.Array(Fix))
	})
);

const BomPath = Schema.fromJsonString(Schema.Struct({ bom: Schema.String }));

type Line = { refs: string; qty: number; mpn: string; lcsc: string | null };

type Part = {
	source: string;
	buyMpn: string;
	minBuy: number;
	tiers: ReadonlyArray<Tier>;
	fixes?: ReadonlyArray<Fix>;
};

class MissingPriceError extends Schema.TaggedError<MissingPriceError>()('MissingPriceError', {
	message: Schema.String
}) {}

const round = (usd: number) => Math.round(usd * 100) / 100;

const normalize = (mpn: string) => mpn.replaceAll(/[\s-]/g, '').toLowerCase();

const toPart = (product: LcscProduct | null): Part | null =>
	product?.productPriceList?.length
		? {
				source: `LCSC ${product.productCode}`,
				buyMpn: product.productModel,
				minBuy: product.minBuyNumber,
				tiers: product.productPriceList.map((tier) => ({ ladder: tier.ladder, usd: tier.usdPrice }))
			}
		: null;

const partByCode = (code: string) =>
	Lcsc.use((lcsc) => lcsc.productByCode(code)).pipe(Effect.map(toPart));

const partByMpn = Effect.fnUntraced(function* (mpn: string) {
	const lcsc = yield* Lcsc;

	for (const keyword of new Set([mpn, mpn.replaceAll('-', '')])) {
		const matches = yield* lcsc.exactMatches(keyword);

		const best = matches
			.filter((product) => normalize(product.productModel) === normalize(mpn))
			.sort((a, b) => b.stockNumber - a.stockNumber)[0];

		if (best) return toPart(best);
	}

	return null;
});

const lookUpPart = (line: Line, override: PriceOverride | undefined) => {
	if (!override) return line.lcsc ? partByCode(line.lcsc) : partByMpn(line.mpn);

	if ('lcsc' in override) return partByCode(override.lcsc);

	return Effect.succeed<Part>({ buyMpn: line.mpn, ...override });
};

const findPart = Effect.fn('findPart')(function* (line: Line, override: PriceOverride | undefined) {
	const part = yield* lookUpPart(line, override);

	if (!part)
		return yield* new MissingPriceError({
			message: `No price for ${line.mpn} (${line.refs}); add it to part-prices.json`
		});

	return override
		? { ...part, buyMpn: override.buyMpn ?? part.buyMpn, fixes: override.fixes }
		: part;
});

function cost({ minBuy, tiers }: Pick<Part, 'minBuy' | 'tiers'>, needed: number) {
	const buy = Math.max(needed, minBuy);
	const unitUsd = tiers.filter((tier) => tier.ladder <= buy).at(-1)?.usd ?? tiers[0]!.usd;

	return { buy, unitUsd, usd: round(buy * unitUsd) };
}

const priceLine = Effect.fn('priceLine')(function* (
	line: Line,
	override: PriceOverride | undefined
) {
	const { tiers, minBuy, ...part } = yield* findPart(line, override);

	return {
		...line,
		...part,
		oneBoard: cost({ minBuy, tiers }, line.qty),
		fiveBoards: cost({ minBuy, tiers }, line.qty * BATCH_BOARDS)
	};
});

type PricedLine = Effect.Success<ReturnType<typeof priceLine>>;

function scenarioCost(
	priced: ReadonlyArray<PricedLine>,
	{ pcbUsd, assemblyUsd }: Quote,
	scenario: 'oneBoard' | 'fiveBoards'
) {
	const componentsUsd = round(priced.reduce((sum, line) => sum + line[scenario].usd, 0));

	return {
		pcbUsd,
		assemblyUsd,
		componentsUsd,
		totalUsd: round(pcbUsd + assemblyUsd + componentsUsd)
	};
}

const command = Command.make('price', { runId: Argument.String('run-id') }, ({ runId }) =>
	Effect.gen(function* () {
		const fs = yield* FileSystem.FileSystem;
		const runDir = runDirectory(runId);

		const priceOverrides = yield* Schema.decodeEffect(PriceOverrides)(
			yield* fs.readFileString(`${import.meta.dir}/part-prices.json`)
		);

		const quote = yield* Schema.decodeEffect(PcbwayQuote)(
			yield* fs.readFileString(`${runDir}/pcbway-quote.json`)
		);

		const [width, height] = quote.options.size_mm.split('x').map(Number);
		const boardSizeMm = { width, height };

		const { bom: bomPath } = yield* Schema.decodeEffect(BomPath)(
			yield* fs.readFileString(`${runDir}/info.json`)
		);

		const bom = yield* readBom(`${runDir}/output/${bomPath}`);
		const lcscColumn = bom.column(/lcsc/i);

		const lines: Line[] = bom.lines.flatMap(({ refs, qty, mpn, fitted, row }) =>
			fitted && qty > 0 && mpn
				? [{ refs, qty, mpn, lcsc: /^C\d+$/.test(row[lcscColumn] ?? '') ? row[lcscColumn]! : null }]
				: []
		);

		const priced = yield* Effect.forEach(lines, (line) =>
			priceLine(line, priceOverrides[line.mpn])
		);

		const fiveBoards = scenarioCost(priced, quote.five, 'fiveBoards');

		const fixes = [
			...(quote.fixes ?? []),
			...priced.flatMap(({ refs, mpn, fixes = [] }) => fixes.map((fix) => ({ ...fix, refs, mpn })))
		];

		const boardCost = {
			afterFixes: fixes.length > 0,
			oneBoard: { pcbQty: quote.one.pcbQty, ...scenarioCost(priced, quote.one, 'oneBoard') },
			fiveBoards: { ...fiveBoards, perBoardUsd: round(fiveBoards.totalUsd / BATCH_BOARDS) },
			pricedAt: DateTime.formatIso(yield* DateTime.now),
			source:
				"PCB and assembly from PCBWay's instant quote (pcbway-quote.json) with the options in the run's fab notes, standard build, shipping excluded, no new-customer promo. PCBWay makes at least 5 bare PCBs, so one board means 5 PCBs with 1 assembled. Components at distributor list prices (components-pricing.json) for max(needed, minimum order): bench/part-prices.json where listed, else LCSC. When afterFixes is true, the design couldn't be ordered as delivered, and these are the prices after the changes listed in fixes."
		};

		yield* fs.writeFileString(
			`${runDir}/components-pricing.json`,
			`${JSON.stringify(priced, null, '\t')}\n`
		);

		yield* Console.table(
			priced.map(({ mpn, source, buyMpn, oneBoard, fiveBoards }) => ({
				mpn,
				source,
				buyMpn,
				one: oneBoard.usd,
				five: fiveBoards.usd
			}))
		);

		yield* updateMetrics(runId, { boardSizeMm, fixes, boardCost });
	})
);

if (import.meta.main)
	command.pipe(
		Command.run({ version: '0.0.0' }),
		Effect.provide(Layer.mergeAll(BunServices.layer, Lcsc.layer)),
		BunRuntime.runMain
	);
