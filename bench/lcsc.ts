import { Context, Effect, Layer, Schema } from 'effect';
import { FetchHttpClient, HttpClient, HttpClientRequest, HttpClientResponse } from 'effect/http';

// LCSC leaves out or nulls fields it has no value for, and search results skip some detail fields.
const nullable = <S extends Schema.Top>(schema: S) => Schema.optional(Schema.NullOr(schema));

export const LcscProduct = Schema.Struct({
	productCode: Schema.String,
	productModel: Schema.String,
	minBuyNumber: Schema.Number,
	stockNumber: Schema.Number,
	productCycle: nullable(Schema.String),
	encapStandard: nullable(Schema.String),
	edaSvgInfo: nullable(Schema.Struct({ pcbSvg: nullable(Schema.String) })),
	productPriceList: nullable(
		Schema.Array(Schema.Struct({ ladder: Schema.Number, usdPrice: Schema.Number }))
	)
});

export type LcscProduct = typeof LcscProduct.Type;

const ProductResponse = Schema.Struct({ result: Schema.NullOr(LcscProduct) });

const SearchResponse = Schema.Struct({
	result: Schema.NullOr(
		Schema.Struct({ exactMatchResult: Schema.NullOr(Schema.Array(LcscProduct)) })
	)
});

export class LcscError extends Schema.TaggedError<LcscError>()('LcscError', {
	cause: Schema.Defect()
}) {}

const API = 'https://wmsc.lcsc.com/ftps/wm';

export class Lcsc extends Context.Service<
	Lcsc,
	{
		productByCode(code: string): Effect.Effect<LcscProduct | null, LcscError>;
		exactMatches(keyword: string): Effect.Effect<ReadonlyArray<LcscProduct>, LcscError>;
		// LCSC's own footprint for the part, as an SVG with one element per pad.
		footprintPadNumbers(product: LcscProduct): Effect.Effect<Array<string>, LcscError>;
	}
>()('pcbbench/bench/Lcsc') {
	static readonly layer = Layer.effect(
		Lcsc,
		Effect.gen(function* () {
			const client = (yield* HttpClient.HttpClient).pipe(
				HttpClient.mapRequest(HttpClientRequest.setHeader('User-Agent', 'Mozilla/5.0')),
				HttpClient.transformResponse(
					Effect.provideService(HttpClient.TracerPropagationEnabled, false)
				)
			);

			const api = (request: HttpClientRequest.HttpClientRequest) =>
				client.execute(HttpClientRequest.setHeader(request, 'Content-Type', 'application/json'));

			const productByCode = Effect.fn('Lcsc.productByCode')(
				function* (code: string) {
					const response = yield* api(
						HttpClientRequest.get(`${API}/product/detail?productCode=${code}`)
					);

					return (yield* HttpClientResponse.schemaBodyJson(ProductResponse)(response)).result;
				},
				Effect.mapError((cause) => new LcscError({ cause }))
			);

			const exactMatches = Effect.fn('Lcsc.exactMatches')(
				function* (keyword: string) {
					const response = yield* api(
						HttpClientRequest.post(`${API}/search/v3/global`).pipe(
							HttpClientRequest.bodyJsonUnsafe({ keyword })
						)
					);

					const { result } = yield* HttpClientResponse.schemaBodyJson(SearchResponse)(response);

					return result?.exactMatchResult ?? [];
				},
				Effect.mapError((cause) => new LcscError({ cause }))
			);

			const footprintPadNumbers = Effect.fn('Lcsc.footprintPadNumbers')(
				function* (product: LcscProduct) {
					const svgUrl = product.edaSvgInfo?.pcbSvg;

					if (!svgUrl) return [];
					const svg = yield* (yield* client.get(`https:${svgUrl}`)).text;

					return [...svg.matchAll(/<[^>]*c_partid="part_pad"[^>]*>/g)].flatMap(
						([tag]) => tag.match(/\bnumber="([^"]+)"/)?.[1] ?? []
					);
				},
				Effect.mapError((cause) => new LcscError({ cause }))
			);

			return Lcsc.of({ productByCode, exactMatches, footprintPadNumbers });
		})
	).pipe(Layer.provide(FetchHttpClient.layer));
}
