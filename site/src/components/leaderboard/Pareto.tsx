import { useEffect, useRef, useState } from 'preact/hooks';
import { points } from '../../data/format';
import type { LeaderboardData } from '../../data/leaderboard';
import styles from './Leaderboard.module.css';
import type { ConfigRow } from './score';
import { METRICS, X_AXES, lookup, type XAxis } from './state';

type Props = {
	data: LeaderboardData;
	rows: ReadonlyArray<ConfigRow>;
	x: XAxis;
	onX: (x: XAxis) => void;
};

const MARGIN = { top: 16, right: 20, bottom: 48, left: 44 };

// The harness palette in Leaderboard.module.css has this many colors.
const PALETTE_SIZE = 8;

function logTicks(low: number, high: number, ticks: ReadonlyArray<number>) {
	const perDecade = ticks.every((tick) => tick < 10);
	const firstDecade = Math.floor(Math.log10(low));
	const decades = Math.ceil(Math.log10(high)) - firstDecade + 1;

	const candidates = perDecade
		? Array.from({ length: decades }, (_, index) => 10 ** (firstDecade + index)).flatMap((decade) =>
				ticks.map((tick) => tick * decade)
			)
		: ticks;

	return candidates.filter((tick) => tick >= low && tick <= high);
}

// Higher score at a lower value is better, so each frontier row beats every row left of it.
function frontier(rows: ReadonlyArray<ConfigRow>, x: XAxis) {
	let best = -Infinity;

	return rows
		.toSorted((a, b) => a[x] - b[x] || b.score - a.score)
		.filter((row) => {
			if (row.score <= best) return false;

			best = row.score;

			return true;
		});
}

export default function Pareto({ data, rows, x, onX }: Props) {
	const wrap = useRef<HTMLDivElement>(null);
	const [width, setWidth] = useState(720);
	const [active, setActive] = useState<string | null>(null);

	useEffect(() => {
		const element = wrap.current;

		if (!element) return;

		const observer = new ResizeObserver(([entry]) => {
			setWidth(entry.contentRect.width);
		});

		observer.observe(element);

		return () => observer.disconnect();
	}, []);

	const metric = METRICS[x];
	const height = Math.round(Math.min(460, Math.max(300, width * 0.6)));
	const plotWidth = width - MARGIN.left - MARGIN.right;
	const plotHeight = height - MARGIN.top - MARGIN.bottom;
	const values = rows.map((row) => row[x]).filter((value) => value > 0);
	const low = Math.min(...values) / 1.35;
	const high = Math.max(...values) * 1.35;
	const scores = rows.map((row) => row.score);
	const scoreLow = Math.max(0, Math.floor((Math.min(...scores) - 5) / 10) * 10);
	const scoreHigh = Math.min(100, Math.ceil((Math.max(...scores) + 5) / 10) * 10);

	const scaleX = (value: number) =>
		MARGIN.left + (Math.log(Math.max(value, low) / low) / Math.log(high / low)) * plotWidth;

	const scaleY = (score: number) =>
		MARGIN.top + (1 - (score - scoreLow) / (scoreHigh - scoreLow)) * plotHeight;

	const allTicks = logTicks(low, high, metric.ticks);
	const tickStep = Math.ceil(allTicks.length / Math.max(2, Math.floor(plotWidth / 64)));
	const xTicks = allTicks.filter((_, index) => index % tickStep === 0);

	const yTicks = Array.from(
		{ length: (scoreHigh - scoreLow) / 10 + 1 },
		(_, index) => scoreLow + index * 10
	);

	const best = frontier(rows, x);
	const onFrontier = new Set(best.map((row) => row.key));

	const path = best
		.map((row, index) =>
			index === 0
				? `M${scaleX(row[x])},${scaleY(row.score)}`
				: `H${scaleX(row[x])}V${scaleY(row.score)}`
		)
		.join('');

	const harnessIndex = (id: string) => data.harnesses.findIndex((harness) => harness.id === id);
	const { harness: harnessName, model: modelName } = lookup(data);
	const color = (id: string) => `var(--h${harnessIndex(id) % PALETTE_SIZE})`;

	const shownHarnesses = data.harnesses.filter((harness) =>
		rows.some((row) => row.harness === harness.id)
	);

	const activeRow = rows.find((row) => row.key === active);

	const describe = (row: ConfigRow) =>
		`${modelName(row.model)} in ${harnessName(row.harness)}: ${points(row.score)} points, ${metric.label} ${metric.format(row[x])}`;

	return (
		<div class={styles.pareto}>
			<div class={styles.axisPicker} role="group" aria-label="Horizontal axis">
				<span class={styles.chipsLabel}>Score against</span>
				{X_AXES.map((axis) => (
					<button
						key={axis}
						type="button"
						class={styles.chip}
						aria-pressed={axis === x}
						onClick={() => onX(axis)}
					>
						{METRICS[axis].label}
					</button>
				))}
			</div>
			<div ref={wrap} class={styles.chart}>
				<svg
					width={width}
					height={height}
					viewBox={`0 0 ${width} ${height}`}
					role="group"
					aria-label={`Score against ${metric.label}, log scale`}
				>
					{yTicks.map((tick) => (
						<g key={tick} class={styles.gridline}>
							<line
								x1={MARGIN.left}
								x2={width - MARGIN.right}
								y1={scaleY(tick)}
								y2={scaleY(tick)}
							/>
							<text x={MARGIN.left - 8} y={scaleY(tick)} dy="0.32em" text-anchor="end">
								{tick}
							</text>
						</g>
					))}
					{xTicks.map((tick) => (
						<g key={tick} class={styles.gridline}>
							<line
								x1={scaleX(tick)}
								x2={scaleX(tick)}
								y1={MARGIN.top}
								y2={height - MARGIN.bottom}
							/>
							<text x={scaleX(tick)} y={height - MARGIN.bottom + 18} text-anchor="middle">
								{metric.tick(tick)}
							</text>
						</g>
					))}
					<text class={styles.axisTitle} x={MARGIN.left} y={height - 6}>
						{metric.label}, log scale →
					</text>
					<text
						class={styles.axisTitle}
						transform={`translate(12 ${MARGIN.top}) rotate(-90)`}
						text-anchor="end"
					>
						Score →
					</text>
					<path class={styles.frontier} d={path} />
					{rows.map((row) => {
						const cx = scaleX(row[x]);
						const cy = scaleY(row.score);
						const labelled = onFrontier.has(row.key) || row.key === active;
						// The frontier leaves each point to the right, so labels sit left of it or above it.
						const leftSide = cx > MARGIN.left + 110;
						const onlyRun = row.runs.length === 1 ? row.runs[0] : undefined;

						const dot = (
							<>
								<circle
									cx={cx}
									cy={cy}
									r={onFrontier.has(row.key) ? 7 : 5.5}
									fill={color(row.harness)}
									class={styles.dot}
								/>
								{labelled && (
									<text
										class={styles.pointLabel}
										x={leftSide ? cx - 11 : cx - 6}
										y={leftSide ? cy : cy - 15}
										dy="0.32em"
										text-anchor={leftSide ? 'end' : 'start'}
									>
										{modelName(row.model)}
									</text>
								)}
							</>
						);

						const events = {
							onMouseEnter: () => setActive(row.key),
							onMouseLeave: () => setActive(null),
							onFocus: () => setActive(row.key),
							onBlur: () => setActive(null)
						};

						return onlyRun ? (
							<a
								key={row.key}
								href={`/runs/${onlyRun.entry.runId}`}
								aria-label={describe(row)}
								class={styles.point}
								{...events}
							>
								{dot}
							</a>
						) : (
							<g
								key={row.key}
								tabIndex={0}
								role="img"
								aria-label={describe(row)}
								class={styles.point}
								{...events}
							>
								{dot}
							</g>
						);
					})}
				</svg>
				{activeRow && (
					<div
						class={styles.tooltip}
						style={{
							left: `${Math.min(scaleX(activeRow[x]), width - 180)}px`,
							top: `${scaleY(activeRow.score) + 14}px`
						}}
						aria-hidden="true"
					>
						<strong>{modelName(activeRow.model)}</strong>
						<span>{harnessName(activeRow.harness)}</span>
						<span>
							{points(activeRow.score)} points, {metric.format(activeRow[x])}
						</span>
					</div>
				)}
			</div>
			<ul class={styles.legend}>
				{shownHarnesses.map((harness) => (
					<li key={harness.id}>
						<span
							class={styles.legendDot}
							style={{ background: color(harness.id) }}
							aria-hidden="true"
						/>
						{harness.name}
					</li>
				))}
				<li>
					<span class={styles.legendLine} aria-hidden="true" />
					Frontier: nothing scores higher for less
				</li>
			</ul>
		</div>
	);
}
