"""Unit tests for Playwright-related exceptions.

Tests cover:
- PlaywrightNotInstalledError initialization and default message
- FetchError with all attributes
- ConversionError with all attributes
"""

from mixseek_plus.errors import ConversionError, FetchError, PlaywrightNotInstalledError


class TestPlaywrightNotInstalledError:
    """Tests for PlaywrightNotInstalledError exception."""

    def test_default_message_includes_install_instructions(self) -> None:
        """Default message should include installation instructions."""
        error = PlaywrightNotInstalledError()

        assert "playwright is not installed" in str(error)
        assert "pip install mixseek-plus[playwright]" in str(error)
        assert "playwright install chromium" in str(error)

    def test_custom_message_is_used(self) -> None:
        """Custom message should override default."""
        custom_msg = "Custom error message"
        error = PlaywrightNotInstalledError(custom_msg)

        assert str(error) == custom_msg

    def test_is_import_error_subclass(self) -> None:
        """Should be a subclass of ImportError."""
        error = PlaywrightNotInstalledError()

        assert isinstance(error, ImportError)


class TestFetchError:
    """Tests for FetchError exception."""

    def test_stores_url_attribute(self) -> None:
        """Should store URL as attribute."""
        error = FetchError(message="Failed", url="https://example.com")

        assert error.url == "https://example.com"

    def test_stores_cause_attribute(self) -> None:
        """Should store cause exception as attribute."""
        cause = ValueError("Original error")
        error = FetchError(message="Failed", url="https://example.com", cause=cause)

        assert error.cause is cause

    def test_stores_attempts_attribute(self) -> None:
        """Should store attempts count as attribute."""
        error = FetchError(message="Failed", url="https://example.com", attempts=3)

        assert error.attempts == 3

    def test_defaults_to_one_attempt(self) -> None:
        """Attempts should default to 1."""
        error = FetchError(message="Failed", url="https://example.com")

        assert error.attempts == 1

    def test_message_is_preserved(self) -> None:
        """Error message should be preserved."""
        error = FetchError(message="HTTP 404 error", url="https://example.com/notfound")

        assert "HTTP 404 error" in str(error)


class TestConversionError:
    """Tests for ConversionError exception."""

    def test_stores_url_attribute(self) -> None:
        """Should store URL as attribute."""
        error = ConversionError(message="Failed", url="https://example.com")

        assert error.url == "https://example.com"

    def test_stores_cause_attribute(self) -> None:
        """Should store cause exception as attribute."""
        cause = RuntimeError("Parsing failed")
        error = ConversionError(
            message="Conversion failed", url="https://example.com", cause=cause
        )

        assert error.cause is cause

    def test_cause_defaults_to_none(self) -> None:
        """Cause should default to None."""
        error = ConversionError(message="Failed", url="https://example.com")

        assert error.cause is None

    def test_message_is_preserved(self) -> None:
        """Error message should be preserved."""
        error = ConversionError(
            message="Invalid HTML structure", url="https://example.com"
        )

        assert "Invalid HTML structure" in str(error)
