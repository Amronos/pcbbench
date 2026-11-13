import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { MODELS as MODEL_IDS, RUNS } from '@pcbbench/bench/runs';
import { GROUPS, ITEMS } from '@pcbbench/bench/scoring';
import type { ImageMetadata } from 'astro';
import { z } from 'astro/zod';
import type { Box, RenderInfo, View } from '../../scripts/renders';
import renderInfo from '../generated/renders.json';
import { HARNESSES, MACHINES, MODELS } from './catalog';
import { renderMarkdown } from './markdown';
import { TASKS } from './tasks';

// The build bundles this module elsewhere, so paths start from the site folder it runs in.
const REPO_ROOT = new URL('../', pathToFileURL(`${process.cwd()}/`));

const REPO = 'Amronos/pcbbench';

export const GITHUB = `https://github.com/${REPO}`;

const Info = z.object({
	reasoning: z.string(),
	versions: z.record(z.string(), z.string()),
	board: z.string(),
	bom: z.string(),
	placement: z.string(),
	fabZip: z.string()
});

const Refs = z.object({ refs: z.string(), mpn: z.string().nullable() });

const Findings = z.object({ minor: z.number(), major: z.number() });

const GroundedNets = z.object({
	nets: z.array(z.string()),
	mm: z.number(),
	groundedMm: z.number()
});

const Keepout = z.object({
	owner: z.string(),
	name: z.string(),
	layers: z.array(z.string()),
	copperInside: z.object({
		tracks: z.number(),
		vias: z.number(),
		zoneFills: z.array(z.string()),
		pads: z.array(z.string())
	})
});

const BoardCost = z.object({
	pcbUsd: z.number(),
	assemblyUsd: z.number(),
	componentsUsd: z.number(),
	totalUsd: z.number()
});

const Metrics = z.object({
	finishedAt: z.string(),
	minutes: z.number(),
	tokens: z.object({
		input: z.number(),
		cacheRead: z.number(),
		cacheWrite: z.number(),
		output: z.number()
	}),
	costUsd: z.number(),
	boardCost: z.object({
		afterFixes: z.boolean(),
		oneBoard: BoardCost,
		fiveBoards: BoardCost.extend({ perBoardUsd: z.number() })
	}),
	fixes: z.array(
		z.object({
			area: z.enum(['bom', 'fabSpec', 'pcb']),
			problem: z.string(),
			fix: z.string(),
			refs: z.string().optional()
		})
	),
	boardSizeMm: z.object({ width: z.number(), height: z.number() }),
	missing3dModels: z.object({ count: z.number(), refs: z.array(z.string()) }),
	bom: z.object({ lines: z.number() }),
	parts: z.object({
		inStockPercent: z.number(),
		notStocked: z.array(Refs.extend({ needed: z.number() })),
		discontinued: z.array(Refs.extend({ discontinuedAt: z.array(z.string()) }))
	}),
	drc: z.object({
		errors: z.number(),
		warnings: z.number(),
		unconnectedItems: z.number(),
		byType: z.record(z.string(), z.number())
	}),
	erc: z.object({ errors: z.number(), warnings: z.number() }),
	needsFixes: z.object({
		fabNotes: z.array(z.string()),
		board: z.array(z.string()),
		assembly: z.array(z.string()),
		bomLines: z.object({ total: z.number(), needingFixes: z.array(z.string()) })
	}),
	features: z.record(z.string(), z.object({ status: z.string(), refs: z.array(z.string()) })),
	gates: z.record(
		z.string(),
		z.object({ pass: z.boolean(), reason: z.string(), refs: z.array(z.string()) })
	),
	layout: z.object({
		thermal: z.object({
			fraction: z.number(),
			pads: z.array(
				z.object({
					ref: z.string(),
					net: z.string(),
					vias: z.number(),
					minVias: z.number(),
					planeOnOtherLayer: z.boolean(),
					share: z.number()
				})
			)
		}),
		grounding: z.object({
			fraction: z.number(),
			usb: GroundedNets,
			qspi: GroundedNets,
			microSd: GroundedNets
		}),
		silkscreen: z.object({
			fraction: z.number(),
			minTextHeightMm: z.number(),
			texts: z.number(),
			textsBelowMin: z.number(),
			smallestTextMm: z.number()
		})
	}),
	design: z.object({
		decoupling: z.object({
			maxMm: z.number(),
			pinsWithin: z.number(),
			powerPins: z.number(),
			pins: z.array(
				z.object({
					pin: z.string(),
					pad: z.string(),
					net: z.string(),
					capacitor: z.string().nullable(),
					mm: z.number().nullable()
				})
			)
		}),
		battery: z.object({
			fuelGauges: z.array(z.string()),
			dividers: z.array(
				z.object({
					top: z.string(),
					bottom: z.string(),
					topOhms: z.number(),
					bottomOhms: z.number(),
					bufferedBy: z.string().nullable(),
					microampsAtFullCharge: z.number(),
					switchedBy: z.string().nullable()
				})
			)
		}),
		usb: z.object({
			dPlusNets: z.array(z.string()),
			dMinusNets: z.array(z.string()),
			dPlusMm: z.number(),
			dMinusMm: z.number(),
			mismatchMm: z.number(),
			vias: z.number(),
			pair: z.object({
				layer: z.string(),
				widthMm: z.number(),
				gapMm: z.number(),
				lengthMm: z.number()
			}),
			differentialOhms: z.number().nullable(),
			esd: z.array(z.string())
		}),
		antennaKeepout: z.object({ module: z.string(), keepouts: z.array(Keepout) })
	}),
	review: z.object({
		judge: z.enum(MODEL_IDS),
		findings: z.object({ layout: Findings, routing: Findings, fatal: z.number() })
	}),
	suppliers: z.object({
		lines: z.number(),
		linesWithValidNumber: z.number(),
		validPercent: z.record(z.string(), z.number())
	}),
	score: z.object({
		total: z.number(),
		groups: z.record(z.enum(GROUPS), z.number()),
		fractions: z.record(z.enum(ITEMS.map((item) => item.name)), z.number()),
		failedGates: z.array(z.string())
	})
});

const ReviewFindings = z.array(
	z.object({
		area: z.enum(['layout', 'routing', 'other']),
		severity: z.enum(['minor', 'major', 'fatal']),
		refs: z.array(z.string()),
		nets: z.array(z.string()),
		issue: z.string(),
		evidence: z.string()
	})
);

export type ScaledRender = {
	image: ImageMetadata;
	// Where the board outline sits in the image, as fractions of the image size.
	board: Box;
	pxPerMm: number;
};

const renderImages = import.meta.glob<{ default: ImageMetadata }>('../generated/renders/*.png', {
	eager: true
});

const renderEntries: Record<string, Record<View, RenderInfo>> = renderInfo;

const readText = (path: string) => readFile(new URL(path, REPO_ROOT), 'utf8');

const readJson = async (path: string) => JSON.parse(await readText(path));

const renderImage = (runId: string, view: View) =>
	renderImages[`../generated/renders/${runId}-${view}.png`].default;

function scaledRender(
	runId: string,
	view: 'top' | 'bottom',
	boardMm: z.infer<typeof Metrics>['boardSizeMm']
): ScaledRender {
	const entry = renderEntries[runId][view];

	if (!entry.board) throw new Error(`${runId} has no board measured in its ${view} render`);

	const { x, y, width, height } = entry.board;

	return {
		image: renderImage(runId, view),
		board: {
			x: x / entry.width,
			y: y / entry.height,
			width: width / entry.width,
			height: height / entry.height
		},
		pxPerMm: (width / boardMm.width + height / boardMm.height) / 2
	};
}

const outputUrl = (runId: string, path: string) =>
	`${GITHUB}/blob/main/runs/${runId}/output/${path}`;

const textOnly = { link: () => null, image: () => null };

export const textOnlyMarkdown = (markdown: string) => renderMarkdown(markdown, textOnly);

// A judge's notes are its final message, then one `## Subagent: <task>` section per subagent.
function judgeNotes(markdown: string) {
	const sections = markdown.split(/^## /m).slice(1);
	const final = sections.find((section) => section.startsWith('Final message'));

	return {
		final: textOnlyMarkdown(final?.replace(/^Final message\n/, '') ?? ''),
		subagents: sections
			.filter((section) => section.startsWith('Subagent: '))
			.map((section) => {
				const [heading, ...body] = section.split('\n');

				return {
					task: heading.replace(/^Subagent: /, ''),
					report: textOnlyMarkdown(body.join('\n'))
				};
			})
	};
}

async function loadRun(run: (typeof RUNS)[number]) {
	const dir = `runs/${run.id}`;
	const info = Info.parse(await readJson(`${dir}/info.json`));
	const metrics = Metrics.parse(await readJson(`${dir}/metrics.json`));
	const { judge } = metrics.review;
	const harness = HARNESSES[run.harness];
	const readme = await readText(`${dir}/output/README.md`);

	return {
		id: run.id,
		// Every run so far is the one task. When the bench tags runs with a task, read it here.
		task: TASKS[0].id,
		model: { id: run.model, ...MODELS[run.model] },
		harness: { id: run.harness, ...harness, about: harness.about(run.model) },
		machine: MACHINES[run.machine],
		reasoning: info.reasoning,
		versions: info.versions,
		files: {
			output: `${GITHUB}/tree/main/runs/${run.id}/output`,
			board: outputUrl(run.id, info.board),
			bom: outputUrl(run.id, info.bom),
			placement: outputUrl(run.id, info.placement),
			fabZip: outputUrl(run.id, info.fabZip),
			metrics: `${GITHUB}/blob/main/${dir}/metrics.json`
		},
		metrics,
		totalTokens: Object.values(metrics.tokens).reduce((total, count) => total + count, 0),
		renders: {
			top: scaledRender(run.id, 'top', metrics.boardSizeMm),
			bottom: scaledRender(run.id, 'bottom', metrics.boardSizeMm),
			iso: renderImage(run.id, 'iso')
		},
		review: {
			judge,
			findings: ReviewFindings.parse(await readJson(`${dir}/review/${judge}.json`)),
			notes: judgeNotes(await readText(`${dir}/review/${judge}.md`))
		},
		readme: renderMarkdown(readme, {
			link: (path) => outputUrl(run.id, path),
			image: (path) =>
				`https://raw.githubusercontent.com/${REPO}/main/runs/${run.id}/output/${path}`
		})
	};
}

export type Run = Awaited<ReturnType<typeof loadRun>> & { rank: number };

// Ranked within their task.
export const runs: Run[] = (await Promise.all(RUNS.map(loadRun)))
	.toSorted((a, b) => b.metrics.score.total - a.metrics.score.total)
	.map((run, _, all) => ({
		...run,
		rank: all.filter((other) => other.task === run.task).indexOf(run) + 1
	}));

export const tasks = await Promise.all(
	TASKS.map(async (task) => ({
		...task,
		prompt: await readText(task.prompt),
		runs: runs.filter((run) => run.task === task.id)
	}))
);

export type Task = (typeof tasks)[number];
