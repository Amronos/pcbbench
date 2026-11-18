import { useEffect, useState } from 'preact/hooks';
import type { LeaderboardData } from '../../data/leaderboard';
import styles from './Leaderboard.module.css';
import type { Weights } from './score';
import { MAX_WEIGHT } from './state';

type Props = {
	groups: LeaderboardData['groups'];
	weights: Weights;
	changed: boolean;
	onChange: (weights: Weights) => void;
	onReset: () => void;
};

export default function Mix({ groups, weights, changed, onChange, onReset }: Props) {
	const total = weights.reduce((sum, weight) => sum + weight, 0);
	const [open, setOpen] = useState(false);

	// A shared link with a custom mix opens with its weights showing.
	useEffect(() => {
		if (changed) setOpen(true);
	}, [changed]);

	return (
		<details class={styles.mix} open={open} onToggle={(event) => setOpen(event.currentTarget.open)}>
			<summary>
				Change the mix
				{changed && <span class={styles.mixNote}> (custom weights)</span>}
			</summary>
			<div class={styles.mixBody}>
				<p class={styles.mixHelp}>
					Each group's weight sets its share of the 100 points. The defaults are the official score.
				</p>
				<ul class={styles.weights}>
					{groups.map((group, index) => {
						const weight = weights[index];

						return (
							<li key={group.id} style={{ '--color': `var(--${group.id})` }}>
								<label for={`weight-${group.id}`}>
									<span class={styles.swatch} aria-hidden="true" />
									{group.label}
								</label>
								<input
									id={`weight-${group.id}`}
									type="range"
									min={0}
									max={MAX_WEIGHT}
									step={1}
									value={weight}
									aria-valuetext={`${weight}, ${share(weight, total)} of the score`}
									onInput={(event) =>
										onChange(weights.with(index, Number(event.currentTarget.value)))
									}
								/>
								<output for={`weight-${group.id}`} class={styles.share}>
									{share(weight, total)}
								</output>
							</li>
						);
					})}
				</ul>
				<button type="button" class={styles.reset} disabled={!changed} onClick={onReset}>
					Reset to {groups.map((group) => group.points).join(', ')}
				</button>
			</div>
		</details>
	);
}

const share = (weight: number, total: number) =>
	`${total ? Math.round((weight / total) * 100) : 0}%`;
