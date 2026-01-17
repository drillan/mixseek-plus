"""pytest fixtures for mixseek-plus tests."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def mock_workspace_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Set MIXSEEK_WORKSPACE environment variable for all tests.

    mixseek-core requires a workspace path to be set.

    Returns:
        Path to the temporary workspace directory
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("MIXSEEK_WORKSPACE", str(workspace))
    return workspace


@pytest.fixture
def mock_groq_api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """GROQ_API_KEY環境変数を有効な値でモックする.

    Returns:
        モックされたAPIキーの値
    """
    api_key = "gsk_test_api_key_1234567890abcdef"
    monkeypatch.setenv("GROQ_API_KEY", api_key)
    # Also set TAVILY_API_KEY for web search tests
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test_api_key_1234567890")
    return api_key


@pytest.fixture
def clear_groq_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """GROQ_API_KEY環境変数をクリアする."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


@pytest.fixture
def empty_groq_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """GROQ_API_KEY環境変数を空文字に設定する."""
    monkeypatch.setenv("GROQ_API_KEY", "")


@pytest.fixture
def invalid_format_groq_api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """不正な形式のGROQ_API_KEY環境変数を設定する.

    Returns:
        モックされた不正なAPIキーの値
    """
    api_key = "invalid_api_key_without_gsk_prefix"
    monkeypatch.setenv("GROQ_API_KEY", api_key)
    return api_key


@pytest.fixture
def mock_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> str:
    """OPENAI_API_KEY環境変数を有効な値でモックする.

    Returns:
        モックされたAPIキーの値
    """
    api_key = "sk-test_openai_api_key_1234567890"
    monkeypatch.setenv("OPENAI_API_KEY", api_key)
    return api_key


def pytest_configure(config: pytest.Config) -> None:
    """pytest設定にカスタムマーカーを追加する."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    )
