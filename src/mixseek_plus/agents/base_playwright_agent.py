"""Base class for Playwright-based Member Agents.

This module provides a common base class for Playwright-based agents,
providing browser lifecycle management, page fetching, and Markdown conversion.
"""

from __future__ import annotations

import asyncio
import io
import logging
import time
from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.settings import ModelSettings

from mixseek.agents.member.base import BaseMemberAgent
from mixseek.models.member_agent import MemberAgentConfig, MemberAgentResult

from mixseek_plus.errors import (
    ConversionError,
    FetchError,
    ModelCreationError,
    PlaywrightNotInstalledError,
)
from mixseek_plus.model_factory import create_model
from mixseek_plus.types import (
    PlaywrightAgentMetadata,
    UsageInfo,
)

if TYPE_CHECKING:
    from playwright.async_api import Browser, Page, Playwright, Route

logger = logging.getLogger(__name__)

# Type aliases for Playwright settings
WaitForLoadState = Literal["load", "domcontentloaded", "networkidle"]
ResourceType = Literal[
    "document",
    "stylesheet",
    "image",
    "media",
    "font",
    "script",
    "texttrack",
    "xhr",
    "fetch",
    "eventsource",
    "websocket",
    "manifest",
    "other",
]


def _check_playwright_available() -> None:
    """Check if Playwright is installed and raise a clear error if not.

    Raises:
        PlaywrightNotInstalledError: If playwright is not installed
    """
    try:
        import playwright  # noqa: F401
    except ImportError as e:
        raise PlaywrightNotInstalledError() from e


def _check_markitdown_available() -> None:
    """Check if MarkItDown is installed and raise a clear error if not.

    Raises:
        ImportError: If markitdown is not installed
    """
    try:
        import markitdown  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "markitdown is not installed. Install it with:\n"
            "  pip install mixseek-plus[playwright]"
        ) from e


class PlaywrightConfig(BaseModel):
    """Playwright固有の設定.

    Attributes:
        headless: ヘッドレスモードで実行するか（デフォルト: True）
        timeout_ms: ページ読み込みタイムアウト（ミリ秒）（デフォルト: 30000）
        wait_for_load_state: 待機条件（デフォルト: "load"）
        retry_count: リトライ回数（デフォルト: 0）
        retry_delay_ms: リトライ遅延（ミリ秒）（デフォルト: 1000）
        block_resources: ブロックするリソースタイプ（デフォルト: None）
    """

    headless: bool = Field(default=True, description="ヘッドレスモードで実行")
    timeout_ms: int = Field(
        default=30000, ge=1000, le=300000, description="タイムアウト（ms）"
    )
    wait_for_load_state: WaitForLoadState = Field(
        default="load", description="待機条件"
    )
    retry_count: int = Field(default=0, ge=0, le=10, description="リトライ回数")
    retry_delay_ms: int = Field(
        default=1000, ge=100, le=60000, description="リトライ遅延（ms）"
    )
    block_resources: list[ResourceType] | None = Field(
        default=None, description="ブロックするリソース"
    )


@dataclass(frozen=True)
class FetchResult:
    """ページ取得結果.

    Attributes:
        content: 取得したMarkdownコンテンツ
        url: 最終的なURL（リダイレクト後）
        status: 成功/失敗
        error: エラーメッセージ（失敗時のみ）
        attempts: 試行回数
    """

    content: str
    url: str
    status: Literal["success", "error"]
    error: str | None = None
    attempts: int = 1

    @classmethod
    def success(cls, content: str, url: str, attempts: int = 1) -> FetchResult:
        """成功結果を作成.

        Args:
            content: 取得したMarkdownコンテンツ
            url: 最終的なURL
            attempts: 試行回数

        Returns:
            成功ステータスのFetchResult
        """
        return cls(content=content, url=url, status="success", attempts=attempts)

    @classmethod
    def failure(cls, url: str, error: str, attempts: int = 1) -> FetchResult:
        """失敗結果を作成.

        Args:
            url: 取得を試みたURL
            error: エラーメッセージ
            attempts: 試行回数

        Returns:
            エラーステータスのFetchResult
        """
        return cls(content="", url=url, status="error", error=error, attempts=attempts)


class BasePlaywrightAgent(BaseMemberAgent):
    """Base class for Playwright-based Member Agents.

    Provides common functionality:
    - Browser lifecycle management (lazy initialization)
    - Page fetching with configurable wait conditions
    - HTML to Markdown conversion using MarkItDown
    - Retry logic with exponential backoff
    - Resource blocking

    Subclasses must implement:
    - _get_agent(): Return the Pydantic AI agent instance
    - _create_deps(): Create dependencies for agent execution
    """

    _playwright: Playwright | None
    _browser: Browser | None
    _model: Model
    _playwright_config: PlaywrightConfig

    def __init__(self, config: MemberAgentConfig) -> None:
        """Initialize Base Playwright Agent.

        Args:
            config: Validated agent configuration

        Raises:
            PlaywrightNotInstalledError: If playwright is not installed
            ValueError: If model creation fails
        """
        # Check dependencies before initialization
        _check_playwright_available()
        _check_markitdown_available()

        super().__init__(config)

        # Initialize browser state (lazy initialization)
        self._playwright = None
        self._browser = None

        # Parse playwright settings from config
        playwright_dict = getattr(config, "playwright", None)
        if playwright_dict and isinstance(playwright_dict, dict):
            self._playwright_config = PlaywrightConfig(**playwright_dict)
        else:
            self._playwright_config = PlaywrightConfig()

        # Create model using mixseek-plus factory
        try:
            self._model = create_model(config.model)
        except ModelCreationError as e:
            raise ValueError(f"Model creation failed: {e}") from e

    @property
    def playwright_config(self) -> PlaywrightConfig:
        """Get Playwright configuration.

        Returns:
            PlaywrightConfig instance
        """
        return self._playwright_config

    async def _ensure_browser(self) -> Browser:
        """Ensure browser is initialized (lazy initialization).

        Returns:
            Initialized Browser instance

        Raises:
            PlaywrightNotInstalledError: If playwright is not available
            FetchError: If browser launch fails
        """
        if self._browser is None:
            from playwright.async_api import async_playwright

            playwright_instance = await async_playwright().start()
            try:
                browser = await playwright_instance.chromium.launch(
                    headless=self._playwright_config.headless
                )
            except Exception as e:
                # Clean up playwright instance on browser launch failure
                await playwright_instance.stop()

                # Provide context-specific guidance based on error type
                error_str = str(e).lower()
                if "executable doesn't exist" in error_str or "not found" in error_str:
                    guidance = (
                        "Ensure Chromium is installed: playwright install chromium"
                    )
                elif "permission" in error_str:
                    guidance = "Check file permissions for the browser executable"
                elif "memory" in error_str or "resource" in error_str:
                    guidance = (
                        "Insufficient system resources - try closing other applications"
                    )
                elif (
                    "display" in error_str
                    or "x11" in error_str
                    or "wayland" in error_str
                ):
                    guidance = (
                        "For headless mode, set headless=True in playwright config"
                    )
                else:
                    guidance = (
                        "Ensure Chromium is installed: playwright install chromium. "
                        "If installed, check system resources and permissions"
                    )

                raise FetchError(
                    message=f"Failed to launch browser: {e}. {guidance}",
                    url="",
                    cause=e,
                ) from e

            self._playwright = playwright_instance
            self._browser = browser
            logger.debug(
                "Browser launched (headless=%s)", self._playwright_config.headless
            )

        return self._browser

    async def close(self) -> None:
        """Release browser resources.

        Should be called when the agent is no longer needed.
        Safe to call multiple times.
        """
        if self._browser:
            await self._browser.close()
            self._browser = None
            logger.debug("Browser closed")

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
            logger.debug("Playwright stopped")

    async def _setup_resource_blocking(self, page: Page) -> None:
        """Set up resource blocking on a page.

        Args:
            page: Playwright Page instance
        """
        if not self._playwright_config.block_resources:
            return

        blocked_types = set(self._playwright_config.block_resources)

        async def block_handler(route: Route) -> None:
            if route.request.resource_type in blocked_types:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_handler)
        logger.debug("Resource blocking enabled for: %s", blocked_types)

    async def _fetch_page(self, url: str) -> tuple[str, str]:
        """Fetch a web page and return its HTML content and final URL.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (HTML content, final URL after redirects)

        Raises:
            FetchError: If page fetch fails
        """
        browser = await self._ensure_browser()
        context = await browser.new_context()

        try:
            page = await context.new_page()

            # Set up resource blocking if configured
            await self._setup_resource_blocking(page)

            # Navigate with timeout
            response = await page.goto(
                url,
                timeout=self._playwright_config.timeout_ms,
                wait_until=self._playwright_config.wait_for_load_state,
            )

            # Check response status
            if response and response.status >= 400:
                raise FetchError(
                    message=f"HTTP {response.status} error for {url}",
                    url=url,
                )

            # Get final URL (after redirects)
            final_url = page.url

            # Check content type for non-HTML responses (T030)
            content_type = ""
            if response:
                content_type = response.headers.get("content-type", "")
            if content_type and not any(
                ct in content_type.lower() for ct in ["text/html", "application/xhtml"]
            ):
                raise FetchError(
                    message=f"Non-HTML content type: {content_type}. "
                    f"This agent only supports HTML pages.",
                    url=url,
                )

            # Get HTML content
            html_content = await page.content()

            # Check for empty body (T029)
            body_content = await page.evaluate("document.body?.innerText || ''")
            if not body_content.strip():
                logger.warning("Page has empty body: %s", url)

            # Check for JavaScript error page (T027)
            # Common patterns for error pages
            error_indicators = await page.evaluate("""
                () => {
                    const body = document.body?.innerText || '';
                    const hasErrorInTitle = document.title.toLowerCase().includes('error');
                    const hasErrorInBody = /error|exception|failed/i.test(body.slice(0, 500));
                    return { hasErrorInTitle, hasErrorInBody };
                }
            """)
            if error_indicators.get("hasErrorInTitle") and error_indicators.get(
                "hasErrorInBody"
            ):
                logger.warning("Page may contain JavaScript errors: %s", url)

            # Log redirect if occurred (T028)
            if final_url != url:
                logger.info("Redirect detected: %s -> %s", url, final_url)

            logger.debug("Page fetched: %s -> %s", url, final_url)

            return html_content, final_url

        except Exception as e:
            if isinstance(e, FetchError):
                raise
            # Provide clearer timeout error message (T021)
            error_str = str(e).lower()
            if "timeout" in error_str:
                raise FetchError(
                    message=f"Page load timeout after {self._playwright_config.timeout_ms}ms for {url}. "
                    f"Try increasing timeout_ms or using a different wait_for_load_state.",
                    url=url,
                    cause=e,
                ) from e
            raise FetchError(
                message=f"Failed to fetch page: {e}",
                url=url,
                cause=e,
            ) from e
        finally:
            await context.close()

    def _convert_to_markdown(self, html: str, url: str) -> str:
        """Convert HTML content to Markdown using MarkItDown.

        Args:
            html: HTML content to convert
            url: Source URL (for error messages)

        Returns:
            Markdown formatted content

        Raises:
            ConversionError: If conversion fails
        """
        try:
            from markitdown import MarkItDown

            md = MarkItDown(enable_plugins=False)

            # MarkItDown expects a file-like object or path
            # Create an in-memory file-like object from HTML string
            html_buffer = io.BytesIO(html.encode("utf-8"))
            setattr(html_buffer, "name", "page.html")

            result = md.convert(html_buffer)
            text_content: str = result.text_content
            return text_content

        except Exception as e:
            raise ConversionError(
                message=f"Failed to convert HTML to Markdown: {e}",
                url=url,
                cause=e,
            ) from e

    async def _fetch_with_retry(self, url: str) -> FetchResult:
        """Fetch a page with retry logic and convert to Markdown.

        Uses exponential backoff: delay * 2^attempt

        Args:
            url: URL to fetch

        Returns:
            FetchResult with content or error information
        """
        last_error: Exception | None = None
        max_attempts = self._playwright_config.retry_count + 1

        for attempt in range(max_attempts):
            try:
                # Fetch HTML and final URL in a single request
                html, final_url = await self._fetch_page(url)

                # Convert to Markdown
                markdown = self._convert_to_markdown(html, url)

                return FetchResult.success(
                    content=markdown, url=final_url, attempts=attempt + 1
                )

            except (FetchError, ConversionError) as e:
                last_error = e
                logger.warning(
                    "Fetch attempt %d/%d failed for %s: %s",
                    attempt + 1,
                    max_attempts,
                    url,
                    e,
                )

                # Check if we should retry
                if attempt < self._playwright_config.retry_count:
                    # Only retry for potentially transient errors
                    if self._is_retryable_error(e):
                        delay = (
                            self._playwright_config.retry_delay_ms * (2**attempt) / 1000
                        )
                        logger.info("Retrying in %.1f seconds...", delay)
                        await asyncio.sleep(delay)
                    else:
                        # Non-retryable error, exit early
                        break

        # All attempts failed
        error_message = str(last_error) if last_error else "Unknown error"
        return FetchResult.failure(
            url=url,
            error=f"All {max_attempts} attempts failed: {error_message}",
            attempts=max_attempts,
        )

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable.

        Args:
            error: The exception to check

        Returns:
            True if the error is potentially transient and worth retrying
        """
        if isinstance(error, FetchError):
            error_str = str(error).lower()
            # Retry on server errors or network issues
            return any(
                indicator in error_str
                for indicator in [
                    "503",
                    "502",
                    "timeout",
                    "connection",
                    "network",
                    "temporary",
                ]
            )
        return False

    def _create_model_settings(self) -> ModelSettings:
        """Create ModelSettings from MemberAgentConfig.

        Returns:
            ModelSettings TypedDict with configured values
        """
        settings: ModelSettings = {}

        if self.config.temperature is not None:
            settings["temperature"] = self.config.temperature
        if self.config.max_tokens is not None:
            settings["max_tokens"] = self.config.max_tokens
        if self.config.stop_sequences is not None:
            settings["stop_sequences"] = self.config.stop_sequences
        if self.config.top_p is not None:
            settings["top_p"] = self.config.top_p
        if self.config.seed is not None:
            settings["seed"] = self.config.seed
        if self.config.timeout_seconds is not None:
            settings["timeout"] = float(self.config.timeout_seconds)

        return settings

    @abstractmethod
    def _get_agent(self) -> Agent[object, str]:
        """Get the Pydantic AI agent instance.

        Returns:
            The configured Pydantic AI agent
        """
        ...

    @abstractmethod
    def _create_deps(self) -> object:
        """Create dependencies for agent execution.

        Returns:
            Dependencies object appropriate for the agent type
        """
        ...

    async def execute(
        self,
        task: str,
        context: dict[str, object] | None = None,
        **kwargs: object,
    ) -> MemberAgentResult:
        """Execute task with Playwright agent.

        Args:
            task: User task or prompt to execute
            context: Optional context information
            **kwargs: Additional execution parameters

        Returns:
            MemberAgentResult with execution outcome
        """
        start_time = time.time()

        # Log execution start
        execution_id = self.logger.log_execution_start(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            task=task,
            model_id=self.config.model,
            context=context,
            **kwargs,
        )

        # Validate input
        if not task.strip():
            return MemberAgentResult.error(
                error_message="Task cannot be empty or contain only whitespace",
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                error_code="EMPTY_TASK",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        try:
            # Create dependencies (implemented by subclass)
            deps = self._create_deps()

            # Execute with Pydantic AI agent
            result = await self._get_agent().run(task, deps=deps, **kwargs)  # type: ignore[call-overload]

            # Capture complete message history
            all_messages = result.all_messages()

            execution_time_ms = int((time.time() - start_time) * 1000)

            # Extract usage information if available
            usage_info: UsageInfo = {}
            if hasattr(result, "usage"):
                usage = result.usage()
                usage_info = UsageInfo(
                    total_tokens=getattr(usage, "total_tokens", None),
                    prompt_tokens=getattr(usage, "prompt_tokens", None),
                    completion_tokens=getattr(usage, "completion_tokens", None),
                    requests=getattr(usage, "requests", None),
                )

            # Build metadata
            metadata: PlaywrightAgentMetadata = PlaywrightAgentMetadata(
                model_id=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                playwright_headless=self._playwright_config.headless,
            )
            if context:
                # Context values are compatible with the allowed types
                context_dict: dict[str, str | int | float | bool | None] = {}
                for k, v in context.items():
                    if isinstance(v, str | int | float | bool) or v is None:
                        context_dict[k] = v
                metadata["context"] = context_dict

            # Cast TypedDicts to dict[str, object] for API compatibility
            usage_dict = cast(dict[str, object], usage_info) if usage_info else None
            metadata_dict = cast(dict[str, object], metadata)

            result_obj = MemberAgentResult.success(
                content=str(result.output),
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                execution_time_ms=execution_time_ms,
                usage_info=usage_dict,
                metadata=metadata_dict,
                all_messages=all_messages,
            )

            # Log completion
            self.logger.log_execution_complete(
                execution_id=execution_id, result=result_obj, usage_info=usage_dict
            )

            return result_obj

        except Exception as e:
            return self._handle_execution_error(
                e, task, kwargs, execution_id, start_time
            )

    def _handle_execution_error(
        self,
        error: Exception,
        task: str,
        kwargs: dict[str, object],
        execution_id: str,
        start_time: float,
    ) -> MemberAgentResult:
        """Handle execution errors with proper logging and result creation.

        Args:
            error: The exception that was raised
            task: The task that was being executed
            kwargs: Additional execution parameters
            execution_id: The execution ID for logging
            start_time: When execution started

        Returns:
            MemberAgentResult with error information
        """
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Determine error code and message
        error_message = str(error)
        error_code = "EXECUTION_ERROR"

        if isinstance(error, FetchError):
            error_code = "FETCH_ERROR"
        elif isinstance(error, ConversionError):
            error_code = "CONVERSION_ERROR"
        elif isinstance(error, PlaywrightNotInstalledError):
            error_code = "PLAYWRIGHT_NOT_INSTALLED"

        error_context: dict[str, object] = {
            "task": task,
            "kwargs": kwargs,
            "error_type": type(error).__name__,
        }
        self.logger.log_error(
            execution_id=execution_id,
            error=error,
            context=error_context,
        )

        result_obj = MemberAgentResult.error(
            error_message=error_message,
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            error_code=error_code,
            execution_time_ms=execution_time_ms,
        )

        self.logger.log_execution_complete(execution_id=execution_id, result=result_obj)
        return result_obj
