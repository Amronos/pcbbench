import { Glob } from 'bun';
import { readRun } from '../board.ts';

type Part = {
	number: number;
	createdAt: number;
	kind: string;
	prompt?: { text?: string };
	completion?: { items: { type?: string; text?: string }[] };
};

const SYSTEM_PROMPTS = ['# Workspace instructions', '# Environment'];

// Headings become bold so they nest under this file's own, and the Sprocket account id in transcript paths is hidden.
const clean = (text: string) =>
	text
		.trim()
		.replace(/^#{1,6} +(.+)$/gm, '**$1**')
		.replace(/user_[0-9A-Z]{26}/g, '<user>');

async function readThread(dir: string) {
	const parts: Part[] = [];

	for await (const file of new Glob('parts/*.jsonl').scan(dir)) {
		for (const line of (await Bun.file(`${dir}/${file}`).text()).split('\n').filter(Boolean))
			parts.push(JSON.parse(line));
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
}

// Writes each judge's final message and its subagents' final reports next to its review, from the logs `judge.ts` keeps.
export async function writeReasoning(runId: string, models: string[]) {
	const { runDir } = await readRun(runId);
	const state = `${import.meta.dir}/../.state/judge/${runId}`;

	for (const model of models) {
		const attempts = await Array.fromAsync(new Glob(`${model}/attempt-*/judge.out`).scan(state));

		const logs = `${state}/${attempts
			.sort()
			.at(-1)
			?.replace(/\/judge\.out$/, '')}`;

		const threadStates = await Array.fromAsync(new Glob('transcripts/*/*/state.json').scan(logs));

		const threads = (
			await Promise.all(
				threadStates.map((path) => readThread(`${logs}/${path.replace(/\/state\.json$/, '')}`))
			)
		).sort((a, b) => a.start - b.start);

		const subagents = threads.filter(
			({ task, report }) =>
				report && !task.startsWith('Review the RP2350') && !task.slice(0, 200).includes('cleanup')
		);

		const sections = [
			`# ${model}'s review`,
			'## Final message',
			clean(await Bun.file(`${logs}/judge.out`).text()),
			...subagents.flatMap(({ task, report }) => [
				`## Subagent: ${clean(task.split('\n')[0] ?? '')}`,
				clean(report ?? '')
			])
		];

		await Bun.write(`${runDir}/review/${model}.md`, `${sections.join('\n\n')}\n`);
	}
}

if (import.meta.main) {
	const [runId, ...models] = Bun.argv.slice(2);

	if (!runId || !models.length)
		throw new Error('Usage: bun judge/reasoning.ts <run id> <judge models>');
	await writeReasoning(runId, models);
}
