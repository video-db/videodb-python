from unittest.mock import Mock, patch

import pytest

from videodb._constants import SandboxStatus
from videodb.exceptions import InvalidRequestError, RequestTimeoutError
from videodb.sandbox import Sandbox


def test_refresh_keeps_error_until_server_clears_it():
    connection = Mock()
    connection.get.side_effect = [
        {"status": SandboxStatus.failed, "error": "Startup failed"},
        {"status": SandboxStatus.failed},
        {"error": None},
    ]
    sandbox = Sandbox(connection, sandbox_id="bx_test")
    sandbox.refresh()
    assert sandbox.error == "Startup failed"
    sandbox.refresh()
    assert sandbox.error == "Startup failed"
    sandbox.refresh()
    assert sandbox.error is None


def test_terminal_wait_includes_server_error():
    connection = Mock()
    connection.get.return_value = {"status": SandboxStatus.failed, "error": "Out of capacity"}
    sandbox = Sandbox(connection, sandbox_id="bx_test")
    with pytest.raises(InvalidRequestError) as caught:
        sandbox.wait_for_ready(timeout=0)
    assert "entered terminal state: failed" in str(caught.value)
    assert "Out of capacity" in str(caught.value)


def test_timed_out_wait_can_resume_same_sandbox():
    connection = Mock()
    connection.get.side_effect = [{"status": "provisioning"}, {"status": SandboxStatus.active}]
    sandbox = Sandbox(connection, sandbox_id="bx_test")
    with patch("videodb.sandbox.time.time", side_effect=[100, 110, 120]):
        with pytest.raises(RequestTimeoutError) as caught:
            sandbox.wait_for_ready(timeout=10)
        assert "same sandbox ID" in str(caught.value)
        assert sandbox.wait_for_ready(timeout=10) is sandbox
    connection.post.assert_not_called()
