import requests
import pytest

from utils.groq_client import GroqClient, GroqClientDisabledError


class DummyResponse:
    def __init__(self, data, status_code=200):
        self._data = data
        self.status_code = status_code
        self.headers = {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)

    def json(self):
        return self._data


class RecordingSession:
    def __init__(self, response):
        self._response = response
        self.calls = 0

    def post(self, *args, **kwargs):
        self.calls += 1
        return self._response


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    # Ensure each test starts from a clean slate
    for key in [
        "GROQ_ENABLED",
        "GROQ_API_KEY",
        "GROQ_TIMEOUT_SECONDS",
        "GROQ_TIMEOUT",
        "GROQ_MAX_RETRIES",
        "GROQ_RETRY_BACKOFF",
        "GROQ_CACHE_ENABLED",
        "GROQ_CACHE_TTL",
        "GROQ_CACHE_MAX_ITEMS",
        "GROQ_DISABLE_AFTER_FAILURES",
        "GROQ_DISABLE_COOLDOWN",
    ]:
        monkeypatch.delenv(key, raising=False)
    yield


def test_groq_client_disabled_by_flag(monkeypatch):
    monkeypatch.setenv("GROQ_ENABLED", "false")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    client = GroqClient(session=RecordingSession(DummyResponse({})))

    with pytest.raises(GroqClientDisabledError):
        client.call({"model": "demo"})


def test_groq_client_caches_responses(monkeypatch):
    monkeypatch.setenv("GROQ_ENABLED", "true")
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GROQ_CACHE_ENABLED", "true")
    monkeypatch.setenv("GROQ_CACHE_TTL", "60")
    monkeypatch.setenv("GROQ_CACHE_MAX_ITEMS", "5")
    monkeypatch.setenv("GROQ_MAX_RETRIES", "0")

    response_payload = {"choices": [{"message": {"content": "{}"}}]}
    session = RecordingSession(DummyResponse(response_payload))
    client = GroqClient(session=session)

    payload = {"model": "demo", "messages": []}

    first = client.call(payload)
    second = client.call(payload)

    assert first == response_payload
    assert second == response_payload
    assert session.calls == 1
