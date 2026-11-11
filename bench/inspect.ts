import { $ } from 'bun';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { readRun } from './board.ts';
import { matchFab } from './fab-match.ts';

const RENDERS = {
	top: ['--side', 'top'],
	bottom: ['--side', 'bottom'],
	iso: ['--rotate', '-40,0,30', '--perspective', '--floor', '--zoom', '0.7']
};

const [runId, kicadCli] = Bun.argv.slice(2);

if (!runId || !kicadCli)
	throw new Error(
		'Usage: bun bench/inspect.ts <run id> <kicad-cli of the KiCad version the run used>'
	);

const { runDir, info, board, footprints, parts, copperLayers, updateMetrics } =
	await readRun(runId);

// kicad-cli writes a local-settings .kicad_prl next to the board when there is none.
const localSettings = board.replace(/\.kicad_pcb$/, '.kicad_prl');
const hadLocalSettings = await Bun.file(localSettings).exists();

const cliVersion = (await $`${kicadCli} version --format about`.text()).match(
	/^Version: ([^,]+)/m
)?.[1];

const runVersion = info.versions.kicad.split(' ')[0];

// Backplane's fork calls itself 10.99.0-unknown-bp.4.
if (cliVersion?.replace('-unknown-', '-') !== runVersion)
	throw new Error(`${kicadCli} is KiCad ${cliVersion}, but the run used ${runVersion}`);

const work = await mkdtemp(join(tmpdir(), 'pcbbench-inspect-'));

type Violation = { severity: string; type: string };

const bySeverity = (violations: Violation[]) => ({
	errors: violations.filter((violation) => violation.severity === 'error').length,
	warnings: violations.filter((violation) => violation.severity === 'warning').length
});

// KiCad only warns about copper narrower than the board's own minimum connection width, but the fab has to make that copper.
const DRC_MANUFACTURING_ERRORS = ['connection_width'];

// The footprint differs from its library copy. That's an edit to the footprint, not a design fault.
const DRC_IGNORED = ['lib_footprint_mismatch'];

const classifyDrc = (violations: Violation[]) =>
	violations
		.filter((violation) => !DRC_IGNORED.includes(violation.type))
		.map((violation) =>
			DRC_MANUFACTURING_ERRORS.includes(violation.type)
				? { ...violation, severity: 'error' }
				: violation
		);

const countByType = (violations: Violation[]) =>
	Object.fromEntries(
		[...Map.groupBy(violations, (violation) => violation.type)].map(([type, group]) => [
			type,
			group.length
		])
	);

try {
	// Saved zone fills can be stale; refilling checks the design as KiCad would plot it.
	await $`${kicadCli} pcb drc --format json --severity-error --severity-warning --schematic-parity --refill-zones -o ${work}/drc.json ${board}`.quiet();
	const drc = await Bun.file(`${work}/drc.json`).json();
	await $`${kicadCli} sch erc --format json --severity-error --severity-warning -o ${work}/erc.json ${board.replace(/\.kicad_pcb$/, '.kicad_sch')}`.quiet();
	const erc = await Bun.file(`${work}/erc.json`).json();

	const smdSides = new Set(parts.filter((part) => part.smd).map((part) => part.side));

	const expectedLayers = [
		...copperLayers,
		'Edge.Cuts',
		'F.Mask',
		'B.Mask',
		'F.Silkscreen',
		...(smdSides.has('top') ? ['F.Paste'] : []),
		...(smdSides.has('bottom') ? ['B.Paste'] : []),
		'PTH',
		...(footprints.some((footprint) => footprint.pads.some((pad) => pad.type === 'np_thru_hole'))
			? ['NPTH']
			: [])
	];

	const fab = await matchFab(
		kicadCli,
		board,
		`${runDir}/output/${info.fabZip}`,
		expectedLayers,
		work
	);

	// KiCad reports each model it can't load while exporting a mesh, using its own path resolution.
	const glb = await $`${kicadCli} pcb export glb --no-dnp -f -o ${work}/board.glb ${board}`
		.quiet()
		.nothrow();

	const unloaded = new Set(
		[...`${glb.stdout}${glb.stderr}`.matchAll(/Could not add 3D model for (\S+?)\.?$/gm)].map(
			([, ref]) => ref
		)
	);

	const missing3dModels = parts
		.filter((part) => !part.hasModel || unloaded.has(part.ref))
		.map((part) => part.ref);

	for (const [name, args] of Object.entries(RENDERS)) {
		await $`${kicadCli} pcb render --quality high --width 1600 --height 1200 ${args} -o ${runDir}/renders/${name}.png ${board}`.quiet();
	}

	await updateMetrics({
		drc: {
			...bySeverity(classifyDrc(drc.violations)),
			unconnectedItems: drc.unconnected_items.length,
			schematicParityIssues: drc.schematic_parity.length,
			byType: countByType(drc.violations)
		},
		erc: bySeverity(erc.sheets.flatMap((sheet: { violations: Violation[] }) => sheet.violations)),
		fab,
		missing3dModels: { count: missing3dModels.length, refs: missing3dModels }
	});
} finally {
	await rm(work, { recursive: true, force: true });

	if (!hadLocalSettings) await rm(localSettings, { force: true });
}
