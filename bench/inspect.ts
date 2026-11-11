import { BunRuntime, BunServices } from '@effect/platform-bun';
import { Effect, FileSystem, Schema } from 'effect';
import { Argument, Command } from 'effect/cli';
import { ChildProcess } from 'effect/process';
import { readRun, updateMetrics } from './board.ts';
import { exec, run } from './command.ts';
import { matchFab } from './fab-match.ts';
import { runIdArgument } from './runs.ts';

const RENDERS = {
	top: ['--side', 'top'],
	bottom: ['--side', 'bottom'],
	iso: ['--rotate', '-40,0,30', '--perspective', '--floor', '--zoom', '0.7']
};

const Violation = Schema.Struct({ severity: Schema.String, type: Schema.String });

type Violation = typeof Violation.Type;

const Drc = Schema.fromJsonString(
	Schema.Struct({
		violations: Schema.Array(Violation),
		unconnected_items: Schema.Array(Schema.Unknown),
		schematic_parity: Schema.Array(Schema.Unknown)
	})
);

const Erc = Schema.fromJsonString(
	Schema.Struct({ sheets: Schema.Array(Schema.Struct({ violations: Schema.Array(Violation) })) })
);

class KicadVersionError extends Schema.TaggedError<KicadVersionError>()('KicadVersionError', {
	message: Schema.String
}) {}

const bySeverity = (violations: ReadonlyArray<Violation>) => ({
	errors: violations.filter((violation) => violation.severity === 'error').length,
	warnings: violations.filter((violation) => violation.severity === 'warning').length
});

// KiCad only warns about copper narrower than the board's own minimum connection width, but the fab has to make that copper.
const DRC_MANUFACTURING_ERRORS = ['connection_width'];

// The footprint differs from its library copy. That's an edit to the footprint, not a design fault.
const DRC_IGNORED = ['lib_footprint_mismatch'];

const classifyDrc = (violations: ReadonlyArray<Violation>) =>
	violations.flatMap((violation) =>
		DRC_IGNORED.includes(violation.type)
			? []
			: [
					DRC_MANUFACTURING_ERRORS.includes(violation.type)
						? { ...violation, severity: 'error' }
						: violation
				]
	);

const countByType = (violations: ReadonlyArray<Violation>) =>
	Object.fromEntries(
		[...Map.groupBy(violations, (violation) => violation.type)].map(([type, group]) => [
			type,
			group.length
		])
	);

const inspect = Effect.fn('inspect')(function* ({
	runId,
	kicadCli
}: {
	readonly runId: string;
	readonly kicadCli: string;
}) {
	const fs = yield* FileSystem.FileSystem;
	const { runDir, info, board, footprints, parts, copperLayers } = yield* readRun(runId);

	// kicad-cli writes a local-settings .kicad_prl next to the board when there is none.
	const localSettings = board.replace(/\.kicad_pcb$/, '.kicad_prl');
	const hadLocalSettings = yield* fs.exists(localSettings);

	const cliVersion = (yield* run(ChildProcess.make`${kicadCli} version --format about`)).match(
		/^Version: ([^,]+)/m
	)?.[1];

	const runVersion = info.versions.kicad.split(' ')[0];

	// Backplane's fork calls itself 10.99.0-unknown-bp.4.
	if (cliVersion?.replace('-unknown-', '-') !== runVersion)
		return yield* new KicadVersionError({
			message: `${kicadCli} is KiCad ${cliVersion}, but the run used ${runVersion}`
		});

	if (!hadLocalSettings)
		yield* Effect.addFinalizer(() => fs.remove(localSettings, { force: true }).pipe(Effect.ignore));

	const work = yield* fs.makeTempDirectoryScoped({ prefix: 'pcbbench-inspect-' });

	// Saved zone fills can be stale; refilling checks the design as KiCad would plot it.
	yield* run(
		ChildProcess.make`${kicadCli} pcb drc --format json --severity-error --severity-warning --schematic-parity --refill-zones -o ${work}/drc.json ${board}`
	);
	const drc = yield* Schema.decodeEffect(Drc)(yield* fs.readFileString(`${work}/drc.json`));
	yield* run(
		ChildProcess.make`${kicadCli} sch erc --format json --severity-error --severity-warning -o ${work}/erc.json ${board.replace(/\.kicad_pcb$/, '.kicad_sch')}`
	);
	const erc = yield* Schema.decodeEffect(Erc)(yield* fs.readFileString(`${work}/erc.json`));

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

	const fab = yield* matchFab(
		kicadCli,
		board,
		`${runDir}/output/${info.fabZip}`,
		expectedLayers,
		work
	);

	// KiCad reports each model it can't load while exporting a mesh, using its own path resolution.
	const glb = yield* exec(
		ChildProcess.make`${kicadCli} pcb export glb --no-dnp -f -o ${work}/board.glb ${board}`
	);

	const unloaded = new Set(
		[...`${glb.stdout}${glb.stderr}`.matchAll(/Could not add 3D model for (\S+?)\.?$/gm)].map(
			([, ref]) => ref
		)
	);

	const missing3dModels = parts
		.filter((part) => !part.hasModel || unloaded.has(part.ref))
		.map((part) => part.ref);

	for (const [name, args] of Object.entries(RENDERS)) {
		yield* run(
			ChildProcess.make`${kicadCli} pcb render --quality high --width 1600 --height 1200 ${args} -o ${runDir}/renders/${name}.png ${board}`
		);
	}

	yield* updateMetrics(runId, {
		drc: {
			...bySeverity(classifyDrc(drc.violations)),
			unconnectedItems: drc.unconnected_items.length,
			schematicParityIssues: drc.schematic_parity.length,
			byType: countByType(drc.violations)
		},
		erc: bySeverity(erc.sheets.flatMap((sheet) => sheet.violations)),
		fab,
		missing3dModels: { count: missing3dModels.length, refs: missing3dModels }
	});
}, Effect.scoped);

Command.make(
	'inspect',
	{
		runId: runIdArgument,
		kicadCli: Argument.String('kicad-cli').pipe(
			Argument.withDescription('kicad-cli of the KiCad version the run used')
		)
	},
	inspect
).pipe(Command.run({ version: '0.0.0' }), Effect.provide(BunServices.layer), BunRuntime.runMain);
