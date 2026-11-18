import {
	BOM_LINE_FIX_COST,
	DRAIN_FULL_UA,
	DRAIN_NONE_UA,
	FEATHER_MM,
	GROUPS,
	ITEMS,
	MAJOR_COST,
	MINOR_COST,
	REVIEW_AREA_POINTS,
	ZERO_SIZE_FACTOR,
	groupPoints,
	type Group,
	type Item
} from '@pcbbench/bench/scoring';
import type { Run } from './runs';

export const GROUP_LABELS: Record<Group, string> = {
	designReview: 'Design review',
	circuitChecks: 'Circuit checks',
	layoutChecks: 'Layout checks',
	orderable: 'Orderable',
	partsData: 'Parts data'
};

export const ITEM_LABELS: Record<Item['name'], { label: string; fraction: string }> = {
	layout: {
		label: 'Layout',
		fraction: `1 minus ${MINOR_COST / REVIEW_AREA_POINTS} per minor and ${MAJOR_COST / REVIEW_AREA_POINTS} per major layout finding, down to 0`
	},
	routing: { label: 'Routing', fraction: 'the same, for routing findings' },
	decoupling: {
		label: 'Decoupling',
		fraction: 'RP2350 power pins with a capacitor within 3.2 mm'
	},
	usbProtection: {
		label: 'USB protection',
		fraction: '0.5 for an ESD part on D+ and D−, plus 0.25 for each line with a series resistor'
	},
	antennaKeepout: {
		label: 'Antenna keepout',
		fraction: '1 when there are keepouts and no copper is in them'
	},
	batteryDrain: {
		label: 'Battery drain',
		fraction: `1 at ${DRAIN_FULL_UA} µA or less drawn by unswitched battery dividers, falling linearly to 0 at ${DRAIN_NONE_UA} µA`
	},
	thermal: {
		label: 'Thermal pads',
		fraction:
			'mean over the exposed pads of their vias over the number needed, 0 for a pad with no plane on another layer'
	},
	grounding: {
		label: 'Grounding',
		fraction: 'USB, QSPI and microSD track length over a ground plane on the next layer'
	},
	silkscreen: { label: 'Silkscreen', fraction: 'texts at least 0.8 mm high' },
	boardSize: {
		label: 'Board size',
		fraction: `1 at the Feather RP2350's ${FEATHER_MM.width} × ${FEATHER_MM.height} mm area or less, falling linearly to 0 at ${ZERO_SIZE_FACTOR} times that area`
	},
	fabNotesWithoutFixes: {
		label: 'Fab notes',
		fraction: '1 when every fab option in the notes can be ordered from PCBWay'
	},
	boardWithoutRework: { label: 'Board', fraction: '1 when the board needs no rework' },
	bomLinesWithoutFixes: {
		label: 'BOM lines',
		fraction: `1 minus ${BOM_LINE_FIX_COST} for each BOM line that needs a fix, down to 0`
	},
	models3d: { label: '3D models', fraction: 'parts with a 3D model' },
	supplierNumbers: {
		label: 'Supplier part numbers',
		fraction: 'BOM lines with a valid number from at least one supplier'
	}
};

export const itemPoints = (name: Item['name']) =>
	ITEMS.filter((item) => item.name === name).reduce((total, item) => total + item.points, 0);

export const itemEarned = (run: Run, name: Item['name']) =>
	itemPoints(name) * run.metrics.score.fractions[name];

// The share of each group's points a run earned, which custom weights rescale. Built from the item
// fractions, because the stored group points are rounded.
export const groupShares = (run: Run) =>
	Object.fromEntries(
		GROUPS.map((group) => [
			group,
			ITEMS.filter((item) => item.group === group).reduce(
				(total, item) => total + itemEarned(run, item.name),
				0
			) / groupPoints(group)
		])
	);

const GATE_LABELS = new Map([
	['crystal', 'Crystal and load capacitors'],
	['buttons', 'BOOTSEL and RUN buttons'],
	['powerPath', 'Charger power path'],
	['fatalFinding', 'Fatal review finding']
]);

const FEATURE_LABELS = new Map([
	['rp2350', 'RP2350'],
	['qspiFlash', 'QSPI flash'],
	['psram', 'PSRAM'],
	['usbC', 'USB-C'],
	['wifiBle', 'Wi-Fi and BLE'],
	['microSd', 'microSD'],
	['qwiic', 'Qwiic'],
	['rgbLed', 'RGB LED'],
	['chargerWithPowerPath', 'Power-path charger'],
	['batteryMonitoring', 'Battery monitoring']
]);

export const gateLabel = (gate: string) => GATE_LABELS.get(gate) ?? gate;

export const featureLabel = (feature: string) => FEATURE_LABELS.get(feature) ?? feature;

// bench/score.ts names a failed gate `missing <feature>` or by its gate name.
export function failedGateLabel(gate: string) {
	const feature = /^missing (.+)$/.exec(gate)?.[1];

	if (feature) return `Missing ${featureLabel(feature)}`;

	return gateLabel(gate);
}
