import logging
import asyncio
import json
import uuid
import os
import warnings
import hashlib
import math
import re
import sys
import time
from copy import deepcopy
from typing import Optional, Dict, List, Any

from videodb._constants import VIDEO_DB_API

logger = logging.getLogger(__name__)


def get_capture_binary_path():
    """
    Attempts to find the path to the capture binary.
    If the optional 'videodb-capture-bin' package is not installed,
    it raises a RuntimeError with instructions.
    """
    try:
        import videodb_capture_bin

        return videodb_capture_bin.get_binary_path()
    except ImportError:
        error_msg = (
            "Capture runtime not found.\n"
            "To use capture features, please install the capture dependencies:\n"
            "pip install 'videodb[capture]'"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.error(f"Failed to resolve capture binary path: {e}")
        raise


class Channel:
    """Base class for capture channels."""

    def __init__(
        self,
        id: str,
        name: str,
        type: str,
        client: Optional["CaptureClient"] = None,
    ):
        """Object representing a capture channel.

        :param str id: The unique ID of the channel.
        :param str name: The display name of the channel.
        :param str type: The type of the channel (audio/video).
        :param CaptureClient client: Reference to the capture client.
        """
        self.id = id
        self.name = name
        self.type = type
        self._client = client
        self.store = False
        self.is_primary = False

    def __repr__(self):
        return f"Channel(id={self.id}, name={self.name}, type={self.type})"

    async def pause(self) -> None:
        """Pause recording for this channel."""
        if not self._client:
            raise RuntimeError("Channel not bound to a CaptureClient")

        track_map = {
            "audio": "mic" if "mic" in self.id else "system_audio",
            "video": "screen",
        }
        track = track_map.get(self.type)
        if track:
            await self._client.pause_tracks([track])

    async def resume(self) -> None:
        """Resume recording for this channel."""
        if not self._client:
            raise RuntimeError("Channel not bound to a CaptureClient")

        track_map = {
            "audio": "mic" if "mic" in self.id else "system_audio",
            "video": "screen",
        }
        track = track_map.get(self.type)
        if track:
            await self._client.resume_tracks([track])

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation of the channel."""
        return {
            "channel_id": self.id,
            "type": self.type,
            "name": self.name,
            "store": self.store,
            "is_primary": self.is_primary,
        }


class AudioChannel(Channel):
    """Represents an audio source channel."""

    def __init__(self, id: str, name: str, client: Optional["CaptureClient"] = None):
        super().__init__(id, name, type="audio", client=client)

    def __repr__(self):
        return f"AudioChannel(id={self.id}, name={self.name})"


class VideoChannel(Channel):
    """Represents a video source channel."""

    def __init__(self, id: str, name: str, client: Optional["CaptureClient"] = None):
        super().__init__(id, name, type="video", client=client)

    def __repr__(self):
        return f"VideoChannel(id={self.id}, name={self.name})"


class ChannelList(list):
    """List subclass with a default property for channel collections."""

    @property
    def default(self) -> Optional[Channel]:
        """Get the first (default) channel, or None if empty."""
        return self[0] if self else None


class Channels:
    """Container for available channels, grouped by type."""

    def __init__(
        self,
        mics: List[AudioChannel] = None,
        displays: List[VideoChannel] = None,
        system_audio: List[AudioChannel] = None,
        cameras: List[VideoChannel] = None,
    ):
        self.mics: ChannelList = ChannelList(mics or [])
        self.displays: ChannelList = ChannelList(displays or [])
        self.system_audio: ChannelList = ChannelList(system_audio or [])
        self.cameras: ChannelList = ChannelList(cameras or [])

    def __repr__(self):
        return (
            f"Channels("
            f"mics={len(self.mics)}, "
            f"displays={len(self.displays)}, "
            f"system_audio={len(self.system_audio)}, "
            f"cameras={len(self.cameras)})"
        )

    def all(self) -> List[Channel]:
        """Return a flat list of all capturable channels (excludes cameras)."""
        return list(self.mics) + list(self.displays) + list(self.system_audio)


class CaptureCommandError(RuntimeError):
    """Native command rejection with a stable machine-readable code."""

    def __init__(self, result):
        detail = result if isinstance(result, dict) else {}
        self.code = detail.get("code", "UNKNOWN_ERROR")
        super().__init__(detail.get("message", "Recorder command failed"))


class _DeliveryRetryingError(RuntimeError):
    pass


class CaptureClient:
    """Async native capture client. Method arguments use snake_case; native
    results and event payloads retain their wire keys (for example recordingId).
    """

    def __init__(
        self,
        client_token: Optional[str] = None,
        base_url: Optional[str] = None,
        *,
        get_recorder_token=None,
        max_token_refresh_attempts: int = 3,
    ):
        if (
            isinstance(max_token_refresh_attempts, bool)
            or not isinstance(max_token_refresh_attempts, int)
            or max_token_refresh_attempts < 1
        ):
            raise ValueError("max_token_refresh_attempts must be a positive integer")
        self.client_token = client_token
        self.base_url = base_url or os.environ.get("VIDEO_DB_API", VIDEO_DB_API)
        self._binary_path = get_capture_binary_path()
        self._proc = None
        self._initialization = None
        self._readers = []
        self._futures = {}
        self._event_queue = asyncio.Queue()
        self._changed = asyncio.Event()
        self._capture_lock = asyncio.Lock()
        self._listing_lock = asyncio.Lock()
        self._session_id = None
        self._managed_id = None
        self._managed_started_at = 0
        self._capabilities = {}
        self._pending_sessions = set()
        self._pending_recordings = set()
        self._recording_sessions = {}
        self._owners = {}
        self._listing_events = {}
        self._starting_events = {}
        self._outcomes = {}
        self._retrying = set()
        self._token_provider = get_recorder_token
        self._max_refresh = max_token_refresh_attempts
        self._token_hashes = {}
        self._refresh_attempts = {}
        self._token_tasks = {}
        self._token_requests = {}
        self._generation = 0
        self._shutting_down = False
        self._suspending = False

    def __repr__(self):
        return f"CaptureClient(base_url={self.base_url})"

    @property
    def initialized(self):
        return self._proc is not None and self._proc.returncode is None

    @property
    def is_capturing(self):
        return bool(self._session_id or self._managed_id)

    def _check_open(self):
        if self._shutting_down:
            raise RuntimeError("CaptureClient is shutting down")

    @staticmethod
    def _timeout(value):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ValueError("timeout must be positive and finite (seconds)")
        return value

    async def _ensure_process(self):
        if self._suspending:
            raise RuntimeError("CaptureClient is suspending")
        if self._initialization is None:
            if self.initialized:
                return
            self._initialization = asyncio.create_task(self._initialize())
        task = self._initialization
        try:
            await asyncio.shield(task)
        finally:
            if task.done() and self._initialization is task:
                self._initialization = None

    async def _initialize(self):
        self._capabilities = {}
        proc = await asyncio.create_subprocess_exec(
            self._binary_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._proc = proc
        self._readers = [
            asyncio.create_task(self._read_stdout_loop(proc)),
            asyncio.create_task(self._read_stderr_loop(proc)),
        ]
        try:
            params = {"apiUrl": self.base_url}
            if self.client_token:
                params["sessionToken"] = self.client_token
            result = await self._write_command("init", params)
            self._capabilities = (result or {}).get("capabilities", {})
        except BaseException:
            if proc.returncode is None:
                try:
                    proc.terminate()
                except ProcessLookupError:
                    pass
            await proc.wait()
            raise

    async def _send_command(self, command, params=None, timeout=30):
        await self._ensure_process()
        return await self._write_command(command, params, timeout)

    async def _write_command(self, command, params=None, timeout=30):
        self._timeout(timeout)
        command_id = str(uuid.uuid4())
        future = asyncio.get_running_loop().create_future()
        # Register before write/drain: a reply may arrive while drain yields.
        self._futures[command_id] = future
        try:
            payload = {
                "command": command,
                "commandId": command_id,
                "params": params or {},
            }
            self._proc.stdin.write(
                ("videodb_recorder|" + json.dumps(payload) + "\n").encode()
            )

            async def receive():
                await self._proc.stdin.drain()
                return await future

            return await asyncio.wait_for(receive(), timeout)
        finally:
            self._futures.pop(command_id, None)
            if not future.done():
                future.cancel()

    async def _read_stdout_loop(self, proc):
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                line = line.decode("utf-8", errors="replace").strip()
                if not line.startswith("videodb_recorder|"):
                    continue
                try:
                    data = json.loads(line.split("|", 1)[1])
                except (ValueError, TypeError):
                    logger.warning("Ignoring malformed capture message")
                    continue
                if not isinstance(data, dict):
                    continue
                if data.get("type") == "response":
                    future = self._futures.get(data.get("commandId"))
                    if future is not None and not future.done():
                        if data.get("status") == "success":
                            future.set_result(data.get("result"))
                        else:
                            future.set_exception(
                                CaptureCommandError(data.get("result"))
                            )
                elif data.get("type") == "event":
                    self._handle_event(data)
        finally:
            if self._proc is proc:
                self._generation += 1
                self._session_id = self._managed_id = None
                self._proc = None
                for future in list(self._futures.values()):
                    if not future.done():
                        future.set_exception(
                            RuntimeError("Recorder exited; recover retained jobs")
                        )
                self._changed.set()

    async def _read_stderr_loop(self, proc):
        while await proc.stderr.readline():
            # Native diagnostics may include credentials; never echo raw output.
            pass

    def _set_outcome(self, event, outcome):
        rid = event["recordingId"]
        self._outcomes["recording:" + rid] = outcome
        sid = event.get("sessionId") or self._recording_sessions.get(rid)
        if sid:
            self._outcomes["session:" + sid] = outcome
        if not isinstance(outcome, Exception):
            self._pending_recordings.discard(rid)
            self._pending_sessions.discard(sid)
            self._retrying.discard(rid)
            self._token_hashes.pop(rid, None)
        self._changed.set()

    def _handle_event(self, event, replay=False):
        if not replay:
            self._event_queue.put_nowait(event)
        name, payload = event.get("event"), event.get("payload", {})
        if not isinstance(payload, dict):
            return
        rid, owner = payload.get("recordingId"), payload.get("owner")
        if name == "error" and payload.get("code") in {
            "INSTANCE_ALREADY_RUNNING",
            "INSTANCE_LOCK_UNAVAILABLE",
        }:
            for future in list(self._futures.values()):
                if not future.done():
                    future.set_exception(CaptureCommandError(payload))
        if (
            name in {"recording-complete", "recording:stopped"}
            and payload.get("sessionId") == self._session_id
        ):
            self._session_id = None
        if not rid:
            return
        if owner:
            if self._owners.get(rid) != owner:
                for buffer in (self._listing_events, self._starting_events):
                    if owner in buffer:
                        buffer[owner].append(event)
                return
            if name == "recording-ready" and self._managed_id == rid:
                self._managed_id = None
            if (
                name == "processing-progress"
                and isinstance(payload.get("etaSeconds"), (int, float))
                and math.isfinite(payload["etaSeconds"])
            ):
                self._refresh_attempts.pop(rid, None)
                self._retrying.discard(rid)
        else:
            sid = payload.get("sessionId")
            if not sid or not (
                self.client_token
                or self._token_provider
                or rid in self._pending_recordings
            ):
                return
            self._recording_sessions[rid] = sid
        if name == "processing-complete":
            self._set_outcome(payload, payload)
        elif name in {
            "recording-failed",
            "processing-failed",
            "local-recording-failed",
            "recording-relay-failed",
        }:
            if payload.get("retrying") is True:
                self._retrying.add(rid)
                self._changed.set()
            else:
                self._retrying.discard(rid)
                self._set_outcome(
                    payload,
                    CaptureCommandError(
                        {
                            "code": payload.get("errorCode", "RECORDING_FAILED"),
                            "message": "Recording could not complete; inspect retained jobs before retrying",
                        }
                    ),
                )
        elif name in {"local-recording-ready", "recording-token-needed"}:
            self._pending_recordings.add(rid)
            if name == "recording-token-needed" and self._token_provider:
                current = self._token_requests.get(rid)
                if owner and current and not current["submitted"]:
                    return
                request = {"submitted": False}
                self._token_requests[rid] = request
                previous = self._token_tasks.get(rid)
                task = asyncio.create_task(
                    self._supply_token(payload, self._generation, request, previous)
                )
                self._token_tasks[rid] = task

    async def _supply_token(self, event, generation, request, previous):
        rid = event["recordingId"]
        try:
            if previous:
                await previous
            if generation != self._generation:
                return
            outcome = self._outcomes.get("recording:" + rid)
            if outcome is not None and not isinstance(outcome, Exception):
                return
            hashes = self._token_hashes.setdefault(rid, set())
            attempts = (
                self._refresh_attempts.get(rid, 0)
                if event.get("owner")
                else len(hashes)
            )
            if attempts >= self._max_refresh:
                raise ValueError("Refresh limit")
            token = await self._token_provider(dict(event, forceRefresh=True))
            if generation != self._generation:
                return
            if token is None:
                self._pending_recordings.discard(rid)
                self._changed.set()
                return
            if not isinstance(token, str) or not token.strip():
                raise ValueError("Empty token")
            digest = hashlib.sha256(token.encode()).hexdigest()
            if digest in hashes:
                raise ValueError("Cached token")
            hashes.add(digest)
            self._refresh_attempts[rid] = attempts + 1
            request["submitted"] = True
            await self.relay_recording(rid, token, owner=event.get("owner"))
        except Exception:
            if generation == self._generation:
                error = "Could not obtain or submit a fresh recorder token"
                self._set_outcome(
                    event,
                    CaptureCommandError(
                        {"code": "TOKEN_REFRESH_FAILED", "message": error}
                    ),
                )
                self._event_queue.put_nowait(
                    {
                        "type": "event",
                        "event": "recording-token-error",
                        "payload": dict(event, error=error),
                    }
                )
        finally:
            if self._token_requests.get(rid) is request:
                self._token_requests.pop(rid, None)
            if self._token_tasks.get(rid) is asyncio.current_task():
                self._token_tasks.pop(rid, None)

    async def get_capabilities(self):
        await self._ensure_process()
        result = {
            "managedDeferredRecording": self._capabilities.get(
                "managedDeferredRecording"
            )
            is True
        }
        for key in ("resolutions", "recordingNotices", "instantStart"):
            if key in self._capabilities:
                result[key] = deepcopy(self._capabilities[key])
        return result

    async def get_notices(self):
        return await self._send_command("getNotices")

    async def get_windows(self):
        if sys.platform not in {"darwin", "win32", "linux"}:
            return dict(
                dict.fromkeys(
                    (
                        "supported",
                        "supportsSwitchWindow",
                        "supportsDeferredWindow",
                        "supportsPlaceholder",
                        "supportsSetWindowEnabled",
                        "supportsAddWindowMidRecording",
                    ),
                    False,
                ),
                windows=[],
            )
        return await self._send_command("getWindows")

    async def switch_window(self, channel_id, source_channel_id=None):
        async with self._capture_lock:
            self._check_open()
            if not isinstance(channel_id, str) or not channel_id.startswith("window:"):
                raise ValueError("A discovered window channel_id is required")
            params = {"channelId": channel_id}
            if source_channel_id is not None:
                params["sourceChannelId"] = source_channel_id
            return await self._send_command("switchWindow", params)

    async def set_window_enabled(
        self, enabled, channel_id=None, source_channel_id=None
    ):
        async with self._capture_lock:
            self._check_open()
            if not isinstance(enabled, bool):
                raise ValueError("enabled must be a boolean")
            params = {"enabled": enabled}
            if channel_id is not None:
                params["channelId"] = channel_id
            if source_channel_id is not None:
                params["sourceChannelId"] = source_channel_id
            return await self._send_command("setWindowEnabled", params)

    async def get_permission_status(self, kind):
        if kind not in self.VALID_PERMISSIONS:
            raise ValueError("Invalid permission type")
        result = await self._send_command(
            "getPermissionStatus", {"permission": kind.replace("_", "-")}
        )
        return result.get("status", "undetermined")

    # Valid permission types
    VALID_PERMISSIONS = {
        "microphone",
        "screen_capture",
        "screen-capture",
        "accessibility",
    }

    async def request_permission(self, kind: str) -> bool:
        """Request system permissions.

        :param str kind: One of "microphone", "screen_capture"
        :return: True if granted, False if denied
        :raises ValueError: If kind is not a valid permission type
        """
        # Validate permission type
        if kind not in self.VALID_PERMISSIONS:
            raise ValueError(
                f"Invalid permission type: '{kind}'. "
                f"Valid types: {', '.join(sorted(self.VALID_PERMISSIONS))}"
            )

        # Map python-friendly names to binary-expected names
        # e.g. "screen_capture" -> "screen-capture"
        permission_map = {
            "screen_capture": "screen-capture",
        }
        binary_kind = permission_map.get(kind, kind)
        result = await self._send_command(
            "requestPermission", {"permission": binary_kind}
        )

        # Binary returns {"requested": True} to confirm the request was initiated
        # or may return {"status": "granted"} if already granted.
        if result.get("requested") is True:
            return True

        status = result.get("status", result.get("permission_status"))
        if status == "granted":
            return True
        elif status == "denied":
            logger.warning(f"Permission '{kind}' was denied.")
            return False

        return False

    async def list_channels(self) -> Channels:
        """Query the system for available audio and video channels.

        :return: Channels object with grouped collections (mics, displays, system_audio).
        :rtype: Channels
        """
        response = await self._send_command("getChannels")
        raw_channels = response.get("channels", [])

        mics = []
        displays = []
        system_audio = []
        cameras = []

        for ch in raw_channels:
            c_type = ch.get("type")
            c_id = ch.get("channel_id") or ch.get("channelId") or ch.get("id")
            c_name = ch.get("name", "")

            if not c_id:
                logger.warning(f"Skipping channel with missing ID: {ch}")
                continue

            # Categorize based on channel ID prefix
            if c_id.startswith("mic:"):
                mics.append(AudioChannel(id=c_id, name=c_name, client=self))
            elif c_id.startswith("display:") or c_id.startswith("screen:"):
                displays.append(VideoChannel(id=c_id, name=c_name, client=self))
            elif c_id.startswith("system_audio:"):
                system_audio.append(AudioChannel(id=c_id, name=c_name, client=self))
            elif c_id.startswith("camera:"):
                cameras.append(VideoChannel(id=c_id, name=c_name, client=self))
            elif c_type == "audio":
                mics.append(AudioChannel(id=c_id, name=c_name, client=self))
            elif c_type == "video":
                displays.append(VideoChannel(id=c_id, name=c_name, client=self))
            else:
                logger.debug(f"Unknown channel type '{c_type}' for channel '{c_name}'")

        return Channels(
            mics=mics, displays=displays, system_audio=system_audio, cameras=cameras
        )

    @staticmethod
    def _channels(channels, managed=False):
        if not isinstance(channels, list) or not channels:
            raise ValueError("At least one channel must be specified for capture")
        result = []
        for channel in channels:
            value = channel.to_dict() if isinstance(channel, Channel) else dict(channel)
            cid = value.get("channel_id") or value.get("channelId")
            if not cid:
                raise ValueError("Every channel requires channel_id")
            item = {"channel_id": cid, "type": value.get("type")}
            if not managed:
                item.update(
                    store=value.get("store", True),
                    is_primary=value.get("is_primary", value.get("isPrimary", False)),
                )
            result.append(item)
        if managed and (
            sum(c["type"] == "video" for c in result) > 1
            or any(
                not re.fullmatch(r"screen|display:[0-9]+|window:[^:]+", c["channel_id"])
                if c["type"] == "video"
                else c["type"] != "audio"
                or c["channel_id"] not in {"mic:default", "system_audio:default"}
                for c in result
            )
        ):
            raise ValueError("Select a display/window, default audio sources, or both")
        return result

    async def start_session(
        self,
        capture_session_id: str,
        channels: List[Channel],
        primary_video_channel_id: Optional[str] = None,
        *,
        resolution=None,
    ):
        """Start live + local capture and return the native acknowledgement.

        Live streams become available on recording-live, not on this response.
        """
        async with self._capture_lock:
            self._check_open()
            if self.is_capturing:
                raise RuntimeError("A recording is already active")
            if not self.client_token or not capture_session_id:
                raise ValueError("client_token and capture_session_id are required")
            selected = self._channels(channels)
            if primary_video_channel_id is not None:
                warnings.warn(
                    "primary_video_channel_id is deprecated; set channel.is_primary instead",
                    DeprecationWarning,
                    stacklevel=2,
                )
                for channel in selected:
                    if channel["channel_id"] == primary_video_channel_id:
                        channel["is_primary"] = True
            await self._ensure_process()
            params = {
                "sessionId": capture_session_id,
                "uploadToken": self.client_token,
                "channels": selected,
            }
            primary = next(
                (c for c in selected if c["type"] == "video" and c["is_primary"]),
                next((c for c in selected if c["type"] == "video"), None),
            )
            if primary:
                params["primary_video_channel_id"] = primary["channel_id"]
            if resolution is not None:
                params["resolution"] = resolution
            self._session_id = capture_session_id
            if sys.platform in {"win32", "linux"} or (
                sys.platform == "darwin"
                and (
                    primary
                    or self._capabilities.get("managedDeferredRecording") is True
                )
            ):
                self._pending_sessions.add(capture_session_id)
                self._outcomes.pop("session:" + capture_session_id, None)
            try:
                return await self._send_command("startRecording", params, timeout=310)
            except BaseException:
                self._session_id = None
                self._pending_sessions.discard(capture_session_id)
                raise

    async def stop_session(self):
        """Stop capture; use wait_for_processing for delivery completion."""
        async with self._capture_lock:
            if self._managed_id:
                raise RuntimeError("Use stop_recording for managed capture")
            if not self.initialized:
                return
            await self._send_command(
                "stopRecording",
                {"sessionId": self._session_id or "current"},
                timeout=155,
            )
            self._session_id = None

    async def start_recording(
        self,
        *,
        owner,
        collection_id,
        upload_token,
        channels,
        name=None,
        resolution=None,
        recording_id=None,
        live=None,
    ):
        """Authorized deferred capture without live streams; stop queues delivery."""
        async with self._capture_lock:
            self._check_open()
            if self.is_capturing:
                raise RuntimeError("A recording is already active")
            if live is not None and live is not False:
                raise ValueError(
                    "start_recording supports live=False only; use start_session for live capture"
                )
            if sys.platform not in {"darwin", "win32", "linux"}:
                raise RuntimeError("Managed capture requires macOS, Windows or Linux")
            if any(
                not isinstance(v, str) or not v.strip()
                for v in (owner, collection_id, upload_token)
            ):
                raise ValueError("owner, collection_id and upload_token are required")
            selected = self._channels(channels, managed=True)
            if not (await self.get_capabilities())["managedDeferredRecording"]:
                raise RuntimeError(
                    "The installed recorder does not support managed deferred recording"
                )
            params = {
                "mode": "deferred",
                "owner": owner,
                "collectionId": collection_id,
                "uploadToken": upload_token,
                "channels": selected,
            }
            for key, value in (
                ("live", live),
                ("resolution", resolution),
                ("name", name),
                ("recordingId", recording_id),
            ):
                if value is not None:
                    params[key] = value
            # Buffer same-chunk events until the response supplies the authorized ID.
            buffered = []
            self._starting_events[owner] = buffered
            try:
                started = await self._send_command(
                    "startRecording", params, timeout=310
                )
                rid = started["recordingId"]
                self._managed_id = rid
                self._managed_started_at = time.monotonic()
                self._owners[rid] = owner
                self._pending_recordings.add(rid)
                self._outcomes.pop("recording:" + rid, None)
                for event in list(buffered):
                    if event["payload"].get("recordingId") == rid:
                        self._handle_event(event, replay=True)
                return started
            finally:
                self._starting_events.pop(owner, None)

    async def stop_recording(self, *, upload_token=None, timeout=None):
        """Wait for finalization readiness, not ingestion. Timeout is in seconds."""
        async with self._capture_lock:
            if not self._managed_id:
                raise RuntimeError("No managed recording is active")
            timeout = self._timeout(
                timeout
                if timeout is not None
                else max(155, (time.monotonic() - self._managed_started_at) / 4 + 30)
            )
            params = {} if upload_token is None else {"uploadToken": upload_token}
            try:
                result = await self._send_command(
                    "stopRecording", params, timeout=timeout
                )
                self._managed_id = None
                return result
            except CaptureCommandError as error:
                if error.code == "FINALIZE_FAILED":
                    self._managed_id = None
                raise

    async def pause_tracks(self, tracks):
        await self._control_tracks("pauseTracks", tracks)

    async def resume_tracks(self, tracks):
        await self._control_tracks("resumeTracks", tracks)

    async def _control_tracks(self, command, tracks):
        async with self._capture_lock:
            self._check_open()
            if not self.initialized:
                raise RuntimeError("CaptureClient not initialized")
            if (
                not isinstance(tracks, list)
                or not tracks
                or any(
                    not isinstance(t, str)
                    or (
                        t not in {"mic", "system_audio", "screen"}
                        and not re.fullmatch(r"[^:\s]+:[^\s]+", t)
                    )
                    for t in tracks
                )
            ):
                raise ValueError("Use track names or channel IDs supplied at start")
            await self._send_command(command, {"tracks": tracks})

    async def list_recordings(self, owner):
        """Adopt owner-scoped retained jobs; a configured provider may resume delivery."""
        async with self._listing_lock:
            self._check_open()
            if not isinstance(owner, str) or not owner.strip():
                raise ValueError("owner is required")
            if not (await self.get_capabilities())["managedDeferredRecording"]:
                raise RuntimeError("Managed deferred recording is unsupported")
            buffered = []
            self._listing_events[owner] = buffered
            try:
                response = await self._send_command("listRecordings", {"owner": owner})
                jobs = response["recordings"]
                adopted = set()
                for job in jobs:
                    if job.get("owner") != owner:
                        continue
                    rid = job["recordingId"]
                    adopted.add(rid)
                    self._owners[rid] = owner
                    if job["stage"] == "complete" and job.get("result"):
                        self._set_outcome(
                            job,
                            {
                                "recordingId": rid,
                                "owner": owner,
                                "result": job["result"],
                            },
                        )
                    elif (
                        job["stage"] in {"ready", "uploaded", "processing"}
                        and "recording:" + rid not in self._outcomes
                    ):
                        self._pending_recordings.add(rid)
                for event in buffered:
                    if event["payload"].get("recordingId") in adopted:
                        self._handle_event(event, replay=True)
                self._changed.set()
                return jobs
            finally:
                self._listing_events.pop(owner, None)

    async def list_local_recordings(self):
        """List session jobs for this API environment; does not itself relay them."""
        response = await self._send_command("listLocalRecordings")
        for job in response["recordings"]:
            self._recording_sessions[job["recordingId"]] = job["sessionId"]
        return response["recordings"]

    async def relay_recording(self, recording_id, upload_token, *, owner=None):
        """Submit fresh authorization; acceptance is not processing completion."""
        if (
            not recording_id
            or not isinstance(upload_token, str)
            or not upload_token.strip()
        ):
            raise ValueError("recording_id and fresh upload_token are required")
        await self._ensure_process()
        managed_owner = self._owners.get(recording_id)
        if managed_owner and owner != managed_owner:
            raise ValueError("Matching owner is required for managed relay")
        if owner:
            self._owners[recording_id] = owner
        self._pending_recordings.add(recording_id)
        self._retrying.discard(recording_id)
        self._outcomes.pop("recording:" + recording_id, None)
        sid = self._recording_sessions.get(recording_id)
        if sid:
            self._outcomes.pop("session:" + sid, None)
        params = {"recordingId": recording_id, "uploadToken": upload_token}
        if owner:
            params["owner"] = owner
        try:
            result = await self._send_command("relayRecording", params)
            return result
        except Exception:
            error = RuntimeError(
                "Relay request rejected; recording retained for recovery"
            )
            self._set_outcome({"recordingId": recording_id, "sessionId": sid}, error)
            raise error from None

    async def wait_for_processing(
        self, *, recording_id=None, session_id=None, timeout=900
    ):
        """Await processing-complete, including cached outcomes. Timeout is seconds."""
        return await self._wait_for_processing(recording_id, session_id, timeout)

    async def _wait_for_processing(
        self, recording_id, session_id, timeout, release_on_retry=False
    ):
        self._timeout(timeout)
        if bool(recording_id) == bool(session_id):
            raise ValueError("Exactly one of recording_id or session_id is required")
        key = "recording:" + recording_id if recording_id else "session:" + session_id
        await self._ensure_process()
        generation = self._generation

        async def wait():
            while True:
                self._changed.clear()
                outcome = self._outcomes.get(key)
                if isinstance(outcome, Exception):
                    raise outcome
                if outcome is not None:
                    return outcome
                if release_on_retry and (
                    (
                        recording_id
                        and (
                            recording_id in self._retrying
                            or recording_id not in self._pending_recordings
                        )
                    )
                    or (
                        session_id
                        and any(
                            sid == session_id and rid in self._retrying
                            for rid, sid in self._recording_sessions.items()
                        )
                    )
                ):
                    raise _DeliveryRetryingError()
                if generation != self._generation or not self.initialized:
                    raise RuntimeError(
                        "Recorder exited before processing completed; recover retained jobs"
                    )
                await self._changed.wait()

        return await asyncio.wait_for(wait(), timeout)

    async def shutdown(self, *, wait_for_processing=True, timeout=900):
        """Stop capture and await delivery. False suspends retained jobs for recovery.

        Processing failure/timeout leaves the process running for explicit recovery.
        """
        if self._shutting_down:
            raise RuntimeError("Shutdown already in progress")
        self._timeout(timeout)
        self._shutting_down = True
        try:
            async with self._capture_lock:
                pass
            async with self._listing_lock:
                pass
            if self._initialization:
                await asyncio.shield(self._initialization)
            if not self.initialized:
                return
            if self._managed_id:
                await self.stop_recording()
            if self._session_id:
                await self.stop_session()
            if wait_for_processing:
                for sid in list(self._pending_sessions):
                    try:
                        await self._wait_for_processing(None, sid, timeout, True)
                    except _DeliveryRetryingError:
                        pass
                for rid in list(self._pending_recordings):
                    try:
                        await self._wait_for_processing(rid, None, timeout, True)
                    except _DeliveryRetryingError:
                        pass
            self._suspending = True
            self._generation += 1
            proc = self._proc
            await self._write_command("shutdown", timeout=155)
            # Acknowledgement precedes process exit. Do not terminate finalization.
            await asyncio.wait_for(proc.wait(), 155)
            await asyncio.gather(*self._readers, return_exceptions=True)
            self._proc = None
            self._session_id = self._managed_id = None
            self._pending_sessions.clear()
            self._pending_recordings.clear()
        finally:
            self._shutting_down = self._suspending = False

    async def events(self):
        """Yield native event envelopes, including meeting and recording notices."""
        while True:
            try:
                yield await asyncio.wait_for(self._event_queue.get(), timeout=1)
            except asyncio.TimeoutError:
                if not self.initialized:
                    break
