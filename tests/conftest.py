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
    config.addinivalue_line(
        "markers",
        "playwright: marks tests that require playwright (deselect with '-m \"not playwright\"')",
    )


# Playwright fixtures


@pytest.fixture
def mock_playwright_config() -> dict[str, object]:
    """Default Playwright configuration for tests.

    Returns:
        Dictionary with default Playwright settings
    """
    return {
        "headless": True,
        "timeout_ms": 30000,
        "wait_for_load_state": "load",
        "retry_count": 0,
        "retry_delay_ms": 1000,
        "block_resources": None,
    }


@pytest.fixture
def mock_playwright_config_with_retries() -> dict[str, object]:
    """Playwright configuration with retries enabled.

    Returns:
        Dictionary with Playwright settings including retries
    """
    return {
        "headless": True,
        "timeout_ms": 30000,
        "wait_for_load_state": "load",
        "retry_count": 3,
        "retry_delay_ms": 500,
        "block_resources": None,
    }


@pytest.fixture
def mock_playwright_config_with_blocking() -> dict[str, object]:
    """Playwright configuration with resource blocking.

    Returns:
        Dictionary with Playwright settings including resource blocking
    """
    return {
        "headless": True,
        "timeout_ms": 30000,
        "wait_for_load_state": "networkidle",
        "retry_count": 0,
        "retry_delay_ms": 1000,
        "block_resources": ["image", "font", "media"],
    }
