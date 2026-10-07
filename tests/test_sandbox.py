from unittest.mock import Mock, patch

import pytest

from videodb._constants import ApiPath, SandboxStatus
from videodb.exceptions import InvalidRequestError, RequestTimeoutError
from videodb.sandbox import Sandbox


@pytest.mark.parametrize("error_fields", [{}, {"error": None}, {"error": "Startup failed"}])
def test_constructor_preserves_optional_server_error(error_fields):
    sandbox = Sandbox(Mock(), sandbox_id="bx_test", **error_fields)

    assert sandbox.error == error_fields.get("error")


def test_refresh_preserves_missing_error_and_clears_explicit_null():
    connection = Mock()
    connection.get.side_effect = [
        {"status": SandboxStatus.failed, "error": "Startup failed"},
        {"status": SandboxStatus.failed},
        {"error": None},
    ]
    sandbox = Sandbox(connection, sandbox_id="bx_test")

    assert sandbox.refresh() is sandbox
    assert sandbox.error == "Startup failed"
    sandbox.refresh()
    assert sandbox.error == "Startup failed"
    sandbox.refresh()
    assert sandbox.error is None


@pytest.mark.parametrize("status", [SandboxStatus.failed, SandboxStatus.stopped])
def test_terminal_wait_includes_server_error(status):
    connection = Mock()
    connection.get.return_value = {
        "status": status,
        "error": "We could not start your sandbox. Please contact support.",
    }
    sandbox = Sandbox(connection, sandbox_id="bx_test")

    with pytest.raises(InvalidRequestError) as caught:
        sandbox.wait_for_ready(timeout=0)

    assert f"Sandbox bx_test entered terminal state: {status}" in str(caught.value)
    assert sandbox.error in str(caught.value)
    connection.get.assert_called_once_with(path=f"{ApiPath.sandbox}/bx_test")
    connection.post.assert_not_called()


@pytest.mark.parametrize("error_fields", [{}, {"error": None}, {"error": ""}])
def test_terminal_wait_without_error_keeps_existing_message(error_fields):
    connection = Mock()
    connection.get.return_value = {"status": SandboxStatus.failed, **error_fields}
    sandbox = Sandbox(connection, sandbox_id="bx_test")

    with pytest.raises(InvalidRequestError) as caught:
        sandbox.wait_for_ready(timeout=0)

    assert str(caught.value).strip() == "Sandbox bx_test entered terminal state: failed"


@pytest.mark.parametrize("status", [SandboxStatus.active, SandboxStatus.alert])
def test_ready_wait_returns_same_sandbox(status):
    connection = Mock()
    connection.get.return_value = {"status": status}
    sandbox = Sandbox(connection, sandbox_id="bx_test")

    assert sandbox.wait_for_ready(timeout=0) is sandbox


def test_timed_out_wait_can_resume_same_sandbox_without_creating_or_stopping():
    connection = Mock()
    connection.get.side_effect = [
        {"sandbox_id": "bx_test", "status": "provisioning"},
        {"sandbox_id": "bx_test", "status": SandboxStatus.active},
    ]
    sandbox = Sandbox(connection, sandbox_id="bx_test")

    with patch("videodb.sandbox.time.time", side_effect=[100, 110, 120]):
        with pytest.raises(RequestTimeoutError) as caught:
            sandbox.wait_for_ready(timeout=10)
        assert sandbox.status == "provisioning"
        assert "Sandbox bx_test not ready within 10s" in str(caught.value)
        assert "may still be in progress" in str(caught.value)
        assert "same sandbox ID" in str(caught.value)

        assert sandbox.wait_for_ready(timeout=10) is sandbox

    assert sandbox.id == "bx_test"
    assert connection.get.call_count == 2
    for call in connection.get.call_args_list:
        assert call.kwargs == {"path": f"{ApiPath.sandbox}/bx_test"}
    connection.post.assert_not_called()
