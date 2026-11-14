import type { LeaderboardData } from '../../data/leaderboard';
import { hours, tokens, usd } from '../../data/format';
import { isOfficialMix, type Weights } from './score';

export const VIEWS = ['table', 'pareto'] as const;

export type View = (typeof VIEWS)[number];

const wholeUsd = (value: number) => `$${Number(value.toPrecision(2))}`;

export const METRICS = {
	costUsd: {
		label: 'AI cost',
		title: "The run's API cost at market prices, including subagents",
		format: usd,
		tick: wholeUsd,
		ticks: [1, 1.5, 2, 3, 5, 7]
	},
	minutes: {
		label: 'Time',
		title: 'Wall-clock time of the run',
		format: hours,
		tick: (minutes: number) => (minutes < 60 ? `${minutes} min` : `${minutes / 60} h`),
		ticks: [15, 30, 60, 120, 180, 240, 360, 480, 720]
	},
	tokens: {
		label: 'Tokens',
		title: 'Input, cached and output tokens, including subagents',
		format: tokens,
		tick: tokens,
		ticks: [1, 2, 5]
	},
	boardUsd: {
		label: 'Board price',
		title: 'Price of one assembled board when ordering 5 from PCBWay, without shipping',
		format: usd,
		tick: wholeUsd,
		ticks: [1, 1.5, 2, 3, 5, 7]
	}
} satisfies Record<string, Metric>;

type Metric = {
	label: string;
	title: string;
	format: (value: number) => string;
	tick: (value: number) => string;
	// Tick values for a log axis, repeated every decade when they are single digits.
	ticks: ReadonlyArray<number>;
};

export type MetricKey = keyof typeof METRICS;

export const METRIC_KEYS = [
	'costUsd',
	'minutes',
	'tokens',
	'boardUsd'
] as const satisfies ReadonlyArray<MetricKey>;

export const X_AXES = [
	'costUsd',
	'minutes',
	'boardUsd'
] as const satisfies ReadonlyArray<MetricKey>;

export type XAxis = (typeof X_AXES)[number];

export const SORT_KEYS = ['score', 'model', 'harness', 'tasks', ...METRIC_KEYS] as const;

export type SortKey = (typeof SORT_KEYS)[number];

// Higher is better for these, so they sort descending first.
const DESCENDING_FIRST: ReadonlyArray<SortKey> = ['score', 'tasks'];

export const descendingFirst = (key: SortKey) => DESCENDING_FIRST.includes(key);

export type State = {
	view: View;
	task: string | null;
	harnesses: ReadonlyArray<string>;
	models: ReadonlyArray<string>;
	weights: Weights;
	sort: SortKey;
	descending: boolean;
	x: XAxis;
};

export const defaultState = (data: LeaderboardData): State => ({
	view: 'table',
	task: null,
	harnesses: [],
	models: [],
	weights: data.groups.map((group) => group.points),
	sort: 'score',
	descending: true,
	x: 'costUsd'
});

const pick = <T extends string>(options: ReadonlyArray<T>, value: string | null) =>
	options.find((option) => option === value);

const known = (values: ReadonlyArray<string>, ids: ReadonlyArray<string>) =>
	values.filter((value) => ids.includes(value));

export const MAX_WEIGHT = 50;

function parseWeights(value: string | null, count: number) {
	const weights = (value ?? '').split('-').map(Number);

	const valid = weights.every(
		(weight) => Number.isInteger(weight) && weight >= 0 && weight <= MAX_WEIGHT
	);

	return valid && weights.length === count ? weights : null;
}

export function lookup(data: LeaderboardData) {
	const findModel = (id: string) => data.models.find((model) => model.id === id);

	return {
		harness: (id: string) => data.harnesses.find((harness) => harness.id === id)?.name ?? id,
		model: (id: string) => findModel(id)?.name ?? id,
		maker: (id: string) => findModel(id)?.maker,
		task: (id: string) => data.tasks.find((task) => task.id === id)?.name ?? id
	};
}

export function parseState(search: string, data: LeaderboardData): State {
	const params = new URLSearchParams(search);
	const defaults = defaultState(data);
	const sort = pick(SORT_KEYS, params.get('sort')) ?? defaults.sort;
	const order = params.get('order');

	return {
		view: pick(VIEWS, params.get('view')) ?? defaults.view,
		task: data.tasks.find((task) => task.id === params.get('task'))?.id ?? null,
		harnesses: known(
			params.getAll('harness'),
			data.harnesses.map((harness) => harness.id)
		),
		models: known(
			params.getAll('model'),
			data.models.map((model) => model.id)
		),
		weights: parseWeights(params.get('mix'), data.groups.length) ?? defaults.weights,
		sort,
		descending: order ? order === 'desc' : descendingFirst(sort),
		x: pick(X_AXES, params.get('x')) ?? defaults.x
	};
}

// Only values that differ from the defaults go in the URL.
export function stateQuery(state: State, data: LeaderboardData) {
	const defaults = defaultState(data);
	const params = new URLSearchParams();

	if (state.view !== defaults.view) params.set('view', state.view);

	if (state.task) params.set('task', state.task);

	for (const harness of state.harnesses) params.append('harness', harness);

	for (const model of state.models) params.append('model', model);

	if (!isOfficialMix(state.weights, data.groups)) params.set('mix', state.weights.join('-'));

	if (state.sort !== defaults.sort) params.set('sort', state.sort);

	if (state.descending !== descendingFirst(state.sort))
		params.set('order', state.descending ? 'desc' : 'asc');

	if (state.x !== defaults.x) params.set('x', state.x);

	return params.toString();
}
