import { BunServices } from '@effect/platform-bun';
import { Effect, Layer, ManagedRuntime } from 'effect';
import { readBom } from './bom.ts';
import { Lcsc, type LcscProduct } from './lcsc.ts';
import { BATCH_BOARDS } from './runs.ts';

const runtime = ManagedRuntime.make(Layer.mergeAll(BunServices.layer, Lcsc.layer));
const lcsc = await runtime.runPromise(Effect.service(Lcsc));
const productByCode = (code: string) => Effect.runPromise(lcsc.productByCode(code));

type Line = { refs: string; qty: number; mpn: string; lcsc: string | null };

type Tier = { ladder: number; usd: number };

export type Fix = {
	area: 'bom' | 'pcb' | 'fabSpec';
	problem: string;
	fix: string;
	refs?: string;
	mpn?: string;
};

type Part = { source: string; buyMpn: string; minBuy: number; tiers: Tier[]; fixes?: Fix[] };

type PriceOverride = { buyMpn?: string; fixes?: Fix[] } & (
	{ lcsc: string } | { source: string; minBuy: number; tiers: Tier[] }
);

type Quote = { pcbUsd: number; assemblyUsd: number };

const [runId] = Bun.argv.slice(2);

if (!runId) throw new Error('Usage: bun bench/price.ts <run id>');

const runDir = `${import.meta.dir}/../runs/${runId}`;
const round = (usd: number) => Math.round(usd * 100) / 100;

const priceOverrides: Record<string, PriceOverride> = await Bun.file(
	`${import.meta.dir}/part-prices.json`
).json();

const quote: {
	one: Quote & { pcbQty: number };
	five: Quote;
	options: { size_mm: string };
	fixes?: Fix[];
} = await Bun.file(`${runDir}/pcbway-quote.json`).json();

const [width, height] = quote.options.size_mm.split('x').map(Number);
const boardSizeMm = { width, height };

const { bom: bomPath } = await Bun.file(`${runDir}/info.json`).json();
const bom = await runtime.runPromise(readBom(`${runDir}/output/${bomPath}`));
const lcscColumn = bom.column(/lcsc/i);

const lines: Line[] = bom.lines
	.filter((line) => line.fitted && line.qty > 0 && line.mpn)
	.map(({ refs, qty, mpn, row }) => ({
		refs,
		qty,
		mpn,
		lcsc: /^C\d+$/.test(row[lcscColumn] ?? '') ? row[lcscColumn]! : null
	}));

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

const partByCode = async (code: string) => toPart(await productByCode(code));

async function partByMpn(mpn: string) {
	for (const keyword of new Set([mpn, mpn.replaceAll('-', '')])) {
		const matches = await Effect.runPromise(lcsc.exactMatches(keyword));

		const best = matches
			.filter((product) => normalize(product.productModel) === normalize(mpn))
			.sort((a, b) => b.stockNumber - a.stockNumber)[0];

		if (best) return toPart(best);
	}

	return null;
}

async function lookUpPart(line: Line, override: PriceOverride | undefined): Promise<Part | null> {
	if (!override) return line.lcsc ? partByCode(line.lcsc) : partByMpn(line.mpn);

	if ('lcsc' in override) return partByCode(override.lcsc);

	return { buyMpn: line.mpn, ...override };
}

async function findPart(line: Line): Promise<Part> {
	const override = priceOverrides[line.mpn];
	const part = await lookUpPart(line, override);

	if (!part) throw new Error(`No price for ${line.mpn} (${line.refs}); add it to part-prices.json`);

	return override
		? { ...part, buyMpn: override.buyMpn ?? part.buyMpn, fixes: override.fixes }
		: part;
}

function cost({ minBuy, tiers }: Pick<Part, 'minBuy' | 'tiers'>, needed: number) {
	const buy = Math.max(needed, minBuy);
	const unitUsd = tiers.filter((tier) => tier.ladder <= buy).at(-1)?.usd ?? tiers[0]!.usd;

	return { buy, unitUsd, usd: round(buy * unitUsd) };
}

async function priceLine(line: Line) {
	const { tiers, minBuy, ...part } = await findPart(line);

	return {
		...line,
		...part,
		oneBoard: cost({ minBuy, tiers }, line.qty),
		fiveBoards: cost({ minBuy, tiers }, line.qty * BATCH_BOARDS)
	};
}

const priced: Awaited<ReturnType<typeof priceLine>>[] = [];

for (const line of lines) priced.push(await priceLine(line));

function scenarioCost({ pcbUsd, assemblyUsd }: Quote, scenario: 'oneBoard' | 'fiveBoards') {
	const componentsUsd = round(priced.reduce((sum, line) => sum + line[scenario].usd, 0));

	return {
		pcbUsd,
		assemblyUsd,
		componentsUsd,
		totalUsd: round(pcbUsd + assemblyUsd + componentsUsd)
	};
}

const fiveBoards = scenarioCost(quote.five, 'fiveBoards');

const fixes = [
	...(quote.fixes ?? []),
	...priced.flatMap(({ refs, mpn, fixes = [] }) => fixes.map((fix) => ({ ...fix, refs, mpn })))
];

const boardCost = {
	afterFixes: fixes.length > 0,
	oneBoard: { pcbQty: quote.one.pcbQty, ...scenarioCost(quote.one, 'oneBoard') },
	fiveBoards: { ...fiveBoards, perBoardUsd: round(fiveBoards.totalUsd / BATCH_BOARDS) },
	pricedAt: new Date().toISOString(),
	source:
		"PCB and assembly from PCBWay's instant quote (pcbway-quote.json) with the options in the run's fab notes, standard build, shipping excluded, no new-customer promo. PCBWay makes at least 5 bare PCBs, so one board means 5 PCBs with 1 assembled. Components at distributor list prices (components-pricing.json) for max(needed, minimum order): bench/part-prices.json where listed, else LCSC. When afterFixes is true, the design couldn't be ordered as delivered, and these are the prices after the changes listed in fixes."
};

await Bun.write(`${runDir}/components-pricing.json`, `${JSON.stringify(priced, null, '\t')}\n`);

const metricsPath = `${runDir}/metrics.json`;

await Bun.write(
	metricsPath,
	`${JSON.stringify({ ...(await Bun.file(metricsPath).json()), boardSizeMm, fixes, boardCost }, null, '\t')}\n`
);

console.table(
	priced.map(({ mpn, source, buyMpn, oneBoard, fiveBoards }) => ({
		mpn,
		source,
		buyMpn,
		one: oneBoard.usd,
		five: fiveBoards.usd
	}))
);

console.log(boardCost);
