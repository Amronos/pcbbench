// Installs Backplane's KiCad fork through its own `kicad.install` RPC, then moves it to ~/.local/share/backplane/kicad,
// a folder every hub searches whatever its home, so each run can start from an empty home.
import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Console, Effect, FileSystem, Schedule } from 'effect';
import { HubError, PREFIX, startHub } from './hub.ts';

const program = Effect.gen(function* () {
	const fs = yield* FileSystem.FileSystem;
	const home = yield* fs.makeTempDirectory({ prefix: 'bp-kicad-' });
	const staged = `${home}/kicad`;

	const entries = Effect.gen(function* () {
		return (yield* fs.exists(staged)) ? yield* fs.readDirectory(staged) : [];
	});

	const installed = Effect.gen(function* () {
		const versions = (yield* entries).filter((d) => !d.startsWith('.'));

		return yield* Effect.filter(versions, (d) => fs.exists(`${staged}/${d}/bin/kicad-cli`));
	});

	const busy = Effect.map(entries, (all) => all.some((d) => d.startsWith('.install-')));

	yield* Effect.scoped(
		Effect.gen(function* () {
			const hub = yield* startHub({
				home,
				port: 3899,
				cwd: home,
				env: { ...process.env, BACKPLANE_NO_UPDATE: '1' },
				log: `${home}/hub.log`
			});

			yield* hub.call('kicad.install', { consent: true });

			yield* Effect.gen(function* () {
				return (yield* installed).length > 0 && !(yield* busy);
			}).pipe(
				Effect.repeat({ until: (done) => done, schedule: Schedule.spaced('2 seconds') }),
				Effect.timeoutOrElse({
					duration: '30 minutes',
					orElse: () =>
						Effect.fail(
							new HubError({ message: `KiCad did not install in 30 min; see ${home}/hub.log` })
						)
				})
			);

			const dest = `${PREFIX}/kicad`;
			yield* fs.makeDirectory(dest, { recursive: true });

			for (const version of yield* installed) {
				yield* fs.rename(`${staged}/${version}`, `${dest}/${version}`);
				yield* Console.log(`KiCad ${version} in ${dest}/${version}`);
			}
		})
	);

	yield* fs.remove(home, { recursive: true });
});

program.pipe(Effect.provide(BunServices.layer), BunRuntime.runMain);
