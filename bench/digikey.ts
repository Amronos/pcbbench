import { isSamePart, normalizePartNumber } from './bom.ts';

const API = 'https://api.digikey.com';

async function accessToken() {
	const { DIGIKEY_CLIENT_ID: clientId, DIGIKEY_CLIENT_SECRET: clientSecret } = process.env;

	if (!clientId || !clientSecret)
		throw new Error(
			'Set DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET to a Digi-Key Product Information v4 app'
		);

	const response = await fetch(`${API}/v1/oauth2/token`, {
		method: 'POST',
		body: new URLSearchParams({
			client_id: clientId,
			client_secret: clientSecret,
			grant_type: 'client_credentials'
		})
	});

	if (!response.ok)
		throw new Error(`Digi-Key sign-in failed: ${response.status} ${await response.text()}`);
	const { access_token }: { access_token: string } = JSON.parse(await response.text());

	return { clientId, token: access_token };
}

let session: ReturnType<typeof accessToken> | undefined;

const DISCONTINUED = ['Obsolete', 'Discontinued at Digi-Key'];

type Product = {
	ManufacturerProductNumber: string;
	QuantityAvailable?: number;
	ProductStatus?: { Status: string };
};

async function headers() {
	const { clientId, token } = await (session ??= accessToken());

	return {
		Authorization: `Bearer ${token}`,
		'X-DIGIKEY-Client-Id': clientId,
		'X-DIGIKEY-Locale-Site': 'US',
		'Content-Type': 'application/json'
	};
}

// Units Digi-Key has on hand for a manufacturer part number, 0 when it doesn't sell the part, and whether every listing of it is discontinued.
export async function digikeyPart(mpn: string) {
	const response = await fetch(`${API}/products/v4/search/keyword`, {
		method: 'POST',
		headers: await headers(),
		body: JSON.stringify({ Keywords: mpn, Limit: 20 })
	});

	if (!response.ok)
		throw new Error(
			`Digi-Key lookup of ${mpn} failed: ${response.status} ${await response.text()}`
		);

	const { Products = [], ExactMatches = [] }: Record<'Products' | 'ExactMatches', Product[]> =
		JSON.parse(await response.text());

	const matches = [...ExactMatches, ...Products].filter((product) =>
		isSamePart(mpn, product.ManufacturerProductNumber)
	);

	return {
		stock: Math.max(0, ...matches.map((product) => product.QuantityAvailable ?? 0)),
		discontinued:
			matches.length > 0 &&
			matches.every((product) => DISCONTINUED.includes(product.ProductStatus?.Status ?? ''))
	};
}

// Whether a Digi-Key part number is one of Digi-Key's listings of the manufacturer part number.
export async function isDigikeyNumberFor(number: string, mpn: string) {
	const response = await fetch(
		`${API}/products/v4/search/${encodeURIComponent(number)}/productdetails`,
		{ headers: await headers() }
	);

	if (response.status === 404) return false;

	if (!response.ok)
		throw new Error(
			`Digi-Key lookup of ${number} failed: ${response.status} ${await response.text()}`
		);

	const {
		Product
	}: { Product: Product & { ProductVariations?: { DigiKeyProductNumber: string }[] } } = JSON.parse(
		await response.text()
	);

	const listed = (Product.ProductVariations ?? []).some(
		(variation) =>
			normalizePartNumber(variation.DigiKeyProductNumber) === normalizePartNumber(number)
	);

	return listed && isSamePart(mpn, Product.ManufacturerProductNumber);
}
