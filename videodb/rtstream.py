from videodb._constants import (
    ApiPath,
    SceneExtractionType,
)


class RTStreamSceneIndex:
    def __init__(
        self, _connection, rtstream_index_id: str, rtstream_id, **kwargs
    ) -> None:
        self._connection = _connection
        self.rtstream_index_id = rtstream_index_id
        self.rtstream_id = rtstream_id
        self.name = kwargs.get("name", None)
        self.status = kwargs.get("status", None)

    def __repr__(self) -> str:
        return (
            f"RTStreamSceneIndex("
            f"rtstream_index_id={self.rtstream_index_id}, "
            f"rtstream_id={self.rtstream_id}, "
            f"name={self.name}, "
            f"status={self.status})"
        )

    def get_scene_index(self):
        index_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{ApiPath.scene}/{self.rtstream_index_id}"
        )
        if not index_data:
            return None
        return index_data.get("scene_index_records", [])

    def start(self):
        return self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{ApiPath.scene}/{self.rtstream_index_id}/{ApiPath.status}",
            data={"status": "running"},
        )

    def stop(self):
        return self._connection.patch(
            f"{ApiPath.rtstream}/{self.rtstream_id}/{ApiPath.index}/{ApiPath.scene}/{self.rtstream_index_id}/{ApiPath.status}",
            data={"status": "stopped"},
        )


class RTStream:
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

    def stream(self, start, end):
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
        model_name="GPT4o",
        model_config={},
        name=None,
    ):
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
            name=index_data.get("name"),
            status=index_data.get("status"),
        )

    def list_scene_indexes(self):
        index_data = self._connection.get(
            f"{ApiPath.rtstream}/{self.id}/{ApiPath.index}/{ApiPath.scene}"
        )
        return [
            RTStreamSceneIndex(
                _connection=self._connection,
                rtstream_index_id=index.get("rtstream_index_id"),
                rtstream_id=self.id,
                name=index.get("name"),
                status=index.get("status"),
            )
            for index in index_data.get("scene_indexes", [])
        ]
