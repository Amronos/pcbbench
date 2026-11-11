import { Glob } from 'bun';

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

async function* jsonLines(dir: string, pattern: string) {
	for await (const path of new Glob(pattern).scan({ cwd: dir, absolute: true, dot: true })) {
		for (const line of (await Bun.file(path).text()).split('\n')) {
			if (!line.trim()) continue;

			try {
				yield { path, entry: JSON.parse(line) };
			} catch {}
		}
	}
}

// Claude Code writes one line per streamed content block, all carrying the same message id and usage.
export async function claudeCodeUsage(dir: string) {
	const seen = new Set<string>();
	const usage = empty();

	for await (const { entry } of jsonLines(dir, '**/*.jsonl')) {
		const message = entry?.message;

		if (entry?.type !== 'assistant' || !message?.usage || seen.has(message.id)) continue;
		seen.add(message.id);
		usage.input += message.usage.input_tokens ?? 0;
		usage.cacheRead += message.usage.cache_read_input_tokens ?? 0;
		usage.cacheWrite += message.usage.cache_creation_input_tokens ?? 0;
		usage.output += message.usage.output_tokens ?? 0;
		usage.reasoning += message.usage.output_tokens_details?.thinking_tokens ?? 0;
	}

	return usage;
}

// Each Codex rollout (the main agent and every subagent) keeps running totals; its last token_count is the total.
// Codex's input_tokens includes cached reads and cache writes.
export async function codexUsage(dir: string) {
	const totals = new Map<
		string,
		{
			input_tokens: number;
			cached_input_tokens: number;
			cache_write_input_tokens?: number;
			output_tokens: number;
			reasoning_output_tokens: number;
		}
	>();

	for await (const { path, entry } of jsonLines(dir, '**/rollout-*.jsonl')) {
		const info = entry?.payload?.type === 'token_count' ? entry.payload.info : null;

		if (!info?.total_token_usage) continue;
		totals.set(path, info.total_token_usage);
	}

	const usage = empty();

	for (const total of totals.values()) {
		const cacheWrite = total.cache_write_input_tokens ?? 0;
		usage.input += total.input_tokens - total.cached_input_tokens - cacheWrite;
		usage.cacheRead += total.cached_input_tokens;
		usage.cacheWrite += cacheWrite;
		usage.output += total.output_tokens;
		usage.reasoning += total.reasoning_output_tokens;
	}

	return usage;
}
