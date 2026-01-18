"""Unit tests for Leader-Member tool warning functionality (Issue #19).

Tests cover:
- LMW-010: Warning when Leader has members but calls none
- LMW-011: No warning when Leader calls member tools
- LMW-012: No warning when team has no members
- LMW-020: AggregationStore patch is applied
- LMW-021: Warning message contains helpful information
"""

import logging
from pathlib import Path

import pytest


class TestCheckMemberToolUsage:
    """Tests for check_member_tool_usage function (LMW-010, LMW-011, LMW-012)."""

    def test_warn_when_leader_has_members_but_calls_none(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """LMW-010: Warning should be logged when Leader has members but calls none."""
        from mixseek_plus.core_patch import check_member_tool_usage

        # Simulate: team has members, but total_count == 0
        team_has_members = True
        member_submissions_total_count = 0

        with caplog.at_level(logging.WARNING):
            check_member_tool_usage(
                team_has_members=team_has_members,
                member_submissions_total_count=member_submissions_total_count,
                team_id="test-team",
            )

        # Verify warning was logged
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelno == logging.WARNING
        assert "Leader did not call any member tools" in record.message
        assert "test-team" in record.message

    def test_no_warn_when_leader_calls_member_tools(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """LMW-011: No warning when Leader actually calls member tools."""
        from mixseek_plus.core_patch import check_member_tool_usage

        # Simulate: team has members, and total_count > 0
        team_has_members = True
        member_submissions_total_count = 3

        with caplog.at_level(logging.WARNING):
            check_member_tool_usage(
                team_has_members=team_has_members,
                member_submissions_total_count=member_submissions_total_count,
                team_id="test-team",
            )

        # Verify no warning was logged
        assert len(caplog.records) == 0

    def test_no_warn_when_team_has_no_members(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """LMW-012: No warning when team has no members configured."""
        from mixseek_plus.core_patch import check_member_tool_usage

        # Simulate: team has no members
        team_has_members = False
        member_submissions_total_count = 0

        with caplog.at_level(logging.WARNING):
            check_member_tool_usage(
                team_has_members=team_has_members,
                member_submissions_total_count=member_submissions_total_count,
                team_id="test-team",
            )

        # Verify no warning was logged
        assert len(caplog.records) == 0


class TestWarningMessage:
    """Tests for warning message content (LMW-021)."""

    def test_warning_message_contains_helpful_info(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """LMW-021: Warning message should contain helpful diagnostic information."""
        from mixseek_plus.core_patch import check_member_tool_usage

        with caplog.at_level(logging.WARNING):
            check_member_tool_usage(
                team_has_members=True,
                member_submissions_total_count=0,
                team_id="my-claudecode-team",
            )

        assert len(caplog.records) == 1
        message = caplog.records[0].message

        # Should mention what happened
        assert "Leader did not call any member tools" in message

        # Should mention the team
        assert "my-claudecode-team" in message

        # Should suggest the cause
        assert "function_tools" in message


class TestAggregationStorePatch:
    """Tests for AggregationStore patch application (LMW-020)."""

    def test_aggregation_store_patch_is_applied_by_patch_core(self) -> None:
        """LMW-020: patch_core() should apply AggregationStore patch."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_EXECUTE_SINGLE_ROUND = None

        # Apply patch
        core_patch.patch_core()

        # Verify AggregationStore patch was applied
        assert core_patch._ORIGINAL_EXECUTE_SINGLE_ROUND is not None

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
        core_patch._ORIGINAL_EXECUTE_SINGLE_ROUND = None
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
        core_patch._ORIGINAL_EXECUTE_SINGLE_ROUND = None
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


class TestResetPatch:
    """Tests for reset_round_controller_patch function."""

    def test_reset_round_controller_patch(self) -> None:
        """reset_round_controller_patch should restore original function."""
        from mixseek_plus import core_patch

        # Reset patch state
        core_patch._PATCH_APPLIED = False
        core_patch._ORIGINAL_EXECUTE_SINGLE_ROUND = None

        # Apply patch
        core_patch.patch_core()

        # Verify patch was applied
        assert core_patch._ORIGINAL_EXECUTE_SINGLE_ROUND is not None

        # Reset
        core_patch.reset_round_controller_patch()

        # Verify reset
        assert core_patch._ORIGINAL_EXECUTE_SINGLE_ROUND is None
