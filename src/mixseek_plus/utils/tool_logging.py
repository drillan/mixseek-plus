"""Pydantic AI tool logging utilities.

This module provides utilities for extracting and logging tool calls
from pydantic-ai message history.
"""

from __future__ import annotations

from typing import TypedDict

from pydantic_ai.messages import ModelMessage, ToolCallPart, ToolReturnPart

from mixseek_plus.utils.constants import (
    ARGS_SUMMARY_DEFAULT_MAX_LENGTH,
    PARAM_VALUE_MAX_LENGTH,
    RESULT_SUMMARY_DEFAULT_MAX_LENGTH,
    TRUNCATION_SUFFIX_LENGTH,
)
from mixseek_plus.utils.verbose import ToolStatus


class ExtractedToolCall(TypedDict):
    """Extracted tool call information from message history."""

    tool_name: str
    args_summary: str
    tool_call_id: str | None
    status: ToolStatus
    result_summary: str | None


class PydanticAIToolCallExtractor:
    """Extract tool calls from pydantic-ai message history.

    This class extracts ToolCallPart and ToolReturnPart from pydantic-ai
    messages and matches them to create a summary of tool invocations.
    Works with all pydantic-ai based agents (Groq, ClaudeCode, Playwright, etc.).
    """

    def __init__(
        self,
        args_max_length: int = ARGS_SUMMARY_DEFAULT_MAX_LENGTH,
        result_max_length: int = RESULT_SUMMARY_DEFAULT_MAX_LENGTH,
    ) -> None:
        """Initialize extractor with truncation limits.

        Args:
            args_max_length: Maximum length for args summary
            result_max_length: Maximum length for result summary
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
            Summarized string representation
        """
        if isinstance(args, dict):
            parts = []
            for k, v in args.items():
                v_str = str(v)
                truncate_at = PARAM_VALUE_MAX_LENGTH - TRUNCATION_SUFFIX_LENGTH
                if len(v_str) > PARAM_VALUE_MAX_LENGTH:
                    v_str = v_str[:truncate_at] + "..."
                parts.append(f"{k}={v_str}")
            summary = ", ".join(parts)
        else:
            summary = str(args)

        if len(summary) > self._args_max_length:
            truncate_at = self._args_max_length - TRUNCATION_SUFFIX_LENGTH
            return summary[:truncate_at] + "..."
        return summary

    def _summarize_result(self, result: str) -> str:
        """Summarize tool result with truncation.

        Args:
            result: Tool result string

        Returns:
            Summarized string
        """
        if len(result) > self._result_max_length:
            truncate_at = self._result_max_length - TRUNCATION_SUFFIX_LENGTH
            return result[:truncate_at] + "..."
        return result


# Backward compatibility alias (deprecated, use PydanticAIToolCallExtractor)
ClaudeCodeToolCallExtractor = PydanticAIToolCallExtractor
