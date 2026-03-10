from typing import List, Optional
from videodb._constants import ApiPath
from videodb.capture import Channel, VideoChannel, AudioChannel
from videodb.rtstream import RTStream


class CaptureSession:
    """CaptureSession class representing a capture session.

    :ivar str id: Unique identifier for the session
    :ivar str collection_id: ID of the collection this session belongs to
    :ivar str end_user_id: ID of the end user
    :ivar str client_id: Client-provided session ID
    :ivar str status: Current status of the session
    :ivar list channels: List of channel dicts with id, name, type, is_primary
    :ivar str primary_video_channel_id: Channel ID of the primary video source
    :ivar str export_status: Current export status (exporting, exported, failed)
    :ivar dict exported_videos: Mapping of channel_id to exported video_id
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
        self.channels = []
        for ch_data in data.get("channels", []):
            ch_type = ch_data.get("type")
            ch_id = ch_data.get("channel_id", "")
            ch_name = ch_data.get("name", "")
            if ch_type == "video":
                ch = VideoChannel(id=ch_id, name=ch_name)
            else:
                ch = AudioChannel(id=ch_id, name=ch_name)
            ch.store = ch_data.get("store", False)
            ch.is_primary = ch_data.get("is_primary", False)
            self.channels.append(ch)

        self.primary_video_channel_id = data.get("primary_video_channel_id")
        self.export_status = data.get("export_status")

        self.rtstreams = []
        for rts_data in data.get("rtstreams", []):
            if not isinstance(rts_data, dict):
                continue
            stream = RTStream(self._connection, **rts_data)
            self.rtstreams.append(stream)

    @property
    def displays(self) -> List[VideoChannel]:
        """Video channels in the session.

        :return: List of VideoChannel objects
        :rtype: list[VideoChannel]
        """
        return [ch for ch in self.channels if isinstance(ch, VideoChannel)]

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

    def export(self, video_channel_id: Optional[str] = None, connection_id: Optional[str] = None) -> dict:
        """Trigger export for this capture session.

        Call repeatedly to poll for completion. Returns ``export_status``
        of ``"exporting"`` while in progress, ``"exported"`` with
        ``video_id``, ``stream_url``, and ``player_url`` when done.

        :param str video_channel_id: Optional channel ID of the video to export.
            Defaults to the primary video channel.
        :param str connection_id: Optional websocket connection ID for push
            notification when export completes.
        :return: Export response with session_id, video_channel_id,
            export_status, and video_id/stream_url/player_url when exported.
        :rtype: dict
        """
        data = {}
        if video_channel_id:
            data["video_channel_id"] = video_channel_id
        if connection_id:
            data["connection_id"] = connection_id

        return self._connection.post(
            path=f"{ApiPath.collection}/{self.collection_id}/{ApiPath.capture}/{ApiPath.session}/{self.id}/{ApiPath.export}",
            data=data,
        )
