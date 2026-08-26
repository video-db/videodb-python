from typing import Optional, List, Dict, Any

from videodb._constants import (
    ApiPath,
    SceneExtractionType,
    Segmenter,
)
from videodb._utils._video import play_stream, build_iframe_embed_code


class RTStreamSearchResult:
    """RTStreamSearchResult class to interact with rtstream search results

    :ivar str collection_id: ID of the collection this rtstream belongs to
    :ivar List[RTStreamShot] shots: List of shots in the search result
    """

    def __init__(
        self,
        collection_id: str,
        shots: List["RTStreamShot"],
    ) -> None:
        self.collection_id = collection_id
        self.shots = shots

    def __repr__(self) -> str:
        return (
            f"RTStreamSearchResult("
            f"collection_id={self.collection_id}, "
            f"shots={len(self.shots)})"
        )

    def get_shots(self) -> List["RTStreamShot"]:
        """Get the list of shots from the search result.

        :return: List of :class:`RTStreamShot <RTStreamShot>` objects
        :rtype: List[:class:`videodb.rtstream.RTStreamShot`]
        """
        return self.shots


class RTStreamExportResult:
    """Result of exporting an RTStream recording.

    :ivar str video_id: ID of the exported video or audio asset
    :ivar str stream_url: URL to stream the exported asset (may be None for audio)
    :ivar str player_url: URL to play the exported asset in a player (may be None for audio)
    :ivar str name: Name of the exported recording
    :ivar float duration: Duration of the exported recording in seconds (may be None on idempotent calls)
    """

    def __init__(
        self,
        video_id: str,
        stream_url: Optional[str] = None,
        player_url: Optional[str] = None,
        name: Optional[str] = None,
        duration: Optional[float] = None,
    ) -> None:
        self.video_id = video_id
        self.stream_url = stream_url
        self.player_url = player_url
        self.name = name
        self.duration = duration

    def __repr__(self) -> str:
        return (
            f"RTStreamExportResult("
            f"video_id={self.video_id}, "
            f"name={self.name}, "
            f"duration={self.duration})"
        )

    def get_embed_code(
        self,
        width: str = "100%",
        height: int = 405,
        title: str = "VideoDB Player",
        allow_fullscreen: bool = True,
    ) -> str:
        """Generate an HTML iframe embed code for the exported recording.

        :param str width: Width of the iframe (default: "100%")
        :param int height: Height of the iframe in pixels (default: 405)
        :param str title: Title attribute for the iframe (default: "VideoDB Player")
        :param bool allow_fullscreen: Whether to allow fullscreen (default: True)
        :return: HTML iframe string
        :rtype: str
        :raises ValueError: If player_url is not available
        """
        if not self.player_url:
            raise ValueError(
                "player_url not available. Export may have failed or returned audio-only content."
            )

        return build_iframe_embed_code(
            player_url=self.player_url,
            width=width,
            height=height,
            title=title,
            allow_fullscreen=allow_fullscreen,
        )


class RTStreamShot:
    """RTStreamShot class for rtstream search results

    :ivar str rtstream_id: ID of the rtstream
    :ivar str rtstream_name: Name of the rtstream
    :ivar float start: Start time in Unix timestamp
    :ivar float end: End time in Unix timestamp
    :ivar str text: Text content of the shot
    :ivar float search_score: Search relevance score
    :ivar str scene_index_id: ID of the scene index (optional)
    :ivar str scene_index_name: Name of the scene index (optional)
    :ivar dict metadata: Additional metadata (optional)
    :ivar str stream_url: URL to stream the shot
    :ivar str player_url: URL to play the shot in a player
    """

    def __init__(
        self,
        _connection,
        rtstream_id: str,
        start: float,
        end: float,
        rtstream_name: Optional[str] = None,
        text: Optional[str] = None,
        search_score: Optional[float] = None,
        scene_index_id: Optional[str] = None,
        scene_index_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        self._connection = _connection
        self.rtstream_id = rtstream_id
        self.rtstream_name = rtstream_name
        self.start = start
        self.end = end
        self.text = text
        self.search_score = search_score
        self.scene_index_id = scene_index_id
        self.scene_index_name = scene_index_name
        self.metadata = metadata
        self.stream_url = None
        self.player_url = None

    def __repr__(self) -> str:
        repr_str = (
            f"RTStreamShot("
            f"rtstream_id={self.rtstream_id}, "
            f"rtstream_name={self.rtstream_name}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"text={self.text}, "
            f"search_score={self.search_score}"
        )
        if self.scene_index_id:
            repr_str += f", scene_index_id={self.scene_index_id}"
        if self.scene_index_name:
            repr_str += f", scene_index_name={self.scene_index_name}"
        if self.metadata:
            repr_str += f", metadata={self.metadata}"
        repr_str += ")"
        return repr_str

    def generate_stream(self) -> str:
        """Generate a stream url for the shot.

        :return: The stream url
        :rtype: str
        """
        if self.stream_url:
            return self.stream_url

        stream_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.stream}",
            params={"start": int(self.start), "end": int(self.end)},
        )
        self.stream_url = stream_data.get("stream_url")
        self.player_url = stream_data.get("player_url")
        return self.stream_url

    def play(self) -> str:
        """Generate a stream url for the shot and open it in the default browser.

        :return: The stream url
        :rtype: str
        """
        self.generate_stream()
        return play_stream(self.stream_url)

    def get_embed_code(
        self,
        width: str = "100%",
        height: int = 405,
        title: str = "VideoDB Player",
        allow_fullscreen: bool = True,
        auto_generate: bool = True,
    ) -> str:
        """Generate an HTML iframe embed code for the rtstream shot.

        :param str width: Width of the iframe (default: "100%")
        :param int height: Height of the iframe in pixels (default: 405)
        :param str title: Title attribute for the iframe (default: "VideoDB Player")
        :param bool allow_fullscreen: Whether to allow fullscreen (default: True)
        :param bool auto_generate: If True and player_url is missing, auto-generate it (default: True)
        :return: HTML iframe string
        :rtype: str
        :raises ValueError: If player_url is not available
        """
        if not self.player_url and auto_generate:
            self.generate_stream()

        if not self.player_url:
            raise ValueError(
                "player_url not available. Call generate_stream() first or set auto_generate=True."
            )

        return build_iframe_embed_code(
            player_url=self.player_url,
            width=width,
            height=height,
            title=title,
            allow_fullscreen=allow_fullscreen,
        )


class RTStreamSceneIndex:
    """RTStreamSceneIndex class to interact with the rtstream scene index

    :ivar str rtstream_index_id: Unique identifier for the rtstream scene index
    :ivar str rtstream_id: ID of the rtstream this scene index belongs to
    :ivar str extraction_type: Type of extraction
    :ivar dict extraction_config: Configuration for extraction
    :ivar str prompt: Prompt for scene extraction
    :ivar str name: Name of the scene index
    :ivar str status: Status of the scene index
    :ivar str sandbox_id: Sandbox ID used for self-hosted inference
    """

    def __init__(
        self, _connection, rtstream_index_id: str, rtstream_id, **kwargs
    ) -> None:
        self._connection = _connection
        self.rtstream_index_id = rtstream_index_id
        self.rtstream_id = rtstream_id
        self.extraction_type = kwargs.get("extraction_type", None)
        self.extraction_config = kwargs.get("extraction_config", None)
        self.prompt = kwargs.get("prompt", None)
        self.name = kwargs.get("name", None)
        self.status = kwargs.get("status", None)
        self.sandbox_id = kwargs.get("sandbox_id", None)

    def __repr__(self) -> str:
        return (
            f"RTStreamSceneIndex("
            f"rtstream_index_id={self.rtstream_index_id}, "
            f"rtstream_id={self.rtstream_id}, "
            f"extraction_type={self.extraction_type}, "
            f"extraction_config={self.extraction_config}, "
            f"prompt={self.prompt}, "
            f"name={self.name}, "
            f"status={self.status}, "
            f"sandbox_id={self.sandbox_id})"
        )

    def get_scenes(self, start: int = None, end: int = None, page=1, page_size=100):
        """Get rtstream scene index scenes.

        :param int start: Start time of the scenes
        :param int end: End time of the scenes
        :param int page: Page number
        :param int page_size: Number of scenes per page
        :return: List of scenes
        :rtype: List[dict]
        """
        params = {"page": page, "page_size": page_size}
        if start and end:
            params["start"] = start
            params["end"] = end

        index_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{ApiPath.scene}/{self.rtstream_index_id}",
            params=params,
        )
        if not index_data:
            return None
        return {
            "scenes": index_data.get("scene_index_records", []),
            "next_page": index_data.get("next_page", False),
        }

    def start(self):
        """Start the scene index.

        :return: None
        :rtype: None
        """
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{ApiPath.scene}/{self.rtstream_index_id}/{ApiPath.status}",
            data={"action": "start"},
        )
        self.status = "connected"

    def stop(self):
        """Stop the scene index.

        :return: None
        :rtype: None
        """
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{ApiPath.scene}/{self.rtstream_index_id}/{ApiPath.status}",
            data={"action": "stop"},
        )
        self.status = "stopped"

    def create_alert(self, event_id, callback_url, ws_connection_id=None) -> str:
        """Create an event alert.

        :param str event_id: ID of the event
        :param str callback_url: URL to receive the alert callback
        :param str ws_connection_id: WebSocket connection ID for real-time alerts
        :return: Alert ID
        :rtype: str
        """
        data = {
            "event_id": event_id,
            "callback_url": callback_url,
        }
        if ws_connection_id:
            data["ws_connection_id"] = ws_connection_id
        alert_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{self.rtstream_index_id}/{ApiPath.alert}",
            data=data,
        )
        return alert_data.get("alert_id", None)

    def list_alerts(self):
        """List all alerts for the rtstream scene index.

        :return: List of alerts
        :rtype: List[dict]
        """
        alert_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{self.rtstream_index_id}/{ApiPath.alert}"
        )
        return alert_data.get("alerts", [])

    def enable_alert(self, alert_id):
        """Enable an alert.

        :param str alert_id: ID of the alert
        :return: None
        :rtype: None
        """
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{self.rtstream_index_id}/{ApiPath.alert}/{alert_id}/{ApiPath.status}",
            data={"action": "enable"},
        )

    def disable_alert(self, alert_id):
        """Disable an alert.

        :param str alert_id: ID of the alert
        :return: None
        :rtype: None
        """
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{self.rtstream_index_id}/{ApiPath.alert}/{alert_id}/{ApiPath.status}",
            data={"action": "disable"},
        )


class RTStreamUnderstanding:
    """RTStreamUnderstanding class to interact with a continuous understanding job.

    Produced by :meth:`RTStream.understand`. It runs VLM analysis over stream
    windows and, when ``store=True``, persists the output so it can be indexed
    later. Understanding is independent of scene indexing.

    :ivar str id: Understanding id (``und-...``)
    :ivar str rtstream_id: ID of the parent RTStream
    :ivar str status: Job status (``running`` | ``stopped`` | ``failed``)
    :ivar bool store: Whether output is persisted for later indexing
    :ivar dict segmentation: Time segmentation, e.g. ``{"type": "time", "window": "10s"}``
    :ivar list analyzers: Analyzer specs for this understanding
    :ivar dict outputs: Named output source descriptors, e.g. ``outputs["scene"]``
    """

    def __init__(
        self,
        _connection,
        understanding_id: str = None,
        rtstream_id: str = None,
        id: str = None,
        **kwargs,
    ) -> None:
        self._connection = _connection
        self.id = understanding_id or id
        self.rtstream_id = rtstream_id
        self.status = kwargs.get("status", None)
        self.store = kwargs.get("store", True)
        self.segmentation = kwargs.get("segmentation", {})
        self.analyzers = kwargs.get("analyzers", [])
        self.outputs = kwargs.get("outputs", {})

    def __repr__(self) -> str:
        return (
            f"RTStreamUnderstanding("
            f"id={self.id}, "
            f"rtstream_id={self.rtstream_id}, "
            f"status={self.status}, "
            f"store={self.store}, "
            f"analyzers={len(self.analyzers)})"
        )

    def refresh(self) -> "RTStreamUnderstanding":
        """Reload this understanding from the server.

        :return: This understanding, updated
        :rtype: :class:`RTStreamUnderstanding <RTStreamUnderstanding>`
        """
        data = self._connection.get(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.understand}/{self.id}"
        )
        if data:
            data.setdefault("understanding_id", self.id)
            data.setdefault("rtstream_id", self.rtstream_id)
            self.__init__(self._connection, **data)
        return self

    def start(self):
        """Resume processing new stream windows.

        :return: None
        :rtype: None
        """
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.understand}/{self.id}/{ApiPath.status}",
            data={"action": "start"},
        )
        self.status = "running"

    def stop(self):
        """Pause processing new stream windows. Existing records remain available.

        :return: None
        :rtype: None
        """
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.understand}/{self.id}/{ApiPath.status}",
            data={"action": "stop"},
        )
        self.status = "stopped"

    def get_records(
        self,
        start: float,
        end: float,
        output: str = "scene",
        page: int = 1,
        page_size: int = 100,
    ):
        """Get understanding output records for a time range.

        :param float start: Start Unix timestamp
        :param float end: End Unix timestamp
        :param str output: Analyzer output name (default: ``"scene"``)
        :param int page: Page number (default: 1)
        :param int page_size: Records per page (default: 100)
        :return: Records payload with ``records`` and ``next_page``
        :rtype: dict
        """
        params = {
            "start": start,
            "end": end,
            "output": output,
            "page": page,
            "page_size": page_size,
        }
        return self._connection.get(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.understand}/{self.id}/{ApiPath.records}",
            params={k: v for k, v in params.items() if v is not None},
        )


class RTStreamIndex:
    """RTStreamIndex — a continuous index over an understanding output.

    Produced by :meth:`RTStream.index`. Materializes an understanding's stored
    output into a searchable index; has its own lifecycle, separate from the
    understanding.

    :ivar str id: Index id (``idx-...``)
    :ivar str rtstream_id: ID of the parent RTStream
    :ivar str name: Index name
    :ivar str status: ``running`` | ``stopped`` | ``failed``
    :ivar list use_for: Index capabilities, e.g. ``["semantic"]``
    :ivar str source_understanding_id: Understanding this index consumes
    :ivar str output: Analyzer output name being indexed (e.g. ``"scene"``)
    """

    def __init__(self, _connection, index_id=None, rtstream_id=None, id=None, **kwargs):
        self._connection = _connection
        self.id = index_id or id
        self.rtstream_id = rtstream_id
        self.name = kwargs.get("name")
        self.status = kwargs.get("status")
        self.use_for = kwargs.get("use_for") or ["semantic"]
        self.source_understanding_id = kwargs.get("source_understanding_id")
        self.output = kwargs.get("output", "scene")

    def __repr__(self) -> str:
        return (
            f"RTStreamIndex("
            f"id={self.id}, "
            f"rtstream_id={self.rtstream_id}, "
            f"status={self.status}, "
            f"use_for={self.use_for}, "
            f"source_understanding_id={self.source_understanding_id})"
        )

    def refresh(self) -> "RTStreamIndex":
        """Reload this index from the server."""
        data = self._connection.get(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.indexes}/{self.id}"
        )
        if data:
            data.setdefault("index_id", self.id)
            data.setdefault("rtstream_id", self.rtstream_id)
            self.__init__(self._connection, **data)
        return self

    def start(self):
        """Resume materializing new understanding output into the index."""
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.indexes}/{self.id}/{ApiPath.status}",
            data={"action": "start"},
        )
        self.status = "running"

    def stop(self):
        """Pause materializing. Existing indexed records remain searchable."""
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.indexes}/{self.id}/{ApiPath.status}",
            data={"action": "stop"},
        )
        self.status = "stopped"

    def get_records(self, start=None, end=None, page: int = 1, page_size: int = 100):
        """Get materialized index records.

        :param int start: Start Unix timestamp (optional)
        :param int end: End Unix timestamp (optional)
        :param int page: Page number
        :param int page_size: Records per page
        :return: Records payload
        :rtype: dict
        """
        params = {"page": page, "page_size": page_size}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        return self._connection.get(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.indexes}/{self.id}/{ApiPath.records}",
            params=params,
        )

    def create_alert(self, event_id, callback_url, ws_connection_id=None) -> str:
        """Attach an event alert to this index.

        :param str event_id: ID of the event
        :param str callback_url: URL to receive the alert callback
        :param str ws_connection_id: WebSocket connection ID for real-time alerts (optional)
        :return: Alert ID
        :rtype: str
        """
        data = {"event_id": event_id, "callback_url": callback_url}
        if ws_connection_id:
            data["ws_connection_id"] = ws_connection_id
        alert_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.indexes}/{self.id}/{ApiPath.alert}",
            data=data,
        )
        return (alert_data or {}).get("alert_id")

    def list_alerts(self):
        """List all alerts on this index.

        :return: List of alerts
        :rtype: List[dict]
        """
        alert_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.indexes}/{self.id}/{ApiPath.alert}"
        )
        return (alert_data or {}).get("alerts", [])

    def enable_alert(self, alert_id):
        """Enable an alert on this index."""
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.indexes}/{self.id}/{ApiPath.alert}/{alert_id}/{ApiPath.status}",
            data={"action": "enable"},
        )

    def disable_alert(self, alert_id):
        """Disable an alert on this index."""
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.indexes}/{self.id}/{ApiPath.alert}/{alert_id}/{ApiPath.status}",
            data={"action": "disable"},
        )


class RTStream:
    """RTStream class to interact with the RTStream

    :ivar str id: Unique identifier for the rtstream
    :ivar str name: Name of the rtstream
    :ivar str collection_id: ID of the collection this rtstream belongs to
    :ivar str created_at: Timestamp of the rtstream creation
    :ivar int sample_rate: Sample rate of the rtstream
    :ivar str status: Status of the rtstream
    :ivar str stream_url: Generated playback URL for the rtstream segment
    :ivar str player_url: Player URL for the generated rtstream segment
    """

    def __init__(self, _connection, id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.name = kwargs.get("name", None)
        self.collection_id = kwargs.get("collection_id", None)
        self.created_at = kwargs.get("created_at", None)
        self.sample_rate = kwargs.get("sample_rate", None)
        self.status = kwargs.get("status", None)
        self.channel_id = kwargs.get("channel_id", None)
        self.stream_url = kwargs.get("stream_url", None)
        self.player_url = kwargs.get("player_url", None)

    def __repr__(self) -> str:
        return (
            f"RTStream("
            f"id={self.id}, "
            f"name={self.name}, "
            f"collection_id={self.collection_id}, "
            f"created_at={self.created_at}, "
            f"sample_rate={self.sample_rate}, "
            f"status={self.status}, "
            f"stream_url={self.stream_url}, "
            f"player_url={self.player_url})"
        )

    def start(self):
        """Connect to the rtstream.

        :return: None
        :rtype: None
        """
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.status}",
            data={"action": "start"},
        )
        self.status = "connected"

    def stop(self):
        """Disconnect from the rtstream.

        :return: None
        :rtype: None
        """
        self._connection.patch(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.status}",
            data={"action": "stop"},
        )
        self.status = "stopped"

    def export(self, name: Optional[str] = None) -> "RTStreamExportResult":
        """Export the latest completed recording as a video or audio asset.

        The stream must be stopped before exporting. The call is idempotent:
        calling it again returns the same asset without re-ingesting.

        :param str name: Name for the exported asset (optional, defaults to "{stream_name} - Recording")
        :return: Export result with the asset ID and metadata
        :rtype: :class:`RTStreamExportResult`
        """
        data = {}
        if name is not None:
            data["name"] = name

        export_data = self._connection.post(
            path=f"{ApiPath.rtstream}/{self.id}/{ApiPath.export}",
            data=data,
        )
        return RTStreamExportResult(
            video_id=export_data.get("video_id"),
            stream_url=export_data.get("stream_url"),
            player_url=export_data.get("player_url"),
            name=export_data.get("name"),
            duration=export_data.get("duration"),
        )

    def start_transcript(
        self, ws_connection_id: Optional[str] = None, engine: Optional[str] = None
    ) -> dict:
        """Start transcription for the rtstream.

        :param str ws_connection_id: WebSocket connection ID for real-time transcript updates (optional)
        :param str engine: Transcription engine (optional, server defaults to "assemblyai")
        :return: Transcription status with start time
        :rtype: dict
        """
        data = {"action": "start"}
        if engine:
            data["engine"] = engine
        if ws_connection_id:
            data["ws_connection_id"] = ws_connection_id

        return self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.transcription}",
            data=data,
        )

    def stop_transcript(self, engine: Optional[str] = None) -> dict:
        """Stop transcription for the rtstream.

        :param str engine: Transcription engine (optional, server defaults to "assemblyai")
        :return: Transcription status with start and end time
        :rtype: dict
        """
        data = {"action": "stop"}
        if engine:
            data["engine"] = engine
        return self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.transcription}",
            data=data,
        )

    def generate_stream(
        self,
        start: int,
        end: int,
        player_config: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generate a stream from the rtstream.

        :param int start: Start time of the stream in Unix timestamp format
        :param int end: End time of the stream in Unix timestamp format
        :param dict player_config: Optional player metadata with `title`,
            `description`, and `slug` keys
        :return: Stream URL
        :rtype: str
        """
        params = {"start": start, "end": end}
        if player_config:
            player_title = player_config.get("title")
            player_description = player_config.get("description")
            player_slug = player_config.get("slug")

            if player_title:
                params["player_title"] = player_title
            if player_description:
                params["player_description"] = player_description
            if player_slug:
                params["player_slug_prefix"] = player_slug

        stream_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.stream}",
            params=params,
        )
        self.stream_url = stream_data.get("stream_url")
        self.player_url = stream_data.get("player_url")
        return self.player_url

    def get_embed_code(
        self,
        width: str = "100%",
        height: int = 405,
        title: str = "VideoDB Player",
        allow_fullscreen: bool = True,
    ) -> str:
        """Generate an HTML iframe embed code for the rtstream.

        Note: Unlike other objects, RTStream does not support auto_generate
        because generate_stream() requires start and end parameters.
        Call generate_stream(start, end) first to populate player_url.

        :param str width: Width of the iframe (default: "100%")
        :param int height: Height of the iframe in pixels (default: 405)
        :param str title: Title attribute for the iframe (default: "VideoDB Player")
        :param bool allow_fullscreen: Whether to allow fullscreen (default: True)
        :return: HTML iframe string
        :rtype: str
        :raises ValueError: If player_url is not available
        """
        if not self.player_url:
            raise ValueError(
                "player_url not available. Call generate_stream(start, end) first to generate a stream."
            )

        return build_iframe_embed_code(
            player_url=self.player_url,
            width=width,
            height=height,
            title=title,
            allow_fullscreen=allow_fullscreen,
        )

    def index_scenes(
        self,
        extraction_type=SceneExtractionType.time_based,
        extraction_config={"time": 2, "frame_count": 5},
        prompt="Describe the scene",
        model_name=None,
        model_config={},
        name=None,
        ws_connection_id: Optional[str] = None,
        sandbox_id: Optional[str] = None,
    ):
        """Index scenes from the rtstream.

        :param str extraction_type: Type of extraction
        :param dict extraction_config: Configuration for extraction
        :param str prompt: Prompt for scene extraction
        :param str model_name: Name of the model
        :param dict model_config: Configuration for the model
        :param str name: Name of the scene index
        :param str ws_connection_id: WebSocket connection ID for real-time updates (optional)
        :param str sandbox_id: ID of the sandbox to route self-hosted inference to (optional)
        :return: Scene index, :class:`RTStreamSceneIndex <RTStreamSceneIndex>` object
        :rtype: :class:`videodb.rtstream.RTStreamSceneIndex`
        """
        data = {
            "extraction_type": extraction_type,
            "extraction_config": extraction_config,
            "prompt": prompt,
            "model_name": model_name,
            "model_config": model_config,
            "name": name,
        }
        if ws_connection_id:
            data["ws_connection_id"] = ws_connection_id
        if sandbox_id:
            data["sandbox_id"] = sandbox_id

        index_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            data=data,
        )
        if not index_data:
            return None
        return RTStreamSceneIndex(
            _connection=self._connection,
            rtstream_index_id=index_data.get("rtstream_index_id"),
            rtstream_id=self.id,
            extraction_type=index_data.get("extraction_type"),
            extraction_config=index_data.get("extraction_config"),
            prompt=index_data.get("prompt"),
            name=index_data.get("name"),
            status=index_data.get("status"),
            sandbox_id=index_data.get("sandbox_id"),
        )

    def index_spoken_words(
        self,
        prompt: str = None,
        segmenter: str = Segmenter.word,
        length: int = 10,
        model_name: str = None,
        model_config: dict = {},
        name: str = None,
        ws_connection_id: Optional[str] = None,
        sandbox_id: Optional[str] = None,
    ):
        """Index spoken words from the rtstream transcript.

        :param str prompt: Prompt for summarizing transcript segments
        :param Segmenter segmenter: Segmentation type (:class:`Segmenter.word`,
            :class:`Segmenter.sentence`, :class:`Segmenter.time`)
        :param int length: Length of segments (words, sentences, or seconds based on segmenter)
        :param str model_name: Name of the model
        :param dict model_config: Configuration for the model
        :param str name: Name of the spoken words index
        :param str ws_connection_id: WebSocket connection ID for real-time updates (optional)
        :param str sandbox_id: ID of the sandbox to route self-hosted inference to (optional)
        :return: Scene index, :class:`RTStreamSceneIndex <RTStreamSceneIndex>` object
        :rtype: :class:`videodb.rtstream.RTStreamSceneIndex`
        """
        extraction_config = {
            "segmenter": segmenter,
            "segmentation_value": length,
        }

        data = {
            "extraction_type": SceneExtractionType.transcript,
            "extraction_config": extraction_config,
            "prompt": prompt,
            "model_name": model_name,
            "model_config": model_config,
            "name": name,
        }
        if ws_connection_id:
            data["ws_connection_id"] = ws_connection_id
        if sandbox_id:
            data["sandbox_id"] = sandbox_id

        index_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            data=data,
        )
        if not index_data:
            return None
        return RTStreamSceneIndex(
            _connection=self._connection,
            rtstream_index_id=index_data.get("rtstream_index_id"),
            rtstream_id=self.id,
            extraction_type=index_data.get("extraction_type"),
            extraction_config=index_data.get("extraction_config"),
            prompt=index_data.get("prompt"),
            name=index_data.get("name"),
            status=index_data.get("status"),
            sandbox_id=index_data.get("sandbox_id"),
        )

    def index_audio(
        self,
        prompt: str = None,
        batch_config: dict = None,
        model_name: str = None,
        model_config: dict = {},
        name: str = None,
        ws_connection_id: Optional[str] = None,
        sandbox_id: Optional[str] = None,
    ):
        """Index audio from the rtstream transcript.

        :param str prompt: Prompt for summarizing transcript segments
        :param dict batch_config: Segmentation config with keys:
            - "type": Segmentation type ("word", "sentence", or "time")
            - "value": Segment length (words, sentences, or seconds)
        :param str model_name: Name of the model
        :param dict model_config: Configuration for the model
        :param str name: Name of the audio index
        :param str ws_connection_id: WebSocket connection ID for real-time updates (optional)
        :param str sandbox_id: ID of the sandbox to route self-hosted inference to (optional)
        :return: Scene index, :class:`RTStreamSceneIndex <RTStreamSceneIndex>` object
        :rtype: :class:`videodb.rtstream.RTStreamSceneIndex`
        """
        if batch_config is not None:
            extraction_config = {
                "segmenter": batch_config.get("type"),
                "segmentation_value": batch_config.get("value"),
            }
        else:
            extraction_config = None

        data = {
            "extraction_type": SceneExtractionType.transcript,
            "extraction_config": extraction_config,
            "prompt": prompt,
            "model_name": model_name,
            "model_config": model_config,
            "name": name,
        }
        if ws_connection_id:
            data["ws_connection_id"] = ws_connection_id
        if sandbox_id:
            data["sandbox_id"] = sandbox_id

        index_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            data=data,
        )
        if not index_data:
            return None
        return RTStreamSceneIndex(
            _connection=self._connection,
            rtstream_index_id=index_data.get("rtstream_index_id"),
            rtstream_id=self.id,
            extraction_type=index_data.get("extraction_type"),
            extraction_config=index_data.get("extraction_config"),
            prompt=index_data.get("prompt"),
            name=index_data.get("name"),
            status=index_data.get("status"),
            sandbox_id=index_data.get("sandbox_id"),
        )

    def index_visuals(
        self,
        prompt: str = None,
        batch_config: dict = None,
        model_name: str = None,
        model_config: dict = {},
        name: str = None,
        ws_connection_id: Optional[str] = None,
        sandbox_id: Optional[str] = None,
    ):
        """Index visuals (scenes) from the rtstream.

        :param str prompt: Prompt for scene description
        :param dict batch_config: Frame extraction config with keys:
            - "type": Only "time" is supported
            - "value": Window size in seconds
            - "frame_count": Number of frames to extract per window
        :param str model_name: Name of the model
        :param dict model_config: Configuration for the model
        :param str name: Name of the visual index
        :param str ws_connection_id: WebSocket connection ID for real-time updates (optional)
        :param str sandbox_id: ID of the sandbox to route self-hosted inference to (optional)
        :return: Scene index, :class:`RTStreamSceneIndex <RTStreamSceneIndex>` object
        :rtype: :class:`videodb.rtstream.RTStreamSceneIndex`
        """
        if batch_config is not None:
            extraction_config = {
                "time": batch_config.get("value"),
                "frame_count": batch_config.get("frame_count"),
            }
        else:
            extraction_config = None

        data = {
            "extraction_type": SceneExtractionType.time_based,
            "extraction_config": extraction_config,
            "prompt": prompt,
            "model_name": model_name,
            "model_config": model_config,
            "name": name,
        }
        if ws_connection_id:
            data["ws_connection_id"] = ws_connection_id
        if sandbox_id:
            data["sandbox_id"] = sandbox_id

        index_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            data=data,
        )
        if not index_data:
            return None
        return RTStreamSceneIndex(
            _connection=self._connection,
            rtstream_index_id=index_data.get("rtstream_index_id"),
            rtstream_id=self.id,
            extraction_type=index_data.get("extraction_type"),
            extraction_config=index_data.get("extraction_config"),
            prompt=index_data.get("prompt"),
            name=index_data.get("name"),
            status=index_data.get("status"),
            sandbox_id=index_data.get("sandbox_id"),
        )

    def list_scene_indexes(self):
        """List all scene indexes for the rtstream.

        :return: List of :class:`RTStreamSceneIndex <RTStreamSceneIndex>` objects
        :rtype: List[:class:`videodb.rtstream.RTStreamSceneIndex`]
        """
        index_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.index}/{ApiPath.scene}"
        )
        return [
            RTStreamSceneIndex(
                _connection=self._connection,
                rtstream_index_id=index.get("rtstream_index_id"),
                rtstream_id=self.id,
                extraction_type=index.get("extraction_type"),
                extraction_config=index.get("extraction_config"),
                prompt=index.get("prompt"),
                name=index.get("name"),
                status=index.get("status"),
                sandbox_id=index.get("sandbox_id"),
            )
            for index in index_data.get("scene_indexes", [])
        ]

    def get_scene_index(self, index_id: str) -> RTStreamSceneIndex:
        """Get a scene index by its ID.

        :param str index_id: ID of the scene index
        :return: Scene index, :class:`RTStreamSceneIndex <RTStreamSceneIndex>` object
        :rtype: :class:`videodb.rtstream.RTStreamSceneIndex`
        """
        index_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.index}/{index_id}"
        )
        return RTStreamSceneIndex(
            _connection=self._connection,
            rtstream_index_id=index_data.get("rtstream_index_id"),
            rtstream_id=self.id,
            extraction_type=index_data.get("extraction_type"),
            extraction_config=index_data.get("extraction_config"),
            prompt=index_data.get("prompt"),
            name=index_data.get("name"),
            status=index_data.get("status"),
            sandbox_id=index_data.get("sandbox_id"),
        )

    def understand(
        self,
        segmentation: Dict = None,
        analyzers: List[Dict] = None,
        store: bool = True,
        ws_connection_id: str = None,
        trigger: str = None,
    ) -> "RTStreamUnderstanding":
        """Start a continuous understanding job on the stream.

        Understanding is independent of indexing: it produces VLM output per
        stream window and (when ``store=True``) persists it so it can be indexed
        later. Supports one ``vlm`` or ``cua`` (computer-use) analyzer with time
        segmentation.

        :param dict segmentation: Time segmentation, e.g. ``{"type": "time", "window": "10s"}``
        :param list analyzers: Exactly one analyzer spec, e.g.
            ``[{"type": "vlm", "name": "scene", "sampling": {"frame_count": 5}, "config": {"prompt": "...", "model": "basic"}}]``
            For a computer-use agent, ``[{"type": "cua", "name": "action", "sampling": {"frame_count": 1}, "config": {"prompt": "<task>", "past_window": {"frames": 3, "actions": 5}}}]``
            (a ``cua`` analyzer defaults its model to Holo)
        :param bool store: Persist output for later indexing (default: True)
        :param str ws_connection_id: WebSocket connection ID for real-time updates (optional)
        :param str trigger: ``"interval"`` (default) samples on a fixed cadence;
            ``"on_demand"`` produces one output per external trigger (CUA loop)
        :return: The understanding job, :class:`RTStreamUnderstanding <RTStreamUnderstanding>` object
        :rtype: :class:`videodb.rtstream.RTStreamUnderstanding`
        """
        data = {
            "segmentation": segmentation or {},
            "analyzers": analyzers or [],
            "store": store,
        }
        if trigger:
            data["trigger"] = trigger
        if ws_connection_id:
            data["ws_connection_id"] = ws_connection_id
        understanding_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.understand}",
            data=data,
        )
        if not understanding_data:
            return None
        understanding_data.setdefault("rtstream_id", self.id)
        return RTStreamUnderstanding(
            _connection=self._connection, **understanding_data
        )

    def get_understanding(self, understanding_id: str) -> "RTStreamUnderstanding":
        """Get an understanding job by id.

        :param str understanding_id: ID of the understanding job
        :return: The understanding job, :class:`RTStreamUnderstanding <RTStreamUnderstanding>` object
        :rtype: :class:`videodb.rtstream.RTStreamUnderstanding`
        """
        if not understanding_id:
            raise ValueError("understanding_id is required")
        understanding_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.understand}/{understanding_id}"
        )
        if not understanding_data:
            return None
        understanding_data.setdefault("rtstream_id", self.id)
        return RTStreamUnderstanding(
            _connection=self._connection, **understanding_data
        )

    def list_understanding(self) -> List["RTStreamUnderstanding"]:
        """List all understanding jobs on the stream.

        :return: List of understanding jobs
        :rtype: List[:class:`RTStreamUnderstanding <RTStreamUnderstanding>`]
        """
        data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.understand}"
        )
        results = (data or {}).get("understandings") or []
        for item in results:
            item.setdefault("rtstream_id", self.id)
        return [
            RTStreamUnderstanding(_connection=self._connection, **item)
            for item in results
        ]

    def index(self, source, name=None, use_for=None) -> "RTStreamIndex":
        """Materialize an understanding output into a searchable index.

        :param dict source: understanding output descriptor, e.g.
            ``understanding.outputs["scene"]``
        :param str name: index name (optional)
        :param list use_for: capabilities; defaults to ``["semantic"]``
        :return: The index, :class:`RTStreamIndex <RTStreamIndex>` object
        :rtype: :class:`videodb.rtstream.RTStreamIndex`
        """
        data = {"source": source}
        if name is not None:
            data["name"] = name
        if use_for is not None:
            data["use_for"] = use_for
        index_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.indexes}", data=data
        )
        if not index_data:
            return None
        index_data.setdefault("rtstream_id", self.id)
        return RTStreamIndex(_connection=self._connection, **index_data)

    def get_index(self, index_id: str) -> "RTStreamIndex":
        """Get an index by id.

        :param str index_id: ID of the index
        :return: :class:`RTStreamIndex <RTStreamIndex>` object
        :rtype: :class:`videodb.rtstream.RTStreamIndex`
        """
        if not index_id:
            raise ValueError("index_id is required")
        index_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.indexes}/{index_id}"
        )
        if not index_data:
            return None
        index_data.setdefault("rtstream_id", self.id)
        return RTStreamIndex(_connection=self._connection, **index_data)

    def list_indexes(self) -> List["RTStreamIndex"]:
        """List all indexes on the stream.

        :return: List of indexes
        :rtype: List[:class:`RTStreamIndex <RTStreamIndex>`]
        """
        data = self._connection.get(f"{ApiPath.rtstream}/{self.id}/{ApiPath.indexes}")
        results = (data or {}).get("indexes") or []
        for item in results:
            item.setdefault("rtstream_id", self.id)
        return [RTStreamIndex(_connection=self._connection, **item) for item in results]

    def get_transcript(
        self,
        page=1,
        page_size=100,
        start=None,
        end=None,
        since=None,
        engine=None,
    ):
        """Get transcription data from the rtstream.

        :param int page: Page number (default: 1)
        :param int page_size: Items per page (default: 100, max: 1000)
        :param float start: Start timestamp filter (optional)
        :param float end: End timestamp filter (optional)
        :param float since: For polling - only get transcriptions after this timestamp (optional)
        :param str engine: Transcription engine (default: "AAIS")
        :return: Transcription data with segments and metadata
        :rtype: dict
        """
        params = {
            "engine": engine,
            "page": page,
            "page_size": page_size,
        }
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        if since is not None:
            params["since"] = since

        transcription_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.transcription}",
            params=params,
        )
        return transcription_data

    def search(
        self,
        query: str,
        index_id: Optional[str] = None,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[float] = None,
        dynamic_score_percentage: Optional[float] = None,
        filter: Optional[List[Dict[str, Any]]] = None,
    ) -> RTStreamSearchResult:
        """Search across scene index records for the rtstream.

        :param str query: Query to search for
        :param str index_id: Filter by specific scene index (optional)
        :param int result_threshold: Number of results to return (optional)
        :param float score_threshold: Minimum score threshold (optional)
        :param float dynamic_score_percentage: Percentage of dynamic score to consider (optional)
        :param list filter: Additional metadata filters (optional)
        :return: :class:`RTStreamSearchResult <RTStreamSearchResult>` object
        :rtype: :class:`videodb.rtstream.RTStreamSearchResult`
        """
        data = {"query": query}

        if index_id is not None:
            data["scene_index_id"] = index_id
        if result_threshold is not None:
            data["result_threshold"] = result_threshold
        if score_threshold is not None:
            data["score_threshold"] = score_threshold
        if dynamic_score_percentage is not None:
            data["dynamic_score_percentage"] = dynamic_score_percentage
        if filter is not None:
            data["filter"] = filter

        search_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.search}",
            data=data,
        )

        results = search_data.get("results", [])
        shots = [
            RTStreamShot(
                _connection=self._connection,
                rtstream_id=self.id,
                rtstream_name=self.name,
                start=result.get("start"),
                end=result.get("end"),
                text=result.get("text"),
                search_score=result.get("score"),
                scene_index_id=result.get("scene_index_id"),
                scene_index_name=result.get("scene_index_name"),
                metadata=result.get("metadata"),
            )
            for result in results
        ]
        return RTStreamSearchResult(
            collection_id=self.collection_id,
            shots=shots,
        )
