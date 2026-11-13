import type { LeaderboardData, LeaderboardEntry } from '../../data/leaderboard';

type Scoring = Pick<LeaderboardData, 'groups' | 'gatePenalty'>;

// Weights are in the same order as `groups`.
export type Weights = ReadonlyArray<number>;

const sum = (values: ReadonlyArray<number>) => values.reduce((total, value) => total + value, 0);

const mean = (values: ReadonlyArray<number>) => (values.length ? sum(values) / values.length : 0);

export const isOfficialMix = (weights: Weights, groups: Scoring['groups']) =>
	groups.every((group, index) => weights[index] === group.points);

export function weightedScore(entry: LeaderboardEntry, scoring: Scoring, weights: Weights) {
	const totalWeight = sum(weights);

	const parts = scoring.groups.map((group, index) =>
		totalWeight ? (weights[index] * entry.shares[group.id] * 100) / totalWeight : 0
	);

	const raw = sum(parts);
	const score = entry.failedGates.length ? Math.max(0, raw - scoring.gatePenalty) : raw;

	return { parts, raw, score };
}

// The bench rounds its total from unrounded fractions, so the default mix shows that exact number.
function runScore(entry: LeaderboardEntry, scoring: Scoring, weights: Weights) {
	const result = weightedScore(entry, scoring, weights);

	return isOfficialMix(weights, scoring.groups) ? { ...result, score: entry.score } : result;
}

export type ScoredRun = ReturnType<typeof runScore> & { entry: LeaderboardEntry };

// Each task counts once, however many times a config ran it.
function meanOverTasks(runs: ReadonlyArray<ScoredRun>, value: (run: ScoredRun) => number) {
	const byTask = Map.groupBy(runs, (run) => run.entry.task);

	return mean([...byTask.values()].map((taskRuns) => mean(taskRuns.map(value))));
}

// A row is one config: a harness and a model at one reasoning effort.
export function configRows(
	entries: ReadonlyArray<LeaderboardEntry>,
	scoring: Scoring,
	weights: Weights
) {
	const scored = entries.map((entry) => ({ entry, ...runScore(entry, scoring, weights) }));

	const byConfig = Map.groupBy(scored, ({ entry }) =>
		[entry.harness, entry.model, entry.reasoning].join(' ')
	);

	return [...byConfig].map(([key, runs]) => {
		const [{ entry }] = runs;

		return {
			key,
			harness: entry.harness,
			model: entry.model,
			reasoning: entry.reasoning,
			runs: runs.toSorted((a, b) => b.score - a.score),
			score: meanOverTasks(runs, (run) => run.score),
			raw: meanOverTasks(runs, (run) => run.raw),
			parts: scoring.groups.map((_, index) => meanOverTasks(runs, (run) => run.parts[index])),
			costUsd: meanOverTasks(runs, (run) => run.entry.costUsd),
			minutes: meanOverTasks(runs, (run) => run.entry.minutes),
			tokens: meanOverTasks(runs, (run) => run.entry.tokens),
			boardUsd: meanOverTasks(runs, (run) => run.entry.boardUsd),
			tasks: new Set(runs.map((run) => run.entry.task)).size
		};
	});
}

export type ConfigRow = ReturnType<typeof configRows>[number];

// Scores that print the same to one decimal share a rank.
export function ranks(rows: ReadonlyArray<ConfigRow>) {
	const shown = (row: ConfigRow) => Math.round(row.score * 10);
	const ordered = rows.toSorted((a, b) => b.score - a.score);

	return new Map(
		ordered.map((row) => [row.key, ordered.findIndex((other) => shown(other) === shown(row)) + 1])
	);
}
