import { cp, mkdir, readdir, rm, stat } from 'node:fs/promises';
import { basename, dirname, join } from 'node:path';

// Names that tell a judge which harness or model made a board.
export const IDENTIFYING =
	/sprocket|backplane|codex|claude|openai|anthropic|chatgpt|\bgpt\b|gpt-\d|opus|fable|texttocad|text-to-cad|\/Users\/|\/home\//i;
const KICAD_FILE = /\.(kicad_sch|kicad_pro|kicad_dru)$|^(fp|sym)-lib-table$/;
const TEXT_FILE = /\.(kicad_\w+|csv)$|-lib-table$/;

const neutralName = (match: string) =>
	match === match.toUpperCase() ? 'KESTREL' : match[0] === 'S' ? 'Kestrel' : 'kestrel';

// Copies a run's KiCad project, BOM and renders into `dir` as board.*, without the agent's notes, scripts or fab files.
export async function buildPackage(runId: string, dir: string) {
	const runDir = `${import.meta.dir}/../../runs/${runId}`;
	const info = await Bun.file(`${runDir}/info.json`).json();
	const projectDir = dirname(`${runDir}/output/${info.board}`);
	const name = basename(info.board, '.kicad_pcb');
	await rm(dir, { recursive: true, force: true });
	await mkdir(dir, { recursive: true });

	const projectFiles = [
		basename(info.board),
		...(await readdir(projectDir)).filter((file) => KICAD_FILE.test(file))
	];
	const texts = await Promise.all(
		projectFiles.map((file) => Bun.file(join(projectDir, file)).text())
	);
	const localPaths = new Set(
		texts.flatMap((text) =>
			[...text.matchAll(/\$\{KIPRJMOD\}\/([^"\n)]+)/g)].map(([, path]) => path!.trim())
		)
	);
	for (const path of localPaths) {
		if (await stat(join(projectDir, path)).catch(() => null))
			await cp(join(projectDir, path), join(dir, path), { recursive: true });
	}
	for (const [index, file] of projectFiles.entries()) {
		await Bun.write(
			join(dir, file.startsWith(`${name}.`) ? `board${file.slice(name.length)}` : file),
			texts[index]!
		);
	}
	await cp(`${runDir}/output/${info.bom}`, join(dir, 'bom.csv'));
	await cp(`${runDir}/renders`, join(dir, 'renders'), { recursive: true });

	const leaks = [];
	for (const file of await Array.fromAsync(new Bun.Glob('**/*').scan({ cwd: dir }))) {
		if (IDENTIFYING.test(file)) leaks.push(file);
		if (!TEXT_FILE.test(file)) continue;
		const text = (await Bun.file(join(dir, file)).text())
			.replaceAll(`${name}.kicad_`, 'board.kicad_')
			.replaceAll(`(project "${name}"`, '(project "board"')
			.replace(/sprocket/gi, neutralName);
		await Bun.write(join(dir, file), text);
		const leak = text.match(new RegExp(`.{0,40}(${IDENTIFYING.source}).{0,40}`, 'i'));
		if (leak) leaks.push(`${file}: ${leak[0]}`);
	}
	if (leaks.length)
		throw new Error(`${runId}'s package still names its harness or model:\n${leaks.join('\n')}`);
}
