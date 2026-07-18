import json

import pytest
import requests

from app import llm


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def test_llm_uses_strict_structured_output(monkeypatch):
    captured: dict = {}
    content = json.dumps(
        {
            "emotion": "calm",
            "keywords": ["rain", "forest", "breathing"],
            "summary": "The user describes feeling calm while listening to rain in the forest.",
        }
    )

    def fake_post(_url, **kwargs):
        captured["headers"] = kwargs["headers"]
        captured["timeout"] = kwargs["timeout"]
        captured.update(kwargs["json"])
        return FakeResponse(200, {"choices": [{"message": {"content": content}}]})

    monkeypatch.setattr(llm, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(llm.requests, "post", fake_post)

    result = llm.analyze_emotion_with_llm("Rain helped me slow down.", "forest")

    assert result["emotion"] == "calm"
    assert captured["model"] == "openai/gpt-oss-20b"
    assert captured["reasoning_effort"] == "low"
    assert captured["max_completion_tokens"] == 800
    assert captured["response_format"]["type"] == "json_schema"
    assert captured["response_format"]["json_schema"]["strict"] is True
    assert captured["response_format"]["json_schema"]["schema"]["additionalProperties"] is False
    assert captured["timeout"] == 30
    assert captured["headers"]["Authorization"] == "Bearer test-key"
    user_content = json.loads(captured["messages"][1]["content"])
    assert user_content == {"ambience": "forest", "journal": "Rain helped me slow down."}


def test_llm_rejects_unstructured_or_unusable_output(monkeypatch):
    content = json.dumps(
        {
            "emotion": "supercalifragilistic",
            "keywords": ["generic"],
            "summary": "Too short",
        }
    )
    monkeypatch.setattr(llm, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        llm.requests,
        "post",
        lambda *_args, **_kwargs: FakeResponse(
            200, {"choices": [{"message": {"content": content}}]}
        ),
    )

    with pytest.raises(llm.LLMProviderError, match="invalid emotion analysis"):
        llm.analyze_emotion_with_llm("Example")


def test_invalid_provider_credentials_are_configuration_error(monkeypatch):
    monkeypatch.setattr(llm, "GROQ_API_KEY", "expired-key")
    monkeypatch.setattr(
        llm.requests,
        "post",
        lambda *_args, **_kwargs: FakeResponse(401, {"error": "invalid"}),
    )

    with pytest.raises(llm.LLMConfigurationError, match="rejected"):
        llm.analyze_emotion_with_llm("Example")


@pytest.mark.parametrize("key", [None, "", "your_groq_api_key"])
def test_missing_or_placeholder_key_is_rejected_before_network(monkeypatch, key):
    monkeypatch.setattr(llm, "GROQ_API_KEY", key)
    monkeypatch.setattr(
        llm.requests,
        "post",
        lambda *_args, **_kwargs: pytest.fail("network must not be called"),
    )
    with pytest.raises(llm.LLMConfigurationError, match="not configured"):
        llm.analyze_emotion_with_llm("Example")


@pytest.mark.parametrize("status_code", [403, 401])
def test_provider_auth_failures_are_configuration_errors(monkeypatch, status_code):
    monkeypatch.setattr(llm, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        llm.requests,
        "post",
        lambda *_args, **_kwargs: FakeResponse(status_code, {}),
    )
    with pytest.raises(llm.LLMConfigurationError, match="rejected"):
        llm.analyze_emotion_with_llm("Example")


@pytest.mark.parametrize("status_code", [400, 429, 500, 503])
def test_provider_http_failures_are_sanitized(monkeypatch, status_code):
    monkeypatch.setattr(llm, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        llm.requests,
        "post",
        lambda *_args, **_kwargs: FakeResponse(status_code, {"secret": "not surfaced"}),
    )
    with pytest.raises(llm.LLMProviderError, match=f"HTTP {status_code}"):
        llm.analyze_emotion_with_llm("Example")


def test_network_failure_is_provider_error(monkeypatch):
    monkeypatch.setattr(llm, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        llm.requests,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(requests.Timeout("slow")),
    )
    with pytest.raises(llm.LLMProviderError, match="request failed"):
        llm.analyze_emotion_with_llm("Example")


@pytest.mark.parametrize(
    "provider_payload",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": "not-json"}}]},
    ],
)
def test_malformed_provider_responses_are_rejected(monkeypatch, provider_payload):
    monkeypatch.setattr(llm, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        llm.requests,
        "post",
        lambda *_args, **_kwargs: FakeResponse(200, provider_payload),
    )
    with pytest.raises(llm.LLMProviderError, match="invalid emotion analysis"):
        llm.analyze_emotion_with_llm("Example")


@pytest.mark.parametrize(
    "keywords",
    [
        ["one", "two", ""],
        ["same", "same", "different"],
        ["x" * 33, "two", "three"],
        ["only", "two"],
        ["one", "two", "three", "four", "five", "six"],
    ],
)
def test_keyword_contract_rejects_unusable_values(keywords):
    with pytest.raises(ValueError):
        llm.EmotionAnalysis(
            emotion="calm",
            keywords=keywords,
            summary="A sufficiently descriptive and neutral summary.",
        )


def test_keyword_contract_normalizes_values():
    analysis = llm.EmotionAnalysis(
        emotion="hopeful",
        keywords=["  Rain ", "FOREST", "Fresh air"],
        summary="The user describes a hopeful experience in nature.",
    )
    assert analysis.keywords == ["rain", "forest", "fresh air"]
