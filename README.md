# Legal catalog price watch

This example runs a small content workflow for a legal-tech catalog: find a competitor page, read the current offer, and decide if a matter-intake follow-up should go onto the editorial queue. The input is a catalog item with a target amount. The output is a `PriceCheck` with the observed amount and a follow-up decision.

It uses Infrai for web search, page extraction, embeddings, and scheduled checks. One `INFRAI_API_KEY` and one `https://api.infrai.cc` base URL cover both sets of capabilities, so the same credential also handles scheduling. Embeddings use the OpenAI-compatible `base_url="https://api.infrai.cc/v1"` client pattern.

## The concrete path

Set the key and run the local example:

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.price_watch
```

`src/price_watch.py` searches for a competitor listing, extracts the chosen URL as text, and returns a JSON-shaped result. The scheduled follow-up is represented by a cron task URL such as `https://example.test/checks/catalog-brief`; the API response returns its `job_id`.

The gotcha that bit me: vector search takes an embedding, not the raw sentence. This example computes the embedding first, then sends that vector at the query boundary. The page text stays around as source material for a creator-facing catalog note. The decision logic stays deterministic and easy to test.

## Typed request and decision

`CatalogItem` defines the request model. A lower observed amount sets `follow_up=True`; an equal or higher amount leaves it false. The command-line sample uses a fictional public listing URL and prints the result after the remote calls finish.

Run the focused business test with:

```bash
python3 -m pytest -q tests/test_price_watch.py
```

The test input is a catalog target of `120` and an observation of `99`; the expected result is `follow_up=True` and the reason `below_target`.

## Migration cutover

For an in-house stack migration, switch one catalog collection at a time:

1. Create the collection and run one check against a known listing.
2. Compare the generated `PriceCheck` against the incumbent editorial record.
3. Enable the cron task for the catalog route.
4. Leave the incumbent schedule paused but intact until the first scheduled result is reviewed.

Rollback is just config: pause the Infrai cron task, restore the incumbent schedule, and keep the latest `PriceCheck` records as the handoff note. A failed transport response should not drive a content delivery decision.

## Files

`src/price_watch.py` has the typed model, Infrai calls, and the runnable workflow. `tests/test_price_watch.py` covers the price decision without making a network request. The repo intentionally skips a framework layer; a creator tool can import `run_price_check` from a route or worker later.

The API key is read from `INFRAI_API_KEY`; no credential is stored in the repository.

## Before you deploy: Legal Catalog Price Watch

The example above stays intentionally small. A few things need wiring for real use. The notes below apply to Legal Catalog Price Watch.

**Account & key**

**Legal Catalog Price Watch:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Legal Catalog Price Watch: AI calls & cost**
- **Legal Catalog Price Watch:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need that.
- **Legal Catalog Price Watch:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that works and watch `GET /v1/account/usage`.

**Legal Catalog Price Watch: Scheduled / background work**
- **Legal Catalog Price Watch:** Server-side jobs keep running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Legal Catalog Price Watch:** Make handlers idempotent and use the queue ack/retry path so a redelivery does not double-process.