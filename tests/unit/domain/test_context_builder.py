"""Unit tests for ContextBuilder."""

import pytest
from lighthouse.domain.services.context_builder import ContextBuilder
from lighthouse.domain.models.execution import (
    ExecutionSession,
    ExecutionStatus,
    NodeExecutionRecord,
)
from datetime import datetime


@pytest.fixture
def context_builder():
    """Create a ContextBuilder instance."""
    return ContextBuilder()


@pytest.fixture
def sample_session():
    """Create a sample execution session with node records."""
    session = ExecutionSession(
        id="exec-123",
        workflow_id="workflow-1",
        workflow_name="Test Workflow",
        status=ExecutionStatus.RUNNING,
        triggered_by="node1",
    )

    # Add some node execution records
    record1 = NodeExecutionRecord(
        node_id="node1",
        node_name="Input",
        status=ExecutionStatus.COMPLETED,
        outputs={"data": {"name": "John", "age": 30}},
    )

    record2 = NodeExecutionRecord(
        node_id="node2",
        node_name="Calculator",
        status=ExecutionStatus.COMPLETED,
        outputs={"data": {"result": 42}},
    )

    record3 = NodeExecutionRecord(
        node_id="node3",
        node_name="Formatter",
        status=ExecutionStatus.PENDING,  # Not completed
        outputs={},
    )

    session.add_node_record(record1)
    session.add_node_record(record2)
    session.add_node_record(record3)

    return session


class TestBuildContext:
    """Tests for building context from execution sessions."""

    def test_build_context_from_completed_nodes(
        self, context_builder, sample_session
    ):
        """Test building context from completed nodes."""
        completed = ["node1", "node2"]

        context = context_builder.build_context(sample_session, completed)

        assert "Input" in context
        assert "Calculator" in context
        assert context["Input"] == {"data": {"name": "John", "age": 30}}
        assert context["Calculator"] == {"data": {"result": 42}}

    def test_build_context_empty_completed_list(
        self, context_builder, sample_session
    ):
        """Test building context with no completed nodes."""
        context = context_builder.build_context(sample_session, [])

        assert context == {}

    def test_build_context_skips_pending_nodes(
        self, context_builder, sample_session
    ):
        """Test that pending nodes are not included in context."""
        completed = ["node1", "node2", "node3"]

        context = context_builder.build_context(sample_session, completed)

        # node3 (Formatter) is pending, should not be in context
        assert "Formatter" not in context
        assert len(context) == 2

    def test_build_context_with_missing_records(self, context_builder):
        """Test building context when node records don't exist."""
        session = ExecutionSession(
            id="exec-123",
            workflow_id="workflow-1",
            workflow_name="Test",
            status=ExecutionStatus.RUNNING,
            triggered_by="node1",
        )

        context = context_builder.build_context(session, ["node1", "node2"])

        assert context == {}


class TestBuildFromOutputs:
    """Tests for building context from simple outputs dictionary."""

    def test_build_from_outputs_simple(self, context_builder):
        """Test building context from outputs dictionary."""
        outputs = {
            "Input": {"data": {"value": 123}},
            "Calculator": {"data": {"result": 456}},
        }

        context = context_builder.build_context_from_outputs(outputs)

        assert context == outputs
        # Verify it's a copy, not the same object
        assert context is not outputs

    def test_build_from_outputs_empty(self, context_builder):
        """Test building context from empty outputs."""
        context = context_builder.build_context_from_outputs({})

        assert context == {}


class TestUpdateContext:
    """Tests for updating context with new outputs."""

    def test_update_context_adds_new_node(self, context_builder):
        """Test updating context with a new node output."""
        context = {"Node1": {"data": {"value": 1}}}

        new_context = context_builder.update_context(
            context, "Node2", {"data": {"value": 2}}
        )

        assert "Node2" in new_context
        assert new_context["Node2"] == {"data": {"value": 2}}
        # Original context should be unchanged
        assert "Node2" not in context

    def test_update_context_overwrites_existing(self, context_builder):
        """Test that updating overwrites existing node."""
        context = {"Node1": {"data": {"value": 1}}}

        new_context = context_builder.update_context(
            context, "Node1", {"data": {"value": 99}}
        )

        assert new_context["Node1"] == {"data": {"value": 99}}
        # Original context should be unchanged
        assert context["Node1"] == {"data": {"value": 1}}


class TestMergeContexts:
    """Tests for merging multiple contexts."""

    def test_merge_two_contexts(self, context_builder):
        """Test merging two contexts."""
        ctx1 = {"Node1": {"data": {"value": 1}}}
        ctx2 = {"Node2": {"data": {"value": 2}}}

        merged = context_builder.merge_contexts(ctx1, ctx2)

        assert "Node1" in merged
        assert "Node2" in merged
        assert len(merged) == 2

    def test_merge_with_conflicts(self, context_builder):
        """Test that later contexts override earlier ones."""
        ctx1 = {"Node1": {"data": {"value": 1}}}
        ctx2 = {"Node1": {"data": {"value": 99}}}

        merged = context_builder.merge_contexts(ctx1, ctx2)

        # ctx2 should override ctx1
        assert merged["Node1"] == {"data": {"value": 99}}

    def test_merge_multiple_contexts(self, context_builder):
        """Test merging more than two contexts."""
        ctx1 = {"Node1": {"data": 1}}
        ctx2 = {"Node2": {"data": 2}}
        ctx3 = {"Node3": {"data": 3}}

        merged = context_builder.merge_contexts(ctx1, ctx2, ctx3)

        assert len(merged) == 3
        assert all(f"Node{i}" in merged for i in range(1, 4))

    def test_merge_empty_contexts(self, context_builder):
        """Test merging with empty contexts."""
        merged = context_builder.merge_contexts({}, {}, {})

        assert merged == {}


class TestFilterContext:
    """Tests for filtering context."""

    def test_filter_context_subset(self, context_builder):
        """Test filtering context to a subset of nodes."""
        context = {
            "Node1": {"data": 1},
            "Node2": {"data": 2},
            "Node3": {"data": 3},
        }

        filtered = context_builder.filter_context(context, ["Node1", "Node3"])

        assert len(filtered) == 2
        assert "Node1" in filtered
        assert "Node3" in filtered
        assert "Node2" not in filtered

    def test_filter_context_empty_list(self, context_builder):
        """Test filtering with empty node list."""
        context = {"Node1": {"data": 1}, "Node2": {"data": 2}}

        filtered = context_builder.filter_context(context, [])

        assert filtered == {}

    def test_filter_context_nonexistent_nodes(self, context_builder):
        """Test filtering with non-existent node names."""
        context = {"Node1": {"data": 1}}

        filtered = context_builder.filter_context(
            context, ["Node1", "NonExistent"]
        )

        # Should only include existing nodes
        assert filtered == {"Node1": {"data": 1}}


class TestValidateContext:
    """Tests for context validation."""

    def test_validate_valid_context(self, context_builder):
        """Test validating a properly formatted context."""
        context = {
            "Node1": {"data": {"value": 1}},
            "Node2": {"data": {"result": 42}},
        }

        is_valid, errors = context_builder.validate_context(context)

        assert is_valid is True
        assert errors == []

    def test_validate_non_dict_context(self, context_builder):
        """Test validating non-dictionary context."""
        is_valid, errors = context_builder.validate_context("not a dict")

        assert is_valid is False
        assert len(errors) > 0
        assert "must be a dictionary" in errors[0]

    def test_validate_non_string_node_name(self, context_builder):
        """Test validating context with non-string node name."""
        context = {123: {"data": "value"}}

        is_valid, errors = context_builder.validate_context(context)

        assert is_valid is False
        assert any("must be string" in err for err in errors)

    def test_validate_non_dict_output(self, context_builder):
        """Test validating context with non-dict output."""
        context = {"Node1": "not a dict"}

        is_valid, errors = context_builder.validate_context(context)

        assert is_valid is False
        assert any("must be dict" in err for err in errors)

    def test_validate_empty_context(self, context_builder):
        """Test validating empty context."""
        is_valid, errors = context_builder.validate_context({})

        assert is_valid is True
        assert errors == []
