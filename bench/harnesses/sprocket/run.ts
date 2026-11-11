import { BunRuntime, BunServices } from '@effect/platform-bun';
import {
	Console,
	DateTime,
	Effect,
	FileSystem,
	Option,
	Predicate,
	Runtime,
	Schema,
	Sink,
	Stdio,
	Stream
} from 'effect';
import type { PlatformError } from 'effect/PlatformError';
import { Argument, Command } from 'effect/cli';
import { ChildProcess, ChildProcessSpawner } from 'effect/process';
import { homedir } from 'node:os';
import {
	MODELS,
	REASONING_EFFORT,
	WALL_CLOCK_LIMIT_HOURS,
	renderPrompt,
	type ModelId
} from '../../runs.ts';

const WORK_DIR = `${homedir()}/pcbbench-run`;
const THREAD_HEADER = /Thread (\S+) \| Run (\S+)/;

class SprocketError extends Schema.TaggedError<SprocketError>()('SprocketError', {
	message: Schema.String
}) {}

// The run's own exit code becomes the driver's, as `sprocket run` already printed why it stopped.
class SprocketRunExit extends Schema.TaggedError<SprocketRunExit>()('SprocketRunExit', {
	exitCode: Schema.Number
}) {
	get [Runtime.errorExitCode]() {
		return this.exitCode;
	}

	readonly [Runtime.errorReported] = false;
}

type Result = {
	runId: string;
	harness: 'sprocket';
	model: ModelId;
	reasoning: typeof REASONING_EFFORT;
	sprocketVersion: string;
	workDir: string;
	startedAt: string;
	finishedAt?: string;
	threadId?: string;
	sprocketRunId?: string;
	exitCode?: number;
};

const now = DateTime.now.pipe(Effect.map(DateTime.formatIso));

const run = Effect.fn('run')(function* (runId: string, model: ModelId, promptFile?: string) {
	const fs = yield* FileSystem.FileSystem;
	const spawner = yield* ChildProcessSpawner.ChildProcessSpawner;
	const stdio = yield* Stdio.Stdio;
	const resultDir = `${homedir()}/pcbbench-results/${runId}`;

	yield* fs.makeDirectory(WORK_DIR, { recursive: true });

	if ((yield* fs.readDirectory(WORK_DIR)).length > 0)
		return yield* new SprocketError({
			message: `${WORK_DIR} is not empty; use a fresh box or clear it first.`
		});

	yield* fs.makeDirectory(resultDir, { recursive: true });

	// Each box needs its own login; a copied refresh token dies 30 s after any other copy refreshes.
	const signedIn = yield* spawner.exitCode(
		ChildProcess.make('sprocket', ['run', '--list-models'], {
			stdin: 'ignore',
			stdout: 'ignore',
			stderr: 'ignore'
		})
	);

	if (signedIn !== 0) {
		// Like the run below, this stays in the terminal's process group: the login reads the
		// terminal, and a hangup that ends the driver also ends the run instead of orphaning it.
		const login = yield* spawner.exitCode(
			ChildProcess.make('sprocket', ['login', '--credential-store', 'file'], {
				stdin: 'inherit',
				stdout: 'inherit',
				stderr: 'inherit',
				detached: false
			})
		);

		if (login !== 0) return yield* new SprocketError({ message: 'sprocket login failed' });
	}

	const renderedPrompt = `${resultDir}/prompt.md`;

	yield* fs.writeFileString(renderedPrompt, yield* renderPrompt(model, promptFile));

	const result: Result = {
		runId,
		harness: 'sprocket',
		model,
		reasoning: REASONING_EFFORT,
		sprocketVersion: (yield* spawner.string(
			ChildProcess.make('sprocket', ['--version'], { stdin: 'ignore', stderr: 'inherit' })
		)).trim(),
		workDir: WORK_DIR,
		startedAt: yield* now
	};

	const saveResult = () =>
		fs.writeFileString(`${resultDir}/result.json`, `${JSON.stringify(result, null, '\t')}\n`);

	yield* saveResult();

	const child = yield* spawner.spawn(
		ChildProcess.make(
			'sprocket',
			[
				'run',
				'--prompt-file',
				renderedPrompt,
				'-C',
				WORK_DIR,
				'--model',
				model,
				'--reasoning',
				REASONING_EFFORT,
				'--timeout',
				`${WALL_CLOCK_LIMIT_HOURS}h`
			],
			{ stdin: 'ignore', detached: false }
		)
	);

	const tee =
		(path: string, echo: Sink.Sink<void, Uint8Array, never, PlatformError>) =>
		(output: Stream.Stream<Uint8Array, PlatformError>) =>
			output.pipe(Stream.tapSink(fs.sink(path)), Stream.tapSink(echo));

	yield* Effect.all(
		[
			child.stdout.pipe(tee(`${resultDir}/stdout.md`, stdio.stdout()), Stream.runDrain),
			child.stderr.pipe(
				tee(`${resultDir}/stderr.log`, stdio.stderr()),
				Stream.decodeText(),
				Stream.splitLines,
				Stream.map((line) => line.match(THREAD_HEADER)),
				Stream.filter(Predicate.isNotNull),
				Stream.runForEach(([, threadId, sprocketRunId]) => {
					if (result.threadId) return Effect.void;
					result.threadId = threadId;
					result.sprocketRunId = sprocketRunId;

					return saveResult();
				})
			)
		],
		{ concurrency: 'unbounded' }
	);

	const exitCode = yield* child.exitCode;

	result.exitCode = exitCode;
	result.finishedAt = yield* now;
	yield* saveResult();
	yield* Console.error(
		`\nSaved ${resultDir}/result.json (thread ${result.threadId}, exit ${exitCode})`
	);

	if (exitCode !== 0) return yield* new SprocketRunExit({ exitCode });
}, Effect.scoped);

Command.make(
	'sprocket',
	{
		runId: Argument.String('run-id'),
		model: Argument.Literals('model', MODELS),
		promptFile: Argument.String('smoke-test-prompt-file').pipe(Argument.optional)
	},
	({ runId, model, promptFile }) => run(runId, model, Option.getOrUndefined(promptFile))
).pipe(Command.run({ version: '0.0.0' }), Effect.provide(BunServices.layer), BunRuntime.runMain);
