from collections import deque

import pytest

from videodb import Sandbox, SandboxModel, SandboxStatus, SandboxTier
from videodb.client import Connection
from videodb.exceptions import InvalidRequestError


class FakeConnection:
    def __init__(self, *, posts=None, gets=None):
        self.post_responses = deque(posts or [])
        self.get_responses = deque(gets or [])
        self.post_calls = []
        self.get_calls = []

    def post(self, path, data=None, **kwargs):
        self.post_calls.append({"path": path, "data": data, "kwargs": kwargs})
        return self.post_responses.popleft()

    def get(self, path, **kwargs):
        self.get_calls.append({"path": path, "kwargs": kwargs})
        return self.get_responses.popleft()


def test_create_sandbox_sends_model_selection_and_returns_resource():
    connection = FakeConnection(
        posts=[
            {
                "sandbox_id": "bx-123",
                "tier": "small",
                "status": "provisioning",
                "name": "demo",
                "models": ["rtdetr-v2-r50vd"],
                "model_categories": ["object_detection"],
                "region": "aws-ap-south-1",
                "expires_at": "2026-07-25T10:00:00Z",
            }
        ]
    )

    sandbox = Connection.create_sandbox(
        connection,
        tier=SandboxTier.small,
        name="demo",
        callback_url="https://example.com/callback",
        models=["rtdetr-v2-r50vd"],
        model_categories=["object_detection"],
    )

    assert connection.post_calls == [
        {
            "path": "sandbox",
            "data": {
                "tier": "small",
                "name": "demo",
                "callback_url": "https://example.com/callback",
                "models": ["rtdetr-v2-r50vd"],
                "model_categories": ["object_detection"],
            },
            "kwargs": {},
        }
    ]
    assert isinstance(sandbox, Sandbox)
    assert sandbox.id == "bx-123"
    assert sandbox.models == ["rtdetr-v2-r50vd"]
    assert sandbox.model_categories == ["object_detection"]
    assert sandbox.region == "aws-ap-south-1"
    assert sandbox.expires_at == "2026-07-25T10:00:00Z"


def test_get_and_list_sandboxes_preserve_server_fields():
    get_connection = FakeConnection(
        gets=[
            {
                "sandbox_id": "bx-123",
                "tier": "small",
                "status": "active",
                "models": ["rtdetr-v2-r50vd"],
            }
        ]
    )
    sandbox = Connection.get_sandbox(get_connection, "bx-123")

    list_connection = FakeConnection(
        gets=[
            {
                "sandboxes": [
                    {
                        "sandbox_id": "bx-123",
                        "tier": "small",
                        "status": "active",
                        "models": ["rtdetr-v2-r50vd"],
                    }
                ]
            }
        ]
    )
    sandboxes = Connection.list_sandboxes(
        list_connection,
        status="active",
        page=2,
        page_size=10,
    )

    assert sandbox.id == "bx-123"
    assert sandbox.is_active
    assert list_connection.get_calls == [
        {
            "path": "sandbox",
            "kwargs": {
                "params": {
                    "page": 2,
                    "page_size": 10,
                    "status": "active",
                }
            },
        }
    ]
    assert [item.id for item in sandboxes] == ["bx-123"]
    assert sandboxes[0].models == ["rtdetr-v2-r50vd"]


def test_refresh_updates_sandbox_state():
    connection = FakeConnection(
        gets=[
            {
                "sandbox_id": "bx-123",
                "status": "active",
                "models": ["k2-fsa/OmniVoice"],
                "model_categories": ["text_to_speech"],
            }
        ]
    )
    sandbox = Sandbox(connection, sandbox_id="bx-123", status="provisioning")

    result = sandbox.refresh()

    assert result is sandbox
    assert sandbox.status == SandboxStatus.active
    assert sandbox.models == ["k2-fsa/OmniVoice"]
    assert sandbox.model_categories == ["text_to_speech"]


def test_stop_uses_flattened_sdk_response_and_updates_state():
    connection = FakeConnection(
        posts=[
            {
                "sandbox_id": "bx-123",
                "status": "stopping",
                "models": ["rtdetr-v2-r50vd"],
            }
        ]
    )
    sandbox = Sandbox(
        connection,
        sandbox_id="bx-123",
        status="active",
        models=["rtdetr-v2-r50vd"],
    )

    result = sandbox.stop(grace=False)

    assert result is sandbox
    assert sandbox.status == SandboxStatus.stopping
    assert sandbox.models == ["rtdetr-v2-r50vd"]
    assert connection.post_calls == [
        {
            "path": "sandbox/bx-123/stop",
            "data": {"grace": False},
            "kwargs": {},
        }
    ]


def test_wait_for_ready_returns_on_active_state(monkeypatch):
    connection = FakeConnection(
        gets=[
            {"sandbox_id": "bx-123", "status": "provisioning"},
            {"sandbox_id": "bx-123", "status": "active"},
        ]
    )
    sandbox = Sandbox(connection, sandbox_id="bx-123", status="provisioning")
    monkeypatch.setattr("videodb.sandbox.time.sleep", lambda _: None)

    result = sandbox.wait_for_ready(timeout=10, interval=0)

    assert result is sandbox
    assert sandbox.status == SandboxStatus.active


def test_wait_for_ready_treats_alert_as_ready():
    connection = FakeConnection(gets=[{"sandbox_id": "bx-123", "status": "alert"}])
    sandbox = Sandbox(connection, sandbox_id="bx-123", status="provisioning")

    result = sandbox.wait_for_ready(timeout=10, interval=0)

    assert result is sandbox
    assert sandbox.is_ready


def test_wait_for_ready_raises_on_terminal_state():
    connection = FakeConnection(gets=[{"sandbox_id": "bx-123", "status": "failed"}])
    sandbox = Sandbox(connection, sandbox_id="bx-123", status="provisioning")

    with pytest.raises(InvalidRequestError, match="entered terminal state"):
        sandbox.wait_for_ready(timeout=10, interval=0)


def test_wait_for_stop_returns_on_stopped_state(monkeypatch):
    connection = FakeConnection(
        gets=[
            {"sandbox_id": "bx-123", "status": "stopping"},
            {"sandbox_id": "bx-123", "status": "stopped"},
        ]
    )
    sandbox = Sandbox(connection, sandbox_id="bx-123", status="stopping")
    monkeypatch.setattr("videodb.sandbox.time.sleep", lambda _: None)

    result = sandbox.wait_for_stop(timeout=10, interval=0)

    assert result is sandbox
    assert sandbox.status == SandboxStatus.stopped


def test_public_sandbox_constants_and_models():
    assert SandboxTier.small == "small"
    assert SandboxTier.medium == "medium"
    assert SandboxStatus.active == "active"
    assert SandboxModel.OMNIVOICE.value == "k2-fsa/OmniVoice"
    assert SandboxModel.FLUX.value == "black-forest-labs/FLUX.1-dev"
    assert SandboxModel.RTDETR_V2_R50VD.value == "rtdetr-v2-r50vd"
