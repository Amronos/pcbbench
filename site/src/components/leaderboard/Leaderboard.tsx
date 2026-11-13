import { useEffect, useState } from 'preact/hooks';
import type { LeaderboardData } from '../../data/leaderboard';
import styles from './Leaderboard.module.css';
import Mix from './Mix';
import Pareto from './Pareto';
import { configRows, isOfficialMix, ranks } from './score';
import { defaultState, parseState, stateQuery, type State } from './state';
import Table from './Table';

export default function Leaderboard({ data }: { data: LeaderboardData }) {
	const [state, setState] = useState(() => defaultState(data));
	const [loaded, setLoaded] = useState(false);
	const [copied, setCopied] = useState(false);
	const update = (change: Partial<State>) => setState((current) => ({ ...current, ...change }));
	const officialWeights = defaultState(data).weights;
	const manyTasks = data.tasks.length > 1;

	// The server renders the defaults, so the URL is read once the page is live.
	useEffect(() => {
		setState(parseState(window.location.search, data));
		setLoaded(true);
	}, [data]);

	useEffect(() => {
		if (!loaded) return;

		const query = stateQuery(state, data);

		window.history.replaceState(
			window.history.state,
			'',
			`${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`
		);
	}, [state, loaded, data]);

	const inScope = data.entries.filter((entry) => !state.task || entry.task === state.task);
	const harnessIds = new Set<string>(inScope.map((entry) => entry.harness));
	const modelIds = new Set<string>(inScope.map((entry) => entry.model));
	const harnesses = data.harnesses.filter((harness) => harnessIds.has(harness.id));
	const models = data.models.filter((model) => modelIds.has(model.id));

	const shown = inScope.filter(
		(entry) =>
			(!state.harnesses.length || state.harnesses.includes(entry.harness)) &&
			(!state.models.length || state.models.includes(entry.model))
	);

	const rows = configRows(shown, data, state.weights);
	const officialRanks = ranks(configRows(shown, data, officialWeights));
	const mixChanged = !isOfficialMix(state.weights, data.groups);

	const toggle = (list: ReadonlyArray<string>, id: string) =>
		list.includes(id) ? list.filter((item) => item !== id) : [...list, id];

	const copyLink = () =>
		navigator.clipboard.writeText(window.location.href).then(
			() => {
				setCopied(true);
				window.setTimeout(() => setCopied(false), 2000);
			},
			() => window.prompt('Copy this link', window.location.href)
		);

	return (
		<div class={styles.leaderboard}>
			<div class={styles.toolbar}>
				<div class={styles.segmented} role="group" aria-label="View">
					<button
						type="button"
						aria-pressed={state.view === 'table'}
						onClick={() => update({ view: 'table' })}
					>
						Table
					</button>
					<button
						type="button"
						aria-pressed={state.view === 'pareto'}
						onClick={() => update({ view: 'pareto' })}
					>
						Pareto
					</button>
				</div>
				{manyTasks && (
					<label class={styles.taskSelect}>
						<span class="visually-hidden">Task</span>
						<select
							value={state.task ?? ''}
							onChange={(event) => update({ task: event.currentTarget.value || null })}
						>
							<option value="">All tasks</option>
							{data.tasks.map((option) => (
								<option key={option.id} value={option.id}>
									{option.name}
								</option>
							))}
						</select>
					</label>
				)}
				<button type="button" class={styles.copy} onClick={copyLink}>
					{copied ? 'Link copied' : 'Copy link'}
				</button>
			</div>

			<div class={styles.filters}>
				{harnesses.length > 1 && (
					<Chips
						label="Harness"
						options={harnesses}
						selected={state.harnesses}
						onToggle={(id) => update({ harnesses: toggle(state.harnesses, id) })}
					/>
				)}
				{models.length > 1 && (
					<Chips
						label="Model"
						options={models}
						selected={state.models}
						onToggle={(id) => update({ models: toggle(state.models, id) })}
					/>
				)}
			</div>

			<Mix
				groups={data.groups}
				weights={state.weights}
				changed={mixChanged}
				onChange={(weights) => update({ weights })}
				onReset={() => update({ weights: officialWeights })}
			/>

			{rows.length === 0 && <p class={styles.empty}>No runs match these filters.</p>}
			{rows.length > 0 && state.view === 'table' && (
				<Table
					data={data}
					rows={rows}
					ranks={ranks(rows)}
					officialRanks={mixChanged ? officialRanks : null}
					sort={state.sort}
					descending={state.descending}
					onSort={(sort, descending) => update({ sort, descending })}
					showTasks={manyTasks && !state.task}
				/>
			)}
			{rows.length > 0 && state.view === 'pareto' && (
				<Pareto data={data} rows={rows} x={state.x} onX={(x) => update({ x })} />
			)}
		</div>
	);
}

type ChipsProps = {
	label: string;
	options: ReadonlyArray<{ id: string; name: string }>;
	selected: ReadonlyArray<string>;
	onToggle: (id: string) => void;
};

function Chips({ label, options, selected, onToggle }: ChipsProps) {
	return (
		<div class={styles.chips} role="group" aria-label={`Filter by ${label.toLowerCase()}`}>
			<span class={styles.chipsLabel}>{label}</span>
			{options.map((option) => (
				<button
					key={option.id}
					type="button"
					class={styles.chip}
					aria-pressed={selected.includes(option.id)}
					onClick={() => onToggle(option.id)}
				>
					{option.name}
				</button>
			))}
		</div>
	);
}
