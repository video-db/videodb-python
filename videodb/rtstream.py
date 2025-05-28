from videodb._constants import (
    ApiPath,
    SceneExtractionType,
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
