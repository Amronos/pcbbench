import type { Footprint } from './board.ts';

export const isGround = (net: string) => /GND/i.test(net);

export const onNet = (footprint: Footprint, net: string) =>
	footprint.pads.some((pad) => pad.net === net);

// RP2350A (QFN-60) pins by pad number, from the RP2350 datasheet, for footprints whose pads don't name their pin functions.
const RP2350A_PINS = new Map(
	Object.entries({
		1: 'IOVDD',
		6: 'DVDD',
		11: 'IOVDD',
		20: 'IOVDD',
		21: 'XIN',
		22: 'XOUT',
		23: 'DVDD',
		26: 'RUN',
		30: 'IOVDD',
		38: 'IOVDD',
		39: 'DVDD',
		40: 'GPIO26/ADC0',
		41: 'GPIO27/ADC1',
		42: 'GPIO28/ADC2',
		43: 'GPIO29/ADC3',
		44: 'ADC_AVDD',
		45: 'IOVDD',
		46: 'VREG_AVDD',
		49: 'VREG_VIN',
		51: 'USB_DM',
		52: 'USB_DP',
		53: 'USB_OTP_VDD',
		54: 'QSPI_IOVDD',
		55: 'QSPI_SD3',
		56: 'QSPI_SCLK',
		57: 'QSPI_SD0',
		58: 'QSPI_SD2',
		59: 'QSPI_SD1',
		60: 'QSPI_SS'
	})
);

// KiCad writes active-low pin names with an overbar, as in ~{QSPI_SS}_60 or QSPI_~{SS}_60.
export const rp2350Pin = (pad: Footprint['pads'][number]) =>
	pad.pinFunction.replace(/_\d+$/, '').replace(/~\{|\}/g, '') || RP2350A_PINS.get(pad.number) || '';

// Copper pads; some footprints add unnumbered paste-only pads.
export const terminals = (footprint: Footprint) => footprint.pads.filter((pad) => pad.number);

export const isTwoTerminal = (footprint: Footprint, prefix: 'R' | 'C') =>
	new RegExp(`^${prefix}\\d`).test(footprint.ref) && terminals(footprint).length === 2;

export const isResistor = (footprint: Footprint) => isTwoTerminal(footprint, 'R');

export const otherNet = (footprint: Footprint, net: string) =>
	terminals(footprint).find((pad) => pad.net !== net)?.net ?? '';
