export type BomLine = { refs: string; qty: number; mpn: string; fitted: boolean; row: string[] };

export const parseCsv = (text: string) =>
	text
		.replace(/^\uFEFF/, '')
		.split(/\r?\n/)
		.filter((row) => row.trim())
		.map((row) => [...row.matchAll(/(?:^|,)("(?:[^"]|"")*"|[^,]*)/g)].map(([, cell = '']) => cell.replace(/^"|"$/g, '').replaceAll('""', '"').trim()));

export const splitRefs = (refs: string) => refs.split(/[\s,;]+/).filter(Boolean);

export const normalizePartNumber = (number: string) => number.toUpperCase().replace(/[^A-Z0-9]/g, '');
// Raspberry Pi parts go by an order code (SC1509-A4) or a stepping-marked name (RP2350A0A4) as well as the part name.
const RASPBERRY_PI_PARTS: [RegExp, string][] = [
	[/^(SC1509|RP2350A0A\d)/, 'RP2350A'],
	[/^SC1169/, 'RMC20452T']
];
const partName = (mpn: string) => RASPBERRY_PI_PARTS.find(([pattern]) => pattern.test(mpn.toUpperCase()))?.[1] ?? mpn.toUpperCase();
// Distributors list some parts with a packaging suffix (TL3342F160QG/TR, S2B-PH-SM4-TB(LF)(SN)) or different spacing (PTS810SJM250SMTR LFS).
export function isSamePart(bomMpn: string, listedMpn: string) {
	const [bom, listed] = [partName(bomMpn), partName(listedMpn)];
	return normalizePartNumber(listed) === normalizePartNumber(bom) || new RegExp(`^${RegExp.escape(bom)}[/#(-]`).test(listed);
}

export async function readBom(path: string) {
	const [header = [], ...rows] = parseCsv(await Bun.file(path).text());
	// PCBWay's BOM template marks required columns with a leading *.
	const column = (pattern: RegExp) => header.findIndex((name) => pattern.test(name.replace(/^\*/, '')));
	const columns = {
		refs: column(/designator|references/i),
		qty: column(/^(qty|quantity)/i),
		mpn: column(/mfg part|mpn|manufacturer part/i),
		fit: column(/^(fit|populate)$/i)
	};
	if (columns.qty < 0 || columns.mpn < 0) throw new Error(`No quantity or MPN column in ${header.join(',')}`);
	const lines: BomLine[] = rows.map((row) => ({
		refs: row[columns.refs] ?? '',
		qty: Number(row[columns.qty]),
		mpn: row[columns.mpn] ?? '',
		fitted: columns.fit < 0 || !/^(no|dnp|n)$/i.test(row[columns.fit] ?? ''),
		row
	}));
	return { column, lines };
}
