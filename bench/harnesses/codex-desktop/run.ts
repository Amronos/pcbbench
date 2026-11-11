import { BunRuntime, BunServices } from '@effect/platform-bun';
import {
	Console,
	DateTime,
	Effect,
	FileSystem,
	Option,
	Predicate,
	Schedule,
	Schema,
	Stream
} from 'effect';
import { Argument, Command } from 'effect/cli';
import { ChildProcess, ChildProcessSpawner } from 'effect/process';
import { homedir } from 'node:os';
import { readRunKey, revokeRunKey } from '../../gateway.ts';
import {
	GATEWAY_MODEL,
	ModelId,
	REASONING_EFFORT,
	RUNS,
	WALL_CLOCK_LIMIT_HOURS,
	kicadFullVersion,
	parseVersions,
	renderPrompt
} from '../../runs.ts';

const INSTANCE_ID = 'i-0667c1457d80ee354';
const BASE_AMI = 'ami-0a11b952507c9bb48';
const HOST = 'ec2-user@54.234.19.231';

const SSH_OPTIONS = [
	'-i',
	`${homedir()}/.ssh/pcbbench.pem`,
	'-o',
	`UserKnownHostsFile=${homedir()}/.config/pcbbench/mac_known_hosts`,
	'-o',
	'StrictHostKeyChecking=accept-new',
	'-o',
	'ConnectTimeout=15',
	'-o',
	'ServerAliveInterval=30',
	'-o',
	'BatchMode=yes'
];

const VNC_PORT = 15901;
const WORK_DIR = '/Users/ec2-user/pcbbench-run';
const HERE = import.meta.dir;
const POLL = '1 minute';

const MacHarness = Schema.Literals(['codex-desktop', 'codex-desktop-texttocad']);
const Outcome = Schema.Literals(['task_complete', 'turn_aborted', 'wall_clock_limit']);

const Result = Schema.Struct({
	runId: Schema.String,
	harness: MacHarness,
	model: ModelId,
	reasoning: Schema.Literal(REASONING_EFFORT),
	versions: Schema.Record(Schema.String, Schema.String),
	startedAt: Schema.String,
	rollout: Schema.String,
	finishedAt: Schema.optional(Schema.String),
	outcome: Schema.optional(Outcome)
});

type Result = typeof Result.Type;

type Run = { runId: string; harness: typeof MacHarness.Type; model: ModelId; resultDir: string };

class MacError extends Schema.TaggedError<MacError>()('MacError', {
	message: Schema.String
}) {}

const resultJson = (result: Result) => `${JSON.stringify(result, null, '\t')}\n`;

const now = DateTime.now.pipe(Effect.map(DateTime.formatIso));

const exec = Effect.fnUntraced(function* (command: ChildProcess.Command) {
	const handle = yield* command;

	const [stdout, stderr, exitCode] = yield* Effect.all(
		[
			Stream.mkString(Stream.decodeText(handle.stdout)),
			Stream.mkString(Stream.decodeText(handle.stderr)),
			handle.exitCode
		],
		{ concurrency: 'unbounded' }
	);

	return { stdout: stdout.trim(), stderr, exitCode };
}, Effect.scoped);

const succeeds = Effect.fnUntraced(function* (name: string, command: ChildProcess.Command) {
	const exitCode = yield* (yield* ChildProcessSpawner.ChildProcessSpawner).exitCode(command);

	if (exitCode !== 0) return yield* new MacError({ message: `${name} exited with ${exitCode}` });
});

const aws = Effect.fn('aws')(function* (args: ReadonlyArray<string>) {
	const { stdout, stderr, exitCode } = yield* exec(
		ChildProcess.make('nix', ['run', 'nixpkgs#awscli2', '--', '--region', 'us-east-1', ...args], {
			stdin: 'ignore'
		})
	);

	if (exitCode !== 0)
		return yield* new MacError({
			message: `aws ${args.join(' ')} exited with ${exitCode}: ${stderr}`
		});

	return stdout;
});

// Commands run as ec2-user in the GUI login session, where the app and its environment live.
const AS_GUI_USER = 'sudo launchctl asuser 501 sudo -u ec2-user';

const mac = Effect.fn('mac')(function* (script: string, { check = true } = {}) {
	const { stdout, exitCode } = yield* exec(
		ChildProcess.make('ssh', [...SSH_OPTIONS, HOST, 'bash -s'], {
			stdin: Stream.make(`set -euo pipefail\n${script}`).pipe(Stream.encodeText),
			stderr: 'inherit'
		})
	);

	if (exitCode !== 0 && check)
		return yield* new MacError({ message: `Mac command failed:\n${script}` });

	return stdout;
});

const vnc = Effect.fn('vnc')(function* (actions: ReadonlyArray<string>) {
	yield* ChildProcess.make(
		'ssh',
		[
			...SSH_OPTIONS,
			'-N',
			'-o',
			'ExitOnForwardFailure=yes',
			'-L',
			`${VNC_PORT}:localhost:5900`,
			HOST
		],
		// In the driver's process group, a hangup that ends the driver also closes the tunnel.
		{ stdin: 'ignore', stdout: 'inherit', stderr: 'inherit', detached: false }
	);

	yield* Effect.sleep('3 seconds');
	yield* succeeds(
		'vnc.py',
		ChildProcess.make('uv', ['run', '--quiet', `${HERE}/vnc.py`, ...actions], {
			env: { MAC_VNC_PORT: String(VNC_PORT) },
			extendEnv: true,
			stdin: 'ignore',
			stdout: 'inherit',
			stderr: 'inherit'
		})
	);
}, Effect.scoped);

const shellQuote = (text: string) => `'${text.replaceAll("'", `'\\''`)}'`;

const MAC_RUNS = RUNS.filter((run) => run.machine === 'mac');

// A suffix such as --smoke reuses a benchmark run's setup under its own id.
function parseRunId(runId: string): Option.Option<Run> {
	const base = MAC_RUNS.find((run) => runId === run.id || runId.startsWith(`${run.id}--`));

	if (!base || !Schema.is(MacHarness)(base.harness)) return Option.none();

	return Option.some({
		runId,
		harness: base.harness,
		model: base.model,
		resultDir: `${homedir()}/pcbbench-results/${runId}`
	});
}

const reset = Effect.gen(function* () {
	const taskId = yield* aws([
		'ec2',
		'create-replace-root-volume-task',
		'--instance-id',
		INSTANCE_ID,
		'--image-id',
		BASE_AMI,
		'--delete-replaced-root-volume',
		'--query',
		'ReplaceRootVolumeTask.ReplaceRootVolumeTaskId',
		'--output',
		'text'
	]);

	yield* Console.log(`Replacing the root volume with ${BASE_AMI} (${taskId})`);

	const state = yield* aws([
		'ec2',
		'describe-replace-root-volume-tasks',
		'--replace-root-volume-task-ids',
		taskId,
		'--query',
		'ReplaceRootVolumeTasks[0].TaskState',
		'--output',
		'text'
	]).pipe(
		Effect.tap(Console.log),
		Effect.repeat({
			schedule: Schedule.spaced('30 seconds'),
			until: (state) => state === 'succeeded' || state.startsWith('fail')
		}),
		Effect.delay('30 seconds')
	);

	if (state !== 'succeeded')
		return yield* new MacError({ message: `Root volume replacement ${taskId} ${state}` });

	yield* mac('pgrep -xu ec2-user Dock >/dev/null && echo ready', { check: false }).pipe(
		Effect.orElseSucceed(() => ''),
		Effect.repeat({ schedule: Schedule.spaced('15 seconds'), until: (ready) => ready === 'ready' })
	);
	yield* Console.log('The Mac is back and logged in.');
});

const start = Effect.fn('start')(function* (run: Run, promptFile: string | undefined) {
	const fs = yield* FileSystem.FileSystem;
	const { runId } = run;
	const { secret } = yield* readRunKey(runId);
	yield* fs.makeDirectory(run.resultDir, { recursive: true });
	const prompt = yield* renderPrompt(run.model, promptFile);
	yield* fs.writeFileString(`${run.resultDir}/prompt.md`, prompt);

	const config = (yield* fs.readFileString(`${HERE}/config.toml`))
		.replaceAll('__MODEL__', GATEWAY_MODEL[run.model])
		.replaceAll('__EFFORT__', REASONING_EFFORT)
		.replaceAll('__RUN_ID__', runId);

	const leftovers = yield* mac(`ls -A ${WORK_DIR}; find ~/.codex/sessions -type f`);

	if (leftovers)
		return yield* new MacError({
			message: `The Mac is not fresh; run \`bun run.ts reset\` first:\n${leftovers}`
		});
	yield* mac(`cat > ~/.codex/config.toml <<'CONFIG'
${config}CONFIG`);

	// The installer adds the plugin to config.toml, so it runs after the config is written.
	if (run.harness === 'codex-desktop-texttocad') {
		yield* Console.log('Installing text-to-cad');

		const log =
			yield* mac(`curl -fsSL https://texttocad.dev/install.sh | sh -s -- --only codex --no-telemetry 2>&1
~/.local/bin/cad doctor 2>&1`);

		yield* fs.writeFileString(`${run.resultDir}/texttocad-install.log`, `${log}\n`);
	}

	yield* Console.log('Starting the app');
	const link = `codex://new?prompt=${encodeURIComponent(prompt)}&path=${encodeURIComponent(WORK_DIR)}`;
	yield* mac(`pkill -f /Applications/ChatGPT.app || true
sleep 3
key=${shellQuote(secret)}
printf %s "$key" | ${AS_GUI_USER} sh -c 'launchctl setenv AI_GATEWAY_API_KEY "$(cat)"'
${AS_GUI_USER} open -a ChatGPT
sleep 20
${AS_GUI_USER} open ${shellQuote(link)}
sleep 5`);
	// Return inside a Markdown list in the composer may add a list item, so click the send button.
	yield* vnc([
		'shot',
		`${run.resultDir}/filled.png`,
		'click',
		'981',
		'666',
		'sleep',
		'10',
		'shot',
		`${run.resultDir}/started.png`
	]);

	const rollout = yield* mac(
		'sleep 20; find ~/.codex/sessions -name "rollout-*.jsonl" | sort | head -1'
	);

	if (!rollout)
		return yield* new MacError({
			message: `No rollout appeared; check ${run.resultDir}/started.png`
		});

	const versions = parseVersions(
		yield* mac(`echo "chatgpt=$(defaults read /Applications/ChatGPT.app/Contents/Info CFBundleShortVersionString)"
echo "codex=$(/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex --version)"
echo "kicad=${kicadFullVersion('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')}"
echo "texttocad=$(~/.local/bin/cad --version 2>/dev/null || echo none)"`)
	);

	const result: Result = {
		runId,
		harness: run.harness,
		model: run.model,
		reasoning: REASONING_EFFORT,
		versions,
		startedAt: yield* now,
		rollout
	};

	yield* fs.writeFileString(`${run.resultDir}/result.json`, resultJson(result));
	yield* Console.log(`Started ${runId}; rollout ${rollout}`);
	yield* wait(run);
});

const wait = Effect.fn('wait')(function* (run: Run) {
	const fs = yield* FileSystem.FileSystem;
	const resultPath = `${run.resultDir}/result.json`;

	const result = yield* Schema.decodeEffect(Schema.fromJsonString(Result))(
		yield* fs.readFileString(resultPath)
	);

	// The deadline comes from result.json, so a restarted `wait` keeps the run's original limit.
	const deadline = DateTime.add(DateTime.makeUnsafe(result.startedAt), {
		hours: WALL_CLOCK_LIMIT_HOURS
	});

	const poll = Effect.gen(function* () {
		const status = yield* mac(
			`grep -oE '"type":"(task_complete|turn_aborted)"' ${result.rollout} | tail -1 | cut -d'"' -f4 || true
grep '"type":"token_count"' ${result.rollout} | tail -1 | grep -oE '"total_token_usage":\\{[^}]*\\}' || true`,
			{ check: false }
		);

		const end = status.match(/^(task_complete|turn_aborted)$/m)?.[1];
		const usage = status.match(/"total_token_usage".*/)?.[0];
		const checkedAt = yield* DateTime.now;
		yield* Console.log(`${DateTime.formatIso(checkedAt)} ${usage ?? 'no token usage yet'}`);

		if (end === 'task_complete' || end === 'turn_aborted') return end;

		if (DateTime.isGreaterThan(checkedAt, deadline)) {
			yield* mac('pkill -f /Applications/ChatGPT.app || true');
			yield* revokeRunKey(yield* readRunKey(run.runId));

			return 'wall_clock_limit' as const;
		}
	});

	const outcome =
		result.outcome ??
		(yield* poll.pipe(
			Effect.repeat({ schedule: Schedule.spaced(POLL), until: Predicate.isNotUndefined })
		));

	const finishedAt = yield* now;
	yield* vnc(['shot', `${run.resultDir}/finished.png`]).pipe(
		Effect.catch((error) => Console.error(`Final screenshot failed: ${error}`))
	);
	yield* collect(run.resultDir);
	yield* fs.writeFileString(resultPath, resultJson({ ...result, outcome, finishedAt }));
	yield* Console.log(`${run.runId} ended with ${outcome}; results in ${run.resultDir}`);
});

const collect = (resultDir: string) =>
	succeeds(
		'collect',
		ChildProcess.make(
			'ssh',
			[...SSH_OPTIONS, HOST, 'tar -C ~ -czf - pcbbench-run .codex/sessions'],
			{ stdin: 'ignore', stderr: 'inherit' }
		).pipe(
			ChildProcess.pipeTo(
				ChildProcess.make('tar', ['-C', resultDir, '-xzf', '-'], {
					stdout: 'inherit',
					stderr: 'inherit'
				})
			)
		)
	);

const runId = Argument.String('run-id').pipe(
	Argument.filterMap(
		parseRunId,
		() =>
			`a mac run id from runs.ts with an optional --suffix: ${MAC_RUNS.map((run) => run.id).join(', ')}`
	)
);

Command.make('codex-desktop').pipe(
	Command.withSubcommands([
		Command.make('reset', {}, () => reset),
		Command.make(
			'start',
			{ run: runId, promptFile: Argument.String('smoke-test-prompt-file').pipe(Argument.optional) },
			({ run, promptFile }) => start(run, Option.getOrUndefined(promptFile))
		),
		Command.make('wait', { run: runId }, ({ run }) => wait(run)),
		Command.make('collect', { run: runId }, ({ run }) => collect(run.resultDir))
	]),
	Command.run({ version: '0.0.0' }),
	Effect.provide(BunServices.layer),
	BunRuntime.runMain
);
