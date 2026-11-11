import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Effect, FileSystem, Schema } from 'effect';
import { Argument, Command } from 'effect/cli';
import { runDirectory } from '../board.ts';
import { MODELS, runIdArgument } from '../runs.ts';

const Part = Schema.fromJsonString(
	Schema.Struct({
		number: Schema.Number,
		createdAt: Schema.Number,
		kind: Schema.String,
		prompt: Schema.optionalKey(Schema.Struct({ text: Schema.optionalKey(Schema.String) })),
		completion: Schema.optionalKey(
			Schema.Struct({
				items: Schema.Array(
					Schema.Struct({
						type: Schema.optionalKey(Schema.String),
						text: Schema.optionalKey(Schema.String)
					})
				)
			})
		)
	})
);

const SYSTEM_PROMPTS = ['# Workspace instructions', '# Environment'];

export const judgeStateDirectory = (runId: string) => `${import.meta.dir}/../.state/judge/${runId}`;

// Headings become bold so they nest under this file's own, and the Sprocket account id in transcript paths is hidden.
const clean = (text: string) =>
	text
		.trim()
		.replace(/^#{1,6} +(.+)$/gm, '**$1**')
		.replace(/user_[0-9A-Z]{26}/g, '<user>');

const readThread = Effect.fn('readThread')(function* (dir: string) {
	const fs = yield* FileSystem.FileSystem;
	const parts = [];

	for (const file of yield* fs.glob('parts/*.jsonl', { root: dir })) {
		for (const line of (yield* fs.readFileString(`${dir}/${file}`)).split('\n').filter(Boolean))
			parts.push(yield* Schema.decodeEffect(Part)(line));
	}

	parts.sort((a, b) => a.number - b.number);

	const task =
		parts.find(
			(part) =>
				part.kind === 'prompt' &&
				!SYSTEM_PROMPTS.some((prefix) => part.prompt?.text?.startsWith(prefix))
		)?.prompt?.text ?? '';

	const texts = parts.flatMap((part) =>
		(part.completion?.items ?? []).flatMap((item) =>
			item.type === 'text' && item.text ? [item.text] : []
		)
	);

	return { start: parts[0]?.createdAt ?? 0, task, report: texts.at(-1) };
});

// Writes each judge's final message and its subagents' final reports next to its review, from the logs `judge.ts` keeps.
export const writeReasoning = Effect.fn('writeReasoning')(function* (
	runId: string,
	models: ReadonlyArray<string>
) {
	const fs = yield* FileSystem.FileSystem;
	const runDir = runDirectory(runId);
	const state = judgeStateDirectory(runId);

	for (const model of models) {
		const attempts = yield* fs.glob(`${model}/attempt-*/judge.out`, { root: state });

		const logs = `${state}/${attempts
			.sort()
			.at(-1)
			?.replace(/\/judge\.out$/, '')}`;

		const threadStates = yield* fs.glob('transcripts/*/*/state.json', { root: logs });

		const threads = (yield* Effect.forEach(
			threadStates,
			(path) => readThread(`${logs}/${path.replace(/\/state\.json$/, '')}`),
			{ concurrency: 'unbounded' }
		)).sort((a, b) => a.start - b.start);

		const subagents = threads.filter(
			({ task, report }) =>
				report && !task.startsWith('Review the RP2350') && !task.slice(0, 200).includes('cleanup')
		);

		const sections = [
			`# ${model}'s review`,
			'## Final message',
			clean(yield* fs.readFileString(`${logs}/judge.out`)),
			...subagents.flatMap(({ task, report }) => [
				`## Subagent: ${clean(task.split('\n')[0] ?? '')}`,
				clean(report ?? '')
			])
		];

		yield* fs.writeFileString(`${runDir}/review/${model}.md`, `${sections.join('\n\n')}\n`);
	}
});

if (import.meta.main)
	Command.make(
		'reasoning',
		{
			runId: runIdArgument,
			models: Argument.Literals('judge-models', MODELS).pipe(Argument.atLeast(1))
		},
		({ runId, models }) => writeReasoning(runId, models)
	).pipe(Command.run({ version: '0.0.0' }), Effect.provide(BunServices.layer), BunRuntime.runMain);
