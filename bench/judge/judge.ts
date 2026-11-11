import { $ } from 'bun';
import { mkdir } from 'node:fs/promises';
import { readRun } from '../board.ts';
import { isModelId, type ModelId } from '../runs.ts';
import { buildPackage } from './package.ts';
import { writeReasoning } from './reasoning.ts';

const JUDGES: ModelId[] = ['gpt-6.1-sol', 'opus-5.5'];
const YES_NO = ['crystal', 'buttons', 'powerPath'] as const;
const SCORES = ['thermal', 'grounding', 'layout', 'routing', 'silkscreen'] as const;
const LAYERS = ['F.Silkscreen', 'B.Silkscreen', 'F.Mask', 'B.Mask', 'F.Fab', 'B.Fab'];
const JUDGE_TIMEOUT_HOURS = 4;
const JUDGE_ATTEMPTS = 3;

type Review = Record<(typeof YES_NO)[number], boolean> & Record<(typeof SCORES)[number], number>;

const [runId, host] = Bun.argv.slice(2);

if (!runId || !host) throw new Error('Usage: bun judge/judge.ts <run id> <judge box address>');

const { runDir, info, copperLayers, updateMetrics } = await readRun(runId);
const state = `${import.meta.dir}/../.state/judge/${runId}`;

const ssh = [
	'-i',
	`${process.env.HOME}/.ssh/pcbbench.pem`,
	'-o',
	'BatchMode=yes',
	'-o',
	'ServerAliveInterval=30'
];

const box = `ubuntu@${host}`;
const remote = (...command: string[]) => $`ssh ${ssh} ${box} ${command}`.text();
const rsync = (...paths: string[]) => $`rsync -az -e ${`ssh ${ssh.join(' ')}`} ${paths}`.quiet();

await buildPackage(runId, `${state}/package`);

await rsync(`${state}/package/`, `${box}:package/`);

await rsync(
	`${import.meta.dir}/export-layers.sh`,
	`${import.meta.dir}/start-judge.sh`,
	`${import.meta.dir}/clear-judge.sh`,
	`${box}:`
);

await rsync(`${import.meta.dir}/prompt.md`, `${box}:.judge-prompt.md`);

// Only the run's KiCad stays on the box, at a path that doesn't name the harness.
const runVersion = info.versions.kicad.split(' ')[0];

await remote(
	`[ -e /opt/kicad-run ] || { sudo mv /opt/kicad-versions/${runVersion} /opt/kicad-run && sudo rm -rf /opt/kicad-versions; }`
);

await remote('bash', '~/export-layers.sh', [...copperLayers, ...LAYERS].join(','));

await rsync(`${box}:package/layers`, `${state}/package/`);

const orderPath = `${state}/order.json`;

if (!(await Bun.file(orderPath).exists()))
	await Bun.write(orderPath, JSON.stringify(JUDGES.toSorted(() => Math.random() - 0.5)));

const order: ModelId[] = (await Bun.file(orderPath).json()).filter(
	(model: string) => isModelId(model) && JUDGES.includes(model)
);

await mkdir(`${runDir}/review`, { recursive: true });

const reviews: Record<string, Review> = {};

// A judge's subagents keep running in its Sprocket server after `sprocket run` exits, so each judge starts on a cleared box.
const clearJudge = () => remote('bash', '~/clear-judge.sh');

await clearJudge();

for (const model of order) {
	const reviewPath = `${runDir}/review/${model}.json`;

	for (
		let attempt = 1;
		attempt <= JUDGE_ATTEMPTS && !(await Bun.file(reviewPath).exists());
		attempt++
	) {
		const logs = `${state}/${model}/attempt-${attempt}`;
		await mkdir(logs, { recursive: true });
		await remote('bash', '~/start-judge.sh', model, String(JUDGE_TIMEOUT_HOURS));

		while (!(await remote('cat ~/judge.exit 2>/dev/null || true').catch(() => '')).trim())
			await Bun.sleep(60_000);
		await rsync(
			`${box}:judge.out`,
			`${box}:judge.err`,
			`${box}:judge.exit`,
			`${box}:review`,
			`${box}:.sprocket/transcripts`,
			logs
		);
		await clearJudge();

		const review: Review | null = await Bun.file(`${logs}/review/review.json`)
			.json()
			.catch(() => null);

		if (!review) continue;

		const invalid = [
			...YES_NO.filter((key) => typeof review[key] !== 'boolean'),
			...SCORES.filter(
				(key) => !Number.isInteger(review[key]) || review[key] < 0 || review[key] > 10
			)
		];

		if (invalid.length)
			throw new Error(
				`${model}'s review of ${runId} has invalid ${invalid.join(', ')}; see ${logs}`
			);
		await Bun.write(
			reviewPath,
			`${JSON.stringify(Object.fromEntries([...YES_NO, ...SCORES].map((key) => [key, review[key]])), null, '\t')}\n`
		);
	}

	if (!(await Bun.file(reviewPath).exists()))
		throw new Error(
			`${model} wrote no review of ${runId} in ${JUDGE_ATTEMPTS} attempts; see ${state}/${model}`
		);
	reviews[model] = await Bun.file(reviewPath).json();
}

const all = Object.values(reviews);

await writeReasoning(runId, order);

await updateMetrics({
	review: {
		judges: order,
		yesVotes: Object.fromEntries(
			YES_NO.map((key) => [key, all.filter((review) => review[key]).length])
		),
		meanScores: Object.fromEntries(
			SCORES.map((key) => [
				key,
				Math.round((all.reduce((sum, review) => sum + review[key], 0) / all.length) * 10) / 10
			])
		)
	}
});
