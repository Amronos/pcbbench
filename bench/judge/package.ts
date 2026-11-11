import { Effect, FileSystem, Path, Schema } from 'effect';
import { readRun } from '../board.ts';

// Names that tell a judge which harness or model made a board.
export const IDENTIFYING =
	/sprocket|backplane|codex|claude|openai|anthropic|chatgpt|\bgpt\b|gpt-\d|opus|fable|texttocad|text-to-cad|\/Users\/|\/home\//i;

const KICAD_FILE = /\.(kicad_sch|kicad_pro|kicad_dru)$|^(fp|sym)-lib-table$/;
const TEXT_FILE = /\.(kicad_\w+|csv)$|-lib-table$/;

const neutralName = (match: string) =>
	match === match.toUpperCase() ? 'KESTREL' : match[0] === 'S' ? 'Kestrel' : 'kestrel';

class PackageLeakError extends Schema.TaggedError<PackageLeakError>()('PackageLeakError', {
	message: Schema.String
}) {}

// Copies a run's KiCad project, BOM and renders into `dir` as board.*, without the agent's notes, scripts or fab files.
export const buildPackage = Effect.fn('buildPackage')(function* (runId: string, dir: string) {
	const fs = yield* FileSystem.FileSystem;
	const { join, dirname, basename } = yield* Path.Path;
	const { runDir, info, board } = yield* readRun(runId);
	const projectDir = dirname(board);
	const name = basename(info.board, '.kicad_pcb');
	yield* fs.remove(dir, { recursive: true, force: true });
	yield* fs.makeDirectory(dir, { recursive: true });

	const projectFiles = [
		basename(info.board),
		...(yield* fs.readDirectory(projectDir)).filter((file) => KICAD_FILE.test(file))
	];

	const texts = yield* Effect.forEach(
		projectFiles,
		(file) => fs.readFileString(join(projectDir, file)),
		{ concurrency: 'unbounded' }
	);

	const localPaths = new Set(
		texts.flatMap((text) =>
			[...text.matchAll(/\$\{KIPRJMOD\}\/([^"\n)]+)/g)].map(([, path]) => path!.trim())
		)
	);

	for (const path of localPaths) {
		if (yield* fs.exists(join(projectDir, path)))
			yield* fs.copy(join(projectDir, path), join(dir, path), { overwrite: true });
	}

	for (const [index, file] of projectFiles.entries()) {
		yield* fs.writeFileString(
			join(dir, file.startsWith(`${name}.`) ? `board${file.slice(name.length)}` : file),
			texts[index]!
		);
	}

	yield* fs.copyFile(`${runDir}/output/${info.bom}`, join(dir, 'bom.csv'));
	yield* fs.copy(`${runDir}/renders`, join(dir, 'renders'), { overwrite: true });

	const leaks = [];

	for (const file of yield* fs.glob('**/*', { root: dir })) {
		if ((yield* fs.stat(join(dir, file))).type !== 'File') continue;

		if (IDENTIFYING.test(file)) leaks.push(file);

		if (!TEXT_FILE.test(file)) continue;

		const text = (yield* fs.readFileString(join(dir, file)))
			.replaceAll(`${name}.kicad_`, 'board.kicad_')
			.replaceAll(`(project "${name}"`, '(project "board"')
			.replace(/sprocket/gi, neutralName);

		yield* fs.writeFileString(join(dir, file), text);
		const leak = text.match(new RegExp(`.{0,40}(${IDENTIFYING.source}).{0,40}`, 'i'));

		if (leak) leaks.push(`${file}: ${leak[0]}`);
	}

	if (leaks.length)
		return yield* new PackageLeakError({
			message: `${runId}'s package still names its harness or model:\n${leaks.join('\n')}`
		});
});
