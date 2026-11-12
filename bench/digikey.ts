import { Config, Context, Effect, Layer, Schema } from 'effect';
import { FetchHttpClient, HttpClient, HttpClientRequest, HttpClientResponse } from 'effect/http';
import { isSamePart, normalizePartNumber } from './bom.ts';

const API = 'https://api.digikey.com';

const DISCONTINUED = ['Obsolete', 'Discontinued at Digi-Key'];

const Token = Schema.Struct({ access_token: Schema.String });

const Product = Schema.Struct({
	ManufacturerProductNumber: Schema.String,
	QuantityAvailable: Schema.optional(Schema.NullOr(Schema.Number)),
	ProductStatus: Schema.optional(Schema.NullOr(Schema.Struct({ Status: Schema.String })))
});

const KeywordSearch = Schema.Struct({
	Products: Schema.optional(Schema.Array(Product)),
	ExactMatches: Schema.optional(Schema.Array(Product))
});

const ProductDetails = Schema.Struct({
	Product: Schema.Struct({
		...Product.fields,
		ProductVariations: Schema.optional(
			Schema.Array(Schema.Struct({ DigiKeyProductNumber: Schema.String }))
		)
	})
});

export class DigikeyError extends Schema.TaggedError<DigikeyError>()('DigikeyError', {
	message: Schema.String
}) {}

const toDigikeyError = ({ message }: { readonly message: string }) => new DigikeyError({ message });

export class Digikey extends Context.Service<
	Digikey,
	{
		// Units Digi-Key has on hand for a manufacturer part number, 0 when it doesn't sell the part, and whether every listing of it is discontinued.
		part(mpn: string): Effect.Effect<{ stock: number; discontinued: boolean }, DigikeyError>;
		// Whether a Digi-Key part number is one of Digi-Key's listings of the manufacturer part number.
		isNumberFor(number: string, mpn: string): Effect.Effect<boolean, DigikeyError>;
	}
>()('pcbbench/bench/Digikey') {
	static readonly layer = Layer.effect(
		Digikey,
		Effect.gen(function* () {
			const client = (yield* HttpClient.HttpClient).pipe(
				HttpClient.transformResponse(
					Effect.provideService(HttpClient.TracerPropagationEnabled, false)
				)
			);

			const failUnlessOk = Effect.fnUntraced(function* (
				what: string,
				response: HttpClientResponse.HttpClientResponse
			) {
				if (response.status >= 200 && response.status < 300) return response;

				return yield* new DigikeyError({
					message: `${what} failed: ${response.status} ${yield* response.text}`
				});
			});

			const session = yield* Effect.cached(
				Effect.gen(function* () {
					const { clientId, clientSecret } = yield* Config.all({
						clientId: Config.NonEmptyString('DIGIKEY_CLIENT_ID'),
						clientSecret: Config.NonEmptyString('DIGIKEY_CLIENT_SECRET')
					}).pipe(
						Effect.mapError(
							() =>
								new DigikeyError({
									message:
										'Set DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET to a Digi-Key Product Information v4 app'
								})
						)
					);

					const response = yield* client.execute(
						HttpClientRequest.post(`${API}/v1/oauth2/token`).pipe(
							HttpClientRequest.bodyUrlParams({
								client_id: clientId,
								client_secret: clientSecret,
								grant_type: 'client_credentials'
							})
						)
					);

					const { access_token } = yield* HttpClientResponse.schemaBodyJson(Token)(
						yield* failUnlessOk('Digi-Key sign-in', response)
					);

					return {
						Authorization: `Bearer ${access_token}`,
						'X-DIGIKEY-Client-Id': clientId,
						'X-DIGIKEY-Locale-Site': 'US',
						'Content-Type': 'application/json'
					};
				})
			);

			const part = Effect.fn('Digikey.part')(function* (mpn: string) {
				const response = yield* client.execute(
					HttpClientRequest.post(`${API}/products/v4/search/keyword`).pipe(
						HttpClientRequest.bodyJsonUnsafe({ Keywords: mpn, Limit: 20 }),
						HttpClientRequest.setHeaders(yield* session)
					)
				);

				const { Products = [], ExactMatches = [] } = yield* HttpClientResponse.schemaBodyJson(
					KeywordSearch
				)(yield* failUnlessOk(`Digi-Key lookup of ${mpn}`, response));

				const matches = [...ExactMatches, ...Products].filter((product) =>
					isSamePart(mpn, product.ManufacturerProductNumber)
				);

				return {
					stock: Math.max(0, ...matches.map((product) => product.QuantityAvailable ?? 0)),
					discontinued:
						matches.length > 0 &&
						matches.every((product) => DISCONTINUED.includes(product.ProductStatus?.Status ?? ''))
				};
			}, Effect.mapError(toDigikeyError));

			const isNumberFor = Effect.fn('Digikey.isNumberFor')(function* (number: string, mpn: string) {
				const response = yield* client.get(
					`${API}/products/v4/search/${encodeURIComponent(number)}/productdetails`,
					{ headers: yield* session }
				);

				if (response.status === 404) return false;

				const { Product } = yield* HttpClientResponse.schemaBodyJson(ProductDetails)(
					yield* failUnlessOk(`Digi-Key lookup of ${number}`, response)
				);

				const listed = (Product.ProductVariations ?? []).some(
					(variation) =>
						normalizePartNumber(variation.DigiKeyProductNumber) === normalizePartNumber(number)
				);

				return listed && isSamePart(mpn, Product.ManufacturerProductNumber);
			}, Effect.mapError(toDigikeyError));

			return Digikey.of({ part, isNumberFor });
		})
	).pipe(Layer.provide(FetchHttpClient.layer));
}
