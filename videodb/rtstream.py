from videodb._constants import (
    ApiPath,
)


class RtStream:
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
            f"RtStream("
            f"id={self.id}, "
            f"name={self.name}, "
            f"collection_id={self.collection_id}, "
            f"created_at={self.created_at}, "
            f"sample_rate={self.sample_rate}, "
            f"status={self.status})"
        )

    def stream(self, start, end):
        stream_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.stream}",
            params={"start": start, "end": end},
        )
        return stream_data.get("stream_url", None)
