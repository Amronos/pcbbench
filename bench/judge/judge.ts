import { BunRuntime, BunServices } from '@effect/platform-bun';
import {
	Config,
	Effect,
	FileSystem,
	Option,
	Random,
	Schedule,
	Schema,
	SchemaIssue,
	Struct
} from 'effect';
import { Argument, Command } from 'effect/cli';
import { ChildProcess } from 'effect/process';
import { readRun, updateMetrics } from '../board.ts';
import { run } from '../command.ts';
import { isModelId, RUNS, type ModelId } from '../runs.ts';
import { buildPackage } from './package.ts';
import { judgeStateDirectory, writeReasoning } from './reasoning.ts';

const JUDGES: ModelId[] = ['gpt-6.1-sol', 'opus-5.5'];
const LAYERS = ['F.Silkscreen', 'B.Silkscreen', 'F.Mask', 'B.Mask', 'F.Fab', 'B.Fab'];
const JUDGE_TIMEOUT_HOURS = 4;
const JUDGE_ATTEMPTS = 3;

const Score = Schema.Int.check(Schema.isBetween({ minimum: 0, maximum: 10 }));

const YesNo = { crystal: Schema.Boolean, buttons: Schema.Boolean, powerPath: Schema.Boolean };

const Scores = {
	thermal: Score,
	grounding: Score,
	layout: Score,
	routing: Score,
	silkscreen: Score
};

const YES_NO = Struct.keys(YesNo);
const SCORES = Struct.keys(Scores);

const Review = Schema.Struct({ ...YesNo, ...Scores });

type Review = typeof Review.Type;

const ReviewJson = Schema.fromJsonString(Review);

const Json = Schema.fromJsonString(Schema.Unknown);

const Order = Schema.fromJsonString(Schema.Array(Schema.String));

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

	yield* remote('bash', '~/export-layers.sh', [...copperLayers, ...LAYERS].join(','));

	yield* rsync(`${box}:package/layers`, `${state}/package/`);

	const orderPath = `${state}/order.json`;

	if (!(yield* fs.exists(orderPath)))
		yield* fs.writeFileString(orderPath, JSON.stringify(yield* Random.shuffle(JUDGES)));

	const order = (yield* Schema.decodeEffect(Order)(yield* fs.readFileString(orderPath))).filter(
		(model): model is ModelId => isModelId(model) && JUDGES.includes(model)
	);

	yield* fs.makeDirectory(`${runDir}/review`, { recursive: true });

	const reviews: Review[] = [];

	// A judge's subagents keep running in its Sprocket server after `sprocket run` exits, so each judge starts on a cleared box.
	const clearJudge = remote('bash', '~/clear-judge.sh');

	yield* clearJudge;

	for (const model of order) {
		const reviewPath = `${runDir}/review/${model}.json`;

		for (let attempt = 1; attempt <= JUDGE_ATTEMPTS && !(yield* fs.exists(reviewPath)); attempt++) {
			const logs = `${state}/${model}/attempt-${attempt}`;
			yield* fs.makeDirectory(logs, { recursive: true });
			yield* remote('bash', '~/start-judge.sh', model, String(JUDGE_TIMEOUT_HOURS));

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

			const review = yield* Schema.decodeUnknownEffect(Review)(written.value, {
				errors: 'all'
			}).pipe(
				Effect.mapError(
					(error) =>
						new JudgeError({
							message: `${model}'s review of ${runId} has invalid ${standardIssues(error.issue)
								.issues.map((issue) => issue.path?.join('.'))
								.join(', ')}; see ${logs}`
						})
				)
			);

			yield* fs.writeFileString(reviewPath, `${JSON.stringify(review, null, '\t')}\n`);
		}

		if (!(yield* fs.exists(reviewPath)))
			return yield* new JudgeError({
				message: `${model} wrote no review of ${runId} in ${JUDGE_ATTEMPTS} attempts; see ${state}/${model}`
			});
		reviews.push(yield* Schema.decodeEffect(ReviewJson)(yield* fs.readFileString(reviewPath)));
	}

	yield* writeReasoning(runId, order);

	yield* updateMetrics(runId, {
		review: {
			judges: order,
			yesVotes: Object.fromEntries(
				YES_NO.map((key) => [key, reviews.filter((review) => review[key]).length])
			),
			meanScores: Object.fromEntries(
				SCORES.map((key) => [
					key,
					Math.round(
						(reviews.reduce((sum, review) => sum + review[key], 0) / reviews.length) * 10
					) / 10
				])
			)
		}
	});
});

Command.make(
	'judge',
	{
		runId: Argument.Literals(
			'run-id',
			RUNS.map((run) => run.id)
		),
		host: Argument.String('host').pipe(Argument.withDescription('Judge box address'))
	},
	judge
).pipe(Command.run({ version: '0.0.0' }), Effect.provide(BunServices.layer), BunRuntime.runMain);
