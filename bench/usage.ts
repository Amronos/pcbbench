import { Effect, FileSystem, Option, Schema } from 'effect';

export type TokenUsage = {
	input: number;
	cacheRead: number;
	cacheWrite: number;
	output: number;
	reasoning: number;
};

const empty = (): TokenUsage => ({
	input: 0,
	cacheRead: 0,
	cacheWrite: 0,
	output: 0,
	reasoning: 0
});

const logEntries = Effect.fnUntraced(function* <S extends Schema.ConstraintDecoder<unknown>>(
	dir: string,
	isLog: (path: string) => boolean,
	entry: S
) {
	const fs = yield* FileSystem.FileSystem;
	const decode = Schema.decodeUnknownOption(Schema.fromJsonString(entry));
	const paths = (yield* fs.readDirectory(dir, { recursive: true })).filter(isLog);

	return yield* Effect.forEach(paths, (path) =>
		fs
			.readFileString(`${dir}/${path}`)
			.pipe(Effect.map((text) => text.split('\n').flatMap((line) => Option.toArray(decode(line)))))
	);
});

const optionalCount = Schema.optional(Schema.NullOr(Schema.Number));

const ClaudeCodeEntry = Schema.Struct({
	type: Schema.Literal('assistant'),
	message: Schema.Struct({
		id: Schema.String,
		usage: Schema.Struct({
			input_tokens: optionalCount,
			cache_read_input_tokens: optionalCount,
			cache_creation_input_tokens: optionalCount,
			output_tokens: optionalCount,
			output_tokens_details: Schema.optional(
				Schema.NullOr(Schema.Struct({ thinking_tokens: optionalCount }))
			)
		})
	})
});

// Claude Code writes one line per streamed content block, all carrying the same message id and usage.
export const claudeCodeUsage = Effect.fn('claudeCodeUsage')(function* (dir: string) {
	const seen = new Set<string>();
	const usage = empty();

	const files = yield* logEntries(dir, (path) => path.endsWith('.jsonl'), ClaudeCodeEntry);

	for (const entry of files.flat()) {
		const { id, usage: counts } = entry.message;

		if (seen.has(id)) continue;
		seen.add(id);
		usage.input += counts.input_tokens ?? 0;
		usage.cacheRead += counts.cache_read_input_tokens ?? 0;
		usage.cacheWrite += counts.cache_creation_input_tokens ?? 0;
		usage.output += counts.output_tokens ?? 0;
		usage.reasoning += counts.output_tokens_details?.thinking_tokens ?? 0;
	}

	return usage;
});

const CodexEntry = Schema.Struct({
	payload: Schema.Struct({
		type: Schema.Literal('token_count'),
		info: Schema.Struct({
			total_token_usage: Schema.Struct({
				input_tokens: Schema.Number,
				cached_input_tokens: Schema.Number,
				cache_write_input_tokens: optionalCount,
				output_tokens: Schema.Number,
				reasoning_output_tokens: Schema.Number
			})
		})
	})
});

const isCodexRollout = (path: string) => /(^|\/)rollout-[^/]*\.jsonl$/.test(path);

// Each Codex rollout (the main agent and every subagent) keeps running totals; its last token_count is the total.
// Codex's input_tokens includes cached reads and cache writes.
export const codexUsage = Effect.fn('codexUsage')(function* (dir: string) {
	const files = yield* logEntries(dir, isCodexRollout, CodexEntry);
	const usage = empty();

	for (const total of files.flatMap(
		(entries) => entries.at(-1)?.payload.info.total_token_usage ?? []
	)) {
		const cacheWrite = total.cache_write_input_tokens ?? 0;
		usage.input += total.input_tokens - total.cached_input_tokens - cacheWrite;
		usage.cacheRead += total.cached_input_tokens;
		usage.cacheWrite += cacheWrite;
		usage.output += total.output_tokens;
		usage.reasoning += total.reasoning_output_tokens;
	}

	return usage;
});
