from typing import List
from videodb.rtstream import RTStream


class CaptureSession:
    """CaptureSession class representing a capture session.

    :ivar str id: Unique identifier for the session
    :ivar str collection_id: ID of the collection this session belongs to
    :ivar str end_user_id: ID of the end user
    :ivar str client_id: Client-provided session ID
    :ivar str status: Current status of the session
    """

    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self._update_attributes(kwargs)

    def __repr__(self) -> str:
        return (
            f"CaptureSession("
            f"id={self.id}, "
            f"status={getattr(self, 'status', None)}, "
            f"collection_id={self.collection_id}, "
            f"end_user_id={getattr(self, 'end_user_id', None)})"
        )

    def _update_attributes(self, data: dict) -> None:
        """Update instance attributes from API response data."""
        self.end_user_id = data.get("end_user_id")
        self.client_id = data.get("client_id")
        self.status = data.get("status")
        self.callback_url = data.get("callback_url")
        self.exported_video_id = data.get("exported_video_id")
        self.metadata = data.get("metadata", {})

        self.rtstreams = []
        for rts_data in data.get("rtstreams", []):
            if not isinstance(rts_data, dict):
                continue
            stream = RTStream(self._connection, **rts_data)
            self.rtstreams.append(stream)

    def get_rtstream(self, category: str) -> List[RTStream]:
        """Get list of RTStreams by category.

        :param str category: Category to filter by. Use :class:`RTStreamChannelType` constants:
            ``RTStreamChannelType.mic``, ``RTStreamChannelType.screen``, ``RTStreamChannelType.system_audio``.
        :return: List of :class:`RTStream <RTStream>` objects
        :rtype: List[:class:`videodb.rtstream.RTStream`]
        """
        filtered_streams = []

        for stream in self.rtstreams:
            channel_id = getattr(stream, "channel_id", "") or ""
            if str(channel_id).lower() == category.lower():
                filtered_streams.append(stream)

        return filtered_streams
