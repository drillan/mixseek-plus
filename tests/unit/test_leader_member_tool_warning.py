"""Unit tests for Leader-Member tool warning functionality (Issue #19).

Tests cover:
- LMW-020: AggregationStore patch is applied
- LMW-021: Warning message contains helpful information
- LMW-022: Reset function restores original AggregationStore method
"""

import logging
from pathlib import Path

import pytest


class TestAggregationStorePatch:
    """Tests for AggregationStore patch application (LMW-020)."""

    def test_aggregation_store_patch_is_applied_by_patch_core(self) -> None:
        """LMW-020: patch_core() should apply AggregationStore patch."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_SAVE_AGGREGATION = None

        # Apply patch
        core_patch.patch_core()

        # Verify AggregationStore patch was applied
        assert core_patch._ORIGINAL_SAVE_AGGREGATION is not None

    @pytest.mark.asyncio
    async def test_patched_save_aggregation_logs_warning_on_zero_submissions(
        self, caplog: pytest.LogCaptureFixture, tmp_path: Path
    ) -> None:
        """LMW-020: Patched save_aggregation should log warning when total_count == 0."""
        from mixseek.agents.leader.models import MemberSubmissionsRecord
        from mixseek.storage.aggregation_store import AggregationStore

        from mixseek_plus import core_patch

        # Reset and apply patch
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_SAVE_AGGREGATION = None
        core_patch.patch_core()

        # Create a mock MemberSubmissionsRecord with zero submissions
        mock_record = MemberSubmissionsRecord(
            execution_id="test-exec-id",
            team_id="test-team-with-zero-calls",
            team_name="Test Team",
            round_number=1,
            submissions=[],  # Empty = total_count == 0
        )

        # Create AggregationStore with temporary database
        db_path = tmp_path / "test.db"
        store = AggregationStore(db_path=db_path)

        # Call patched save_aggregation
        with caplog.at_level(logging.WARNING):
            await store.save_aggregation(
                execution_id="test-exec-id",
                aggregated=mock_record,
                message_history=[],
            )

        # Verify warning was logged
        warning_messages = [
            r.message for r in caplog.records if r.levelno == logging.WARNING
        ]
        assert any(
            "Leader did not call any member tools" in msg for msg in warning_messages
        )
        assert any("test-team-with-zero-calls" in msg for msg in warning_messages)

    @pytest.mark.asyncio
    async def test_patched_save_aggregation_no_warning_on_nonzero_submissions(
        self, caplog: pytest.LogCaptureFixture, tmp_path: Path
    ) -> None:
        """LMW-020: Patched save_aggregation should NOT log warning when total_count > 0."""
        from mixseek.agents.leader.models import (
            MemberSubmission,
            MemberSubmissionsRecord,
        )
        from mixseek.storage.aggregation_store import AggregationStore
        from pydantic_ai import RunUsage

        from mixseek_plus import core_patch

        # Reset and apply patch
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_SAVE_AGGREGATION = None
        core_patch.patch_core()

        # Create a mock MemberSubmissionsRecord with submissions
        mock_submission = MemberSubmission(
            agent_name="test-agent",
            agent_type="test",
            content="Test response",
            status="SUCCESS",
            execution_time_ms=100,
            usage=RunUsage(input_tokens=10, output_tokens=20, requests=1),
        )
        mock_record = MemberSubmissionsRecord(
            execution_id="test-exec-id-2",
            team_id="test-team-with-calls",
            team_name="Test Team",
            round_number=1,
            submissions=[mock_submission],  # Non-empty = total_count > 0
        )

        # Create AggregationStore with temporary database
        db_path = tmp_path / "test2.db"
        store = AggregationStore(db_path=db_path)

        # Call patched save_aggregation
        with caplog.at_level(logging.WARNING):
            await store.save_aggregation(
                execution_id="test-exec-id-2",
                aggregated=mock_record,
                message_history=[],
            )

        # Verify no warning was logged about member tools
        warning_messages = [
            r.message for r in caplog.records if r.levelno == logging.WARNING
        ]
        assert not any(
            "Leader did not call any member tools" in msg for msg in warning_messages
        )


class TestWarningMessage:
    """Tests for warning message content (LMW-021)."""

    @pytest.mark.asyncio
    async def test_warning_message_contains_helpful_info(
        self, caplog: pytest.LogCaptureFixture, tmp_path: Path
    ) -> None:
        """LMW-021: Warning message should contain helpful diagnostic information."""
        from mixseek.agents.leader.models import MemberSubmissionsRecord
        from mixseek.storage.aggregation_store import AggregationStore

        from mixseek_plus import core_patch

        # Reset and apply patch
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_SAVE_AGGREGATION = None
        core_patch.patch_core()

        # Create a mock MemberSubmissionsRecord with zero submissions
        mock_record = MemberSubmissionsRecord(
            execution_id="test-exec-id",
            team_id="my-claudecode-team",
            team_name="Test Team",
            round_number=3,
            submissions=[],
        )

        # Create AggregationStore with temporary database
        db_path = tmp_path / "test.db"
        store = AggregationStore(db_path=db_path)

        # Call patched save_aggregation
        with caplog.at_level(logging.WARNING):
            await store.save_aggregation(
                execution_id="test-exec-id",
                aggregated=mock_record,
                message_history=[],
            )

        assert len([r for r in caplog.records if r.levelno == logging.WARNING]) >= 1
        message = next(
            r.message for r in caplog.records if r.levelno == logging.WARNING
        )

        # Should mention what happened
        assert "Leader did not call any member tools" in message

        # Should mention the team
        assert "my-claudecode-team" in message

        # Should mention round number
        assert "round=3" in message

        # Should suggest the cause
        assert "function_tools" in message


class TestResetPatch:
    """Tests for reset_aggregation_store_patch function (LMW-022)."""

    def test_reset_aggregation_store_patch(self) -> None:
        """LMW-022: reset_aggregation_store_patch should restore original function."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_SAVE_AGGREGATION = None

        # Apply patch
        core_patch.patch_core()

        # Verify patch was applied
        assert core_patch._ORIGINAL_SAVE_AGGREGATION is not None

        # Reset
        core_patch.reset_aggregation_store_patch()

        # Verify reset
        assert core_patch._ORIGINAL_SAVE_AGGREGATION is None

    def test_reset_restores_original_function_reference(self) -> None:
        """LMW-022: After reset, the stored original function should be restored to AggregationStore."""
        from mixseek.storage.aggregation_store import AggregationStore

        from mixseek_plus import core_patch

        # Reset patch state completely
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_SAVE_AGGREGATION = None

        # Store the function BEFORE patching (may already be patched from previous tests,
        # but this is what reset_aggregation_store_patch will restore to)
        before_patch_func = AggregationStore.save_aggregation

        # Apply patch
        core_patch.patch_core()

        # Capture what was saved as original
        saved_original = core_patch._ORIGINAL_SAVE_AGGREGATION
        assert saved_original is before_patch_func

        # Verify patched function is different
        after_patch_func = AggregationStore.save_aggregation
        assert after_patch_func is not before_patch_func
        assert after_patch_func.__name__ == "patched_save_aggregation"

        # Reset to restore original
        core_patch.reset_aggregation_store_patch()

        # Verify the function is restored
        after_reset_func = AggregationStore.save_aggregation
        assert after_reset_func is before_patch_func

        # Verify internal state was cleared
        assert core_patch._ORIGINAL_SAVE_AGGREGATION is None
