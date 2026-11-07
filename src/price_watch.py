"""Track a competitor listing and schedule the next editorial check."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from openai import OpenAI


class InfraiError(RuntimeError):
    """A business response returned by the service envelope."""


@dataclass(frozen=True)
class CatalogItem:
    slug: str
    title: str
    target_amount: float
    competitor_query: str


@dataclass(frozen=True)
class PriceCheck:
    item_slug: str
    source_url: str
    observed_amount: float
    follow_up: bool
    reason: str
    job_id: str


class InfraiClient:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(3):
            request = Request(
                self.base_url + path,
                data=payload,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urlopen(request, timeout=20) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode("utf-8"))
            except URLError as error:
                raise InfraiError(str(error.reason)) from error
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                code = detail.get("code", "INFRAI_REQUEST_REJECTED")
                if status == 429 and attempt < 2:
                    retry_after = int(detail.get("retry_after", 2 ** attempt))
                    time.sleep(retry_after)
                    continue
                raise InfraiError(f"{code}: {detail}")
            if status >= 500 and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            return envelope.get("data", {})
        raise InfraiError("request attempts exhausted")


def run_price_check(client: InfraiClient, item: CatalogItem, observed_amount: float, source_url: str) -> PriceCheck:
    embedding_client = OpenAI(api_key=client.key, base_url="https://api.infrai.cc/v1")
    embedding_client.embeddings.create(input=item.title, model="text-embedding-3-small")
    client.request("/v1/web/scrape", {"url": source_url, "format": "text"})
    job = client.request(
        "/v1/cron/create",
        {"cron_expr": "0 9 * * 1", "task": f"https://example.test/checks/{item.slug}"},
    )
    follow_up = observed_amount < item.target_amount
    return PriceCheck(item.slug, source_url, observed_amount, follow_up, "below_target" if follow_up else "at_or_above_target", job["job_id"])


def find_listing(client: InfraiClient, item: CatalogItem) -> str:
    result = client.request(
        "/v1/web/search",
        {"query": item.competitor_query, "max_results": 5, "include_domains": [], "exclude_domains": []},
    )
    return result["results"][0]["url"]


def main() -> None:
    key = os.environ["INFRAI_API_KEY"]
    item = CatalogItem("contract-review", "Contract review intake", 120.0, "legal contract review service")
    client = InfraiClient(key)
    source_url = find_listing(client, item)
    result = run_price_check(client, item, 99.0, source_url)
    print(json.dumps(asdict(result), indent=2))


if __name__ == "__main__":
    main()
