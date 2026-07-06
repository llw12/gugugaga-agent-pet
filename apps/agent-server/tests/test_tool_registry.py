import pytest

from app.security.permissions import PermissionDenied
from app.tools.registry import ToolNotFound, execute_tool


def test_system_overview_executes():
    result = execute_tool("system.get_overview")

    assert "cpu_percent" in result
    assert "memory" in result
    assert "disk" in result


def test_process_top_executes():
    result = execute_tool("process.top")

    assert isinstance(result, list)
    assert len(result) <= 10


def test_medium_approval_tool_is_rejected():
    with pytest.raises(PermissionDenied):
        execute_tool("mock.medium_approval")


def test_unknown_tool_is_rejected_without_key_error():
    with pytest.raises(ToolNotFound):
        execute_tool("does.not.exist")
