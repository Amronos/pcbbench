import { mkdir, readdir, writeFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { MODELS, REASONING_EFFORT, WALL_CLOCK_LIMIT_HOURS, isModelId, renderPrompt, type ModelId } from '../../runs.ts';

const [runId, model, promptFile] = Bun.argv.slice(2);
if (!runId || !isModelId(model)) {
	console.error(`Usage: bun run.ts <run-id> <${MODELS.join('|')}> [smoke-test prompt file]`);
	process.exit(2);
}

const workDir = join(homedir(), 'pcbbench-run');
const resultDir = join(homedir(), 'pcbbench-results', runId);
await mkdir(workDir, { recursive: true });
if ((await readdir(workDir)).length > 0) {
	console.error(`${workDir} is not empty; use a fresh box or clear it first.`);
	process.exit(1);
}
await mkdir(resultDir, { recursive: true });

// Each box needs its own login; a copied refresh token dies 30 s after any other copy refreshes.
if (Bun.spawnSync(['sprocket', 'run', '--list-models'], { stdout: 'ignore', stderr: 'ignore' }).exitCode !== 0) {
	const login = Bun.spawnSync(['sprocket', 'login', '--credential-store', 'file'], { stdio: ['inherit', 'inherit', 'inherit'] });
	if (login.exitCode !== 0) process.exit(1);
}

const prompt = await renderPrompt(model, promptFile);
const renderedPrompt = join(resultDir, 'prompt.md');
await Bun.write(renderedPrompt, prompt);

const result: {
	runId: string;
	harness: 'sprocket';
	model: ModelId;
	reasoning: typeof REASONING_EFFORT;
	sprocketVersion: string;
	workDir: string;
	startedAt: string;
	finishedAt?: string;
	threadId?: string;
	sprocketRunId?: string;
	exitCode?: number;
} = {
	runId,
	harness: 'sprocket',
	model,
	reasoning: REASONING_EFFORT,
	sprocketVersion: Bun.spawnSync(['sprocket', '--version']).stdout.toString().trim(),
	workDir,
	startedAt: new Date().toISOString()
};
const saveResult = () => writeFile(join(resultDir, 'result.json'), JSON.stringify(result, null, '\t') + '\n');
await saveResult();

const child = Bun.spawn(
	[
		'sprocket', 'run',
		'--prompt-file', renderedPrompt,
		'-C', workDir,
		'--model', model,
		'--reasoning', REASONING_EFFORT,
		'--timeout', `${WALL_CLOCK_LIMIT_HOURS}h`
	],
	{ stdin: 'ignore', stdout: 'pipe', stderr: 'pipe' }
);

async function tee(stream: ReadableStream<Uint8Array>, path: string, echo: NodeJS.WriteStream, onText?: (text: string) => void) {
	const file = Bun.file(path).writer();
	const decoder = new TextDecoder();
	for await (const chunk of stream) {
		file.write(chunk);
		file.flush();
		echo.write(chunk);
		onText?.(decoder.decode(chunk, { stream: true }));
	}
	await file.end();
}

let stderrSoFar = '';
await Promise.all([
	tee(child.stdout, join(resultDir, 'stdout.md'), process.stdout),
	tee(child.stderr, join(resultDir, 'stderr.log'), process.stderr, async (text) => {
		if (result.threadId) return;
		stderrSoFar += text;
		const ids = stderrSoFar.match(/Thread (\S+) \| Run (\S+)/);
		if (ids) {
			result.threadId = ids[1];
			result.sprocketRunId = ids[2];
			await saveResult();
		}
	})
]);

const exitCode = await child.exited;
result.exitCode = exitCode;
result.finishedAt = new Date().toISOString();
await saveResult();
console.error(`\nSaved ${resultDir}/result.json (thread ${result.threadId}, exit ${exitCode})`);
process.exit(exitCode);
