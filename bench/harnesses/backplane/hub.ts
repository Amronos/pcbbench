import { existsSync, readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

export const HOME = homedir();
export const PREFIX = join(HOME, '.local/share/backplane');
const WIRE_DICT = join(PREFIX, 'pcbbench-wire-dict.json');

export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
type Obj = { [key: string]: Json };

export const isObj = (v: Json | undefined): v is Obj =>
	typeof v === 'object' && v !== null && !Array.isArray(v);
export const str = (v: Json | undefined): string => (typeof v === 'string' ? v : '');

function hubBinary(): string {
	const build = readFileSync(join(PREFIX, 'CURRENT'), 'utf8').trim();
	return join(PREFIX, 'builds', build, 'backplane-hub');
}

// The hub answers in Backplane's CBOR subset: map keys from KEYS travel as their index, strings from WORDS as tag 6, other numbers as tag 7 text.
function cborDecoder(): (bytes: Uint8Array) => Json {
	const dict: unknown = JSON.parse(readFileSync(WIRE_DICT, 'utf8'));
	const list = (k: string): string[] => {
		const v: unknown = typeof dict === 'object' && dict !== null ? Reflect.get(dict, k) : undefined;
		return Array.isArray(v) ? v.map(String) : [];
	};
	const keys = list('keys');
	const words = list('words');
	return (b) => {
		let at = 0;
		const arg = (ai: number): number => {
			if (ai < 24) return ai;
			const n = ai === 24 ? 1 : ai === 25 ? 2 : ai === 26 ? 4 : 8;
			let v = 0;
			for (let i = 0; i < n; i++) v = v * 256 + (b[at++] ?? 0);
			return v;
		};
		const text = (n: number): string => new TextDecoder().decode(b.subarray(at, (at += n)));
		const item = (): Json => {
			const h = b[at++] ?? 0;
			const major = h >> 5;
			const ai = h & 31;
			if (major === 7) return ai === 21 ? true : ai === 20 ? false : null;
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
				case 5: {
					const o: Obj = {};
					for (let i = 0; i < n; i++) {
						const k = item();
						o[typeof k === 'number' ? (keys[k] ?? `#${k}`) : String(k)] = item();
					}
					return o;
				}
				default: {
					const v = item();
					if (n === 6 && typeof v === 'number') return words[v] ?? `#word${v}`;
					if (n === 7 && typeof v === 'string') return Number(v);
					return v;
				}
			}
		};
		return item();
	};
}

export type Hub = { proc: Bun.Subprocess; rpc: Rpc };

export async function startHub(opts: {
	home: string;
	port: number;
	cwd: string;
	env: Record<string, string>;
	log: string;
}): Promise<Hub> {
	const out = Bun.file(opts.log);
	const proc = Bun.spawn(
		[
			hubBinary(),
			'--home',
			opts.home,
			'--port',
			String(opts.port),
			'--host',
			'127.0.0.1',
			'--no-tailscale',
			'--foreground'
		],
		{ cwd: opts.cwd, env: opts.env, stdin: 'ignore', stdout: out, stderr: out }
	);
	const url = `http://127.0.0.1:${opts.port}`;
	for (let i = 0; ; i++) {
		if (proc.exitCode !== null)
			throw new Error(`hub exited with ${proc.exitCode}; see ${opts.log}`);
		if (i > 600) throw new Error('hub did not answer /hello within 60 s');
		const ok = await fetch(`${url}/hello`).then(
			(r) => r.ok,
			() => false
		);
		if (ok && existsSync(join(opts.home, 'token'))) break;
		await Bun.sleep(100);
	}
	const token = readFileSync(join(opts.home, 'token'), 'utf8').trim();
	return {
		proc,
		rpc: await Rpc.connect(`ws://127.0.0.1:${opts.port}/ws?token=${encodeURIComponent(token)}`)
	};
}

export async function stopHub(hub: Hub): Promise<void> {
	hub.rpc.close();
	hub.proc.kill('SIGTERM');
	const exited = await Promise.race([
		hub.proc.exited.then(() => true),
		Bun.sleep(15_000).then(() => false)
	]);
	if (!exited) hub.proc.kill('SIGKILL');
}

export class Rpc {
	private next = 1;
	private waiting = new Map<number, (reply: Obj) => void>();

	private constructor(private ws: WebSocket) {
		const decode = cborDecoder();
		ws.binaryType = 'arraybuffer';
		ws.addEventListener('message', (e) => {
			const data: unknown = e.data;
			const msg =
				data instanceof ArrayBuffer
					? decode(new Uint8Array(data))
					: typeof data === 'string'
						? JSON.parse(data)
						: null;
			if (!isObj(msg) || msg.t !== 'reply' || typeof msg.id !== 'number') return;
			this.waiting.get(msg.id)?.(msg);
			this.waiting.delete(msg.id);
		});
	}

	static async connect(url: string): Promise<Rpc> {
		const ws = new WebSocket(url);
		await new Promise((resolve, reject) => {
			ws.addEventListener('open', resolve, { once: true });
			ws.addEventListener('error', reject, { once: true });
		});
		return new Rpc(ws);
	}

	call(m: string, p: Obj, timeoutMs = 30_000): Promise<Obj> {
		const id = this.next++;
		return new Promise((resolve, reject) => {
			const timer = setTimeout(() => {
				this.waiting.delete(id);
				reject(new Error(`${m}: no reply in ${timeoutMs} ms`));
			}, timeoutMs);
			this.waiting.set(id, (reply) => {
				clearTimeout(timer);
				if (reply.ok === false) reject(new Error(`${m}: ${JSON.stringify(reply.error ?? reply)}`));
				else resolve(reply);
			});
			this.ws.send(JSON.stringify({ id, m, p }));
		});
	}

	close(): void {
		this.ws.close();
	}
}
