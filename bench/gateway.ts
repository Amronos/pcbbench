import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Console, DateTime, Effect, FileSystem, Option, Schema, Stream } from 'effect';
import { Argument, Command } from 'effect/cli';
import { ChildProcess, ChildProcessSpawner } from 'effect/process';
import { COST_LIMIT_USD, COST_REVOKE_MARGIN_USD, RUNS } from './runs.ts';

const SCOPE = 'spikonado';
const STATE_DIR = `${import.meta.dir}/.state`;
const POLL_MS = 15_000;

const RunKey = Schema.Struct({
	runId: Schema.String,
	keyId: Schema.String,
	name: Schema.String,
	secret: Schema.String
});

type RunKey = typeof RunKey.Type;

const Budget = Schema.Struct({
	currentSpend: Schema.Number,
	currentByokSpend: Schema.Number,
	active: Schema.Boolean
});

type Budget = typeof Budget.Type;

export class GatewayError extends Schema.TaggedError<GatewayError>()('GatewayError', {
	message: Schema.String
}) {}

const redactSecrets = (text: string) => text.replaceAll(/vck_\w+/g, 'vck_…');

const vercel = Effect.fn('vercel')(function* (args: ReadonlyArray<string>) {
	const spawner = yield* ChildProcessSpawner.ChildProcessSpawner;

	const handle = yield* spawner.spawn(
		ChildProcess.make('bunx', ['vercel@latest', ...args, '--scope', SCOPE], { stdin: 'inherit' })
	);

	const [stdout, stderr, exitCode] = yield* Effect.all(
		[
			Stream.mkString(Stream.decodeText(handle.stdout)),
			Stream.mkString(Stream.decodeText(handle.stderr)),
			handle.exitCode
		],
		{ concurrency: 'unbounded' }
	);

	if (exitCode !== 0)
		return yield* new GatewayError({
			message: `vercel ${args.join(' ')} exited with ${exitCode}: ${redactSecrets(stderr)}`
		});

	return { stdout, stderr };
}, Effect.scoped);

const keyName = (runId: string) => `pcbbench-${runId}`;

const statePath = (runId: string) => `${STATE_DIR}/${runId}.key.json`;

const costLimitUsd = Effect.fnUntraced(function* (runId: string) {
	const run = RUNS.find((candidate) => candidate.id === runId);

	if (!run) return yield* new GatewayError({ message: `Unknown run id: ${runId}` });

	return COST_LIMIT_USD[run.model];
});

const createRunKey = Effect.fn('createRunKey')(function* (runId: string) {
	const name = keyName(runId);

	const out = yield* vercel([
		'ai-gateway',
		'api-keys',
		'create',
		'--name',
		name,
		'--amount',
		String(yield* costLimitUsd(runId)),
		'--include-byok',
		'--expiration',
		'7d'
	]);

	const text = out.stdout + out.stderr;
	const secret = text.match(/vck_\w+/)?.[0];
	const keyId = text.match(/API key \S+ \((\w+)\) created/)?.[1];

	if (!secret || !keyId)
		return yield* new GatewayError({
			message: `Could not parse the new key from: ${redactSecrets(text)}`
		});
	const key = { runId, keyId, name, secret };
	const fs = yield* FileSystem.FileSystem;
	yield* fs.makeDirectory(STATE_DIR, { recursive: true });
	yield* fs.writeFileString(statePath(runId), JSON.stringify(key));
	yield* fs.chmod(statePath(runId), 0o600);

	return key;
});

export const readRunKey = Effect.fn('readRunKey')(function* (runId: string) {
	const text = yield* (yield* FileSystem.FileSystem).readFileString(statePath(runId));

	return yield* Schema.decodeEffect(Schema.fromJsonString(RunKey))(text);
});

export const readBudget = Effect.fn('readBudget')(function* (key: RunKey) {
	const { stdout } = yield* vercel([
		'ai-gateway',
		'budgets',
		'inspect',
		'api-key',
		key.name,
		'--format',
		'json'
	]);

	return yield* Schema.decodeEffect(Schema.fromJsonString(Budget))(
		stdout.slice(stdout.indexOf('{'))
	);
});

export const spentUsd = (budget: Budget) => budget.currentSpend + budget.currentByokSpend;

export const revokeRunKey = Effect.fn('revokeRunKey')(function* (key: RunKey) {
	yield* vercel(['ai-gateway', 'api-keys', 'revoke', key.keyId, '--yes']);
});

const watchRunKey = Effect.fn('watchRunKey')(function* (key: RunKey) {
	const revokeAtUsd = (yield* costLimitUsd(key.runId)) - COST_REVOKE_MARGIN_USD;

	for (;;) {
		const spent = yield* readBudget(key).pipe(
			Effect.map(spentUsd),
			Effect.tapError((error) => Console.error(`Budget read failed: ${error.message}`)),
			Effect.option
		);

		if (Option.isSome(spent) && spent.value >= revokeAtUsd) {
			yield* revokeRunKey(key);
			yield* (yield* FileSystem.FileSystem).writeFileString(
				`${STATE_DIR}/${key.runId}.revoked.json`,
				JSON.stringify({ at: DateTime.formatIso(yield* DateTime.now), spentUsd: spent.value })
			);
			yield* Console.log(`Revoked ${key.name} at $${spent.value.toFixed(2)}`);

			return;
		}

		yield* Effect.sleep(POLL_MS);
	}
});

const runId = Argument.Literals(
	'run-id',
	RUNS.map((run) => run.id)
);

const gateway = Command.make('gateway').pipe(
	Command.withSubcommands([
		Command.make('create', { runId }, ({ runId }) =>
			Effect.gen(function* () {
				const key = yield* createRunKey(runId);
				yield* Console.log(`Created ${key.name} (${key.keyId}); secret in ${statePath(runId)}`);
			})
		),
		Command.make('spent', { runId }, ({ runId }) =>
			readRunKey(runId).pipe(
				Effect.flatMap(readBudget),
				Effect.flatMap((budget) => Console.log(JSON.stringify(budget)))
			)
		),
		Command.make('watch', { runId }, ({ runId }) =>
			readRunKey(runId).pipe(Effect.flatMap(watchRunKey))
		),
		Command.make('revoke', { runId }, ({ runId }) =>
			readRunKey(runId).pipe(Effect.flatMap(revokeRunKey))
		)
	])
);

if (import.meta.main)
	gateway.pipe(
		Command.run({ version: '0.0.0' }),
		Effect.provide(BunServices.layer),
		BunRuntime.runMain
	);
