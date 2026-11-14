import type { Footprint } from './board.ts';
import { isSamePart, splitRefs } from './bom.ts';
import type { CheckedRun, Features } from './check.ts';
import {
	isGround,
	isResistor,
	isTwoTerminal,
	onNet,
	otherNet,
	rp2350Pin,
	terminals
} from './netlist.ts';

type Gate = { pass: boolean; reason: string; refs: string[] };

type Netlist = {
	footprints: Footprint[];
	pinNet: (pin: string) => string;
	mpnOf: (ref: string) => string;
	isFitted: (ref: string) => boolean;
};

// Load capacitance in pF, from each crystal's datasheet.
const CRYSTAL_LOAD_PF: [mpn: string, pf: number][] = [['ABM8-272-T3', 10]];

// Hardware design with RP2350 assumes 3 pF of PCB and pin capacitance; its 15 pF caps give 10.5 pF for a 10 pF crystal.
const STRAY_PF = 3;
const LOAD_CAP_TOLERANCE = 0.25;

// Pad numbers from each charger's datasheet; the RGT package pinout is shared across the BQ2407x family.
const CHARGER_PINS: [RegExp, { input: string; system: string; battery: string }][] = [
	[/^BQ2407[2-59]RGT/i, { input: '13', system: '10', battery: '2' }]
];

// Two-pad parts that pass a supply straight through: fuses, ferrites, inductors and diodes.
const SERIES_PART = /^(F|FB|L|D)\d/;

const fail = (reason: string, refs: string[] = []): Gate => ({ pass: false, reason, refs });

const PICOFARADS = new Map([
	['p', 1],
	['n', 1e3],
	['u', 1e6],
	['µ', 1e6]
]);

const parsePicofarads = (value: string) => {
	const [, number, unit = ''] = value.match(/^([\d.]+)\s*([pnuµ])/) ?? [];

	return Number(number) * (PICOFARADS.get(unit) ?? NaN);
};

function checkCrystal({ footprints, pinNet, mpnOf }: Netlist): Gate {
	const [xin, xout] = [pinNet('XIN'), pinNet('XOUT')];

	const crystal = footprints.find(
		(footprint) =>
			/^Y\d/.test(footprint.ref) &&
			[2, 4].includes(terminals(footprint).length) &&
			onNet(footprint, xin)
	);

	if (!crystal) return fail(`No 2- or 4-pad crystal on XIN (${xin})`);

	const outNet =
		terminals(crystal)
			.map((pad) => pad.net)
			.find((net) => net !== xin && !isGround(net)) ?? '';

	const series = footprints.find(
		(footprint) =>
			isResistor(footprint) && onNet(footprint, xout) && otherNet(footprint, xout) === outNet
	);

	if (outNet !== xout && !series)
		return fail(
			`${crystal.ref} goes from XIN to ${outNet || 'nothing'}, not to XOUT (${xout}) or a resistor from it`,
			[crystal.ref]
		);

	const mpn = mpnOf(crystal.ref);
	const loadPf = CRYSTAL_LOAD_PF.find(([part]) => isSamePart(mpn, part))?.[1];

	if (!loadPf)
		return fail(
			`Unknown crystal ${mpn || crystal.value}; add its load capacitance to CRYSTAL_LOAD_PF`,
			[crystal.ref]
		);

	const targetPf = 2 * (loadPf - STRAY_PF);
	const [minPf, maxPf] = [targetPf * (1 - LOAD_CAP_TOLERANCE), targetPf * (1 + LOAD_CAP_TOLERANCE)];

	const sides = [xin, outNet].map((net) => {
		const caps = footprints.filter(
			(footprint) =>
				isTwoTerminal(footprint, 'C') && onNet(footprint, net) && isGround(otherNet(footprint, net))
		);

		return {
			net,
			caps,
			pf: caps.reduce((sum, cap) => sum + parsePicofarads(cap.value), 0)
		};
	});

	const refs = [
		crystal.ref,
		...(series ? [series.ref] : []),
		...sides.flatMap((side) => side.caps.map((cap) => cap.ref))
	];

	const wrong = sides.filter((side) => !(side.pf >= minPf && side.pf <= maxPf));

	const described = sides
		.map((side) =>
			side.caps.length
				? `${side.net}: ${side.caps.map((cap) => `${cap.ref} ${cap.value}`).join(' + ')}`
				: `${side.net}: no cap to GND`
		)
		.join('; ');

	return {
		pass: !wrong.length,
		reason:
			`${crystal.ref} ${mpn} (CL ${loadPf} pF) between XIN and XOUT${series ? ` via ${series.ref} ${series.value}` : ''}; ` +
			`load caps ${described}; needs ${minPf}–${maxPf} pF per side for ${STRAY_PF} pF stray`,
		refs
	};
}

function checkButtons({ footprints, pinNet, isFitted }: Netlist): Gate {
	const switches = footprints.filter(
		(footprint) =>
			/^(SW|S|K|BTN)\d/.test(footprint.ref) && footprint.isPart && isFitted(footprint.ref)
	);

	const resistorsOn = (net: string) =>
		footprints.filter((footprint) => isResistor(footprint) && onNet(footprint, net));

	// At most one resistor in the path, on either side of the switch.
	const switchToGround = (net: string, allowResistor: boolean) =>
		switches
			.filter((button) => onNet(button, net))
			.map((button) => {
				const others = terminals(button)
					.map((pad) => pad.net)
					.filter((other) => other !== net);

				if (others.some(isGround)) return [button.ref];

				const resistor = allowResistor
					? others.flatMap((other) =>
							resistorsOn(other).filter((r) => isGround(otherNet(r, other)))
						)[0]
					: undefined;

				return resistor ? [button.ref, resistor.ref] : null;
			})
			.find(Boolean);

	const pressedToGround = (net: string) =>
		switchToGround(net, true) ??
		resistorsOn(net)
			.map((resistor) => {
				const path = switchToGround(otherNet(resistor, net), false);

				return path ? [resistor.ref, ...path] : null;
			})
			.find(Boolean);

	const results = ['QSPI_SS', 'RUN'].map((pin) => ({
		pin,
		net: pinNet(pin),
		path: pressedToGround(pinNet(pin))
	}));

	return {
		pass: results.every((result) => result.path),
		reason: results
			.map(({ pin, net, path }) =>
				path
					? `${pin} (${net}) → ${path.join(' → ')} → GND`
					: `no fitted switch pulls ${pin} (${net}) to GND`
			)
			.join('; '),
		refs: results.flatMap((result) => result.path ?? [])
	};
}

function checkPowerPath(
	{ footprints, pinNet, mpnOf }: Netlist,
	charger: Footprint | undefined,
	rp2350: Footprint
): Gate {
	if (!charger) return fail('No power-path charger in the BOM');
	const mpn = mpnOf(charger.ref);
	const pins = CHARGER_PINS.find(([pattern]) => pattern.test(mpn))?.[1];

	if (!pins) return fail(`No pin table for charger ${mpn}; add it to CHARGER_PINS`, [charger.ref]);

	const pinOf = (number: string) => charger.pads.find((pad) => pad.number === number)?.net ?? '';
	const [input, system, battery] = [pinOf(pins.input), pinOf(pins.system), pinOf(pins.battery)];

	const passedThrough = (footprint: Footprint, net: string) => {
		const pads = terminals(footprint);

		if (SERIES_PART.test(footprint.ref) && pads.length === 2) return [otherNet(footprint, net)];

		if (/^Q\d/.test(footprint.ref))
			return pads.filter((pad) => !/^G/i.test(pad.pinFunction)).map((pad) => pad.net);

		return [];
	};

	const joined = (start: string) => {
		const nets = new Set([start]);

		for (const net of nets)
			for (const footprint of footprints.filter((footprint) => onNet(footprint, net)))
				for (const next of passedThrough(footprint, net)) if (!isGround(next)) nets.add(next);

		return nets;
	};

	const touches = (footprint: Footprint, nets: Set<string>) =>
		footprint.pads.some((pad) => nets.has(pad.net));

	const inputNets = joined(input);

	const usb = footprints.find(
		(footprint) =>
			/^J\d/.test(footprint.ref) &&
			footprint.pads.some(
				(pad) =>
					(/VBUS/i.test(pad.pinFunction) || /^[AB][49]$/.test(pad.number)) && inputNets.has(pad.net)
			)
	);

	const pinCount = (footprint: Footprint) =>
		new Set(
			terminals(footprint)
				.filter((pad) => /^\d+$/.test(pad.number))
				.map((pad) => pad.number)
		).size;

	const batteryConnector = footprints.find(
		(footprint) =>
			/^J\d/.test(footprint.ref) &&
			[2, 3].includes(pinCount(footprint)) &&
			touches(footprint, joined(battery))
	);

	const rail = pinNet('IOVDD');

	const onRail = footprints.filter(
		(footprint) =>
			/^U\d/.test(footprint.ref) &&
			footprint !== rp2350 &&
			footprint !== charger &&
			onNet(footprint, rail)
	);

	const regulator = onRail.find((footprint) => touches(footprint, joined(system)));

	const findings = [
		usb
			? `${charger.ref} IN (${input}) is on ${usb.ref} VBUS`
			: `${charger.ref} IN (${input}) doesn't reach USB VBUS`,
		batteryConnector
			? `BAT (${battery}) goes to ${batteryConnector.ref}`
			: `BAT (${battery}) reaches no battery connector`,
		regulator
			? `${regulator.ref} ${mpnOf(regulator.ref)} makes ${rail} from OUT (${system})`
			: `nothing on ${rail} (${onRail.map((footprint) => footprint.ref).join(', ') || 'no ICs'}) takes its input from OUT (${system})`
	];

	return {
		pass: !!usb && !!batteryConnector && !!regulator,
		reason: `${charger.ref} ${mpn}: ${findings.join('; ')}`,
		refs: [charger.ref, usb?.ref, batteryConnector?.ref, regulator?.ref].filter(
			(ref) => ref !== undefined
		)
	};
}

export function checkGates(run: CheckedRun, features: Features) {
	const rp2350 = run.rp2350s[0];

	if (!rp2350) {
		const missing = fail('No RP2350 on the board');

		return { crystal: missing, buttons: missing, powerPath: missing };
	}

	const pinNet = (pin: string) => rp2350.pads.find((pad) => rp2350Pin(pad) === pin)?.net ?? '';
	const lineOf = (ref: string) => run.bom.lines.find((line) => splitRefs(line.refs).includes(ref));

	const netlist: Netlist = {
		footprints: run.footprints,
		pinNet,
		mpnOf: (ref) => lineOf(ref)?.mpn ?? '',
		isFitted: (ref) => !!lineOf(ref)?.fitted
	};

	return {
		crystal: checkCrystal(netlist),
		buttons: checkButtons(netlist),
		powerPath: checkPowerPath(
			netlist,
			run.byReference.get(features.chargerWithPowerPath.refs[0] ?? ''),
			rp2350
		)
	};
}
