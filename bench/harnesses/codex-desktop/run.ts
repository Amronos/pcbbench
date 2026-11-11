import { $ } from 'bun';
import { mkdir } from 'node:fs/promises';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { readRunKey, revokeRunKey } from '../../gateway.ts';
import {
	GATEWAY_MODEL,
	REASONING_EFFORT,
	RUNS,
	WALL_CLOCK_LIMIT_HOURS,
	kicadFullVersion,
	parseVersions,
	renderPrompt,
	type Harness,
	type ModelId
} from '../../runs.ts';

const INSTANCE_ID = 'i-0667c1457d80ee354';
const BASE_AMI = 'ami-0a11b952507c9bb48';
const HOST = 'ec2-user@54.234.19.231';
const SSH_OPTIONS = [
	'-i',
	join(homedir(), '.ssh/pcbbench.pem'),
	'-o',
	`UserKnownHostsFile=${join(homedir(), '.config/pcbbench/mac_known_hosts')}`,
	'-o',
	'StrictHostKeyChecking=accept-new',
	'-o',
	'ConnectTimeout=15',
	'-o',
	'ServerAliveInterval=30',
	'-o',
	'BatchMode=yes'
];
const VNC_PORT = 15901;
const WORK_DIR = '/Users/ec2-user/pcbbench-run';
const HERE = import.meta.dir;
const POLL_MS = 60_000;

type Run = ReturnType<typeof parseRunId>;

type Result = {
	runId: string;
	harness: Harness;
	model: ModelId;
	reasoning: typeof REASONING_EFFORT;
	versions: Record<string, string>;
	startedAt: string;
	rollout: string;
	finishedAt?: string;
	outcome?: 'task_complete' | 'turn_aborted' | 'wall_clock_limit';
};

const aws = (args: string[]) => $`nix run nixpkgs#awscli2 -- --region us-east-1 ${args}`.quiet();

// Commands run as ec2-user in the GUI login session, where the app and its environment live.
const AS_GUI_USER = 'sudo launchctl asuser 501 sudo -u ec2-user';

async function mac(script: string, { check = true } = {}): Promise<string> {
	const child = Bun.spawn(['ssh', ...SSH_OPTIONS, HOST, 'bash -s'], {
		stdin: new Blob([`set -euo pipefail\n${script}`]),
		stdout: 'pipe',
		stderr: 'inherit'
	});
	const stdout = await new Response(child.stdout).text();
	if ((await child.exited) !== 0 && check) throw new Error(`Mac command failed:\n${script}`);
	return stdout.trim();
}

async function vnc(...actions: string[]) {
	const tunnel = Bun.spawn([
		'ssh',
		...SSH_OPTIONS,
		'-N',
		'-o',
		'ExitOnForwardFailure=yes',
		'-L',
		`${VNC_PORT}:localhost:5900`,
		HOST
	]);
	try {
		await Bun.sleep(3000);
		await $`uv run --quiet ${join(HERE, 'vnc.py')} ${actions}`.env({
			...process.env,
			MAC_VNC_PORT: String(VNC_PORT)
		});
	} finally {
		tunnel.kill();
	}
}

const shellQuote = (text: string) => `'${text.replaceAll("'", `'\\''`)}'`;

function parseRunId(runId: string | undefined) {
	// A suffix such as --smoke reuses a benchmark run's setup under its own id.
	const base = RUNS.find(
		(run) => run.machine === 'mac' && (runId === run.id || runId?.startsWith(`${run.id}--`))
	);
	if (!runId || !base) {
		console.error(
			`Run ids are a mac run from runs.ts with an optional --suffix: ${RUNS.filter(
				(run) => run.machine === 'mac'
			)
				.map((run) => run.id)
				.join(', ')}`
		);
		process.exit(2);
	}
	return {
		runId,
		harness: base.harness,
		model: base.model,
		resultDir: join(homedir(), 'pcbbench-results', runId)
	};
}

async function reset() {
	const task = await aws([
		'ec2',
		'create-replace-root-volume-task',
		'--instance-id',
		INSTANCE_ID,
		'--image-id',
		BASE_AMI,
		'--delete-replaced-root-volume',
		'--query',
		'ReplaceRootVolumeTask.ReplaceRootVolumeTaskId',
		'--output',
		'text'
	]);
	const taskId = task.stdout.toString().trim();
	console.log(`Replacing the root volume with ${BASE_AMI} (${taskId})`);
	for (;;) {
		await Bun.sleep(30_000);
		const state = (
			await aws([
				'ec2',
				'describe-replace-root-volume-tasks',
				'--replace-root-volume-task-ids',
				taskId,
				'--query',
				'ReplaceRootVolumeTasks[0].TaskState',
				'--output',
				'text'
			])
		).stdout
			.toString()
			.trim();
		console.log(state);
		if (state === 'succeeded') break;
		if (state.startsWith('fail')) throw new Error(`Root volume replacement ${taskId} ${state}`);
	}
	for (;;) {
		const ready = await mac('pgrep -xu ec2-user Dock >/dev/null && echo ready', {
			check: false
		}).catch(() => '');
		if (ready === 'ready') break;
		await Bun.sleep(15_000);
	}
	console.log('The Mac is back and logged in.');
}

async function start(run: Run, promptFile: string | undefined) {
	const { runId } = run;
	const { secret } = await readRunKey(runId);
	await mkdir(run.resultDir, { recursive: true });
	const prompt = await renderPrompt(run.model, promptFile);
	await Bun.write(join(run.resultDir, 'prompt.md'), prompt);
	const config = (await Bun.file(join(HERE, 'config.toml')).text())
		.replaceAll('__MODEL__', GATEWAY_MODEL[run.model])
		.replaceAll('__EFFORT__', REASONING_EFFORT)
		.replaceAll('__RUN_ID__', runId);

	const leftovers = await mac(`ls -A ${WORK_DIR}; find ~/.codex/sessions -type f`);
	if (leftovers)
		throw new Error(`The Mac is not fresh; run \`bun run.ts reset\` first:\n${leftovers}`);
	await mac(`cat > ~/.codex/config.toml <<'CONFIG'
${config}CONFIG`);

	// The installer adds the plugin to config.toml, so it runs after the config is written.
	if (run.harness === 'codex-desktop-texttocad') {
		console.log('Installing text-to-cad');
		const log =
			await mac(`curl -fsSL https://texttocad.dev/install.sh | sh -s -- --only codex --no-telemetry 2>&1
~/.local/bin/cad doctor 2>&1`);
		await Bun.write(join(run.resultDir, 'texttocad-install.log'), log + '\n');
	}

	console.log('Starting the app');
	const link = `codex://new?prompt=${encodeURIComponent(prompt)}&path=${encodeURIComponent(WORK_DIR)}`;
	await mac(`pkill -f /Applications/ChatGPT.app || true
sleep 3
key=${shellQuote(secret)}
printf %s "$key" | ${AS_GUI_USER} sh -c 'launchctl setenv AI_GATEWAY_API_KEY "$(cat)"'
${AS_GUI_USER} open -a ChatGPT
sleep 20
${AS_GUI_USER} open ${shellQuote(link)}
sleep 5`);
	// Return inside a Markdown list in the composer may add a list item, so click the send button.
	await vnc(
		'shot',
		join(run.resultDir, 'filled.png'),
		'click',
		'981',
		'666',
		'sleep',
		'10',
		'shot',
		join(run.resultDir, 'started.png')
	);

	const rollout = await mac(
		'sleep 20; find ~/.codex/sessions -name "rollout-*.jsonl" | sort | head -1'
	);
	if (!rollout) throw new Error(`No rollout appeared; check ${run.resultDir}/started.png`);
	const versions = parseVersions(
		await mac(`echo "chatgpt=$(defaults read /Applications/ChatGPT.app/Contents/Info CFBundleShortVersionString)"
echo "codex=$(/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex --version)"
echo "kicad=${kicadFullVersion('/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli')}"
echo "texttocad=$(~/.local/bin/cad --version 2>/dev/null || echo none)"`)
	);
	const result: Result = {
		runId,
		harness: run.harness,
		model: run.model,
		reasoning: REASONING_EFFORT,
		versions,
		startedAt: new Date().toISOString(),
		rollout
	};
	await Bun.write(join(run.resultDir, 'result.json'), JSON.stringify(result, null, '\t') + '\n');
	console.log(`Started ${runId}; rollout ${rollout}`);
	await wait(run);
}

async function wait(run: Run) {
	const resultPath = join(run.resultDir, 'result.json');
	const result: Result = await Bun.file(resultPath).json();
	const deadline = Date.parse(result.startedAt) + WALL_CLOCK_LIMIT_HOURS * 3_600_000;
	while (!result.outcome) {
		const status = await mac(
			`grep -oE '"type":"(task_complete|turn_aborted)"' ${result.rollout} | tail -1 | cut -d'"' -f4 || true
grep '"type":"token_count"' ${result.rollout} | tail -1 | grep -oE '"total_token_usage":\\{[^}]*\\}' || true`,
			{ check: false }
		);
		const end = status.match(/^(task_complete|turn_aborted)$/m)?.[1];
		const usage = status.match(/"total_token_usage".*/)?.[0];
		console.log(`${new Date().toISOString()} ${usage ?? 'no token usage yet'}`);
		if (end === 'task_complete' || end === 'turn_aborted') result.outcome = end;
		else if (Date.now() > deadline) {
			await mac('pkill -f /Applications/ChatGPT.app || true');
			await revokeRunKey(await readRunKey(run.runId));
			result.outcome = 'wall_clock_limit';
		} else await Bun.sleep(POLL_MS);
	}
	result.finishedAt = new Date().toISOString();
	await vnc('shot', join(run.resultDir, 'finished.png')).catch((error) =>
		console.error(`Final screenshot failed: ${error}`)
	);
	await collect(run.resultDir);
	await Bun.write(resultPath, JSON.stringify(result, null, '\t') + '\n');
	console.log(`${run.runId} ended with ${result.outcome}; results in ${run.resultDir}`);
}

async function collect(resultDir: string) {
	await $`ssh ${SSH_OPTIONS} ${HOST} 'tar -C ~ -czf - pcbbench-run .codex/sessions' | tar -C ${resultDir} -xzf -`;
}

const [command, runId, promptFile] = Bun.argv.slice(2);
if (command === 'reset') await reset();
else if (command === 'start') await start(parseRunId(runId), promptFile);
else if (command === 'wait') await wait(parseRunId(runId));
else if (command === 'collect') await collect(parseRunId(runId).resultDir);
else {
	console.error(
		'Usage: bun run.ts reset | start <run-id> [smoke-test prompt file] | wait <run-id> | collect <run-id>'
	);
	process.exit(2);
}
