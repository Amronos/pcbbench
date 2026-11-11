import { Effect, FileSystem, Schema } from 'effect';
import { Argument } from 'effect/cli';

export const ModelId = Schema.Literals(['opus-5.5', 'gpt-6.1-sol', 'fable-5.2']);

export type ModelId = typeof ModelId.Type;

export type Harness = 'codex-desktop' | 'codex-desktop-texttocad' | 'backplane' | 'sprocket';

export type Run = {
	id: string;
	harness: Harness;
	model: ModelId;
	machine: 'mac' | 'linux';
};

export const GATEWAY_MODEL: Record<ModelId, string> = {
	'opus-5.5': 'vmc/opus-55',
	'gpt-6.1-sol': 'vmc/gpt-61-sol',
	'fable-5.2': 'vmc/fable-52'
};

export const BACKPLANE_CLI: Record<ModelId, 'claude' | 'codex'> = {
	'opus-5.5': 'claude',
	'gpt-6.1-sol': 'codex',
	'fable-5.2': 'claude'
};

export const isModelId = Schema.is(ModelId);

export const MODELS = ModelId.literals;

export const REASONING_EFFORT = 'medium';
export const WALL_CLOCK_LIMIT_HOURS = 12;

export const COST_LIMIT_USD: Record<ModelId, number> = {
	'opus-5.5': 100,
	'gpt-6.1-sol': 100,
	'fable-5.2': 250
};

export const COST_REVOKE_MARGIN_USD = 5;
export const BATCH_BOARDS = 5;

export const renderPrompt = Effect.fn('renderPrompt')(function* (
	model: ModelId,
	path = `${import.meta.dir}/prompt.md`
) {
	const template = yield* (yield* FileSystem.FileSystem).readFileString(path);

	return template.replaceAll('{{MODEL}}', model).replaceAll('{{EFFORT}}', REASONING_EFFORT);
});

// Harness version scripts print one `name=version` line per tool.
export const parseVersions = (output: string): Record<string, string> =>
	Object.fromEntries(
		output
			.split('\n')
			.filter((line) => line.includes('='))
			.map((line) => [line.slice(0, line.indexOf('=')), line.slice(line.indexOf('=') + 1)])
	);

export const kicadFullVersion = (kicadCli: string) =>
	`$(${kicadCli} version --format about | sed -n 's/^Version: \\([^,]*\\).*/\\1/p')`;

export const minutesBetween = (startMs: number, endMs: number) =>
	Math.round((endMs - startMs) / 600) / 100;

export const RUNS: Run[] = [
	{
		id: 'codex-desktop--gpt-6.1-sol',
		harness: 'codex-desktop',
		model: 'gpt-6.1-sol',
		machine: 'mac'
	},
	{
		id: 'codex-desktop-texttocad--gpt-6.1-sol',
		harness: 'codex-desktop-texttocad',
		model: 'gpt-6.1-sol',
		machine: 'mac'
	},
	{ id: 'backplane--opus-5.5', harness: 'backplane', model: 'opus-5.5', machine: 'linux' },
	{ id: 'backplane--gpt-6.1-sol', harness: 'backplane', model: 'gpt-6.1-sol', machine: 'linux' },
	{ id: 'sprocket--opus-5.5', harness: 'sprocket', model: 'opus-5.5', machine: 'linux' },
	{ id: 'sprocket--gpt-6.1-sol', harness: 'sprocket', model: 'gpt-6.1-sol', machine: 'linux' },
	{ id: 'backplane--fable-5.2', harness: 'backplane', model: 'fable-5.2', machine: 'linux' },
	{ id: 'sprocket--fable-5.2', harness: 'sprocket', model: 'fable-5.2', machine: 'linux' }
];

export const runIdArgument = Argument.Literals(
	'run-id',
	RUNS.map((run) => run.id)
);
