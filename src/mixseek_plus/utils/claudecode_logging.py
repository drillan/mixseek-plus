"""ClaudeCode logging utilities.

This module provides utilities for extracting and logging tool calls
from pydantic-ai message history.
"""

from __future__ import annotations

from typing import TypedDict

from pydantic_ai.messages import ModelMessage, ToolCallPart, ToolReturnPart


class ExtractedToolCall(TypedDict):
    """Extracted tool call information from message history."""

    tool_name: str
    args_summary: str
    tool_call_id: str | None
    status: str  # "success", "error", or "unknown"
    result_summary: str | None


class ClaudeCodeToolCallExtractor:
    """Extract tool calls from pydantic-ai message history.

    This class extracts ToolCallPart and ToolReturnPart from pydantic-ai
    messages and matches them to create a summary of tool invocations.
    """

    def __init__(
        self, args_max_length: int = 100, result_max_length: int = 200
    ) -> None:
        """Initialize extractor with truncation limits.

        Args:
            args_max_length: Maximum length for args summary (default 100)
            result_max_length: Maximum length for result summary (default 200)
        """
        self._args_max_length = args_max_length
        self._result_max_length = result_max_length

    def extract_tool_calls(
        self, messages: list[ModelMessage]
    ) -> list[ExtractedToolCall]:
        """Extract tool calls from message history.

        Args:
            messages: List of pydantic-ai ModelMessage objects

        Returns:
            List of ExtractedToolCall dictionaries with tool call info
        """
        tool_calls: dict[str, ExtractedToolCall] = {}
        tool_returns: dict[str, ToolReturnPart] = {}

        # First pass: collect all tool calls and returns
        for message in messages:
            if not hasattr(message, "parts"):
                continue

            for part in message.parts:
                if isinstance(part, ToolCallPart):
                    tool_call_id = part.tool_call_id
                    if tool_call_id:
                        tool_calls[tool_call_id] = ExtractedToolCall(
                            tool_name=part.tool_name,
                            args_summary=self._summarize_args(part.args),
                            tool_call_id=tool_call_id,
                            status="unknown",
                            result_summary=None,
                        )
                elif isinstance(part, ToolReturnPart):
                    tool_call_id = part.tool_call_id
                    if tool_call_id:
                        tool_returns[tool_call_id] = part

        # Second pass: match returns to calls
        for tool_call_id, extracted in tool_calls.items():
            if tool_call_id in tool_returns:
                return_part = tool_returns[tool_call_id]
                content = str(return_part.content)
                extracted["result_summary"] = self._summarize_result(content)
                extracted["status"] = "success"

        return list(tool_calls.values())

    def _summarize_args(self, args: dict[str, object] | object) -> str:
        """Summarize tool arguments with truncation.

        Args:
            args: Tool arguments dictionary or other object

        Returns:
            Summarized string representation (max 100 chars)
        """
        if isinstance(args, dict):
            parts = []
            for k, v in args.items():
                v_str = str(v)
                if len(v_str) > 50:
                    v_str = v_str[:47] + "..."
                parts.append(f"{k}={v_str}")
            summary = ", ".join(parts)
        else:
            summary = str(args)

        if len(summary) > self._args_max_length:
            return summary[: self._args_max_length - 3] + "..."
        return summary

    def _summarize_result(self, result: str) -> str:
        """Summarize tool result with truncation.

        Args:
            result: Tool result string

        Returns:
            Summarized string (max 200 chars)
        """
        if len(result) > self._result_max_length:
            return result[: self._result_max_length - 3] + "..."
        return result
