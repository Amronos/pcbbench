import { BunServices } from '@effect/platform-bun';
import { Effect } from 'effect';
import {
	appendFileSync,
	chmodSync,
	cpSync,
	existsSync,
	mkdirSync,
	readFileSync,
	readdirSync,
	rmSync,
	writeFileSync
} from 'node:fs';
import { join } from 'node:path';
import { parseArgs } from 'node:util';
import {
	BACKPLANE_CLI,
	GATEWAY_MODEL,
	MODELS,
	REASONING_EFFORT,
	RUNS,
	WALL_CLOCK_LIMIT_HOURS,
	isModelId,
	minutesBetween,
	renderPrompt
} from '../../runs.ts';
import { HOME, PREFIX, isObj, startHub, stopHub, str, type Hub, type Json } from './hub.ts';

const GATEWAY = 'https://ai-gateway.vercel.sh';
const PORT = 3800;
const QUIET_MS = 3 * 60_000;

const ASK_ANSWER =
	'Nobody is available to answer. Make a reasonable decision yourself, record it, and continue.';

const FOLLOWUP = 'continue your work and finish it';

const { values: args } = parseArgs({
	options: {
		'run-id': { type: 'string' },
		model: { type: 'string' },
		prompt: { type: 'string' },
		'key-file': { type: 'string' },
		thread: { type: 'string' }
	}
});

const runId = args['run-id'];
const model = args.model;
const followupThread = args.thread;

if (!runId || !isModelId(model) || !args['key-file']) {
	throw new Error(
		`usage: bun run.ts --run-id <id> --model <${MODELS.join('|')}> --key-file <file> [--prompt <file> | --thread <id to follow up>]`
	);
}

const listed = RUNS.find((r) => r.id === runId);

if (listed && (listed.harness !== 'backplane' || listed.model !== model))
	throw new Error(`${runId} in runs.ts is ${listed.harness} on ${listed.model}`);

const gatewayModel = GATEWAY_MODEL[model];
const provider = BACKPLANE_CLI[model];

// Claude Code does not recognise vmc/ names: without the gateway's [1m] suffix and an output cap it runs Opus with a 200k window and 32k output.
const cliModel = provider === 'claude' ? `${gatewayModel}[1m]` : gatewayModel;
const work = join(HOME, 'pcbbench-run');
const home = join(HOME, 'pcbbench-hub');
const out = join(HOME, 'pcbbench-logs', runId);

if (!followupThread) {
	for (const d of [work, home, out])
		if (existsSync(d) && readdirSync(d).length > 0) throw new Error(`${d} is not empty`);
}

for (const d of [work, home, out]) mkdirSync(d, { recursive: true });

const prompt = await Effect.runPromise(
	renderPrompt(model, args.prompt).pipe(Effect.provide(BunServices.layer))
);

// Deleted once read, so the agent cannot find the key on disk.
const key = readFileSync(args['key-file'], 'utf8').trim();

rmSync(args['key-file']);

const log = (line: string): void => {
	const l = `${new Date().toISOString()} ${line}`;
	console.log(l);
	appendFileSync(join(out, 'driver.log'), `${l}\n`);
};

// Only the run's provider gets credentials, so nothing Backplane runs can reach another model through the key.
const env: Record<string, string> = {};

for (const [k, v] of Object.entries(process.env)) {
	if (v !== undefined && !/^(ANTHROPIC_|CLAUDE_|OPENAI_|CODEX_|AI_GATEWAY_|BACKPLANE_)/.test(k))
		env[k] = v;
}

// The hub looks for CLIs in its own PATH first, so the wrappers below stand in for the real ones.
const binDir = join(home, 'bin');

mkdirSync(binDir, { recursive: true });

const realPath = `${HOME}/.local/bin:${HOME}/.bun/bin:${env.PATH ?? '/usr/bin:/bin'}`;

Object.assign(env, {
	BACKPLANE_NO_UPDATE: '1',
	BACKPLANE_MODELS: JSON.stringify({ [provider]: [cliModel] }),
	PATH: `${binDir}:${realPath}`
});

function writeBin(name: string, body: string): void {
	writeFileSync(join(binDir, name), `#!/bin/sh\n${body}`);
	chmodSync(join(binDir, name), 0o755);
}

function wrap(name: string, script: (real: string) => string): void {
	const real = Bun.which(name, { PATH: realPath });

	if (!real) throw new Error(`${name} is not installed`);
	writeBin(name, script(real));
}

// Backplane lets the agent name any model for a subthread (delegate_task) and runs one-shots at its own effort;
// this rewrites those flag values to the run's model and effort and records each change in model-overrides.log.
const forceFlags = (name: string, cases: string): string =>
	[
		'prev=',
		'for a do',
		'\tshift',
		'\tnew=$a',
		'\tcase $prev in',
		cases,
		'\tesac',
		`\t[ "$new" = "$a" ] || echo "$(date -u +%FT%TZ) ${name}: $a -> $new" >> '${join(out, 'model-overrides.log')}'`,
		'\tset -- "$@" "$new"',
		'\tprev=$a',
		'done',
		''
	].join('\n');

// Backplane's prompt takes KiCad only from PATH, and calls a Backplane build stock KiCad because its --version has no -bp. tag.
const kicadRoot = join(PREFIX, 'kicad');
const kicadVersion = readdirSync(kicadRoot).sort().at(-1);

if (!kicadVersion) throw new Error(`no KiCad runtime in ${kicadRoot}`);

writeBin(
	'kicad-cli',
	`[ "$*" = --version ] && echo ${kicadVersion} && exit\nexec ${join(kicadRoot, kicadVersion, 'bin/kicad-cli')} "$@"\n`
);

env.BACKPLANE_KICAD_COMMIT = readFileSync(
	join(kicadRoot, kicadVersion, 'SOURCE_COMMIT'),
	'utf8'
).trim();

if (provider === 'claude') {
	Object.assign(env, {
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
	});
	wrap(
		'claude',
		(real) =>
			`${forceFlags('claude', `\t\t--model) new='${cliModel}' ;;\n\t\t--effort) new=${REASONING_EFFORT} ;;`)}exec ${real} "$@"\n`
	);
} else {
	env.AI_GATEWAY_API_KEY = key;
	// Backplane v0.15.0 keeps a turn's stdin open, and codex exec reads stdin to EOF before it starts, so a turn never begins.
	// One-shots (--ephemeral) write their text on stdin and close it.
	const effortCase = `\t\t-c) case $a in model_reasoning_effort=*) new='model_reasoning_effort="${REASONING_EFFORT}"' ;; esac ;;`;
	wrap(
		'codex',
		(real) =>
			`${forceFlags('codex', `\t\t-m|--model) new='${gatewayModel}' ;;\n${effortCase}`)}case " $* " in *" --ephemeral "*) ;; " exec "*) exec ${real} "$@" </dev/null ;; esac\nexec ${real} "$@"\n`
	);
	mkdirSync(join(HOME, '.codex'), { recursive: true });

	// Codex has no metadata for vmc/ names and falls back to generic settings; give the slug the bundled metadata of the model it aliases.
	const catalog: Json = JSON.parse(
		Bun.spawnSync(['codex', 'debug', 'models'], { env }).stdout.toString()
	);

	const models = isObj(catalog) && Array.isArray(catalog.models) ? catalog.models : [];
	const own = models.find((m) => isObj(m) && m.slug === model);

	if (!isObj(own)) throw new Error(`codex has no bundled metadata for ${model}`);
	const catalogFile = join(HOME, '.codex/pcbbench-models.json');
	writeFileSync(
		catalogFile,
		JSON.stringify({ models: [...models, { ...own, slug: gatewayModel }] })
	);
	writeFileSync(
		join(HOME, '.codex/config.toml'),
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

type State = {
	projects: string[];
	threads: { id: string; project: string; provider: string; model: string }[];
	turns: Map<string, string>;
	openAsks: Set<string>;
	models: Map<string, number>;
	offset: number;
	lastChange: number;
};

const state: State = {
	projects: [],
	threads: [],
	turns: new Map(),
	openAsks: new Set(),
	models: new Map(),
	offset: 0,
	lastChange: Date.now()
};

function readEvents(): Json[] {
	const file = join(home, 'events.jsonl');

	if (!existsSync(file)) return [];
	const buf = readFileSync(file);
	const end = buf.lastIndexOf(10) + 1;

	if (end <= state.offset) return [];
	const lines = buf.subarray(state.offset, end).toString('utf8').split('\n');
	state.offset = end;

	return lines.filter((l) => l.trim()).map((l): Json => JSON.parse(l));
}

async function follow(hub: Hub): Promise<void> {
	for (const e of readEvents()) {
		if (!isObj(e)) continue;
		const t = str(e.$);

		if (t === 'TurnChanged') {
			state.turns.set(str(e.thread), str(e.state));
			state.lastChange = Date.now();
			log(`turn ${str(e.thread)} ${str(e.state)}`);
		} else if (t === 'ProjectCreated') {
			state.projects.push(str(e.id));
		} else if (t === 'ThreadCreated') {
			state.threads.push({
				id: str(e.id),
				project: str(e.project),
				provider: str(e.provider),
				model: str(e.model)
			});
			log(`thread ${str(e.id)} created: ${str(e.provider)} ${str(e.model)} "${str(e.title)}"`);
		} else if (t === 'TurnUsage') {
			const m = `${str(e.provider)}/${str(e.model)}`;
			state.models.set(m, (state.models.get(m) ?? 0) + 1);
		} else if (t === 'AskOpened') {
			state.openAsks.add(str(e.id));
			const kind = str(e.kind);
			const answer = kind === 'input' || kind === 'question' ? ASK_ANSWER : 'accept';
			log(
				`ask ${str(e.id)} (${kind} ${str(e.tool)}) on ${str(e.thread)}: ${str(e.detail).slice(0, 300)} -> ${answer}`
			);
			await hub.rpc
				.call('ask.answer', { id: str(e.id), answer })
				.catch((err) => log(`ask.answer failed: ${err}`));
		} else if (t === 'AskClosed') {
			state.openAsks.delete(str(e.id));
			state.lastChange = Date.now();
		}
	}
}

const running = (): string[] => [...state.turns].filter(([, s]) => s === 'running').map(([t]) => t);

async function startRun(): Promise<void> {
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
		await hub.rpc.call('setting.set', { key: k, value: v });
	}

	// project.add opens the project's first thread from the settings above; the run uses that thread.
	await hub.rpc.call('project.add', { path: work });
	let first: State['threads'][number] | undefined;

	for (let i = 0; i < 100 && !first; i++) {
		await Bun.sleep(100);
		await follow(hub);
		first = state.threads.find((t) => state.projects.includes(t.project));
	}

	if (!first || first.provider !== provider || first.model !== cliModel)
		throw new Error(
			`project.add opened no ${provider} ${cliModel} thread: ${JSON.stringify(first)}`
		);
	const thread = first.id;
	await hub.rpc.call('thread.modes', { thread, runtime: 'full-access', interaction: 'default' });
	await hub.rpc.call('thread.effort', { thread, effort: REASONING_EFFORT });
	await hub.rpc.call('turn.start', { thread, text: prompt });
	log(
		`run ${runId}: ${provider} ${cliModel} effort ${REASONING_EFFORT}, project ${first.project}, thread ${thread}`
	);
}

const hubOpts = { home, port: PORT, cwd: work, env, log: join(home, 'hub.log') };
let hub = await startHub(hubOpts);
let status = 'error';
const started = Date.now();
const deadline = started + WALL_CLOCK_LIMIT_HOURS * 3600_000;

try {
	if (followupThread) {
		// Skips the earlier run's events so its finished turns and answered asks are not tracked again.
		readEvents();
		await hub.rpc.call('turn.start', { thread: followupThread, text: FOLLOWUP });
		log(`follow-up on ${followupThread}: ${FOLLOWUP}`);
	} else {
		await startRun();
	}

	for (;;) {
		await Bun.sleep(5000);

		if (hub.proc.exitCode !== null) {
			log(`hub exited with ${hub.proc.exitCode}; restarting it`);
			hub = await startHub(hubOpts);
		}

		await follow(hub);

		if (Date.now() > deadline) {
			status = 'timeout';
			log(
				`wall-clock limit of ${WALL_CLOCK_LIMIT_HOURS} h: interrupting ${running().join(' ') || 'nothing'}`
			);

			for (const t of running())
				await hub.rpc
					.call('turn.interrupt', { thread: t })
					.catch((err) => log(`interrupt ${t}: ${err}`));
			await Bun.sleep(30_000);
			await follow(hub);
			break;
		}

		if (
			state.turns.size > 0 &&
			running().length === 0 &&
			state.openAsks.size === 0 &&
			Date.now() - state.lastChange > QUIET_MS
		) {
			status = 'done';
			break;
		}
	}
} catch (err) {
	log(`error: ${err instanceof Error ? err.stack : err}`);
} finally {
	await stopHub(hub);
}

const ended = Date.now();

for (const f of ['events.jsonl', 'hub.log'])
	if (existsSync(join(home, f))) cpSync(join(home, f), join(out, f));

for (const [from, to] of [
	['.claude/projects', 'claude-projects'],
	['.codex/sessions', 'codex-sessions']
]) {
	if (existsSync(join(HOME, from))) cpSync(join(HOME, from), join(out, to), { recursive: true });
}

const summary = {
	runId,
	model,
	gatewayModel,
	cliModel,
	provider,
	effort: REASONING_EFFORT,
	status,
	startedAt: new Date(started).toISOString(),
	endedAt: new Date(ended).toISOString(),
	minutes: minutesBetween(started, ended),
	threads: Object.fromEntries(state.turns),
	usageEventsByModel: Object.fromEntries(state.models)
};

writeFileSync(
	join(out, followupThread ? 'followup-summary.json' : 'summary.json'),
	`${JSON.stringify(summary, null, '\t')}\n`
);

log(`finished: ${JSON.stringify(summary)}`);

process.exit(status === 'error' ? 1 : 0);
