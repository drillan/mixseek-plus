"""TavilyToolsRepositoryMixin - Tavilyツールを提供するMixin.

このモジュールはエージェントにTavilyツール（search, extract, context）を
登録するMixinを提供します。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Protocol

from pydantic_ai import Agent, RunContext

from mixseek_plus.errors import TavilyAPIError
from mixseek_plus.providers.tavily_client import (
    TavilyAPIClient,
    TavilyExtractResult,
    TavilySearchResult,
)
from mixseek_plus.utils.verbose import (
    ToolStatus,
    log_verbose_tool_done,
    log_verbose_tool_start,
)

if TYPE_CHECKING:
    from mixseek.models.member_agent import MemberAgentConfig
    from mixseek.utils.logging import MemberAgentLogger


logger = logging.getLogger(__name__)


@dataclass
class TavilySearchDeps:
    """Tavily検索エージェント用依存性."""

    config: MemberAgentConfig
    tavily_client: TavilyAPIClient


class TavilyAgentProtocol(Protocol):
    """TavilyToolsRepositoryMixinが期待するエージェントインターフェース."""

    @property
    def logger(self) -> MemberAgentLogger:
        """Logger instance for execution logging."""
        ...

    def _get_agent(self) -> Agent[TavilySearchDeps, str]:
        """Get the Pydantic AI agent instance."""
        ...


class TavilyToolsRepositoryMixin:
    """エージェントにTavilyツールを登録するMixin.

    このMixinは3つのTavilyツールをpydantic-aiエージェントに登録します:
    - tavily_search: Web検索
    - tavily_extract: URL群からコンテンツ抽出
    - tavily_context: RAG用検索コンテキスト取得

    使用方法:
        class MyAgent(TavilyToolsRepositoryMixin, BaseGroqAgent):
            def __init__(self, config):
                super().__init__(config)
                self._tavily_client = self._create_tavily_client()
                self._register_tavily_tools()
    """

    # Maximum number of URLs allowed per extract call (NFR-004a)
    MAX_EXTRACT_URLS: int = 20

    def _register_tavily_tools(
        self: TavilyAgentProtocol,
    ) -> list[Callable[..., Any]]:
        """Tavilyツールをエージェントに登録し、登録したツール関数のリストを返す.

        Returns:
            登録したツール関数のリスト
        """
        agent = self._get_agent()
        tools: list[Callable[..., Any]] = []

        mixin_self = self

        @agent.tool
        async def tavily_search(
            ctx: RunContext[TavilySearchDeps],
            query: str,
            search_depth: str = "basic",
            max_results: int = 5,
        ) -> str:
            """Web検索を実行する.

            Args:
                ctx: 実行コンテキスト（依存性注入）
                query: 検索クエリ
                search_depth: 検索詳細度 ("basic" または "advanced")
                max_results: 結果数 (1-20)

            Returns:
                検索結果をフォーマットした文字列
            """
            log_verbose_tool_start("tavily_search", {"query": query})
            start_time = time.perf_counter()
            status: ToolStatus = "success"
            result_str = ""

            try:
                result = await ctx.deps.tavily_client.search(
                    query=query,
                    search_depth=search_depth,
                    max_results=max_results,
                )
                result_str = str(mixin_self.format_search_result(result))  # type: ignore[attr-defined]
                return result_str  # noqa: TRY300
            except TavilyAPIError as e:
                status = "error"
                logger.error(
                    "tavily_search failed: %s (error_type=%s, status_code=%s)",
                    e.message,
                    e.error_type,
                    e.status_code,
                )
                return mixin_self.format_error_message(e)  # type: ignore[attr-defined, no-any-return]
            finally:
                execution_time_ms = int((time.perf_counter() - start_time) * 1000)
                try:
                    log_verbose_tool_done(
                        "tavily_search",
                        status,
                        execution_time_ms,
                        result_preview=result_str[:200] if result_str else None,
                    )
                except Exception as log_error:
                    logger.debug("Failed to log tool completion: %s", log_error)

        @agent.tool
        async def tavily_extract(
            ctx: RunContext[TavilySearchDeps],
            urls: list[str],
        ) -> str:
            """URL群からコンテンツを抽出する.

            Args:
                ctx: 実行コンテキスト（依存性注入）
                urls: 抽出対象URL群

            Returns:
                抽出結果をフォーマットした文字列
            """
            log_verbose_tool_start("tavily_extract", {"urls": urls})
            start_time = time.perf_counter()
            status: ToolStatus = "success"
            result_str = ""

            try:
                # Validate URLs
                validated_urls = mixin_self.validate_extract_urls(urls)  # type: ignore[attr-defined]

                result = await ctx.deps.tavily_client.extract(urls=validated_urls)
                result_str = str(mixin_self.format_extract_result(result))  # type: ignore[attr-defined]
                return result_str  # noqa: TRY300
            except TavilyAPIError as e:
                status = "error"
                logger.error(
                    "tavily_extract failed: %s (error_type=%s, status_code=%s)",
                    e.message,
                    e.error_type,
                    e.status_code,
                )
                return mixin_self.format_error_message(e)  # type: ignore[attr-defined, no-any-return]
            finally:
                execution_time_ms = int((time.perf_counter() - start_time) * 1000)
                try:
                    log_verbose_tool_done(
                        "tavily_extract",
                        status,
                        execution_time_ms,
                        result_preview=result_str[:200] if result_str else None,
                    )
                except Exception as log_error:
                    logger.debug("Failed to log tool completion: %s", log_error)

        @agent.tool
        async def tavily_context(
            ctx: RunContext[TavilySearchDeps],
            query: str,
            max_tokens: int | None = None,
        ) -> str:
            """RAG用検索コンテキストを取得する.

            Args:
                ctx: 実行コンテキスト（依存性注入）
                query: 検索クエリ
                max_tokens: 最大トークン数

            Returns:
                RAG用に最適化されたコンテキスト文字列
            """
            log_verbose_tool_start("tavily_context", {"query": query})
            start_time = time.perf_counter()
            status: ToolStatus = "success"
            result_str = ""

            try:
                result = await ctx.deps.tavily_client.get_search_context(
                    query=query,
                    max_tokens=max_tokens,
                )
                result_str = str(mixin_self.format_context_result(query, result))  # type: ignore[attr-defined]
                return result_str  # noqa: TRY300
            except TavilyAPIError as e:
                status = "error"
                logger.error(
                    "tavily_context failed: %s (error_type=%s, status_code=%s)",
                    e.message,
                    e.error_type,
                    e.status_code,
                )
                return mixin_self.format_error_message(e)  # type: ignore[attr-defined, no-any-return]
            finally:
                execution_time_ms = int((time.perf_counter() - start_time) * 1000)
                try:
                    log_verbose_tool_done(
                        "tavily_context",
                        status,
                        execution_time_ms,
                        result_preview=result_str[:200] if result_str else None,
                    )
                except Exception as log_error:
                    logger.debug("Failed to log tool completion: %s", log_error)

        tools.extend([tavily_search, tavily_extract, tavily_context])
        return tools

    def validate_extract_urls(self, urls: list[str]) -> list[str]:
        """URL群のバリデーションを行う.

        Args:
            urls: 検証するURL群

        Returns:
            検証済みURL群

        Raises:
            TavilyAPIError: バリデーションエラー
        """
        if not urls:
            raise TavilyAPIError(
                message="URL群が空です。少なくとも1つのURLを指定してください。",
                status_code=400,
                error_type="VALIDATION_ERROR",
            )

        if len(urls) > self.MAX_EXTRACT_URLS:
            logger.warning(
                "URL数が上限(%d)を超えています。最初の%d件のみ処理します。"
                " (指定: %d件)",
                self.MAX_EXTRACT_URLS,
                self.MAX_EXTRACT_URLS,
                len(urls),
            )
            urls = urls[: self.MAX_EXTRACT_URLS]

        # Remove duplicates while preserving order
        seen: set[str] = set()
        unique_urls: list[str] = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def format_search_result(self, result: TavilySearchResult) -> str:
        """検索結果をフォーマットする.

        Format per contracts/tavily-tools.md section 2.4.

        Args:
            result: TavilySearchResult

        Returns:
            フォーマットされた文字列
        """
        lines = [f"## 検索結果: {result.query}", ""]

        if not result.results:
            lines.append("検索結果が見つかりませんでした。")
            return "\n".join(lines)

        for i, item in enumerate(result.results, 1):
            lines.append(f"### {i}. {item.title}")
            lines.append(f"URL: {item.url}")
            lines.append(f"スコア: {item.score:.2f}")
            lines.append(item.content)
            lines.append("")

        return "\n".join(lines)

    def format_extract_result(self, result: TavilyExtractResult) -> str:
        """抽出結果をフォーマットする.

        Format per contracts/tavily-tools.md section 3.4.

        Args:
            result: TavilyExtractResult

        Returns:
            フォーマットされた文字列
        """
        lines = ["## コンテンツ抽出結果", ""]

        if not result.results and result.failed_results:
            lines.append("すべてのURLからコンテンツを抽出できませんでした。")
            lines.append("")

        for item in result.results:
            lines.append(f"### URL: {item.url}")
            lines.append(item.raw_content)
            lines.append("")
            lines.append("---")
            lines.append("")

        # Remove trailing separator if there are results
        if result.results:
            lines = lines[:-2]  # Remove last "---\n"

        if result.failed_results:
            lines.append("")
            lines.append("## 失敗したURL")
            for failed_item in result.failed_results:
                lines.append(f"- {failed_item.url}: {failed_item.error}")

        return "\n".join(lines)

    def format_context_result(self, query: str, context: str) -> str:
        """RAGコンテキスト結果をフォーマットする.

        Format per contracts/tavily-tools.md section 4.4.

        Args:
            query: 検索クエリ
            context: コンテキスト文字列

        Returns:
            フォーマットされた文字列
        """
        return f"## RAG用検索コンテキスト: {query}\n\n{context}"

    def format_error_message(self, error: TavilyAPIError) -> str:
        """エラーメッセージをフォーマットする.

        Format per contracts/tavily-tools.md section 5.3.

        Args:
            error: TavilyAPIError

        Returns:
            フォーマットされた文字列
        """
        return f"Tavily API エラー: {error.message}\nエラータイプ: {error.error_type}"
