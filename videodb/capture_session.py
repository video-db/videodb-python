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
        self.rtstreams = data.get("rtstreams", [])
        self.exported_video_id = data.get("exported_video_id")
        self.metadata = data.get("metadata", {})

    def get_rtstream(self, category: str) -> List[RTStream]:
        """Get list of RTStreams by category.
        
        :param str category: Category to filter by ("mics", "displays", "system_audio")
        :return: List of :class:`RTStream <RTStream>` objects
        :rtype: List[:class:`videodb.rtstream.RTStream`]
        """
        filtered_streams = []
        print(self.rtstreams)
        for rts_data in self.rtstreams:
            rts_id = rts_data.get("rtstream_id") or rts_data.get("id")
            if not rts_id:
                continue
                
            # Names can vary: "mic", "Microphone", "screen", "Screen Share", etc.
            name = (rts_data.get("name") or "").lower()
            
            is_match = False
            
            if category == "mics" and "mic" in name:
                    is_match = True
            elif category == "displays" and ("screen" in name or "display" in name):
                    is_match = True
            elif category == "system_audio" and "system" in name:
                    is_match = True
            elif category == "cameras":
                if "camera" in name:
                    is_match = True
            
            if is_match:
                # Remove keys we pass explicitly to avoid duplicates
                extra_data = {k: v for k, v in rts_data.items() if k not in ("id", "rtstream_id", "name", "collection_id")}
                stream = RTStream(
                    self._connection,
                    id=rts_id,
                    collection_id=self.collection_id,
                    name=rts_data.get("name"),
                    **extra_data
                )
                filtered_streams.append(stream)
                
        return filtered_streams
