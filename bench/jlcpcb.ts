import { Context, Effect, Layer, Schema } from 'effect';
import { FetchHttpClient, HttpClient, HttpClientRequest, HttpClientResponse } from 'effect/http';
import { isSamePart } from './bom.ts';

const SearchResponse = Schema.Struct({
	data: Schema.NullOr(
		Schema.Struct({
			componentPageInfo: Schema.Struct({
				list: Schema.NullOr(
					Schema.Array(
						Schema.Struct({
							componentCode: Schema.String,
							componentModelEn: Schema.String,
							stockCount: Schema.Number
						})
					)
				)
			})
		})
	)
});

export class JlcpcbError extends Schema.TaggedError<JlcpcbError>()('JlcpcbError', {
	cause: Schema.Defect()
}) {}

const SEARCH =
	'https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList';

export class Jlcpcb extends Context.Service<
	Jlcpcb,
	{
		// JLCPCB's assembly stock, which is separate from LCSC's store stock.
		stock(mpn: string, lcscCode: string | null): Effect.Effect<number, JlcpcbError>;
	}
>()('pcbbench/bench/Jlcpcb') {
	static readonly layer = Layer.effect(
		Jlcpcb,
		Effect.gen(function* () {
			const client = (yield* HttpClient.HttpClient).pipe(
				HttpClient.mapRequest(HttpClientRequest.setHeader('User-Agent', 'Mozilla/5.0'))
			);

			const stock = Effect.fn('Jlcpcb.stock')(
				function* (mpn: string, lcscCode: string | null) {
					const response = yield* client.execute(
						HttpClientRequest.post(SEARCH).pipe(
							HttpClientRequest.bodyJsonUnsafe({
								keyword: lcscCode ?? mpn,
								currentPage: 1,
								pageSize: 25
							})
						)
					);

					const { data } = yield* HttpClientResponse.schemaBodyJson(SearchResponse)(response);

					const matches = (data?.componentPageInfo.list ?? []).filter(
						(part) => part.componentCode === lcscCode || isSamePart(mpn, part.componentModelEn)
					);

					return Math.max(0, ...matches.map((part) => part.stockCount));
				},
				Effect.mapError((cause) => new JlcpcbError({ cause }))
			);

			return Jlcpcb.of({ stock });
		})
	).pipe(Layer.provide(FetchHttpClient.layer));
}
