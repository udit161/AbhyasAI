import os
from app.core.config import Settings

def test_settings_default_values():
    """
    Test that default configuration values are properly set up via pydantic-settings.
    """
    settings = Settings()
    assert settings.APP_NAME == "AI Learning Assistant & Mock Interview Platform"
    assert settings.ENVIRONMENT == "development"
    assert settings.PORT == 8000
    assert settings.AWS_REGION == "us-east-1"
    assert settings.VECTOR_DB_TYPE == "chroma"
    assert settings.DEFAULT_LLM_PROVIDER == "bedrock"

def test_settings_environment_override(monkeypatch):
    """
    Test environment variable overrides using pydantic-settings.
    """
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_key_id")
    monkeypatch.setenv("VECTOR_DB_API_KEY", "test_vector_db_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("DEFAULT_LLM_PROVIDER", "openai")

    settings = Settings()
    assert settings.AWS_REGION == "eu-west-1"
    assert settings.AWS_ACCESS_KEY_ID == "test_key_id"
    assert settings.VECTOR_DB_API_KEY == "test_vector_db_key"
    assert settings.OPENAI_API_KEY == "test_openai_key"
    assert settings.DEFAULT_LLM_PROVIDER == "openai"
