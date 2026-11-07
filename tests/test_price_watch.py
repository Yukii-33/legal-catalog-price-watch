from src.price_watch import CatalogItem, InfraiClient, run_price_check


class FakeEmbedding:
    def create(self, **kwargs):
        return {"data": [{"embedding": [0.1, 0.2]}]}


def test_below_target_creates_editorial_follow_up(monkeypatch):
    monkeypatch.setattr("src.price_watch.OpenAI", lambda **kwargs: type("Client", (), {"embeddings": FakeEmbedding()})())
    client = InfraiClient("test-key")
    calls = []

    def request(path, body):
        calls.append((path, body))
        if path == "/v1/cron/create":
            return {"job_id": "job-17"}
        return {"text": "Contract review: 99"}

    client.request = request
    item = CatalogItem("contract-review", "Contract review intake", 120.0, "review")
    result = run_price_check(client, item, 99.0, "https://example.test/listing")

    assert result.follow_up is True
    assert result.reason == "below_target"
    assert calls[0][0] == "/v1/web/scrape"
    assert calls[1][1]["task"] == "https://example.test/checks/contract-review"
