import httpx
import pytest

from app import ai
from app.config import settings


@pytest.fixture()
def ai_enabled(monkeypatch):
    """Pretend the Gemini URL/key were filled in (frozen dataclass -> patch the instance)."""
    monkeypatch.setattr(settings, "gemini_api_url", "https://example.test/generate", raising=False)
    monkeypatch.setattr(settings, "gemini_api_key", "test-key", raising=False)


def test_ai_returns_503_when_not_configured(client, make_lead, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_url", None, raising=False)
    monkeypatch.setattr(settings, "gemini_api_key", None, raising=False)
    lead = make_lead()
    response = client.post(f"/api/leads/{lead['id']}/follow-up", json={})
    assert response.status_code == 503
    assert "GEMINI_API_URL" in response.json()["detail"]


def test_summarize_requires_notes(client, make_lead, ai_enabled):
    lead = make_lead(notes="")
    response = client.post(f"/api/leads/{lead['id']}/summarize")
    assert response.status_code == 400


def test_ai_unknown_lead_is_404(client, ai_enabled):
    assert client.post("/api/leads/999/summarize").status_code == 404
    assert client.post("/api/leads/999/follow-up", json={}).status_code == 404


def test_summarize_and_follow_up_happy_path(client, make_lead, ai_enabled, monkeypatch):
    seen = {}

    def fake_post(url, json, headers, timeout):
        seen["url"], seen["headers"], seen["prompt"] = url, headers, json["contents"][0]["parts"][0]["text"]
        body = {"candidates": [{"content": {"parts": [{"text": "Generated text"}]}}]}
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(ai.httpx, "post", fake_post)
    lead = make_lead()

    summary = client.post(f"/api/leads/{lead['id']}/summarize")
    assert summary.status_code == 200
    assert summary.json() == {"lead_id": lead["id"], "kind": "summary", "text": "Generated text"}
    assert "Interested in analytics" in seen["prompt"]
    assert seen["headers"]["x-goog-api-key"] == "test-key"

    draft = client.post(
        f"/api/leads/{lead['id']}/follow-up", json={"tone": "professional", "sender_name": "Priya"}
    )
    assert draft.status_code == 200
    assert draft.json()["kind"] == "follow_up"
    assert "professional" in seen["prompt"] and "Priya" in seen["prompt"]
    assert "SaaStr 2026" in seen["prompt"]


def test_follow_up_works_without_body(client, make_lead, ai_enabled, monkeypatch):
    def fake_post(url, json, headers, timeout):
        body = {"candidates": [{"content": {"parts": [{"text": "Hi"}]}}]}
        return httpx.Response(200, json=body, request=httpx.Request("POST", url))

    monkeypatch.setattr(ai.httpx, "post", fake_post)
    lead = make_lead()
    assert client.post(f"/api/leads/{lead['id']}/follow-up").status_code == 200


def test_upstream_failures_become_502(client, make_lead, ai_enabled, monkeypatch):
    lead = make_lead()

    def http_error(url, json, headers, timeout):
        return httpx.Response(429, json={}, request=httpx.Request("POST", url))

    monkeypatch.setattr(ai.httpx, "post", http_error)
    assert client.post(f"/api/leads/{lead['id']}/follow-up", json={}).status_code == 502

    def blocked(url, json, headers, timeout):
        return httpx.Response(200, json={"promptFeedback": {}}, request=httpx.Request("POST", url))

    monkeypatch.setattr(ai.httpx, "post", blocked)
    assert client.post(f"/api/leads/{lead['id']}/follow-up", json={}).status_code == 502

    def offline(url, json, headers, timeout):
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(ai.httpx, "post", offline)
    assert client.post(f"/api/leads/{lead['id']}/follow-up", json={}).status_code == 502
