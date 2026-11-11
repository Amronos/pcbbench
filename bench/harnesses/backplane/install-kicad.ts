// Installs Backplane's KiCad fork through its own `kicad.install` RPC, then moves it to ~/.local/share/backplane/kicad,
// a folder every hub searches whatever its home, so each run can start from an empty home.
import { existsSync, mkdirSync, mkdtempSync, readdirSync, renameSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { PREFIX, startHub, stopHub } from './hub.ts';

const home = mkdtempSync(join(tmpdir(), 'bp-kicad-'));
const staged = join(home, 'kicad');
const hub = await startHub({
	home,
	port: 3899,
	cwd: home,
	env: { ...process.env, BACKPLANE_NO_UPDATE: '1' },
	log: join(home, 'hub.log')
});
try {
	await hub.rpc.call('kicad.install', { consent: true });
	const deadline = Date.now() + 30 * 60_000;
	const installed = (): string[] =>
		existsSync(staged)
			? readdirSync(staged).filter(
					(d) => !d.startsWith('.') && existsSync(join(staged, d, 'bin/kicad-cli'))
				)
			: [];
	const busy = (): boolean =>
		existsSync(staged) && readdirSync(staged).some((d) => d.startsWith('.install-'));
	while (installed().length === 0 || busy()) {
		if (Date.now() > deadline)
			throw new Error(`KiCad did not install in 30 min; see ${home}/hub.log`);
		await Bun.sleep(2000);
	}
	const dest = join(PREFIX, 'kicad');
	mkdirSync(dest, { recursive: true });
	for (const version of installed()) {
		renameSync(join(staged, version), join(dest, version));
		console.log(`KiCad ${version} in ${join(dest, version)}`);
	}
} finally {
	await stopHub(hub);
}
rmSync(home, { recursive: true, force: true });
