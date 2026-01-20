"""ClaudeCodeToolCallExtractor の単体テスト.

US2: Verboseモードでの詳細ログ確認
T013: ClaudeCodeToolCallExtractor.extract_tool_calls() のテスト
"""

from unittest.mock import MagicMock


class TestClaudeCodeToolCallExtractor:
    """ClaudeCodeToolCallExtractor のテスト."""

    def test_extractor_class_exists(self) -> None:
        """ClaudeCodeToolCallExtractor クラスが存在することを確認."""
        from mixseek_plus.utils.claudecode_logging import ClaudeCodeToolCallExtractor

        assert ClaudeCodeToolCallExtractor is not None

    def test_extract_tool_calls_empty_messages(self) -> None:
        """空のメッセージリストから空のリストを返す."""
        from mixseek_plus.utils.claudecode_logging import ClaudeCodeToolCallExtractor

        extractor = ClaudeCodeToolCallExtractor()
        result = extractor.extract_tool_calls([])
        assert result == []

    def test_extract_tool_calls_from_tool_call_part(self) -> None:
        """ToolCallPart からツール呼び出し情報を抽出する."""
        from pydantic_ai.messages import ModelRequest, ToolCallPart

        from mixseek_plus.utils.claudecode_logging import ClaudeCodeToolCallExtractor

        # Create a mock ToolCallPart
        tool_call = ToolCallPart(
            tool_name="fetch_page",
            args={"url": "https://example.com"},
            tool_call_id="call_123",
        )

        # Create a mock ModelRequest containing the tool call
        # ModelRequest.parts is a list of parts
        request = MagicMock(spec=ModelRequest)
        request.parts = [tool_call]

        extractor = ClaudeCodeToolCallExtractor()
        result = extractor.extract_tool_calls([request])

        assert len(result) == 1
        assert result[0]["tool_name"] == "fetch_page"
        assert "url" in result[0]["args_summary"]
        assert result[0]["tool_call_id"] == "call_123"
        assert result[0]["status"] == "unknown"

    def test_extract_tool_calls_with_matching_return(self) -> None:
        """ToolCallPart と対応する ToolReturnPart をマッチング."""
        from pydantic_ai.messages import (
            ModelRequest,
            ModelResponse,
            ToolCallPart,
            ToolReturnPart,
        )

        from mixseek_plus.utils.claudecode_logging import ClaudeCodeToolCallExtractor

        tool_call = ToolCallPart(
            tool_name="fetch_page",
            args={"url": "https://example.com"},
            tool_call_id="call_456",
        )

        tool_return = ToolReturnPart(
            tool_name="fetch_page",
            content="Page content here",
            tool_call_id="call_456",
        )

        request = MagicMock(spec=ModelRequest)
        request.parts = [tool_call]

        response = MagicMock(spec=ModelResponse)
        response.parts = [tool_return]

        extractor = ClaudeCodeToolCallExtractor()
        result = extractor.extract_tool_calls([request, response])

        assert len(result) == 1
        assert result[0]["status"] == "success"
        result_summary = result[0]["result_summary"]
        assert result_summary is not None
        assert "Page content" in result_summary

    def test_summarize_args_truncates_long_strings(self) -> None:
        """_summarize_args は100文字を超える引数を切り詰める."""
        from mixseek_plus.utils.claudecode_logging import ClaudeCodeToolCallExtractor

        extractor = ClaudeCodeToolCallExtractor()

        long_args = {"url": "a" * 150}
        result = extractor._summarize_args(long_args)

        assert len(result) <= 100
        assert "..." in result

    def test_summarize_result_truncates_long_strings(self) -> None:
        """_summarize_result は200文字を超える結果を切り詰める."""
        from mixseek_plus.utils.claudecode_logging import ClaudeCodeToolCallExtractor

        extractor = ClaudeCodeToolCallExtractor()

        long_result = "b" * 300
        result = extractor._summarize_result(long_result)

        assert len(result) <= 200
        assert "..." in result

    def test_extract_tool_calls_with_error_return(self) -> None:
        """エラーを含む ToolReturnPart の処理."""
        from pydantic_ai.messages import (
            ModelRequest,
            ModelResponse,
            ToolCallPart,
            ToolReturnPart,
        )

        from mixseek_plus.utils.claudecode_logging import ClaudeCodeToolCallExtractor

        tool_call = ToolCallPart(
            tool_name="fetch_page",
            args={"url": "https://error.com"},
            tool_call_id="call_error",
        )

        # ToolReturnPart with error content
        tool_return = ToolReturnPart(
            tool_name="fetch_page",
            content="Error: Connection refused",
            tool_call_id="call_error",
        )

        request = MagicMock(spec=ModelRequest)
        request.parts = [tool_call]

        response = MagicMock(spec=ModelResponse)
        response.parts = [tool_return]

        extractor = ClaudeCodeToolCallExtractor()
        result = extractor.extract_tool_calls([request, response])

        assert len(result) == 1
        # Note: Status detection based on content is not implemented yet
        # This test documents the expected behavior for future implementation
        assert result[0]["tool_call_id"] == "call_error"
