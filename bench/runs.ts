import { Effect, FileSystem, Schema } from 'effect';
import { Argument } from 'effect/cli';

export const ModelId = Schema.Literals(['opus-5.5', 'gpt-6.1-sol', 'fable-5.2']);

export type ModelId = typeof ModelId.Type;

export type Harness = 'codex-desktop' | 'codex-desktop-texttocad' | 'backplane' | 'sprocket';

export const TaskId = Schema.Literals(['rp2350-devboard']);

export type TaskId = typeof TaskId.Type;

export const TASKS = TaskId.literals;

export type Run = {
	id: string;
	task: TaskId;
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

export const taskDirectory = (task: TaskId) => `${import.meta.dir}/tasks/${task}`;

class PromptError extends Schema.TaggedError<PromptError>()('PromptError', {
	message: Schema.String
}) {}

export const renderPrompt = Effect.fn('renderPrompt')(function* (
	runId: string,
	model: ModelId,
	promptFile: string | undefined
) {
	const task = RUNS.find((run) => run.id === runId)?.task;
	const path = promptFile ?? (task && `${taskDirectory(task)}/prompt.md`);

	if (!path)
		return yield* new PromptError({
			message: `${runId} isn't in runs.ts, so pass a prompt file`
		});

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

const run = (task: TaskId, harness: Harness, model: ModelId, machine: Run['machine']): Run => ({
	id: `${task}/${harness}--${model}`,
	task,
	harness,
	model,
	machine
});

export const RUNS: Run[] = [
	run('rp2350-devboard', 'codex-desktop', 'gpt-6.1-sol', 'mac'),
	run('rp2350-devboard', 'codex-desktop-texttocad', 'gpt-6.1-sol', 'mac'),
	run('rp2350-devboard', 'backplane', 'opus-5.5', 'linux'),
	run('rp2350-devboard', 'backplane', 'gpt-6.1-sol', 'linux'),
	run('rp2350-devboard', 'sprocket', 'opus-5.5', 'linux'),
	run('rp2350-devboard', 'sprocket', 'gpt-6.1-sol', 'linux'),
	run('rp2350-devboard', 'backplane', 'fable-5.2', 'linux')
];

export const runIdArgument = Argument.Literals(
	'run-id',
	RUNS.map((run) => run.id)
);

export const runArgument = Argument.ChoiceWithValue(
	'run-id',
	RUNS.map((run) => [run.id, run] as const)
);
