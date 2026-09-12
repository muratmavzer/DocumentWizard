from belgeiz.config import Settings


def test_environment_configuration_has_safe_fallback(monkeypatch):
    monkeypatch.setenv("BELGEIZ_RETRIEVAL_THRESHOLD", "not-a-number")
    monkeypatch.setenv("BELGEIZ_MODEL", "test-model")
    settings = Settings.from_env()
    assert settings.model == "test-model"
    assert settings.retrieval_threshold == 0.18

