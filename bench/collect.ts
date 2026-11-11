import { $ } from 'bun';
import { mkdir } from 'node:fs/promises';
import { homedir } from 'node:os';
import { readBudget, readRunKey, spentUsd } from './gateway.ts';
import {
	BACKPLANE_CLI,
	REASONING_EFFORT,
	RUNS,
	kicadFullVersion,
	minutesBetween,
	parseVersions,
	type Run
} from './runs.ts';
import { claudeCodeUsage, codexUsage, type TokenUsage } from './usage.ts';

// GitHub rejects files over 100 MB; agents sometimes leave large downloads in their folder.
const MAX_FILE_SIZE = '50M';

type Timing = { startedAt: string; finishedAt: string; minutes: number; endedBy: string };

type CollectedHarness = {
	logs: (runId: string, source: string) => [from: string, local: string][];
	timing: (logsDir: string) => Promise<Timing>;
	tokens: (logsDir: string, run: Run) => Promise<TokenUsage | null>;
	// Linux boxes are asked directly; the Codex driver records the Mac's versions when the run starts.
	versions: (logsDir: string) => Promise<Record<string, string>>;
};

// The Codex driver copies the Mac's results to this machine, so Mac runs are collected from that local folder.
const codexDesktop: CollectedHarness = {
	logs: (runId, source) => [
		[source, 'codex-desktop'],
		[`${import.meta.dir}/.state/${runId}.driver.log`, 'driver.log']
	],
	timing: async (logsDir) => {
		const result = await Bun.file(`${logsDir}/codex-desktop/result.json`).json();
		return {
			startedAt: result.startedAt,
			finishedAt: result.finishedAt,
			minutes: minutesBetween(Date.parse(result.startedAt), Date.parse(result.finishedAt)),
			endedBy: result.outcome === 'task_complete' ? 'done' : result.outcome
		};
	},
	tokens: (logsDir) => codexUsage(logsDir),
	versions: async (logsDir) =>
		(await Bun.file(`${logsDir}/codex-desktop/result.json`).json()).versions
};

const HARNESSES: Record<Run['harness'], CollectedHarness> = {
	backplane: {
		logs: (runId, source) => [
			[`${source}pcbbench-logs/${runId}/`, 'backplane'],
			[`${source}driver.log`, 'driver.log']
		],
		timing: async (logsDir) => {
			const summary = await Bun.file(`${logsDir}/backplane/summary.json`).json();
			return {
				startedAt: summary.startedAt,
				finishedAt: summary.endedAt,
				minutes: summary.minutes,
				endedBy: summary.status
			};
		},
		tokens: (logsDir, run) =>
			BACKPLANE_CLI[run.model] === 'claude' ? claudeCodeUsage(logsDir) : codexUsage(logsDir),
		versions: () =>
			remoteVersions(`echo "backplane=$(~/.local/share/backplane/builds/*/backplane-hub --version)"
echo "claudeCode=$(~/.local/bin/claude --version)"
echo "codex=$(codex --version)"
kicad=$(ls -d ~/.local/share/backplane/kicad/*/ | head -1)
echo "kicad=$(basename $kicad) ($(cat $kicad/SOURCE_COMMIT))"`)
	},
	sprocket: {
		logs: (runId, source) => [
			[`${source}pcbbench-results/${runId}/`, 'sprocket'],
			[`${source}.sprocket/transcripts/`, 'sprocket-transcripts'],
			[`${source}driver.log`, 'driver.log']
		],
		timing: async (logsDir) => {
			const result = await Bun.file(`${logsDir}/sprocket/result.json`).json();
			return {
				startedAt: result.startedAt,
				finishedAt: result.finishedAt,
				// Runs resumed after server errors record only the time a turn was running.
				minutes:
					result.activeMinutes ??
					minutesBetween(Date.parse(result.startedAt), Date.parse(result.finishedAt)),
				endedBy: result.exitCode === 0 ? 'done' : `exit ${result.exitCode}`
			};
		},
		// Sprocket keeps token usage in its cloud; it is read from the thread in the web UI and added to metrics.json by hand.
		tokens: async () => null,
		versions: () =>
			remoteVersions(`echo "sprocket=$(sprocket --version)"
echo "kicadConnector=$(ls ~/.sprocket/connectors/kicad | grep '^v')"
echo "kicad=${kicadFullVersion('~/.sprocket/connectors/kicad/bin/kicad-cli')}"`)
	},
	'codex-desktop': codexDesktop,
	'codex-desktop-texttocad': codexDesktop
};

const [runId, host] = Bun.argv.slice(2);
const run = RUNS.find((candidate) => candidate.id === runId);
if (!run || (run.machine === 'linux' && !host)) {
	throw new Error('Usage: bun bench/collect.ts <run id> [user@host, for Linux runs]');
}
const harness = HARNESSES[run.harness];
const source = run.machine === 'mac' ? `${homedir()}/pcbbench-results/${run.id}/` : `${host}:`;

const runDir = `${import.meta.dir}/../runs/${run.id}`;
// Logs hold account ids and transcripts, so they stay on this machine and out of the public repo.
const logsDir = `${import.meta.dir}/.state/logs/${run.id}`;
const ssh = `ssh -i ${homedir()}/.ssh/pcbbench.pem -o BatchMode=yes`;
const remoteVersions = async (script: string) =>
	parseVersions(await $`${{ raw: ssh }} ${host} ${script}`.text());
await mkdir(logsDir, { recursive: true });

// Agents clone reference repos into their folder; a nested .git would become a gitlink here.
await $`rsync -a --delete --delete-excluded --max-size=${MAX_FILE_SIZE} --exclude=.git --exclude=.venv --exclude=node_modules --exclude=__pycache__ -e ${ssh} ${source}pcbbench-run/ ${runDir}/output/`;
const findLarge = `find pcbbench-run -type f -size +${MAX_FILE_SIZE}`;
const skipped =
	run.machine === 'mac'
		? await $`${{ raw: findLarge }}`.cwd(source).text()
		: await $`${{ raw: ssh }} ${host} ${findLarge}`.text();
for (const [from, local] of harness.logs(run.id, source)) {
	await $`rsync -a --exclude=/pcbbench-run -e ${ssh} ${from} ${logsDir}/${local}`;
}

const usesGateway = run.harness !== 'sprocket';
// A revoked key's budget can no longer be read, so a re-collect keeps the cost recorded before revocation.
const budget = usesGateway ? await readBudget(await readRunKey(run.id)).catch(() => null) : null;
const metricsPath = `${runDir}/metrics.json`;
const previous = (await Bun.file(metricsPath).exists()) ? await Bun.file(metricsPath).json() : {};
const collected = {
	...(await harness.timing(logsDir)),
	tokens: (await harness.tokens(logsDir, run)) ?? previous.tokens ?? null,
	costUsd: budget ? spentUsd(budget) : (previous.costUsd ?? null),
	costSource: usesGateway ? 'API cost at market prices' : 'Sprocket thread usage in the web UI',
	boardCost: previous.boardCost ?? null
};
// Fields added later by hand or by price.ts (fixes, costByModel) survive a re-collect.
const metrics = { ...collected, ...previous, ...collected };
const infoPath = `${runDir}/info.json`;
// These are set by hand once the run's final files are known.
const {
	board = null,
	bom = null,
	placement = null,
	fabZip = null
} = (await Bun.file(infoPath).exists()) ? await Bun.file(infoPath).json() : {};
const info = {
	runId: run.id,
	harness: run.harness,
	model: run.model,
	reasoning: REASONING_EFFORT,
	machine: run.machine,
	versions: await harness.versions(logsDir),
	skippedLargeFiles: skipped.split('\n').filter(Boolean),
	board,
	bom,
	placement,
	fabZip
};
for (const [name, data] of [
	['metrics', metrics],
	['info', info]
] as const) {
	await Bun.write(`${runDir}/${name}.json`, `${JSON.stringify(data, null, '\t')}\n`);
	console.log(JSON.stringify(data, null, '\t'));
}

// The repo is public, so stop before anything that looks like a credential gets committed.
const leaks =
	await $`grep -rlE ${'vck_[A-Za-z0-9]{20,}|gh[opsu]_[A-Za-z0-9]{30,}|\\bsk-[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}'} ${runDir}`
		.nothrow()
		.text();
if (leaks.trim()) throw new Error(`Possible credentials in:\n${leaks}`);
