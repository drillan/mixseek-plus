"""TavilyAPIClient - Tavily公式APIのラッパークラス.

このモジュールはTavily APIとの通信を担当し、
リトライロジックとエラーハンドリングを提供します。
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from collections.abc import Awaitable, Callable
from typing import Any

from httpx import HTTPStatusError
from pydantic import BaseModel, Field
from tavily import AsyncTavilyClient  # type: ignore[import-untyped]

from mixseek_plus.errors import TavilyAPIError

logger = logging.getLogger(__name__)


# Pydantic Models for API responses


class TavilySearchResultItem(BaseModel):
    """単一の検索結果アイテム."""

    title: str = Field(..., description="検索結果のタイトル")
    url: str = Field(..., description="検索結果のURL")
    content: str = Field(..., description="コンテンツの概要")
    score: float = Field(..., description="関連度スコア (0.0-1.0)")
    raw_content: str | None = Field(
        default=None, description="生HTMLコンテンツ (include_raw_content=True時)"
    )


class TavilySearchResult(BaseModel):
    """Web検索結果全体."""

    query: str = Field(..., description="検索クエリ")
    answer: str | None = Field(
        default=None, description="AI生成回答 (include_answer=True時)"
    )
    results: list[TavilySearchResultItem] = Field(
        default_factory=list, description="検索結果リスト"
    )
    images: list[str] | None = Field(
        default=None, description="画像URL群 (include_images=True時)"
    )
    response_time: float = Field(..., description="API応答時間（秒）")


class TavilyExtractResultItem(BaseModel):
    """単一のURL抽出結果."""

    url: str = Field(..., description="抽出元URL")
    raw_content: str = Field(..., description="抽出されたコンテンツ")


class TavilyExtractFailedItem(BaseModel):
    """抽出失敗アイテム."""

    url: str = Field(..., description="失敗したURL")
    error: str = Field(..., description="エラーメッセージ")


class TavilyExtractResult(BaseModel):
    """URL抽出結果全体."""

    results: list[TavilyExtractResultItem] = Field(
        default_factory=list, description="成功した抽出結果"
    )
    failed_results: list[TavilyExtractFailedItem] = Field(
        default_factory=list, description="失敗した抽出結果"
    )
    response_time: float = Field(..., description="API応答時間（秒）")


@dataclass
class TavilyAPIClient:
    """Tavily公式APIとの通信を担当するラッパークラス.

    Attributes:
        api_key: Tavily APIキー
        timeout: リクエストタイムアウト（秒）
        max_retries: 最大リトライ回数
        base_delay: 初回リトライ待機時間（秒）
        max_delay: 最大待機時間（秒）
    """

    api_key: str
    timeout: float = 30.0
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 10.0

    _client: AsyncTavilyClient = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the underlying Tavily client."""
        # Client is created lazily via _get_client() for better testability
        pass

    def _get_client(self) -> AsyncTavilyClient:
        """Get or create the AsyncTavilyClient instance.

        Returns:
            AsyncTavilyClient instance
        """
        if not hasattr(self, "_client") or self._client is None:
            self._client = AsyncTavilyClient(api_key=self.api_key)
        return self._client

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate delay for retry using exponential backoff.

        Args:
            retry_count: Current retry attempt number (0-indexed)

        Returns:
            Delay in seconds, capped at max_delay
        """
        delay = self.base_delay * (2**retry_count)
        return float(min(delay, self.max_delay))

    def _is_retryable_status(self, status_code: int) -> bool:
        """Check if HTTP status code is retryable.

        Args:
            status_code: HTTP status code

        Returns:
            True if the error is retryable
        """
        return status_code in (429, 500, 502, 503, 504)

    def _handle_http_error(
        self, error: HTTPStatusError, retry_count: int
    ) -> TavilyAPIError:
        """Convert HTTP error to TavilyAPIError.

        Args:
            error: The HTTP status error
            retry_count: Number of retries attempted

        Returns:
            TavilyAPIError with appropriate error type
        """
        status_code = error.response.status_code

        if status_code == 401:
            return TavilyAPIError(
                message="Tavily API認証に失敗しました。APIキーを確認してください。",
                status_code=status_code,
                error_type="AUTH_ERROR",
            )
        elif status_code == 400:
            return TavilyAPIError(
                message=f"Tavily APIバリデーションエラー: {error}",
                status_code=status_code,
                error_type="VALIDATION_ERROR",
            )
        elif status_code == 429:
            return TavilyAPIError(
                message="Tavily APIレート制限に達しました。しばらく待ってから再試行してください。",
                status_code=status_code,
                error_type="RATE_LIMIT_ERROR",
            )
        elif status_code in (500, 502, 504):
            return TavilyAPIError(
                message=f"Tavily APIサーバーエラー (HTTP {status_code})",
                status_code=status_code,
                error_type="SERVER_ERROR",
            )
        elif status_code == 503:
            return TavilyAPIError(
                message="Tavily APIサービスが一時的に利用できません。",
                status_code=status_code,
                error_type="SERVICE_UNAVAILABLE",
            )
        else:
            return TavilyAPIError(
                message=f"Tavily APIエラー (HTTP {status_code}): {error}",
                status_code=status_code,
                error_type="API_ERROR",
            )

    async def _execute_with_retry[T](
        self,
        operation: str,
        func: Callable[..., Awaitable[T]],
        **kwargs: object,
    ) -> T:
        """Execute an async function with retry logic.

        Args:
            operation: Name of the operation (for logging)
            func: Async function to execute
            **kwargs: Arguments to pass to the function

        Returns:
            Result from the function

        Raises:
            TavilyAPIError: If all retries fail
        """
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                return await func(**kwargs)
            except HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code

                if not self._is_retryable_status(status_code):
                    raise self._handle_http_error(e, attempt)

                if attempt < self.max_retries - 1:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "Tavily %s failed (HTTP %s), retrying in %.1fs (attempt %d/%d)",
                        operation,
                        status_code,
                        delay,
                        attempt + 1,
                        self.max_retries,
                    )
                    await asyncio.sleep(delay)
                else:
                    raise self._handle_http_error(e, attempt)

            except asyncio.TimeoutError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self._calculate_retry_delay(attempt)
                    logger.warning(
                        "Tavily %s timed out, retrying in %.1fs (attempt %d/%d)",
                        operation,
                        delay,
                        attempt + 1,
                        self.max_retries,
                    )
                    await asyncio.sleep(delay)
                else:
                    raise TavilyAPIError(
                        message="Tavily APIリクエストがタイムアウトしました。",
                        status_code=None,
                        error_type="TIMEOUT_ERROR",
                    )

        # This should not be reached, but just in case
        raise TavilyAPIError(
            message=f"Tavily {operation}がすべてのリトライで失敗しました: {last_error}",
            status_code=None,
            error_type="RETRY_EXHAUSTED",
        )

    async def search(
        self,
        query: str,
        *,
        search_depth: str = "basic",
        max_results: int = 5,
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
    ) -> TavilySearchResult:
        """Web検索を実行.

        Args:
            query: 検索クエリ
            search_depth: 検索詳細度 ("basic" または "advanced")
            max_results: 結果数 (1-20)
            include_answer: AI生成回答を含める
            include_raw_content: 生HTMLを含める
            include_images: 画像URLを含める
            include_domains: 対象ドメイン制限
            exclude_domains: 除外ドメイン

        Returns:
            TavilySearchResult with search results

        Raises:
            TavilyAPIError: API呼び出しエラー
        """
        client = self._get_client()

        kwargs: dict[str, object] = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content,
            "include_images": include_images,
        }

        if include_domains is not None:
            kwargs["include_domains"] = include_domains
        if exclude_domains is not None:
            kwargs["exclude_domains"] = exclude_domains

        result: dict[str, Any] = await self._execute_with_retry(
            "search", client.search, **kwargs
        )

        # Convert dict response to Pydantic model
        result_dict: dict[str, Any] = dict(result)

        # Parse results
        results = [
            TavilySearchResultItem(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=item.get("content", ""),
                score=item.get("score", 0.0),
                raw_content=item.get("raw_content"),
            )
            for item in result_dict.get("results", [])
        ]

        return TavilySearchResult(
            query=result_dict.get("query", query),
            answer=result_dict.get("answer"),
            results=results,
            images=result_dict.get("images"),
            response_time=result_dict.get("response_time", 0.0),
        )

    async def extract(
        self,
        urls: list[str],
    ) -> TavilyExtractResult:
        """URL群からコンテンツを抽出.

        Args:
            urls: 抽出対象URL群

        Returns:
            TavilyExtractResult with extraction results

        Raises:
            TavilyAPIError: API呼び出しエラー
        """
        client = self._get_client()

        result: dict[str, Any] = await self._execute_with_retry(
            "extract", client.extract, urls=urls
        )

        # Convert dict response to Pydantic model
        result_dict: dict[str, Any] = dict(result)

        # Parse results
        results = [
            TavilyExtractResultItem(
                url=item.get("url", ""),
                raw_content=item.get("raw_content", ""),
            )
            for item in result_dict.get("results", [])
        ]

        failed_results = [
            TavilyExtractFailedItem(
                url=item.get("url", ""),
                error=item.get("error", "Unknown error"),
            )
            for item in result_dict.get("failed_results", [])
        ]

        return TavilyExtractResult(
            results=results,
            failed_results=failed_results,
            response_time=result_dict.get("response_time", 0.0),
        )

    async def get_search_context(
        self,
        query: str,
        *,
        search_depth: str = "basic",
        max_results: int = 5,
        max_tokens: int | None = None,
    ) -> str:
        """RAG用検索コンテキストを取得.

        Args:
            query: 検索クエリ
            search_depth: 検索詳細度 ("basic" または "advanced")
            max_results: 検索結果数
            max_tokens: 最大トークン数

        Returns:
            RAG用に最適化されたコンテキスト文字列

        Raises:
            TavilyAPIError: API呼び出しエラー
        """
        client = self._get_client()

        kwargs: dict[str, object] = {
            "query": query,
            "search_depth": search_depth,
            "max_results": max_results,
        }

        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens

        result = await self._execute_with_retry(
            "get_search_context", client.get_search_context, **kwargs
        )

        return str(result)
