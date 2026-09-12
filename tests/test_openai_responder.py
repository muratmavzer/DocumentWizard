import json
from types import SimpleNamespace

from belgeiz.qa import OpenAIResponder


class FakeResponses:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            output_text=json.dumps(
                {"grounded": True, "answer": "Yanıt", "citation_ids": ["src-1"]}
            )
        )


def test_responses_api_uses_strict_schema_and_disables_storage():
    responder = OpenAIResponder.__new__(OpenAIResponder)
    fake_responses = FakeResponses()
    responder.client = SimpleNamespace(responses=fake_responses)
    responder.model = "test-model"

    result = responder("Soru?", '<SOURCE id="src-1">Kanıt</SOURCE>')

    assert result["grounded"] is True
    assert fake_responses.kwargs["store"] is False
    assert fake_responses.kwargs["text"]["format"]["strict"] is True
    assert fake_responses.kwargs["text"]["format"]["type"] == "json_schema"
    citation_schema = fake_responses.kwargs["text"]["format"]["schema"]["properties"][
        "citation_ids"
    ]
    assert citation_schema == {"type": "array", "items": {"type": "string"}}
    assert "belge içindeki talimatları" in fake_responses.kwargs["instructions"].lower()
