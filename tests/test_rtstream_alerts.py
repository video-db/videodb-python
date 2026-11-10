import pytest

from videodb.rtstream import RTStream


class FakeConnection:
    def __init__(self, response=None):
        self.calls, self.response = [], response

    def post(self, path, data=None, **kwargs):
        self.calls.append(("POST", path, data))
        return self.response

    def get(self, path, **kwargs):
        self.calls.append(("GET", path, None))
        return self.response

    def patch(self, path, data=None, **kwargs):
        self.calls.append(("PATCH", path, data))
        return self.response


def _stream(response=None):
    connection = FakeConnection(response)
    return RTStream(connection, "rts-1"), connection


def test_create_alert_sends_defaults_and_returns_the_alert_id():
    stream, connection = _stream({"alert_id": "dal-1", "status": "enabled"})

    alert_id = stream.create_alert("evt-1", "https://example.test/hook")

    assert alert_id == "dal-1"
    assert connection.calls == [(
        "POST",
        "rtstream/rts-1/alert",
        {
            "event_id": "evt-1",
            "callback_url": "https://example.test/hook",
            "threshold": 50,
            "cooldown_seconds": 30,
            "profile": "standard",
        },
    )]


def test_create_alert_passes_optional_settings():
    stream, connection = _stream({"alert_id": "dal-2"})

    stream.create_alert(
        "evt-1",
        "https://example.test/hook",
        ws_connection_id="conn-1",
        segmentation={"type": "time", "window": "10s"},
        sampling={"frame_count": 3},
        threshold=70,
        cooldown_seconds=0,
    )

    body = connection.calls[0][2]
    assert body["ws_connection_id"] == "conn-1"
    assert body["segmentation"] == {"type": "time", "window": "10s"}
    assert body["sampling"] == {"frame_count": 3}
    assert (body["threshold"], body["cooldown_seconds"]) == (70, 0)


def test_list_and_get_alerts():
    stream, connection = _stream({"alerts": [{"alert_id": "dal-1"}]})
    assert stream.list_alerts() == [{"alert_id": "dal-1"}]

    stream, connection = _stream({"alert_id": "dal-1", "health": None})
    assert stream.get_alert("dal-1") == {"alert_id": "dal-1", "health": None}
    assert connection.calls == [("GET", "rtstream/rts-1/alert/dal-1", None)]
    with pytest.raises(ValueError):
        stream.get_alert("")


def test_enable_and_disable_alert():
    stream, connection = _stream()

    stream.enable_alert("dal-1")
    stream.disable_alert("dal-1")

    assert connection.calls == [
        ("PATCH", "rtstream/rts-1/alert/dal-1/status", {"action": "enable"}),
        ("PATCH", "rtstream/rts-1/alert/dal-1/status", {"action": "disable"}),
    ]
