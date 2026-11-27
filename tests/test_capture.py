"""Capture wire contracts and asynchronous lifecycle; no hardware/network access."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from videodb.capture import (
    CaptureClient,
    CaptureCommandError,
    AudioChannel,
    VideoChannel,
)
from videodb.client import Connection


def run(function):
    def test(*args, **kwargs):
        return asyncio.run(function(*args, **kwargs))

    test.__name__ = function.__name__
    return test


def client(**options):
    with patch("videodb.capture.get_capture_binary_path", return_value="/mock/capture"):
        c = CaptureClient(**options)
    c._proc = SimpleNamespace(returncode=None, wait=AsyncMock(return_value=0))
    c._capabilities = {"managedDeferredRecording": True, "instantStart": True}
    c._ensure_process = AsyncMock()

    async def command(name, params=None, timeout=30):
        if name == "startRecording":
            return (
                {"recordingId": "r", "mode": "deferred"}
                if params.get("mode")
                else {
                    "sessionId": params["sessionId"],
                    "status": "recording",
                    "recordingId": "r",
                }
            )
        if name == "stopRecording":
            return {"recordingId": "r", "status": "ready"}
        return {}

    c._send_command = AsyncMock(side_effect=command)
    c._write_command = AsyncMock(return_value={})
    return c


def event(c, name, **payload):
    c._handle_event({"type": "event", "event": name, "payload": payload})


async def start(c, **options):
    return await c.start_recording(
        owner="alice",
        collection_id="coll",
        upload_token="initial",
        channels=[AudioChannel("mic:default", "Mic")],
        **options,
    )


@run
async def test_session_identity_payload_and_native_error_retry():
    c = client(client_token="token")
    video = VideoChannel("display:1", "Display")
    video.is_primary = True
    result = await c.start_session("s", [video], resolution="1080p")
    assert result["recordingId"] == "r"
    params = c._send_command.call_args.args[1]
    assert params["resolution"] == "1080p"
    assert params["primary_video_channel_id"] == "display:1"
    assert "live" not in params
    await c.stop_session()
    assert not c.is_capturing
    c._send_command.side_effect = CaptureCommandError({"code": "INSUFFICIENT_STORAGE"})
    with pytest.raises(CaptureCommandError) as error:
        await c.start_session("s2", [video])
    assert error.value.code == "INSUFFICIENT_STORAGE"
    assert not c.is_capturing
    assert "s2" not in c._pending_sessions
    c._send_command.side_effect = None
    c._send_command.return_value = {"sessionId": "s2", "status": "recording"}
    assert "recordingId" not in await c.start_session("s2", [video])


@run
async def test_managed_authorization_live_false_and_validation():
    c = client()
    assert (await start(c, live=False, resolution="720p"))["recordingId"] == "r"
    params = c._send_command.call_args.args[1]
    assert params == {
        "mode": "deferred",
        "owner": "alice",
        "collectionId": "coll",
        "uploadToken": "initial",
        "live": False,
        "resolution": "720p",
        "channels": [{"channel_id": "mic:default", "type": "audio"}],
    }
    with pytest.raises(RuntimeError, match="active"):
        await start(c)
    await c.stop_recording()
    assert not c.is_capturing
    for live in (True, 0, "false"):
        with pytest.raises(ValueError, match="live=False"):
            await start(c, live=live)
    c._capabilities = {}
    with pytest.raises(RuntimeError, match="does not support"):
        await start(c)


@run
async def test_capabilities_copy_and_optional_fields():
    c = client()
    c._capabilities = {"resolutions": ["720p"], "recordingNotices": False}
    caps = await c.get_capabilities()
    caps["resolutions"].append("1080p")
    assert c._capabilities["resolutions"] == ["720p"]
    assert caps["managedDeferredRecording"] is False
    assert "instantStart" not in caps


@run
async def test_track_ids_and_native_errors_and_channel_helpers():
    c = client()
    await c.pause_tracks(["display:1", "mic:default", "system_audio"])
    c._send_command.assert_awaited_with(
        "pauseTracks", {"tracks": ["display:1", "mic:default", "system_audio"]}
    )
    await AudioChannel("mic:default", "Mic", c).resume()
    c._send_command.assert_awaited_with("resumeTracks", {"tracks": ["mic"]})
    for invalid in ([], ["bad"], ["mic:"], ["a: b"], [1], "mic"):
        with pytest.raises(ValueError):
            await c.pause_tracks(invalid)
    c._send_command.side_effect = CaptureCommandError({"code": "TRACK_NOT_SELECTED"})
    with pytest.raises(CaptureCommandError) as error:
        await c.resume_tracks(["display:2"])
    assert error.value.code == "TRACK_NOT_SELECTED"


@run
async def test_events_forwarded_without_inventing_live_readiness():
    c = client()
    for name in (
        "recording-live",
        "meeting-detected",
        "meeting-ended",
        "recording-notice",
        "window-suspended",
    ):
        event(c, name, recordingId="r", arbitrary="preserved")
        received = await c._event_queue.get()
        assert received["event"] == name
        assert received["payload"]["arbitrary"] == "preserved"


@run
async def test_wait_before_after_completion_and_retrying():
    c = client()
    await start(c)
    wait = asyncio.create_task(c.wait_for_processing(recording_id="r", timeout=1))
    await asyncio.sleep(0)
    event(c, "processing-failed", recordingId="r", owner="alice", retrying=True)
    await asyncio.sleep(0)
    assert not wait.done()
    event(
        c,
        "processing-complete",
        recordingId="r",
        owner="alice",
        result={"videoId": "v"},
    )
    assert (await wait)["result"]["videoId"] == "v"
    assert (await c.wait_for_processing(recording_id="r"))["result"]["videoId"] == "v"
    assert "r" not in c._pending_recordings
    with pytest.raises(ValueError, match="Exactly one"):
        await c.wait_for_processing(recording_id="r", session_id="s")


@run
async def test_failure_and_timeout_preserve_recorder():
    c = client()
    await start(c)
    await c.stop_recording()
    with pytest.raises(asyncio.TimeoutError):
        await c.shutdown(timeout=0.01)
    assert c.initialized
    c._write_command.assert_not_called()
    event(
        c,
        "processing-failed",
        recordingId="r",
        owner="alice",
        errorCode="FAILED",
        retryable=True,
    )
    with pytest.raises(CaptureCommandError):
        await c.wait_for_processing(recording_id="r", timeout=0.1)
    await c.shutdown(wait_for_processing=False)
    assert not c.initialized


@run
async def test_shutdown_waits_then_exits_and_releases_delayed_retry():
    for retrying in (False, True):
        c = client()
        await start(c)
        if retrying:
            event(c, "processing-failed", recordingId="r", owner="alice", retrying=True)
        else:
            event(
                c,
                "processing-complete",
                recordingId="r",
                owner="alice",
                result={"videoId": "v"},
            )
        await c.shutdown(timeout=0.1)
        c._write_command.assert_awaited_with("shutdown", timeout=155)
        assert not c.initialized


@run
async def test_owner_scoped_listing_buffers_early_events():
    provider = AsyncMock(return_value="fresh")
    c = client(get_recorder_token=provider)

    async def command(name, params=None, timeout=30):
        if name == "listRecordings":
            event(
                c,
                "recording-token-needed",
                recordingId="r",
                owner="alice",
                collectionId="coll",
            )
            event(
                c,
                "recording-token-needed",
                recordingId="other",
                owner="bob",
                collectionId="coll",
            )
            return {
                "recordings": [{"recordingId": "r", "owner": "alice", "stage": "ready"}]
            }
        return {"status": "accepted"}

    c._send_command.side_effect = command
    await c.list_recordings("alice")
    await asyncio.gather(*list(c._token_tasks.values()))
    assert provider.await_count == 1
    assert provider.call_args.args[0]["forceRefresh"] is True
    assert "other" not in c._owners
    with pytest.raises(ValueError, match="Matching owner"):
        await c.relay_recording("r", "token", owner="bob")


@run
async def test_start_adopts_only_own_early_events():
    c = client()

    async def command(name, params=None, timeout=30):
        event(
            c,
            "processing-complete",
            recordingId="r",
            owner="alice",
            result={"videoId": "v"},
        )
        event(
            c,
            "processing-complete",
            recordingId="other",
            owner="alice",
            result={"videoId": "other"},
        )
        return {"recordingId": "r", "mode": "deferred"}

    c._send_command.side_effect = command
    await start(c)
    assert (await c.wait_for_processing(recording_id="r"))["result"]["videoId"] == "v"
    assert "recording:other" not in c._outcomes


@run
async def test_token_coalescing_cached_rejection_and_privacy():
    gate = asyncio.Event()

    async def provider(request):
        await gate.wait()
        return "secret"

    c = client(get_recorder_token=AsyncMock(side_effect=provider))
    await start(c)
    for _ in range(2):
        event(
            c,
            "recording-token-needed",
            recordingId="r",
            owner="alice",
            collectionId="coll",
        )
    gate.set()
    await asyncio.gather(*list(c._token_tasks.values()))
    assert c._token_provider.await_count == 1
    event(
        c, "recording-token-needed", recordingId="r", owner="alice", collectionId="coll"
    )
    await asyncio.gather(*list(c._token_tasks.values()))
    with pytest.raises(CaptureCommandError, match="fresh recorder token") as error:
        await c.wait_for_processing(recording_id="r")
    assert "secret" not in str(error.value)


@run
async def test_token_refresh_reset_requires_measured_progress():
    c = client(
        get_recorder_token=AsyncMock(side_effect=["one", "two", "three"]),
        max_token_refresh_attempts=1,
    )
    await start(c)
    event(c, "recording-token-needed", recordingId="r", owner="alice")
    await asyncio.gather(*list(c._token_tasks.values()))
    event(c, "processing-progress", recordingId="r", owner="alice", etaSeconds=None)
    assert c._refresh_attempts["r"] == 1
    event(c, "processing-progress", recordingId="r", owner="alice", etaSeconds=3)
    event(c, "recording-token-needed", recordingId="r", owner="alice")
    await asyncio.gather(*list(c._token_tasks.values()))
    assert c._token_provider.await_count == 2


@run
async def test_late_provider_does_not_restart_shutdown_process():
    gate = asyncio.Event()

    async def provider(request):
        await gate.wait()
        return "fresh"

    c = client(get_recorder_token=provider)
    await start(c)
    event(c, "recording-token-needed", recordingId="r", owner="alice")
    tasks = list(c._token_tasks.values())
    await asyncio.sleep(0)
    await c.shutdown(wait_for_processing=False)
    gate.set()
    await asyncio.gather(*tasks)
    assert not any(
        call.args[0] == "relayRecording" for call in c._send_command.call_args_list
    )


@run
async def test_stop_timeout_late_ready_allows_next_capture():
    c = client()
    await start(c)
    c._send_command.side_effect = asyncio.TimeoutError()
    with pytest.raises(asyncio.TimeoutError):
        await c.stop_recording(timeout=0.01)
    assert c.is_capturing
    event(c, "recording-ready", recordingId="r", owner="alice")
    assert not c.is_capturing


@run
async def test_native_window_and_permission_contracts():
    c = client()
    c._send_command.side_effect = None
    c._send_command.return_value = {"supported": False, "windows": []}
    with patch("videodb.capture.sys.platform", "linux"):
        assert not (await c.get_windows())["supported"]
        c._send_command.assert_awaited_with("getWindows")
    await c.switch_window("window:opaque", "window:none")
    c._send_command.assert_awaited_with(
        "switchWindow", {"channelId": "window:opaque", "sourceChannelId": "window:none"}
    )
    await c.set_window_enabled(False)
    c._send_command.assert_awaited_with("setWindowEnabled", {"enabled": False})
    c._send_command.return_value = {"status": "granted"}
    assert await c.get_permission_status("screen_capture") == "granted"
    assert await c.request_permission("accessibility") is True
    with pytest.raises(ValueError):
        await c.get_permission_status("invalid")


@run
async def test_ipc_fast_reply_registered_before_drain():
    c = client()
    c._write_command = CaptureClient._write_command.__get__(c)

    def write(raw):
        payload = json.loads(raw.decode().split("|", 1)[1])
        assert payload["commandId"] in c._futures
        c._futures[payload["commandId"]].set_result({"ok": True})

    c._proc.stdin = SimpleNamespace(write=write, drain=AsyncMock())
    assert await c._write_command("ping") == {"ok": True}
    assert not c._futures


@run
async def test_ipc_timeout_and_process_exit_reject_pending_commands():
    c = client()
    c._write_command = CaptureClient._write_command.__get__(c)
    c._proc.stdin = SimpleNamespace(write=Mock(), drain=AsyncMock())
    with pytest.raises(asyncio.TimeoutError):
        await c._write_command("ping", timeout=0.01)
    assert not c._futures
    pending = asyncio.get_running_loop().create_future()
    c._futures["pending"] = pending
    c._proc.stdout = SimpleNamespace(readline=AsyncMock(return_value=b""))
    await c._read_stdout_loop(c._proc)
    with pytest.raises(RuntimeError, match="Recorder exited"):
        await pending


def test_token_endpoints_preserve_existing_signature():
    c = Connection.__new__(Connection)
    c.post = Mock(return_value={"token": "fresh", "collection_id": "resolved"})
    assert c.generate_client_token(60) == "fresh"
    assert c.post.call_args.kwargs["data"] == {"expires_in": 60}
    c.generate_client_token(60, "alice")
    assert c.post.call_args.kwargs["data"]["user_id"] == "alice"
    assert c.generate_recorder_token("default", "alice")["collectionId"] == "resolved"
    assert c.post.call_args.kwargs["data"] == {
        "collection_id": "default",
        "user_id": "alice",
        "expires_in": 3600,
    }
    with pytest.raises(ValueError):
        c.generate_recorder_token("", "alice")
    c.post.return_value = {"token": "fresh"}
    with pytest.raises(RuntimeError, match="resolved collection"):
        c.generate_recorder_token("default", "alice")


def test_real_subprocess_initialization_serialization_and_shutdown(tmp_path):
    """Exercise real pipes with a fake recorder, without capture or network access."""
    import sys

    script = tmp_path / "capture"
    script.write_text(
        "#!"
        + sys.executable
        + "\n"
        + """import json, sys
initialized = False
for line in sys.stdin:
    command = json.loads(line.split('|', 1)[1])
    name = command['command']
    if name == 'init':
        if initialized:
            raise RuntimeError('duplicate init')
        initialized = True
        result = {'capabilities': {'instantStart': True}}
    elif not initialized:
        raise RuntimeError('command before init')
    elif name == 'getNotices':
        result = {'notices': []}
    else:
        result = {}
    print('videodb_recorder|' + json.dumps({'type': 'response', 'commandId': command['commandId'], 'status': 'success', 'result': result}), flush=True)
    if name == 'shutdown':
        break
"""
    )
    script.chmod(0o755)

    async def scenario():
        with patch("videodb.capture.get_capture_binary_path", return_value=str(script)):
            c = CaptureClient()
        results = await asyncio.gather(
            c.get_capabilities(), c.get_notices(), c.get_capabilities()
        )
        assert results == [
            {"managedDeferredRecording": False, "instantStart": True},
            {"notices": []},
            {"managedDeferredRecording": False, "instantStart": True},
        ]
        await c.shutdown()
        assert not c.initialized
        assert not c._futures
        assert all(task.done() for task in c._readers)

    asyncio.run(asyncio.wait_for(scenario(), 5))


@run
async def test_parallel_starts_allow_only_one_active_recording():
    c = client()
    results = await asyncio.gather(start(c), start(c), return_exceptions=True)
    assert sum(isinstance(result, RuntimeError) for result in results) == 1
    assert c._send_command.await_count == 1


@run
async def test_listed_completion_and_legacy_session_completion():
    c = client(client_token="token")
    c._send_command.side_effect = None
    c._send_command.return_value = {
        "recordings": [
            {
                "recordingId": "r",
                "owner": "alice",
                "stage": "complete",
                "result": {"videoId": "v"},
            }
        ]
    }
    await c.list_recordings("alice")
    assert (await c.wait_for_processing(recording_id="r"))["result"]["videoId"] == "v"
    event(c, "local-recording-ready", recordingId="legacy", sessionId="s")
    event(
        c,
        "processing-complete",
        recordingId="legacy",
        sessionId="s",
        result={"videoId": "legacy-v"},
    )
    assert (await c.wait_for_processing(session_id="s"))["result"][
        "videoId"
    ] == "legacy-v"


@run
async def test_invalid_managed_channels_and_owner_never_reach_binary():
    c = client()
    for channels in (
        [],
        [{"channel_id": "camera:0", "type": "video"}],
        [{"channel_id": "mic:other", "type": "audio"}],
        [VideoChannel("display:1", "one"), VideoChannel("display:2", "two")],
    ):
        with pytest.raises(ValueError):
            await c.start_recording(
                owner="alice", collection_id="c", upload_token="t", channels=channels
            )
    with pytest.raises(ValueError):
        await c.start_recording(
            owner="",
            collection_id="c",
            upload_token="t",
            channels=[AudioChannel("mic:default", "Mic")],
        )
    c._send_command.assert_not_called()
