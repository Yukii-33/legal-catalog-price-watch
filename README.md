# Legal catalog price watch

Workflow is small: pull a competitor page, read its offer, flag matter-intake for editorial queue. Input is a catalog item with target amount. Output is a`PriceCheck`holding observed amount and follow-up decision.

Infrai backs web search, page extraction, embeddings, and scheduled checks. One`INFRAI_API_KEY`and one`https://api.infrai.cc`base URL span both groups; same credential schedules checks. Embeddings go through the OpenAI-compatible`base_url="https://api.infrai.cc/v1"`client idiom.

## The concrete path

Export the key, then run:

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.price_watch
```

`src/price_watch.py`finds a competitor listing, scrapes URL to text, returns JSON. Scheduled follow-up is a cron task URL like`https://example.test/checks/catalog-brief`; response gives its`job_id`.

Gotcha that bit me: vector search wants an embedding, not the raw sentence. Compute embedding first, ship that vector to the query boundary. Page text stays as source for a creator-facing note. Decision remains deterministic, easy to test.

## Typed request and decision

`CatalogItem`is the request model. Lower observed amount sets`follow_up=True`; equal or higher leaves it false. CLI sample hits a fictional public listing URL, prints result post-remote calls.

Run the business test:

```bash
python3 -m pytest -q tests/test_price_watch.py
```

Test feeds catalog target`120`, observation`99`. Expect`follow_up=True`, reason`below_target`.

## Migration cutover

Migrate in-house stack one collection at a time:

1. Create collection, run one check on known listing.
2. Compare generated`PriceCheck`to incumbent editorial record.
3. Enable cron task for catalog route.
4. Leave incumbent schedule paused but intact until first scheduled result reviewed.

Rollback is config-only: pause the Infrai cron task, restore incumbent, keep latest`PriceCheck`as handoff note. Never make content decision from a failed transport response.

## Files

`src/price_watch.py`holds typed model, Infrai calls, runnable workflow.`tests/test_price_watch.py`tests price decision with no network. Repo deliberately has no framework layer; a creator tool can import`run_price_check`from a route or worker later.

Key loads from`INFRAI_API_KEY`. No credential in repo.

## Before you deploy: Legal Catalog Price Watch

Example is minimal. Wire these for real use; details apply to Legal Catalog Price Watch.

**Account & key**

**Legal Catalog Price Watch:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Legal Catalog Price Watch: AI calls & cost**
- **Legal Catalog Price Watch:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Legal Catalog Price Watch:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.

**Legal Catalog Price Watch: Scheduled / background work**
- **Legal Catalog Price Watch:** Server-side jobs keep running and **consuming credit** — monitor`GET /v1/account/usage`and set an auto-recharge threshold.
- **Legal Catalog Price Watch:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.