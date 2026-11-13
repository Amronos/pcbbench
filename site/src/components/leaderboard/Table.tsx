import { useState } from 'preact/hooks';
import { points } from '../../data/format';
import type { LeaderboardData } from '../../data/leaderboard';
import styles from './Leaderboard.module.css';
import type { ConfigRow, ScoredRun } from './score';
import {
	METRIC_KEYS,
	METRICS,
	descendingFirst,
	lookup,
	type MetricKey,
	type SortKey
} from './state';

type Props = {
	data: LeaderboardData;
	rows: ReadonlyArray<ConfigRow>;
	ranks: Map<string, number>;
	// Ranks under the official weights, shown as movement while the mix is changed.
	officialRanks: Map<string, number> | null;
	sort: SortKey;
	descending: boolean;
	onSort: (sort: SortKey, descending: boolean) => void;
	showTasks: boolean;
};

const LOW_PRIORITY: ReadonlyArray<MetricKey> = ['minutes', 'tokens'];

const metricClass = (key: MetricKey) =>
	[styles.num, LOW_PRIORITY.includes(key) && styles.lowPriority].filter(Boolean).join(' ');

export default function Table({
	data,
	rows,
	ranks,
	officialRanks,
	sort,
	descending,
	onSort,
	showTasks
}: Props) {
	const [expanded, setExpanded] = useState<ReadonlySet<string>>(new Set());
	const { harness: harnessName, model: modelName, maker, task: taskName } = lookup(data);

	const compare = (a: ConfigRow, b: ConfigRow) => {
		if (sort === 'model') return modelName(a.model).localeCompare(modelName(b.model));

		if (sort === 'harness') return harnessName(a.harness).localeCompare(harnessName(b.harness));

		return a[sort] - b[sort];
	};

	const sorted = rows.toSorted(
		(a, b) => (descending ? -1 : 1) * compare(a, b) || b.score - a.score
	);

	const header = (key: SortKey, label: string, className?: string, title?: string) => {
		const active = sort === key;

		return (
			<th
				scope="col"
				class={className}
				aria-sort={active ? (descending ? 'descending' : 'ascending') : undefined}
			>
				<button
					type="button"
					class={styles.sortButton}
					title={title}
					onClick={() => onSort(key, active ? !descending : descendingFirst(key))}
				>
					{label}
					<span class={styles.sortMark} aria-hidden="true">
						{active ? (descending ? '↓' : '↑') : ''}
					</span>
				</button>
			</th>
		);
	};

	const toggle = (key: string) =>
		setExpanded((current) => {
			const next = new Set(current);

			if (!next.delete(key)) next.add(key);

			return next;
		});

	return (
		<div class={styles.tableWrap}>
			<table class={styles.table}>
				<thead>
					<tr>
						<th scope="col" class={styles.rank}>
							<span class="visually-hidden">Rank</span>
						</th>
						{header('model', 'Model')}
						{header('harness', 'Harness', styles.harnessCol)}
						{header('score', 'Score', styles.scoreCol)}
						{showTasks && header('tasks', 'Tasks', styles.num, 'Tasks this config ran')}
						{METRIC_KEYS.map((key) =>
							header(key, METRICS[key].label, metricClass(key), METRICS[key].title)
						)}
					</tr>
				</thead>
				<tbody>
					{sorted.map((row) => {
						const rank = ranks.get(row.key) ?? 0;
						const move = (officialRanks?.get(row.key) ?? rank) - rank;
						const onlyRun = row.runs.length === 1 ? row.runs[0] : undefined;
						const open = expanded.has(row.key);

						return [
							<tr key={row.key} class={styles.row}>
								<td class={styles.rank}>
									{rank}
									{move !== 0 && (
										<span
											class={move > 0 ? styles.up : styles.down}
											title={`${Math.abs(move)} ${move > 0 ? 'up' : 'down'} from the official mix`}
										>
											{move > 0 ? '▲' : '▼'}
											{Math.abs(move)}
										</span>
									)}
								</td>
								<th scope="row" class={styles.who}>
									{onlyRun ? (
										<a class={styles.modelName} href={`/runs/${onlyRun.entry.runId}`}>
											{modelName(row.model)}
										</a>
									) : (
										<button
											type="button"
											class={styles.expand}
											aria-expanded={open}
											onClick={() => toggle(row.key)}
										>
											<span class={styles.modelName}>{modelName(row.model)}</span>
											<span class={styles.runCount}>
												{row.runs.length} runs {open ? '▴' : '▾'}
											</span>
										</button>
									)}
									<span class={styles.meta}>
										<span class={styles.maker}>{maker(row.model)}, </span>
										{row.reasoning} reasoning
									</span>
									<span class={`${styles.meta} ${styles.harnessInline}`}>
										{harnessName(row.harness)}
									</span>
								</th>
								<td class={styles.harnessCol}>{harnessName(row.harness)}</td>
								<td class={styles.scoreCol}>
									<ScoreBar data={data} scored={row} runs={row.runs} />
								</td>
								{showTasks && <td class={styles.num}>{row.tasks}</td>}
								{METRIC_KEYS.map((key) => (
									<td key={key} class={metricClass(key)}>
										{METRICS[key].format(row[key])}
									</td>
								))}
							</tr>,
							...(open
								? row.runs.map((run) => {
										const repeats = row.runs.filter((other) => other.entry.task === run.entry.task);

										return (
											<tr key={run.entry.runId} class={styles.subRow}>
												<td class={styles.rank} />
												<th scope="row" class={styles.who}>
													<a href={`/runs/${run.entry.runId}`}>
														{taskName(run.entry.task)}
														{repeats.length > 1 && `, run ${repeats.indexOf(run) + 1}`}
													</a>
												</th>
												<td class={styles.harnessCol} />
												<td class={styles.scoreCol}>
													<ScoreBar data={data} scored={run} runs={[run]} />
												</td>
												{showTasks && <td />}
												{METRIC_KEYS.map((key) => (
													<td key={key} class={metricClass(key)}>
														{METRICS[key].format(run.entry[key])}
													</td>
												))}
											</tr>
										);
									})
								: [])
						];
					})}
				</tbody>
			</table>
			<p class={styles.columnsNote}>
				{rows.some((row) => row.runs.length > 1) &&
					"A row with several runs shows the mean over tasks of each task's mean. "}
				Board price is for one assembled board when ordering 5 from PCBWay, without shipping.
			</p>
		</div>
	);
}

type BarProps = {
	data: LeaderboardData;
	scored: Pick<ScoredRun, 'parts' | 'raw' | 'score'>;
	runs: ReadonlyArray<ScoredRun>;
};

function ScoreBar({ data, scored: { parts, raw, score }, runs }: BarProps) {
	// Under the default mix the score is the bench's own rounded total, so tiny gaps are rounding.
	const penalty = raw - score > 0.5 ? raw - score : 0;

	const label = [
		...data.groups.map((group, index) => `${group.label} ${points(parts[index])}`),
		...(penalty ? [`minus ${points(penalty)} for a failed gate`] : [])
	].join(', ');

	return (
		<span class={styles.score}>
			<span class={styles.scoreNum}>{points(score)}</span>
			<span class={styles.bar} role="img" aria-label={label} title={label}>
				{data.groups.map((group, index) => (
					<span
						key={group.id}
						class={styles.segment}
						style={{
							width: `${parts[index].toFixed(2)}%`,
							background: `var(--${group.id})`
						}}
					/>
				))}
				{penalty > 0 && (
					<span class={styles.penalty} style={{ left: `${score}%`, width: `${penalty}%` }} />
				)}
			</span>
			<GateNote data={data} runs={runs} />
		</span>
	);
}

function GateNote({ data, runs }: { data: LeaderboardData; runs: ReadonlyArray<ScoredRun> }) {
	const failed = runs.filter((run) => run.entry.failedGates.length);

	if (!failed.length) return null;

	const gates = [...new Set(failed.flatMap((run) => run.entry.failedGates))].join(', ');

	return (
		<span class={styles.gate}>
			−{data.gatePenalty}
			{runs.length > 1 && ` on ${failed.length} of ${runs.length} runs`}, gate failed: {gates}
		</span>
	);
}
