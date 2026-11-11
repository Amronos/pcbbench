import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Console, Effect, FileSystem, Option, Schema, Stream } from 'effect';
import type { PlatformError } from 'effect/PlatformError';
import { Argument, Command } from 'effect/cli';
import { ChildProcess, ChildProcessSpawner } from 'effect/process';
import { homedir } from 'node:os';
import { runDirectory } from './board.ts';
import { readBudget, readRunKey, spentUsd } from './gateway.ts';
import {
	BACKPLANE_CLI,
	REASONING_EFFORT,
	RUNS,
	kicadFullVersion,
	minutesBetween,
	parseVersions,
	type Run
} from './runs.ts';
import { claudeCodeUsage, codexUsage, type TokenUsage } from './usage.ts';

// GitHub rejects files over 100 MB; agents sometimes leave large downloads in their folder.
const MAX_FILE_SIZE = '50M';
const USAGE = 'Usage: bun bench/collect.ts <run id> [user@host, for Linux runs]';
const SSH_OPTIONS = ['-i', `${homedir()}/.ssh/pcbbench.pem`, '-o', 'BatchMode=yes'];
const FIND_LARGE = `find pcbbench-run -type f -size +${MAX_FILE_SIZE}`;

const CREDENTIALS =
	'vck_[A-Za-z0-9]{20,}|gh[opsu]_[A-Za-z0-9]{30,}|\\bsk-[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}';

class CollectError extends Schema.TaggedError<CollectError>()('CollectError', {
	message: Schema.String
}) {}

type Timing = { startedAt: string; finishedAt: string; minutes: number; endedBy: string };

type Shell = (
	script: string
) => Effect.Effect<string, CollectError | PlatformError, ChildProcessSpawner.ChildProcessSpawner>;

type Read<A> = Effect.Effect<
	A,
	CollectError | PlatformError | Schema.SchemaError,
	FileSystem.FileSystem | ChildProcessSpawner.ChildProcessSpawner
>;

type CollectedHarness = {
	logs: (runId: string, source: string) => [from: string, local: string][];
	timing: (logsDir: string) => Read<Timing>;
	tokens: (logsDir: string, run: Run) => Read<TokenUsage | null>;
	// Linux boxes are asked directly; the Codex driver records the Mac's versions when the run starts.
	versions: (logsDir: string, shell: Shell) => Read<Record<string, string>>;
};

const readJson = <S extends Schema.ConstraintDecoder<unknown>>(path: string, schema: S) =>
	FileSystem.FileSystem.pipe(
		Effect.flatMap((fs) => fs.readFileString(path)),
		Effect.flatMap(Schema.decodeUnknownEffect(Schema.fromJsonString(schema)))
	);

const readJsonOr = <S extends Schema.ConstraintDecoder<unknown>>(
	path: string,
	schema: S,
	missing: S['Type']
) =>
	FileSystem.FileSystem.pipe(
		Effect.flatMap((fs) => fs.exists(path)),
		Effect.flatMap((exists) => (exists ? readJson(path, schema) : Effect.succeed(missing)))
	);

const output = Effect.fnUntraced(function* (command: ChildProcess.StandardCommand) {
	const handle = yield* command;

	const [stdout, exitCode] = yield* Effect.all(
		[Stream.mkString(Stream.decodeText(handle.stdout)), handle.exitCode],
		{ concurrency: 'unbounded' }
	);

	if (exitCode !== 0)
		return yield* new CollectError({ message: `${command.command} exited with ${exitCode}` });

	return stdout;
}, Effect.scoped);

const CodexResult = Schema.Struct({
	startedAt: Schema.String,
	finishedAt: Schema.String,
	outcome: Schema.String,
	versions: Schema.Record(Schema.String, Schema.String)
});

const BackplaneSummary = Schema.Struct({
	startedAt: Schema.String,
	endedAt: Schema.String,
	minutes: Schema.Number,
	status: Schema.String
});

const SprocketResult = Schema.Struct({
	startedAt: Schema.String,
	finishedAt: Schema.String,
	activeMinutes: Schema.optional(Schema.Number),
	exitCode: Schema.Number
});

// The Codex driver copies the Mac's results to this machine, so Mac runs are collected from that local folder.
const codexDesktop: CollectedHarness = {
	logs: (runId, source) => [
		[source, 'codex-desktop'],
		[`${import.meta.dir}/.state/${runId}.driver.log`, 'driver.log']
	],
	timing: (logsDir) =>
		readJson(`${logsDir}/codex-desktop/result.json`, CodexResult).pipe(
			Effect.map((result) => ({
				startedAt: result.startedAt,
				finishedAt: result.finishedAt,
				minutes: minutesBetween(Date.parse(result.startedAt), Date.parse(result.finishedAt)),
				endedBy: result.outcome === 'task_complete' ? 'done' : result.outcome
			}))
		),
	tokens: (logsDir) => codexUsage(logsDir),
	versions: (logsDir) =>
		readJson(`${logsDir}/codex-desktop/result.json`, CodexResult).pipe(
			Effect.map((result) => result.versions)
		)
};

const HARNESSES: Record<Run['harness'], CollectedHarness> = {
	backplane: {
		logs: (runId, source) => [
			[`${source}pcbbench-logs/${runId}/`, 'backplane'],
			[`${source}driver.log`, 'driver.log']
		],
		timing: (logsDir) =>
			readJson(`${logsDir}/backplane/summary.json`, BackplaneSummary).pipe(
				Effect.map((summary) => ({
					startedAt: summary.startedAt,
					finishedAt: summary.endedAt,
					minutes: summary.minutes,
					endedBy: summary.status
				}))
			),
		tokens: (logsDir, run) =>
			BACKPLANE_CLI[run.model] === 'claude' ? claudeCodeUsage(logsDir) : codexUsage(logsDir),
		versions: (_, shell) =>
			shell(`echo "backplane=$(~/.local/share/backplane/builds/*/backplane-hub --version)"
echo "claudeCode=$(~/.local/bin/claude --version)"
echo "codex=$(codex --version)"
kicad=$(ls -d ~/.local/share/backplane/kicad/*/ | head -1)
echo "kicad=$(basename $kicad) ($(cat $kicad/SOURCE_COMMIT))"`).pipe(Effect.map(parseVersions))
	},
	sprocket: {
		logs: (runId, source) => [
			[`${source}pcbbench-results/${runId}/`, 'sprocket'],
			[`${source}.sprocket/transcripts/`, 'sprocket-transcripts'],
			[`${source}driver.log`, 'driver.log']
		],
		timing: (logsDir) =>
			readJson(`${logsDir}/sprocket/result.json`, SprocketResult).pipe(
				Effect.map((result) => ({
					startedAt: result.startedAt,
					finishedAt: result.finishedAt,
					// Runs resumed after server errors record only the time a turn was running.
					minutes:
						result.activeMinutes ??
						minutesBetween(Date.parse(result.startedAt), Date.parse(result.finishedAt)),
					endedBy: result.exitCode === 0 ? 'done' : `exit ${result.exitCode}`
				}))
			),
		// Sprocket keeps token usage in its cloud; it is read from the thread in the web UI and added to metrics.json by hand.
		tokens: () => Effect.succeed(null),
		versions: (_, shell) =>
			shell(`echo "sprocket=$(sprocket --version)"
echo "kicadConnector=$(ls ~/.sprocket/connectors/kicad | grep '^v')"
echo "kicad=${kicadFullVersion('~/.sprocket/connectors/kicad/bin/kicad-cli')}"`).pipe(
				Effect.map(parseVersions)
			)
	},
	'codex-desktop': codexDesktop,
	'codex-desktop-texttocad': codexDesktop
};

const machine = (run: Run, host: Option.Option<string>) => {
	if (run.machine === 'mac') {
		const source = `${homedir()}/pcbbench-results/${run.id}/`;

		return Effect.succeed({
			source,
			shell: (script: string) => output(ChildProcess.make(script, { cwd: source, shell: true }))
		});
	}

	return Option.match(host, {
		onNone: () => Effect.fail(new CollectError({ message: USAGE })),
		onSome: (host) =>
			Effect.succeed({
				source: `${host}:`,
				shell: (script: string) =>
					output(ChildProcess.make('ssh', [...SSH_OPTIONS, host, script], { stdin: 'ignore' }))
			})
	});
};

const rsync = Effect.fnUntraced(function* (args: ReadonlyArray<string>) {
	const exitCode = yield* (yield* ChildProcessSpawner.ChildProcessSpawner).exitCode(
		ChildProcess.make('rsync', ['-a', ...args], {
			stdin: 'ignore',
			stdout: 'inherit',
			stderr: 'inherit'
		})
	);

	if (exitCode !== 0) return yield* new CollectError({ message: `rsync exited with ${exitCode}` });
});

const FinalFiles = Schema.Struct({
	board: Schema.optional(Schema.NullOr(Schema.String)),
	bom: Schema.optional(Schema.NullOr(Schema.String)),
	placement: Schema.optional(Schema.NullOr(Schema.String)),
	fabZip: Schema.optional(Schema.NullOr(Schema.String))
});

const collect = Effect.fn('collect')(function* (run: Run, host: Option.Option<string>) {
	const fs = yield* FileSystem.FileSystem;
	const harness = HARNESSES[run.harness];
	const { source, shell } = yield* machine(run, host);
	const runDir = runDirectory(run.id);

	// Logs hold account ids and transcripts, so they stay on this machine and out of the public repo.
	const logsDir = `${import.meta.dir}/.state/logs/${run.id}`;
	const ssh = ['ssh', ...SSH_OPTIONS].join(' ');

	yield* fs.makeDirectory(logsDir, { recursive: true });

	// Agents clone reference repos into their folder; a nested .git would become a gitlink here.
	yield* rsync([
		'--delete',
		'--delete-excluded',
		`--max-size=${MAX_FILE_SIZE}`,
		'--exclude=.git',
		'--exclude=.venv',
		'--exclude=node_modules',
		'--exclude=__pycache__',
		'-e',
		ssh,
		`${source}pcbbench-run/`,
		`${runDir}/output/`
	]);

	const skipped = yield* shell(FIND_LARGE);

	for (const [from, local] of harness.logs(run.id, source)) {
		yield* rsync(['--exclude=/pcbbench-run', '-e', ssh, from, `${logsDir}/${local}`]);
	}

	const usesGateway = run.harness !== 'sprocket';

	// A revoked key's budget can no longer be read, so a re-collect keeps the cost recorded before revocation.
	const budget = usesGateway
		? yield* readBudget(yield* readRunKey(run.id)).pipe(Effect.option)
		: Option.none();

	const previous = yield* readJsonOr(`${runDir}/metrics.json`, Schema.JsonObject, {});

	const collected = {
		...(yield* harness.timing(logsDir)),
		tokens: (yield* harness.tokens(logsDir, run)) ?? previous.tokens ?? null,
		costUsd: Option.isSome(budget) ? spentUsd(budget.value) : (previous.costUsd ?? null),
		costSource: usesGateway ? 'API cost at market prices' : 'Sprocket thread usage in the web UI',
		boardCost: previous.boardCost ?? null
	};

	// Fields added later by hand or by price.ts (fixes, costByModel) survive a re-collect.
	const metrics = { ...collected, ...previous, ...collected };

	// These are set by hand once the run's final files are known.
	const {
		board = null,
		bom = null,
		placement = null,
		fabZip = null
	} = yield* readJsonOr(`${runDir}/info.json`, FinalFiles, {});

	const info = {
		runId: run.id,
		harness: run.harness,
		model: run.model,
		reasoning: REASONING_EFFORT,
		machine: run.machine,
		versions: yield* harness.versions(logsDir, shell),
		skippedLargeFiles: skipped.split('\n').filter(Boolean),
		board,
		bom,
		placement,
		fabZip
	};

	for (const [name, data] of [
		['metrics', metrics],
		['info', info]
	] as const) {
		yield* fs.writeFileString(`${runDir}/${name}.json`, `${JSON.stringify(data, null, '\t')}\n`);
		yield* Console.log(JSON.stringify(data, null, '\t'));
	}

	// The repo is public, so stop before anything that looks like a credential gets committed.
	const leaks = yield* (yield* ChildProcessSpawner.ChildProcessSpawner).string(
		ChildProcess.make('grep', ['-rlE', CREDENTIALS, runDir], { stdin: 'ignore', stderr: 'inherit' })
	);

	if (leaks.trim())
		return yield* new CollectError({ message: `Possible credentials in:\n${leaks}` });
});

Command.make(
	'collect',
	{
		run: Argument.String('run-id').pipe(
			Argument.filterMap(
				(id) => Option.fromNullishOr(RUNS.find((run) => run.id === id)),
				() => `a run id from runs.ts: ${RUNS.map((run) => run.id).join(', ')}`
			)
		),
		host: Argument.String('user@host').pipe(Argument.optional)
	},
	({ run, host }) => collect(run, host)
).pipe(Command.run({ version: '0.0.0' }), Effect.provide(BunServices.layer), BunRuntime.runMain);
