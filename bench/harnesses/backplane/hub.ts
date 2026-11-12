import { BunSocket } from '@effect/platform-bun';
import {
	Deferred,
	Effect,
	Fiber,
	FileSystem,
	Layer,
	Match,
	Option,
	Predicate,
	Schedule,
	Schema,
	Stream
} from 'effect';
import { FetchHttpClient, HttpClient } from 'effect/http';
import { ChildProcess, ChildProcessSpawner } from 'effect/process';
import type { PlatformError } from 'effect/PlatformError';
import { Socket } from 'effect/socket';
import { homedir } from 'node:os';

export const HOME = homedir();
export const PREFIX = `${HOME}/.local/share/backplane`;

const REPLY_TIMEOUT_MS = 30_000;

export class HubError extends Schema.TaggedError<HubError>()('HubError', {
	message: Schema.String
}) {}

const WireDict = Schema.fromJsonString(
	Schema.Struct({ keys: Schema.Array(Schema.String), words: Schema.Array(Schema.String) })
);

const Reply = Schema.Struct({
	t: Schema.Literal('reply'),
	id: Schema.Number,
	ok: Schema.optionalKey(Schema.Boolean),
	error: Schema.optionalKey(Schema.Json)
});

type Reply = typeof Reply.Type;

const replyFromCbor = Schema.decodeUnknownOption(Reply);
const replyFromText = Schema.decodeUnknownOption(Schema.fromJsonString(Reply));
const textDecoder = new TextDecoder();

// The hub answers in Backplane's CBOR subset: map keys from KEYS travel as their index, strings from WORDS as tag 6, other numbers as tag 7 text.
const cborDecoder =
	({ keys, words }: typeof WireDict.Type) =>
	(b: Uint8Array): Schema.Json => {
		let at = 0;

		const arg = (ai: number): number => {
			if (ai < 24) return ai;
			let v = 0;

			for (let i = 0; i < 2 ** (ai - 24); i++) v = v * 256 + (b[at++] ?? 0);

			return v;
		};

		const text = (n: number): string => textDecoder.decode(b.subarray(at, (at += n)));

		const key = (k: Schema.Json): string =>
			Predicate.isNumber(k) ? (keys[k] ?? `#${k}`) : String(k);

		const item = (): Schema.Json => {
			const h = b[at++] ?? 0;
			const major = h >> 5;
			const ai = h & 31;

			if (major === 7)
				return Match.value(ai).pipe(
					Match.when(21, () => true),
					Match.when(20, () => false),
					Match.orElse(() => null)
				);
			const n = arg(ai);

			switch (major) {
				case 0:
					return n;
				case 1:
					return -1 - n;
				case 2:
					at += n;

					return null;
				case 3:
					return text(n);
				case 4:
					return Array.from({ length: n }, item);
				case 5:
					return Object.fromEntries(Array.from({ length: n }, () => [key(item()), item()]));
				default: {
					const v = item();

					if (n === 6 && Predicate.isNumber(v)) return words[v] ?? `#word${v}`;

					if (n === 7 && Predicate.isString(v)) return Number(v);

					return v;
				}
			}
		};

		return item();
	};

export type Hub = {
	exited: Effect.Effect<Option.Option<string>, PlatformError>;
	call(m: string, p: Schema.JsonObject): Effect.Effect<void, HubError>;
};

export type HubOptions = {
	home: string;
	port: number;
	cwd: string;
	env: Record<string, string | undefined>;
	log: string;
};

export const startHub = Effect.fn('startHub')(
	function* (opts: HubOptions) {
		const fs = yield* FileSystem.FileSystem;

		const decode = cborDecoder(
			yield* Schema.decodeEffect(WireDict)(
				yield* fs.readFileString(`${PREFIX}/pcbbench-wire-dict.json`)
			)
		);

		const build = (yield* fs.readFileString(`${PREFIX}/CURRENT`)).trim();

		const proc = yield* (yield* ChildProcessSpawner.ChildProcessSpawner).spawn(
			ChildProcess.make(
				`${PREFIX}/builds/${build}/backplane-hub`,
				[
					'--home',
					opts.home,
					'--port',
					String(opts.port),
					'--host',
					'127.0.0.1',
					'--no-tailscale',
					'--foreground'
				],
				{ cwd: opts.cwd, env: opts.env, stdin: 'ignore' }
			)
		);

		const logging = yield* Effect.forkScoped(
			Stream.run(proc.all, fs.sink(opts.log, { flag: 'a' }))
		);

		// Runs before the spawner's own cleanup, so the hub's shutdown output still reaches the log.
		yield* Effect.addFinalizer(() =>
			Effect.ignore(proc.kill({ forceKillAfter: '15 seconds' })).pipe(
				Effect.andThen(Fiber.join(logging).pipe(Effect.timeout('5 seconds'))),
				Effect.ignore
			)
		);

		const exited = Effect.gen(function* () {
			if (yield* proc.isRunning) return Option.none<string>();

			// exitCode fails when a signal ended the process.
			return Option.some(
				yield* proc.exitCode.pipe(
					Effect.map(String),
					Effect.orElseSucceed(() => 'a signal')
				)
			);
		});

		const client = HttpClient.filterStatusOk(yield* HttpClient.HttpClient);
		const tokenFile = `${opts.home}/token`;

		yield* Effect.gen(function* () {
			const exit = yield* exited;

			if (Option.isSome(exit))
				return yield* new HubError({
					message: `hub exited with ${exit.value}; see ${opts.log}`
				});

			const hello = yield* client.get(`http://127.0.0.1:${opts.port}/hello`).pipe(
				Effect.as(true),
				Effect.orElseSucceed(() => false)
			);

			return hello && (yield* fs.exists(tokenFile));
		}).pipe(
			Effect.repeat({ until: (ready) => ready, schedule: Schedule.spaced('100 millis') }),
			Effect.timeoutOrElse({
				duration: '60 seconds',
				orElse: () =>
					Effect.fail(new HubError({ message: 'hub did not answer /hello within 60 s' }))
			})
		);

		const token = (yield* fs.readFileString(tokenFile)).trim();

		const socket = yield* Socket.makeWebSocket(
			`ws://127.0.0.1:${opts.port}/ws?token=${encodeURIComponent(token)}`
		);

		const { pull } = yield* socket.reader.pipe(
			Effect.mapError((error) => new HubError({ message: `hub websocket: ${error.message}` }))
		);

		const { write } = yield* socket.writer;
		const waiting = new Map<number, Deferred.Deferred<Reply>>();
		let next = 1;

		yield* pull.pipe(
			Effect.flatMap((frames) => {
				const replies = frames.flatMap((frame) =>
					Option.toArray(
						Predicate.isString(frame) ? replyFromText(frame) : replyFromCbor(decode(frame))
					)
				);

				return Effect.forEach(replies, (reply) => {
					const waiter = waiting.get(reply.id);

					return waiter ? Deferred.succeed(waiter, reply) : Effect.void;
				});
			}),
			Effect.forever,
			Effect.ignore,
			Effect.forkScoped
		);

		const call = (m: string, p: Schema.JsonObject) =>
			Effect.suspend(() => {
				const id = next++;

				return Effect.gen(function* () {
					const reply = yield* Deferred.make<Reply>();
					waiting.set(id, reply);

					yield* write(JSON.stringify({ id, m, p })).pipe(
						Effect.mapError((error) => new HubError({ message: `${m}: ${error.message}` }))
					);

					return yield* Deferred.await(reply);
				}).pipe(
					Effect.timeoutOrElse({
						duration: REPLY_TIMEOUT_MS,
						orElse: () =>
							Effect.fail(new HubError({ message: `${m}: no reply in ${REPLY_TIMEOUT_MS} ms` }))
					}),
					Effect.flatMap((reply) =>
						reply.ok === false
							? Effect.fail(
									new HubError({ message: `${m}: ${JSON.stringify(reply.error ?? reply)}` })
								)
							: Effect.void
					),
					Effect.ensuring(Effect.sync(() => waiting.delete(id)))
				);
			});

		return { exited, call } satisfies Hub;
	},
	Effect.provide(Layer.mergeAll(FetchHttpClient.layer, BunSocket.layerWebSocketConstructor))
);
