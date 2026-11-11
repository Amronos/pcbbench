import { $ } from 'bun';
import { chmod, mkdir } from 'node:fs/promises';
import { COST_LIMIT_USD, COST_REVOKE_MARGIN_USD, RUNS } from './runs.ts';

const SCOPE = 'spikonado';
const STATE_DIR = `${import.meta.dir}/.state`;
const POLL_MS = 15_000;

type RunKey = { runId: string; keyId: string; name: string; secret: string };

type Budget = { currentSpend: number; currentByokSpend: number; active: boolean };

const vercel = (args: string[]) => $`bunx vercel@latest ${args} --scope ${SCOPE}`.quiet();

const keyName = (runId: string) => `pcbbench-${runId}`;

const statePath = (runId: string) => `${STATE_DIR}/${runId}.key.json`;

function costLimitUsd(runId: string) {
	const run = RUNS.find((candidate) => candidate.id === runId);
	if (!run) throw new Error(`Unknown run id: ${runId}`);
	return COST_LIMIT_USD[run.model];
}

export async function createRunKey(runId: string): Promise<RunKey> {
	const name = keyName(runId);
	const out = await vercel([
		'ai-gateway',
		'api-keys',
		'create',
		'--name',
		name,
		'--amount',
		String(costLimitUsd(runId)),
		'--include-byok',
		'--expiration',
		'7d'
	]);
	const text = out.stdout.toString() + out.stderr.toString();
	const secret = text.match(/vck_\w+/)?.[0];
	const keyId = text.match(/API key \S+ \((\w+)\) created/)?.[1];
	if (!secret || !keyId)
		throw new Error(`Could not parse the new key from: ${text.replaceAll(/vck_\w+/g, 'vck_…')}`);
	const key = { runId, keyId, name, secret };
	await mkdir(STATE_DIR, { recursive: true });
	await Bun.write(statePath(runId), JSON.stringify(key));
	await chmod(statePath(runId), 0o600);
	return key;
}

export async function readRunKey(runId: string): Promise<RunKey> {
	return Bun.file(statePath(runId)).json();
}

export async function readBudget(key: RunKey): Promise<Budget> {
	const out = await vercel([
		'ai-gateway',
		'budgets',
		'inspect',
		'api-key',
		key.name,
		'--format',
		'json'
	]);
	const text = out.stdout.toString();
	return JSON.parse(text.slice(text.indexOf('{')));
}

export const spentUsd = (budget: Budget) => budget.currentSpend + budget.currentByokSpend;

export async function revokeRunKey(key: RunKey) {
	await vercel(['ai-gateway', 'api-keys', 'revoke', key.keyId, '--yes']);
}

async function watchRunKey(key: RunKey) {
	const revokeAtUsd = costLimitUsd(key.runId) - COST_REVOKE_MARGIN_USD;
	for (;;) {
		const budget = await readBudget(key).catch((error: Error) => {
			console.error(`Budget read failed: ${error.message}`);
			return null;
		});
		if (budget && spentUsd(budget) >= revokeAtUsd) {
			await revokeRunKey(key);
			await Bun.write(
				`${STATE_DIR}/${key.runId}.revoked.json`,
				JSON.stringify({ at: new Date(), spentUsd: spentUsd(budget) })
			);
			console.log(`Revoked ${key.name} at $${spentUsd(budget).toFixed(2)}`);
			return;
		}
		await Bun.sleep(POLL_MS);
	}
}

if (import.meta.main) {
	const [command, runId] = Bun.argv.slice(2);
	if (!RUNS.some((run) => run.id === runId)) throw new Error(`Unknown run id: ${runId}`);
	if (command === 'create') {
		const key = await createRunKey(runId);
		console.log(`Created ${key.name} (${key.keyId}); secret in ${statePath(runId)}`);
	} else if (command === 'spent') {
		console.log(JSON.stringify(await readBudget(await readRunKey(runId))));
	} else if (command === 'watch') {
		await watchRunKey(await readRunKey(runId));
	} else if (command === 'revoke') {
		await revokeRunKey(await readRunKey(runId));
	} else {
		throw new Error('Usage: bun bench/gateway.ts create|spent|watch|revoke <run-id>');
	}
}
