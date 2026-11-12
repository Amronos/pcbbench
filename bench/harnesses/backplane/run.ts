import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Clock, Console, Effect, FileSystem, Match, Option, Schema } from 'effect';
import { Command, Flag } from 'effect/cli';
import type { PlatformError } from 'effect/PlatformError';
import { ChildProcess, ChildProcessSpawner } from 'effect/process';
import {
	BACKPLANE_CLI,
	GATEWAY_MODEL,
	MODELS,
	REASONING_EFFORT,
	RUNS,
	WALL_CLOCK_LIMIT_HOURS,
	minutesBetween,
	renderPrompt,
	type ModelId
} from '../../runs.ts';
import { HOME, PREFIX, startHub, type Hub, type HubError, type HubOptions } from './hub.ts';

const GATEWAY = 'https://ai-gateway.vercel.sh';
const PORT = 3800;
const QUIET_MS = 3 * 60_000;

const ASK_ANSWER =
	'Nobody is available to answer. Make a reasonable decision yourself, record it, and continue.';

const FOLLOWUP = 'continue your work and finish it';

class RunError extends Schema.TaggedError<RunError>()('RunError', {
	message: Schema.String
}) {}

// Fields only used in log lines; Backplane leaves some of them out on some events.
const LogText = Schema.String.pipe(Schema.withDecodingDefaultKey(Effect.succeed('')));

const EventLine = Schema.fromJsonString(
	Schema.Union([
		Schema.Struct({
			$: Schema.Literal('TurnChanged'),
			thread: Schema.String,
			state: Schema.String
		}),
		Schema.Struct({ $: Schema.Literal('ProjectCreated'), id: Schema.String }),
		Schema.Struct({
			$: Schema.Literal('ThreadCreated'),
			id: Schema.String,
			project: Schema.String,
			provider: LogText,
			model: LogText,
			title: LogText
		}),
		Schema.Struct({
			$: Schema.Literal('TurnUsage'),
			provider: Schema.String,
			model: Schema.String
		}),
		Schema.Struct({
			$: Schema.Literal('AskOpened'),
			id: Schema.String,
			thread: LogText,
			kind: LogText,
			tool: LogText,
			detail: LogText
		}),
		Schema.Struct({ $: Schema.Literal('AskClosed'), id: Schema.String }),
		Schema.Struct({ $: Schema.String })
	])
);

const CodexCatalog = Schema.fromJsonString(
	Schema.Struct({
		models: Schema.Array(
			Schema.StructWithRest(Schema.Struct({ slug: Schema.String }), [
				Schema.Record(Schema.String, Schema.Json)
			])
		)
	})
);

type Status = 'done' | 'timeout' | 'error';

type Outcome = Exclude<Status, 'error'> | 'hubExited';

type DriverError = HubError | RunError | PlatformError | Schema.SchemaError;

type Thread = { id: string; project: string; provider: string; model: string };

type State = {
	projects: string[];
	threads: Thread[];
	turns: Map<string, string>;
	openAsks: Set<string>;
	models: Map<string, number>;
	offset: number;
	lastChange: number;
};

const iso = (ms: number) => new Date(ms).toISOString();

// Backplane lets the agent name any model for a subthread (delegate_task) and runs one-shots at its own effort;
// this rewrites those flag values to the run's model and effort and records each change in model-overrides.log.
const forceFlags = (name: string, cases: string, overridesLog: string): string =>
	[
		'prev=',
		'for a do',
		'\tshift',
		'\tnew=$a',
		'\tcase $prev in',
		cases,
		'\tesac',
		`\t[ "$new" = "$a" ] || echo "$(date -u +%FT%TZ) ${name}: $a -> $new" >> '${overridesLog}'`,
		'\tset -- "$@" "$new"',
		'\tprev=$a',
		'done',
		''
	].join('\n');

const run = Effect.fn('run')(function* ({
	runId,
	model,
	prompt: promptFile,
	keyFile,
	thread: followupThread
}: {
	runId: string;
	model: ModelId;
	prompt: Option.Option<string>;
	keyFile: string;
	thread: Option.Option<string>;
}) {
	const fs = yield* FileSystem.FileSystem;
	const listed = RUNS.find((r) => r.id === runId);

	if (listed && (listed.harness !== 'backplane' || listed.model !== model))
		return yield* new RunError({
			message: `${runId} in runs.ts is ${listed.harness} on ${listed.model}`
		});

	const gatewayModel = GATEWAY_MODEL[model];
	const provider = BACKPLANE_CLI[model];

	// Claude Code does not recognise vmc/ names: without the gateway's [1m] suffix and an output cap it runs Opus with a 200k window and 32k output.
	const cliModel = provider === 'claude' ? `${gatewayModel}[1m]` : gatewayModel;
	const work = `${HOME}/pcbbench-run`;
	const home = `${HOME}/pcbbench-hub`;
	const out = `${HOME}/pcbbench-logs/${runId}`;

	if (Option.isNone(followupThread)) {
		for (const d of [work, home, out])
			if ((yield* fs.exists(d)) && (yield* fs.readDirectory(d)).length > 0)
				return yield* new RunError({ message: `${d} is not empty` });
	}

	for (const d of [work, home, out]) yield* fs.makeDirectory(d, { recursive: true });

	const prompt = yield* renderPrompt(model, Option.getOrUndefined(promptFile));

	// Deleted once read, so the agent cannot find the key on disk.
	const key = (yield* fs.readFileString(keyFile)).trim();

	yield* fs.remove(keyFile);

	const log = Effect.fnUntraced(function* (line: string) {
		const l = `${iso(yield* Clock.currentTimeMillis)} ${line}`;
		yield* Console.log(l);
		yield* fs.writeFileString(`${out}/driver.log`, `${l}\n`, { flag: 'a' });
	});

	// The hub looks for CLIs in its own PATH first, so the wrappers below stand in for the real ones.
	const binDir = `${home}/bin`;

	yield* fs.makeDirectory(binDir, { recursive: true });

	// Only the run's provider gets credentials, so nothing Backplane runs can reach another model through the key.
	const inherited = Object.fromEntries(
		Object.entries(process.env).filter(
			([k]) => !/^(ANTHROPIC_|CLAUDE_|OPENAI_|CODEX_|AI_GATEWAY_|BACKPLANE_)/.test(k)
		)
	);

	const realPath = `${HOME}/.local/bin:${HOME}/.bun/bin:${inherited.PATH ?? '/usr/bin:/bin'}`;

	const writeBin = Effect.fnUntraced(function* (name: string, body: string) {
		yield* fs.writeFileString(`${binDir}/${name}`, `#!/bin/sh\n${body}`);
		yield* fs.chmod(`${binDir}/${name}`, 0o755);
	});

	const wrap = Effect.fnUntraced(function* (name: string, script: (real: string) => string) {
		const real = Bun.which(name, { PATH: realPath });

		if (!real) return yield* new RunError({ message: `${name} is not installed` });
		yield* writeBin(name, script(real));
	});

	const overridesLog = `${out}/model-overrides.log`;

	// Backplane's prompt takes KiCad only from PATH, and calls a Backplane build stock KiCad because its --version has no -bp. tag.
	const kicadRoot = `${PREFIX}/kicad`;
	const kicadVersion = (yield* fs.readDirectory(kicadRoot)).toSorted().at(-1);

	if (!kicadVersion) return yield* new RunError({ message: `no KiCad runtime in ${kicadRoot}` });

	yield* writeBin(
		'kicad-cli',
		`[ "$*" = --version ] && echo ${kicadVersion} && exit\nexec ${kicadRoot}/${kicadVersion}/bin/kicad-cli "$@"\n`
	);

	const hubEnv = {
		...inherited,
		BACKPLANE_NO_UPDATE: '1',
		BACKPLANE_MODELS: JSON.stringify({ [provider]: [cliModel] }),
		PATH: `${binDir}:${realPath}`,
		BACKPLANE_KICAD_COMMIT: (yield* fs.readFileString(
			`${kicadRoot}/${kicadVersion}/SOURCE_COMMIT`
		)).trim()
	};

	const env: HubOptions['env'] =
		provider === 'claude'
			? {
					...hubEnv,
					ANTHROPIC_BASE_URL: `${GATEWAY}/claude-code`,
					ANTHROPIC_AUTH_TOKEN: key,
					ANTHROPIC_API_KEY: '',
					ANTHROPIC_MODEL: cliModel,
					ANTHROPIC_DEFAULT_OPUS_MODEL: cliModel,
					ANTHROPIC_DEFAULT_SONNET_MODEL: cliModel,
					ANTHROPIC_DEFAULT_HAIKU_MODEL: cliModel,
					ANTHROPIC_SMALL_FAST_MODEL: cliModel,
					CLAUDE_CODE_SUBAGENT_MODEL: cliModel,
					CLAUDE_CODE_SUBAGENT_MODEL_FORCE: '1',
					CLAUDE_CODE_EFFORT_LEVEL: REASONING_EFFORT,
					CLAUDE_CODE_MAX_OUTPUT_TOKENS: '128000',
					// The default 5-minute timeout cut off every request once the context neared 460K tokens.
					API_TIMEOUT_MS: '1800000',
					DISABLE_AUTOUPDATER: '1'
				}
			: { ...hubEnv, AI_GATEWAY_API_KEY: key };

	if (provider === 'claude') {
		yield* wrap(
			'claude',
			(real) =>
				`${forceFlags('claude', `\t\t--model) new='${cliModel}' ;;\n\t\t--effort) new=${REASONING_EFFORT} ;;`, overridesLog)}exec ${real} "$@"\n`
		);
	} else {
		// Backplane v0.15.0 keeps a turn's stdin open, and codex exec reads stdin to EOF before it starts, so a turn never begins.
		// One-shots (--ephemeral) write their text on stdin and close it.
		const effortCase = `\t\t-c) case $a in model_reasoning_effort=*) new='model_reasoning_effort="${REASONING_EFFORT}"' ;; esac ;;`;
		yield* wrap(
			'codex',
			(real) =>
				`${forceFlags('codex', `\t\t-m|--model) new='${gatewayModel}' ;;\n${effortCase}`, overridesLog)}case " $* " in *" --ephemeral "*) ;; " exec "*) exec ${real} "$@" </dev/null ;; esac\nexec ${real} "$@"\n`
		);
		yield* fs.makeDirectory(`${HOME}/.codex`, { recursive: true });

		// Codex has no metadata for vmc/ names and falls back to generic settings; give the slug the bundled metadata of the model it aliases.
		const { models } = yield* Schema.decodeEffect(CodexCatalog)(
			yield* (yield* ChildProcessSpawner.ChildProcessSpawner).string(
				ChildProcess.make('codex', ['debug', 'models'], { env, stderr: 'inherit' })
			)
		);

		const own = models.find((m) => m.slug === model);

		if (!own) return yield* new RunError({ message: `codex has no bundled metadata for ${model}` });
		const catalogFile = `${HOME}/.codex/pcbbench-models.json`;

		yield* fs.writeFileString(
			catalogFile,
			JSON.stringify({ models: [...models, { ...own, slug: gatewayModel }] })
		);

		yield* fs.writeFileString(
			`${HOME}/.codex/config.toml`,
			[
				`model = "${gatewayModel}"`,
				'model_provider = "vercel"',
				`model_reasoning_effort = "${REASONING_EFFORT}"`,
				`model_catalog_json = "${catalogFile}"`,
				'check_for_update_on_startup = false',
				'',
				// Backplane forbids provider-native subagents in its prompt and disables Claude's; this does the same for codex.
				'[features]',
				'multi_agent = false',
				'',
				'[model_providers.vercel]',
				'name = "Vercel AI Gateway"',
				`base_url = "${GATEWAY}/codex/v1"`,
				'env_key = "AI_GATEWAY_API_KEY"',
				'wire_api = "responses"',
				''
			].join('\n')
		);
	}

	const state: State = {
		projects: [],
		threads: [],
		turns: new Map(),
		openAsks: new Set(),
		models: new Map(),
		offset: 0,
		lastChange: yield* Clock.currentTimeMillis
	};

	const eventsFile = `${home}/events.jsonl`;

	const readEvents = Effect.gen(function* () {
		if (!(yield* fs.exists(eventsFile))) return [];
		const buf = yield* fs.readFile(eventsFile);
		const end = buf.lastIndexOf(10) + 1;

		if (end <= state.offset) return [];
		const lines = new TextDecoder().decode(buf.subarray(state.offset, end)).split('\n');
		state.offset = end;

		return yield* Effect.forEach(
			lines.filter((l) => l.trim()),
			(l) => Schema.decodeEffect(EventLine)(l)
		);
	});

	const touch = Effect.map(Clock.currentTimeMillis, (now) => {
		state.lastChange = now;
	});

	const follow = Effect.fn('follow')(function* (hub: Hub) {
		for (const event of yield* readEvents) {
			yield* Match.value(event).pipe(
				Match.discriminator('$')('TurnChanged', (e) =>
					Effect.gen(function* () {
						state.turns.set(e.thread, e.state);
						yield* touch;
						yield* log(`turn ${e.thread} ${e.state}`);
					})
				),
				Match.discriminator('$')('ProjectCreated', (e) =>
					Effect.sync(() => state.projects.push(e.id))
				),
				Match.discriminator('$')('ThreadCreated', (e) => {
					state.threads.push({
						id: e.id,
						project: e.project,
						provider: e.provider,
						model: e.model
					});

					return log(`thread ${e.id} created: ${e.provider} ${e.model} "${e.title}"`);
				}),
				Match.discriminator('$')('TurnUsage', (e) =>
					Effect.sync(() => {
						const m = `${e.provider}/${e.model}`;
						state.models.set(m, (state.models.get(m) ?? 0) + 1);
					})
				),
				Match.discriminator('$')('AskOpened', (e) =>
					Effect.gen(function* () {
						state.openAsks.add(e.id);
						const answer = e.kind === 'input' || e.kind === 'question' ? ASK_ANSWER : 'accept';

						yield* log(
							`ask ${e.id} (${e.kind} ${e.tool}) on ${e.thread}: ${e.detail.slice(0, 300)} -> ${answer}`
						);

						yield* hub
							.call('ask.answer', { id: e.id, answer })
							.pipe(Effect.catch((error) => log(`ask.answer failed: ${error.message}`)));
					})
				),
				Match.discriminator('$')('AskClosed', (e) =>
					Effect.gen(function* () {
						state.openAsks.delete(e.id);
						yield* touch;
					})
				),
				Match.orElse(() => Effect.void)
			);
		}
	});

	const running = () =>
		[...state.turns].flatMap(([thread, turn]) => (turn === 'running' ? [thread] : []));

	const startRun = Effect.fn('startRun')(function* (hub: Hub) {
		// The benchmark task excludes quoting and ordering, so Backplane's order flow is off.
		const settings = {
			'agent.provider': provider,
			'agent.model': cliModel,
			'text.provider': provider,
			'text.model': cliModel,
			'thread.env': 'local',
			'order.enabled': 'off',
			'order.estimates': 'off'
		};

		for (const [k, v] of Object.entries(settings)) {
			yield* hub.call('setting.set', { key: k, value: v });
		}

		// project.add opens the project's first thread from the settings above; the run uses that thread.
		yield* hub.call('project.add', { path: work });
		let first: Thread | undefined;

		for (let i = 0; i < 100 && !first; i++) {
			yield* Effect.sleep(100);
			yield* follow(hub);
			first = state.threads.find((t) => state.projects.includes(t.project));
		}

		if (!first || first.provider !== provider || first.model !== cliModel)
			return yield* new RunError({
				message: `project.add opened no ${provider} ${cliModel} thread: ${JSON.stringify(first)}`
			});
		const thread = first.id;
		yield* hub.call('thread.modes', { thread, runtime: 'full-access', interaction: 'default' });
		yield* hub.call('thread.effort', { thread, effort: REASONING_EFFORT });
		yield* hub.call('turn.start', { thread, text: prompt });

		yield* log(
			`run ${runId}: ${provider} ${cliModel} effort ${REASONING_EFFORT}, project ${first.project}, thread ${thread}`
		);
	});

	const watch = Effect.fn('watch')(function* (
		hub: Hub,
		deadline: number
	): Effect.fn.Return<Outcome, DriverError> {
		for (;;) {
			yield* Effect.sleep('5 seconds');
			const exit = yield* hub.exited;

			if (Option.isSome(exit)) {
				yield* log(`hub exited with ${exit.value}; restarting it`);

				return 'hubExited';
			}

			yield* follow(hub);

			if ((yield* Clock.currentTimeMillis) > deadline) {
				yield* log(
					`wall-clock limit of ${WALL_CLOCK_LIMIT_HOURS} h: interrupting ${running().join(' ') || 'nothing'}`
				);

				for (const t of running())
					yield* hub
						.call('turn.interrupt', { thread: t })
						.pipe(Effect.catch((error) => log(`interrupt ${t}: ${error.message}`)));
				yield* Effect.sleep('30 seconds');
				yield* follow(hub);

				return 'timeout';
			}

			if (
				state.turns.size > 0 &&
				running().length === 0 &&
				state.openAsks.size === 0 &&
				(yield* Clock.currentTimeMillis) - state.lastChange > QUIET_MS
			)
				return 'done';
		}
	});

	const hubOpts: HubOptions = { home, port: PORT, cwd: work, env, log: `${home}/hub.log` };

	const drive = Effect.fn('drive')(function* (
		hub: Hub,
		deadline: number
	): Effect.fn.Return<
		Status,
		DriverError,
		FileSystem.FileSystem | ChildProcessSpawner.ChildProcessSpawner
	> {
		if (Option.isSome(followupThread)) {
			// Skips the earlier run's events so its finished turns and answered asks are not tracked again.
			yield* readEvents;
			yield* hub.call('turn.start', { thread: followupThread.value, text: FOLLOWUP });
			yield* log(`follow-up on ${followupThread.value}: ${FOLLOWUP}`);
		} else {
			yield* startRun(hub);
		}

		let outcome = yield* watch(hub, deadline);

		while (outcome === 'hubExited')
			outcome = yield* Effect.scoped(
				Effect.flatMap(startHub(hubOpts), (restarted) => watch(restarted, deadline))
			);

		return outcome;
	});

	const { started, status } = yield* Effect.scoped(
		Effect.gen(function* () {
			const hub = yield* startHub(hubOpts);
			const started = yield* Clock.currentTimeMillis;

			const status = yield* drive(hub, started + WALL_CLOCK_LIMIT_HOURS * 3600_000).pipe(
				Effect.catch((error) => log(`error: ${error.message}`).pipe(Effect.as<Status>('error')))
			);

			return { started, status };
		})
	);

	const ended = yield* Clock.currentTimeMillis;

	for (const f of ['events.jsonl', 'hub.log'])
		if (yield* fs.exists(`${home}/${f}`)) yield* fs.copyFile(`${home}/${f}`, `${out}/${f}`);

	for (const [from, to] of [
		['.claude/projects', 'claude-projects'],
		['.codex/sessions', 'codex-sessions']
	]) {
		if (yield* fs.exists(`${HOME}/${from}`))
			yield* fs.copy(`${HOME}/${from}`, `${out}/${to}`, { overwrite: true });
	}

	const summary = {
		runId,
		model,
		gatewayModel,
		cliModel,
		provider,
		effort: REASONING_EFFORT,
		status,
		startedAt: iso(started),
		endedAt: iso(ended),
		minutes: minutesBetween(started, ended),
		threads: Object.fromEntries(state.turns),
		usageEventsByModel: Object.fromEntries(state.models)
	};

	yield* fs.writeFileString(
		`${out}/${Option.isSome(followupThread) ? 'followup-summary.json' : 'summary.json'}`,
		`${JSON.stringify(summary, null, '\t')}\n`
	);

	yield* log(`finished: ${JSON.stringify(summary)}`);

	if (status === 'error')
		return yield* new RunError({ message: `run ${runId} failed; see ${out}/driver.log` });
});

const command = Command.make(
	'run',
	{
		runId: Flag.String('run-id'),
		model: Flag.Literals('model', MODELS),
		prompt: Flag.String('prompt').pipe(Flag.optional),
		keyFile: Flag.String('key-file'),
		thread: Flag.String('thread').pipe(Flag.optional)
	},
	run
);

command.pipe(
	Command.run({ version: '0.0.0' }),
	Effect.provide(BunServices.layer),
	BunRuntime.runMain
);
