export type LcscProduct = {
	productCode: string;
	productModel: string;
	minBuyNumber: number;
	stockNumber: number;
	productCycle?: string;
	encapStandard?: string;
	edaSvgInfo?: { pcbSvg?: string };
	productPriceList?: { ladder: number; usdPrice: number }[];
};

const USER_AGENT = { 'User-Agent': 'Mozilla/5.0' };

export async function lcsc<T>(path: string, body?: object): Promise<T | null> {
	const response = await fetch(`https://wmsc.lcsc.com/ftps/wm/${path}`, {
		headers: { ...USER_AGENT, 'Content-Type': 'application/json' },
		...(body && { method: 'POST', body: JSON.stringify(body) })
	});
	const { result }: { result: T | null } = JSON.parse(await response.text());
	return result;
}

export const productByCode = (code: string) =>
	lcsc<LcscProduct>(`product/detail?productCode=${code}`);

// LCSC's own footprint for the part, as an SVG with one element per pad.
export async function footprintPadNumbers(product: LcscProduct) {
	const svgUrl = product.edaSvgInfo?.pcbSvg;
	if (!svgUrl) return [];
	const svg = await (await fetch(`https:${svgUrl}`, { headers: USER_AGENT })).text();
	return [...svg.matchAll(/<[^>]*c_partid="part_pad"[^>]*>/g)].flatMap(
		([tag]) => tag.match(/\bnumber="([^"]+)"/)?.[1] ?? []
	);
}
