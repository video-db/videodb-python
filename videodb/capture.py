import logging
import asyncio
import json
import uuid
import os
from typing import Optional, Dict, List, Any

from videodb._constants import VIDEO_DB_API

logger = logging.getLogger(__name__)

def get_recorder_path():
    """
    Attempts to find the path to the recorder binary.
    If the optional 'videodb-capture-bin' package is not installed,
    it raises a RuntimeError with instructions.
    """
    try:
        import videodb_capture_bin
        return videodb_capture_bin.get_binary_path()
    except ImportError:
        error_msg = (
            "Capture runtime not found.\n"
            "To use recording features, please install the capture dependencies:\n"
            "pip install 'videodb[capture]'"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        logger.error(f"Failed to resolve recorder path: {e}")
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
            await self._client._send_command("pauseTracks", {"tracks": [track]})

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
            await self._client._send_command("resumeTracks", {"tracks": [track]})

    def to_dict(self) -> Dict[str, Any]:
        """Return dictionary representation of the channel."""
        return {
            "channel_id": self.id,
            "type": self.type,
            "name": self.name,
            "record": True,
            "store": self.store,
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
    ):
        self.mics: ChannelList = ChannelList(mics or [])
        self.displays: ChannelList = ChannelList(displays or [])
        self.system_audio: ChannelList = ChannelList(system_audio or [])

    def __repr__(self):
        return (
            f"Channels("
            f"mics={len(self.mics)}, "
            f"displays={len(self.displays)}, "
            f"system_audio={len(self.system_audio)})"
        )

    def all(self) -> List[Channel]:
        """Return a flat list of all channels."""
        return list(self.mics) + list(self.displays) + list(self.system_audio)


class CaptureClient:
    """Client for managing local capture sessions."""

    def __init__(
        self,
        client_token: str,
        base_url: Optional[str] = None,
    ):
        """Initialize the capture client.

        :param str client_token: Client token for the capture session.
        :param str base_url: VideoDB API endpoint URL.
        """
        self.client_token = client_token
        self.base_url = base_url or os.environ.get("VIDEO_DB_API", VIDEO_DB_API)
        self._session_id: Optional[str] = None
        self._proc = None
        self._futures: Dict[str, asyncio.Future] = {}
        self._binary_path = get_recorder_path()
        self._event_queue = asyncio.Queue()

    def __repr__(self) -> str:
        return f"CaptureClient(base_url={self.base_url})"

    async def _ensure_process(self):
        """Ensure the recorder binary is running."""
        if self._proc is not None and self._proc.returncode is None:
            return

        self._proc = await asyncio.create_subprocess_exec(
            self._binary_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        asyncio.create_task(self._read_stdout_loop())
        asyncio.create_task(self._read_stderr_loop())

        await self._send_command("init", {"apiUrl": self.base_url})


    async def _send_command(
        self, command: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a command to the recorder binary and await response.

        :param str command: Command name.
        :param dict params: Command parameters.
        :return: Response result.
        :rtype: dict
        """
        await self._ensure_process()

        command_id = str(uuid.uuid4())
        payload = {
            "command": command,
            "commandId": command_id,
            "params": params or {},
        }
        
        # Framing: videodb_recorder|<JSON>\n
        message = f"videodb_recorder|{json.dumps(payload)}\n"
        self._proc.stdin.write(message.encode("utf-8"))
        await self._proc.stdin.drain()

        # Create future to await response
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._futures[command_id] = future

        try:
            return await future
        finally:
            self._futures.pop(command_id, None)

    async def _read_stdout_loop(self):
        """Loop to read stdout and process messages."""
        while True:
            line = await self._proc.stdout.readline()
            if not line:
                break
            
            line_str = line.decode("utf-8", errors="replace").strip()
            if not line_str.startswith("videodb_recorder|"):
                continue

            try:
                json_part = line_str.split("|", 1)[1]
                data = json.loads(json_part)
                
                msg_type = data.get("type")
                if msg_type == "response":
                    cmd_id = data.get("commandId")
                    if cmd_id in self._futures:
                        if data.get("status") == "success":
                            self._futures[cmd_id].set_result(data.get("result"))
                        else:
                            self._futures[cmd_id].set_exception(
                                RuntimeError(data.get("result", "Unknown error"))
                            )
                elif msg_type == "event":
                    await self._event_queue.put(data)

            except Exception as e:
                logger.error(f"Failed to parse recorder message: {e}")

    async def _read_stderr_loop(self):
        """Loop to read stderr and log messages."""
        while True:
            line = await self._proc.stderr.readline()
            if not line:
                break
            logger.debug(f"[Recorder Binary]: {line.decode('utf-8', errors='replace').strip()}")

    async def shutdown(self):
        """Cleanly terminate the recorder binary process."""
        if self._proc:
            try:
                # Try graceful shutdown command first
                await self._send_command("shutdown")
            except Exception:
                pass
            
            try:
                self._proc.terminate()
                await self._proc.wait()
            except Exception:
                pass
            self._proc = None

    # Valid permission types
    VALID_PERMISSIONS = {"microphone", "screen_capture"}

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
        result = await self._send_command("requestPermission", {"permission": binary_kind})
        
        # Binary returns {"requested": True} to confirm the request was initiated
        # or may return {"status": "granted"} if already granted.
        if result.get("requested") is True:
            return True
        
        status = result.get("status")
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
        
        for ch in raw_channels:
            c_type = ch.get("type")
            c_id = ch.get("channel_id") or ch.get("id")
            c_name = ch.get("name", "")
            
            if not c_id:
                logger.warning(f"Skipping channel with missing ID: {ch}")
                continue

            # Categorize based on type and name patterns
            if c_type == "video":
                displays.append(VideoChannel(id=c_id, name=c_name, client=self))
            elif c_type == "audio":
                # Distinguish between mic and system audio based on common patterns
                name_lower = c_name.lower()
                if "system" in name_lower or "output" in name_lower or "speaker" in name_lower:
                    system_audio.append(AudioChannel(id=c_id, name=c_name, client=self))
                else:
                    mics.append(AudioChannel(id=c_id, name=c_name, client=self))
            else:
                logger.debug(f"Unknown channel type '{c_type}' for channel '{c_name}'")
                
        return Channels(mics=mics, displays=displays, system_audio=system_audio)

    async def start_session(
        self,
        capture_session_id: str,
        channels: List[Channel],
        primary_video_channel_id: Optional[str] = None,
    ) -> None:
        """Start the recording session.

        :param str capture_session_id: The ID of the capture session.
        :param list[Channel] channels: List of Channel objects to record.
        :param str primary_video_channel_id: ID of the primary video channel.
        :raises ValueError: If no channels are specified.
        """
        if not channels:
            raise ValueError("At least one channel must be specified for capture.")

        self._session_id = capture_session_id

        payload = {
            "sessionId": capture_session_id,
            "uploadToken": self.client_token,
            "channels": [ch.to_dict() for ch in channels],
        }

        if primary_video_channel_id:
            payload["primary_video_channel_id"] = primary_video_channel_id

        await self._send_command("startRecording", payload)

    async def stop_session(self) -> None:
        """Stop the current recording session."""
        if not self._session_id:
            raise RuntimeError("No active capture session to stop.")
        await self._send_command("stopRecording", {"sessionId": self._session_id})

    async def events(self):
        """Async generator that yields events from the recorder."""
        while True:
            try:
                # Use a timeout so we can check if the process is still alive
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                yield event
            except asyncio.TimeoutError:
                if self._proc is None or self._proc.returncode is not None:
                    break
                continue
            except Exception:
                break
