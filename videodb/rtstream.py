from typing import Optional, List, Dict, Any

from videodb._constants import (
    ApiPath,
    SceneExtractionType,
    Segmenter,
)
from videodb._utils._video import play_stream


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


class RTStreamSceneIndex:
    """RTStreamSceneIndex class to interact with the rtstream scene index

    :ivar str rtstream_index_id: Unique identifier for the rtstream scene index
    :ivar str rtstream_id: ID of the rtstream this scene index belongs to
    :ivar str extraction_type: Type of extraction
    :ivar dict extraction_config: Configuration for extraction
    :ivar str prompt: Prompt for scene extraction
    :ivar str name: Name of the scene index
    :ivar str status: Status of the scene index
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

    def __repr__(self) -> str:
        return (
            f"RTStreamSceneIndex("
            f"rtstream_index_id={self.rtstream_index_id}, "
            f"rtstream_id={self.rtstream_id}, "
            f"extraction_type={self.extraction_type}, "
            f"extraction_config={self.extraction_config}, "
            f"prompt={self.prompt}, "
            f"name={self.name}, "
            f"status={self.status})"
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

    def create_alert(self, event_id, callback_url) -> str:
        """Create an event alert.

        :param str event_id: ID of the event
        :param str callback_url: URL to receive the alert callback
        :return: Alert ID
        :rtype: str
        """
        alert_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{self.rtstream_index_id}/{ApiPath.alert}",
            data={
                "event_id": event_id,
                "callback_url": callback_url,
            },
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


class RTStream:
    """RTStream class to interact with the RTStream

    :ivar str id: Unique identifier for the rtstream
    :ivar str name: Name of the rtstream
    :ivar str collection_id: ID of the collection this rtstream belongs to
    :ivar str created_at: Timestamp of the rtstream creation
    :ivar int sample_rate: Sample rate of the rtstream
    :ivar str status: Status of the rtstream
    """

    def __init__(self, _connection, id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.name = kwargs.get("name", None)
        self.collection_id = kwargs.get("collection_id", None)
        self.created_at = kwargs.get("created_at", None)
        self.sample_rate = kwargs.get("sample_rate", None)
        self.status = kwargs.get("status", None)

    def __repr__(self) -> str:
        return (
            f"RTStream("
            f"id={self.id}, "
            f"name={self.name}, "
            f"collection_id={self.collection_id}, "
            f"created_at={self.created_at}, "
            f"sample_rate={self.sample_rate}, "
            f"status={self.status})"
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

    def generate_stream(self, start, end):
        """Generate a stream from the rtstream.

        :param int start: Start time of the stream in Unix timestamp format
        :param int end: End time of the stream in Unix timestamp format
        :return: Stream URL
        :rtype: str
        """
        stream_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.stream}",
            params={"start": start, "end": end},
        )
        return stream_data.get("stream_url", None)

    def index_scenes(
        self,
        extraction_type=SceneExtractionType.time_based,
        extraction_config={"time": 2, "frame_count": 5},
        prompt="Describe the scene",
        model_name=None,
        model_config={},
        name=None,
    ):
        """Index scenes from the rtstream.

        :param str extraction_type: Type of extraction
        :param dict extraction_config: Configuration for extraction
        :param str prompt: Prompt for scene extraction
        :param str model_name: Name of the model
        :param dict model_config: Configuration for the model
        :param str name: Name of the scene index
        :return: Scene index, :class:`RTStreamSceneIndex <RTStreamSceneIndex>` object
        :rtype: :class:`videodb.rtstream.RTStreamSceneIndex`
        """
        index_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            data={
                "extraction_type": extraction_type,
                "extraction_config": extraction_config,
                "prompt": prompt,
                "model_name": model_name,
                "model_config": model_config,
                "name": name,
            },
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
        )

    def index_spoken_words(
        self,
        prompt: str = None,
        segmenter: str = Segmenter.word,
        length: int = 10,
        model_name: str = None,
        model_config: dict = {},
        name: str = None,
    ):
        """Index spoken words from the rtstream transcript.

        :param str prompt: Prompt for summarizing transcript segments
        :param Segmenter segmenter: Segmentation type (:class:`Segmenter.word`,
            :class:`Segmenter.sentence`, :class:`Segmenter.time`)
        :param int length: Length of segments (words, sentences, or seconds based on segmenter)
        :param str model_name: Name of the model
        :param dict model_config: Configuration for the model
        :param str name: Name of the spoken words index
        :return: Scene index, :class:`RTStreamSceneIndex <RTStreamSceneIndex>` object
        :rtype: :class:`videodb.rtstream.RTStreamSceneIndex`
        """
        extraction_config = {
            "segmenter": segmenter,
            "segmentation_value": length,
        }

        index_data = self._connection.post(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            data={
                "extraction_type": SceneExtractionType.transcript,
                "extraction_config": extraction_config,
                "prompt": prompt,
                "model_name": model_name,
                "model_config": model_config,
                "name": name,
            },
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
        )

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
    ) -> List[RTStreamShot]:
        """Search across scene index records for the rtstream.

        :param str query: Query to search for
        :param str index_id: Filter by specific scene index (optional)
        :param int result_threshold: Number of results to return (optional)
        :param float score_threshold: Minimum score threshold (optional)
        :param float dynamic_score_percentage: Percentage of dynamic score to consider (optional)
        :param list filter: Additional metadata filters (optional)
        :return: List of :class:`RTStreamShot <RTStreamShot>` objects
        :rtype: List[:class:`videodb.rtstream.RTStreamShot`]
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
        return [
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
