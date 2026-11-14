import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Config, Effect, FileSystem, Option, Schedule, Schema, SchemaIssue } from 'effect';
import { Argument, Command } from 'effect/cli';
import { ChildProcess } from 'effect/process';
import { readRun, RENDER_SIZE, RENDERS, updateMetrics } from '../board.ts';
import { run } from '../command.ts';
import { type ModelId, runIdArgument } from '../runs.ts';
import { buildPackage } from './package.ts';
import { judgeStateDirectory, writeReasoning } from './reasoning.ts';

const JUDGE: ModelId = 'opus-5.5';
const LAYERS = ['F.Silkscreen', 'B.Silkscreen', 'F.Mask', 'B.Mask', 'F.Fab', 'B.Fab'];
const JUDGE_TIMEOUT_HOURS = 4;
const JUDGE_ATTEMPTS = 3;

const FindingFields = {
	refs: Schema.Array(Schema.String),
	nets: Schema.Array(Schema.String),
	issue: Schema.String,
	evidence: Schema.String
};

const Finding = Schema.Union([
	Schema.Struct({
		area: Schema.Literals(['layout', 'routing']),
		severity: Schema.Literals(['minor', 'major', 'fatal']),
		...FindingFields
	}),
	Schema.Struct({
		area: Schema.Literal('other'),
		severity: Schema.Literal('fatal'),
		...FindingFields
	})
]);

const Review = Schema.Array(Finding);

type Review = typeof Review.Type;

const ReviewJson = Schema.fromJsonString(Review);

const Json = Schema.fromJsonString(Schema.Unknown);

const standardIssues = SchemaIssue.makeFormatterStandardSchemaV1();

class JudgeError extends Schema.TaggedError<JudgeError>()('JudgeError', {
	message: Schema.String
}) {}

const judge = Effect.fn('judge')(function* ({
	runId,
	host
}: {
	readonly runId: string;
	readonly host: string;
}) {
	const fs = yield* FileSystem.FileSystem;
	const { runDir, info, copperLayers } = yield* readRun(runId);
	const state = judgeStateDirectory(runId);

	const ssh = [
		'-i',
		`${yield* Config.String('HOME')}/.ssh/pcbbench.pem`,
		'-o',
		'BatchMode=yes',
		'-o',
		'ServerAliveInterval=30'
	];

	const box = `ubuntu@${host}`;
	const remote = (...command: string[]) => run(ChildProcess.make`ssh ${ssh} ${box} ${command}`);

	const rsync = (...paths: string[]) =>
		run(ChildProcess.make`rsync -az -e ${`ssh ${ssh.join(' ')}`} ${paths}`);

	yield* buildPackage(runId, `${state}/package`);

	yield* rsync(`${state}/package/`, `${box}:package/`);

	yield* rsync(
		`${import.meta.dir}/export-layers.sh`,
		`${import.meta.dir}/start-judge.sh`,
		`${import.meta.dir}/clear-judge.sh`,
		`${box}:`
	);

	yield* rsync(`${import.meta.dir}/prompt.md`, `${box}:.judge-prompt.md`);

	// Only the run's KiCad stays on the box, at a path that doesn't name the harness.
	const runVersion = info.versions.kicad.split(' ')[0];

	yield* remote(
		`[ -e /opt/kicad-run ] || { sudo mv /opt/kicad-versions/${runVersion} /opt/kicad-run && sudo rm -rf /opt/kicad-versions; }`
	);

	yield* remote('mkdir -p package/renders');

	for (const [name, args] of Object.entries(RENDERS))
		yield* remote(
			'/opt/kicad-run/bin/kicad-cli',
			'pcb',
			'render',
			...RENDER_SIZE,
			...args,
			'-o',
			`package/renders/${name}.png`,
			'package/board.kicad_pcb'
		);

	yield* remote('bash', '~/export-layers.sh', [...copperLayers, ...LAYERS].join(','));

	yield* rsync(`${box}:package/renders`, `${box}:package/layers`, `${state}/package/`);

	// The judge's copy is made from /root/package, so judges don't find a second copy of the board in their home folder.
	yield* remote('sudo rm -rf /root/package && sudo mv ~/package /root/package');

	yield* fs.makeDirectory(`${runDir}/review`, { recursive: true });

	// A judge's subagents keep running in its Sprocket server after `sprocket run` exits, so each judge starts on a cleared box.
	const clearJudge = remote('bash', '~/clear-judge.sh');

	yield* clearJudge;

	const reviewPath = `${runDir}/review/${JUDGE}.json`;

	for (let attempt = 1; attempt <= JUDGE_ATTEMPTS && !(yield* fs.exists(reviewPath)); attempt++) {
		const logs = `${state}/${JUDGE}/attempt-${attempt}`;
		yield* fs.makeDirectory(logs, { recursive: true });
		yield* remote('bash', '~/start-judge.sh', JUDGE, String(JUDGE_TIMEOUT_HOURS));

		yield* remote('cat ~/judge.exit 2>/dev/null || true').pipe(
			Effect.orElseSucceed(() => ''),
			Effect.repeat({
				until: (exit) => exit.trim() !== '',
				schedule: Schedule.spaced('1 minute')
			})
		);
		yield* rsync(
			`${box}:judge.out`,
			`${box}:judge.err`,
			`${box}:judge.exit`,
			`${box}:review`,
			`${box}:.sprocket/transcripts`,
			logs
		);
		yield* clearJudge;

		const written = yield* fs
			.readFileString(`${logs}/review/review.json`)
			.pipe(Effect.flatMap(Schema.decodeEffect(Json)), Effect.option);

		if (Option.isNone(written)) continue;

		const decoded = yield* Schema.decodeUnknownEffect(Review)(written.value, {
			errors: 'all'
		}).pipe(
			Effect.mapError(
				(error) =>
					new JudgeError({
						message: `${JUDGE}'s review of ${runId} has invalid ${standardIssues(error.issue)
							.issues.map((issue) => issue.path?.join('.'))
							.join(', ')}; see ${logs}`
					})
			)
		);

		yield* fs.writeFileString(reviewPath, `${JSON.stringify(decoded, null, '\t')}\n`);
	}

	if (!(yield* fs.exists(reviewPath)))
		return yield* new JudgeError({
			message: `${JUDGE} wrote no review of ${runId} in ${JUDGE_ATTEMPTS} attempts; see ${state}/${JUDGE}`
		});

	const review = yield* Schema.decodeEffect(ReviewJson)(yield* fs.readFileString(reviewPath));

	yield* writeReasoning(runId, [JUDGE]);

	const count = (area: Review[number]['area'], severity: Review[number]['severity']) =>
		review.filter((finding) => finding.area === area && finding.severity === severity).length;

	yield* updateMetrics(runId, {
		review: {
			judge: JUDGE,
			findings: {
				layout: { minor: count('layout', 'minor'), major: count('layout', 'major') },
				routing: { minor: count('routing', 'minor'), major: count('routing', 'major') },
				fatal: review.filter((finding) => finding.severity === 'fatal').length
			}
		}
	});
});

Command.make(
	'judge',
	{
		runId: runIdArgument,
		host: Argument.String('host').pipe(Argument.withDescription('Judge box address'))
	},
	judge
).pipe(Command.run({ version: '0.0.0' }), Effect.provide(BunServices.layer), BunRuntime.runMain);
