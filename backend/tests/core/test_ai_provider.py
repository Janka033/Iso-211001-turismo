"""Tests del GeminiProvider: retries transitorios, caché de embeddings y
thinking configurable. Sin red: se monkeypatcha el cliente del SDK."""

import httpx
import pytest

from app.core.ai import gemini
from app.core.ai.gemini import GeminiProvider, _call_with_retries, _is_retryable


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(gemini.time, "sleep", lambda s: None)


# ---------------------------------------------------------------------------
# _call_with_retries
# ---------------------------------------------------------------------------


def test_retries_transient_timeout_then_succeeds():
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise httpx.ReadTimeout("upstream colgado")
        return "ok"

    assert _call_with_retries(flaky, what="test") == "ok"
    assert calls["n"] == 3  # 2 fallos transitorios + éxito


def test_non_retryable_raises_immediately():
    calls = {"n": 0}

    def broken():
        calls["n"] += 1
        raise ValueError("JSON roto: no es transitorio")

    with pytest.raises(ValueError):
        _call_with_retries(broken, what="test")
    assert calls["n"] == 1


def test_exhausted_retries_raise_last_error():
    def always_timeout():
        raise httpx.ReadTimeout("nunca responde")

    with pytest.raises(httpx.ReadTimeout):
        _call_with_retries(always_timeout, what="test")


def test_is_retryable_covers_timeout_and_not_valueerror():
    assert _is_retryable(httpx.ConnectTimeout("t")) is True
    assert _is_retryable(ValueError("x")) is False


# ---------------------------------------------------------------------------
# GeminiProvider: caché de embeddings y thinking configurable
# ---------------------------------------------------------------------------


class _FakeEmbedding:
    values = [0.1] * gemini.EMBEDDING_DIM


class _FakeEmbedResponse:
    embeddings = [_FakeEmbedding()]


class _FakeGenerateResponse:
    text = '{"ok": true}'


@pytest.fixture
def provider(monkeypatch):
    p = GeminiProvider()
    # La caché es por instancia+texto (lru_cache sobre el método): limpiar para
    # que cada test parta de cero aunque el provider real sea singleton.
    p._embed_cached.cache_clear()
    return p


async def test_embed_caches_by_text(provider, monkeypatch):
    calls = {"n": 0}

    def fake_embed(**kwargs):
        calls["n"] += 1
        return _FakeEmbedResponse()

    monkeypatch.setattr(provider._client.models, "embed_content", fake_embed)

    v1 = await provider.embed("query constante del RAG")
    v2 = await provider.embed("query constante del RAG")
    v3 = await provider.embed("otra query")

    assert calls["n"] == 2  # la repetida salió de caché
    assert v1 == v2
    assert isinstance(v1, list) and len(v3) == gemini.EMBEDDING_DIM


async def test_generate_json_passes_thinking_budget(provider, monkeypatch):
    captured = {}

    def fake_generate(**kwargs):
        captured["config"] = kwargs["config"]
        return _FakeGenerateResponse()

    monkeypatch.setattr(provider._client.models, "generate_content", fake_generate)

    await provider.generate_json("prompt", thinking_budget=0)
    assert captured["config"].thinking_config.thinking_budget == 0

    await provider.generate_json("prompt")  # default: sin thinking_config
    assert captured["config"].thinking_config is None
