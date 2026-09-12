import json

from belgeiz.qa import OllamaResponder, ollama_status


class FakeHTTPResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_ollama_uses_local_chat_api_and_json_schema(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        answer = {
            "grounded": True,
            "answer": "ALFA-42",
            "citation_ids": ["src-1"],
        }
        return FakeHTTPResponse({"message": {"content": json.dumps(answer)}})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    responder = OllamaResponder("qwen3:4b-instruct")
    result = responder("Kod nedir?", '<SOURCE id="src-1">ALFA-42</SOURCE>')

    assert result["answer"] == "ALFA-42"
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["think"] is False
    assert captured["payload"]["format"]["required"] == [
        "grounded",
        "answer",
        "citation_ids",
    ]


def test_ollama_status_lists_installed_models(monkeypatch):
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda url, timeout: FakeHTTPResponse(
            {"models": [{"name": "qwen3:4b-instruct"}, {"name": "qwen3:1.7b"}]}
        ),
    )
    available, models = ollama_status("http://localhost:11434")
    assert available is True
    assert models == ["qwen3:4b-instruct", "qwen3:1.7b"]

