// Each item scores its points times a fraction from 0 to 1.
export const ITEMS = [
	{ group: 'designReview', name: 'layout', points: 10 },
	{ group: 'designReview', name: 'routing', points: 10 },
	{ group: 'circuitChecks', name: 'decoupling', points: 5 },
	{ group: 'circuitChecks', name: 'usbProtection', points: 5 },
	{ group: 'circuitChecks', name: 'antennaKeepout', points: 5 },
	{ group: 'circuitChecks', name: 'batteryDrain', points: 5 },
	{ group: 'layoutChecks', name: 'thermal', points: 10 },
	{ group: 'layoutChecks', name: 'grounding', points: 10 },
	{ group: 'layoutChecks', name: 'silkscreen', points: 5 },
	{ group: 'layoutChecks', name: 'boardSize', points: 5 },
	{ group: 'orderable', name: 'fabNotesWithoutFixes', points: 5 },
	{ group: 'orderable', name: 'boardWithoutRework', points: 5 },
	{ group: 'orderable', name: 'bomLinesWithoutFixes', points: 10 },
	{ group: 'partsData', name: 'models3d', points: 5 },
	{ group: 'partsData', name: 'supplierNumbers', points: 5 }
] as const;

export type Item = {
	group: (typeof ITEMS)[number]['group'];
	name: (typeof ITEMS)[number]['name'];
	points: number;
};

export type Group = Item['group'];

export const GROUPS: ReadonlyArray<Group> = [...new Set(ITEMS.map((item) => item.group))];

export const groupPoints = (group: Group) =>
	ITEMS.filter((item) => item.group === group).reduce((total, item) => total + item.points, 0);

export const GATE_PENALTY = 20;

// A review area starts at REVIEW_AREA_POINTS and loses these points per finding.
export const REVIEW_AREA_POINTS = 10;
export const MINOR_COST = 1;
export const MAJOR_COST = 2;

// Battery current drawn by unswitched monitor dividers: full points at or below the first, none at the second.
export const DRAIN_FULL_UA = 5;
export const DRAIN_NONE_UA = 25;

// Adafruit's Feather RP2350 fits all of the brief but Wi-Fi and microSD. Board size scores full
// points at its area, falling to none at ZERO_SIZE_FACTOR times it.
export const FEATHER_MM = { width: 50.8, height: 22.8 };
export const ZERO_SIZE_FACTOR = 5;

// Each BOM line needing a fix costs this share of the BOM lines item, whatever the BOM's size.
export const BOM_LINE_FIX_COST = 0.2;
