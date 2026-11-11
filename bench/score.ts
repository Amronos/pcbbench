import { readRun } from './board.ts';
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
];
type Items = typeof ITEMS;
const GROUPS = [...new Set(ITEMS.map((item) => item.group))];
const MISSING_FEATURE_CAP = 50;
const USB_TARGET_OHMS = 90;
const USB_FULL_WITHIN = 0.1;
const USB_NONE_BEYOND = 0.35;
const WEIGHT_SHIFT = 10;

const clamp = (value: number) => Math.min(1, Math.max(0, value));
const round = (value: number) => Math.round(value * 10) / 10;
const sum = (values: number[]) => values.reduce((total, value) => total + value, 0);

type Keepout = { copperInside: { tracks: number; vias: number; zoneFills: string[]; pads: string[] } };

async function readFractions(runId: string) {
	const { parts, metrics, updateMetrics } = await readRun(runId);
	const { review, design, needsFixes, suppliers, missing3dModels, features } = metrics;
	if (!review || !suppliers || !needsFixes?.bomLines) throw new Error(`Run judge/judge.ts and check.ts on ${runId} first`);
	const yesVotes: number[] = Object.values(review.yesVotes);
	const meanScores: number[] = Object.values(review.meanScores);
	const ohms: number | null = design.usb.differentialOhms;
	const usbError = ohms === null ? Infinity : Math.abs(ohms - USB_TARGET_OHMS) / USB_TARGET_OHMS;
	const keepouts: Keepout[] = design.antennaKeepout.keepouts;
	const keepoutClear = keepouts.length > 0 && keepouts.every(({ copperInside: c }) => !c.tracks && !c.vias && !c.zoneFills.length && !c.pads.length);
	const supplierLines = (count: number) => count / suppliers.lines;
	const featureStatus: [string, { status: string }][] = Object.entries(features);
	const fractions: Record<string, number> = {
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
	};
	return { id: runId, fractions, missingFeatures: featureStatus.filter(([, { status }]) => status !== 'found').map(([name]) => name), updateMetrics };
}

function score({ fractions, missingFeatures }: Awaited<ReturnType<typeof readFractions>>, items: Items) {
	const groups = Object.fromEntries(GROUPS.map((group) => [group, sum(items.filter((item) => item.group === group).map((item) => item.points * (fractions[item.name] ?? 0)))]));
	const total = sum(Object.values(groups));
	return { total: missingFeatures.length ? Math.min(total, MISSING_FEATURE_CAP) : total, groups };
}

// WEIGHT_SHIFT points moved from one group to another, scaling each group's items in proportion.
function shiftedItems(from: string, to: string): Items {
	const groupPoints = (group: string) => sum(ITEMS.filter((item) => item.group === group).map((item) => item.points));
	const factor = (group: string) => (group === from ? (groupPoints(from) - WEIGHT_SHIFT) / groupPoints(from) : group === to ? (groupPoints(to) + WEIGHT_SHIFT) / groupPoints(to) : 1);
	return ITEMS.map((item) => ({ ...item, points: item.points * factor(item.group) }));
}

const runs = await Promise.all(RUNS.map(({ id }) => readFractions(id)));
const ranking = (items: Items) => runs.toSorted((a, b) => score(b, items).total - score(a, items).total).map((run) => run.id);

for (const run of runs) {
	const { total, groups } = score(run, ITEMS);
	await run.updateMetrics({ score: { total: round(total), groups: Object.fromEntries(Object.entries(groups).map(([group, points]) => [group, round(points)])), missingFeatures: run.missingFeatures } });
}

const baseline = ranking(ITEMS);
console.log(`Ranking: ${baseline.join(' > ')}`);
for (const from of GROUPS) {
	for (const to of GROUPS.filter((group) => group !== from)) {
		const moves = ranking(shiftedItems(from, to)).flatMap((id, place) => (place === baseline.indexOf(id) ? [] : [`${id} ${baseline.indexOf(id) + 1}→${place + 1}`]));
		console.log(`${WEIGHT_SHIFT} points ${from} → ${to}: ${moves.length ? moves.join(', ') : 'same ranking'}`);
	}
}
