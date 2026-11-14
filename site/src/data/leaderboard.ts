import { GATE_PENALTY, GROUPS, groupPoints } from '@pcbbench/bench/scoring';
import { weightedScore } from '../components/leaderboard/score';
import { HARNESSES, MODELS } from './catalog';
import { runs, tasks } from './runs';
import { GROUP_LABELS, failedGateLabel, groupShares } from './scoring';

// Everything the leaderboard island needs, small enough to serialise into the page.
export const leaderboard = {
	entries: runs.map((run) => ({
		runId: run.id,
		task: run.task,
		harness: run.harness.id,
		model: run.model.id,
		reasoning: run.reasoning,
		shares: groupShares(run),
		failedGates: run.metrics.score.failedGates.map(failedGateLabel),
		score: run.metrics.score.total,
		costUsd: run.metrics.costUsd,
		minutes: run.metrics.minutes,
		tokens: run.totalTokens,
		boardUsd: run.metrics.boardCost.fiveBoards.perBoardUsd
	})),
	tasks: tasks.map((task) => ({ id: task.id, name: task.name })),
	harnesses: Object.entries(HARNESSES).map(([id, harness]) => ({
		id,
		name: harness.name,
		url: harness.url
	})),
	models: Object.entries(MODELS).map(([id, model]) => ({ id, ...model })),
	groups: GROUPS.map((group) => ({
		id: group,
		label: GROUP_LABELS[group],
		points: groupPoints(group)
	})),
	gatePenalty: GATE_PENALTY
};

export type LeaderboardData = typeof leaderboard;

export type LeaderboardEntry = LeaderboardData['entries'][number];

const officialWeights = leaderboard.groups.map((group) => group.points);

for (const entry of leaderboard.entries) {
	const { score } = weightedScore(entry, leaderboard, officialWeights);

	if (Math.abs(score - entry.score) > 0.1)
		throw new Error(`${entry.runId} scores ${score} with the default mix, not ${entry.score}`);
}

// Vercel builds without the git history, so this is the day the newest run finished.
export const lastUpdated = runs
	.map((run) => run.metrics.finishedAt.slice(0, 10))
	.reduce((latest, day) => (day > latest ? day : latest));
