from jvsg_triage.settings import Settings


def test_defaults_support_local_development() -> None:
    settings = Settings(_env_file=None)

    assert settings.runtime_mode == "local"
    assert settings.ollama_base_url == "http://127.0.0.1:11434"
    assert settings.sid_hmac_secret is None


def test_environment_values_override_defaults(monkeypatch) -> None:
    monkeypatch.setenv("JVSG_RUNTIME_MODE", "azure")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")

    settings = Settings(_env_file=None)

    assert settings.runtime_mode == "azure"
    assert settings.ollama_model == "test-model"
