from videodb._constants import (
    ApiPath,
)


class Image:
    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self.name = kwargs.get("name", None)
        self.url = kwargs.get("url", None)

    def __repr__(self) -> str:
        return (
            f"Image("
            f"id={self.id}, "
            f"collection_id={self.collection_id}, "
            f"name={self.name}, "
            f"url={self.url})"
        )

    def delete(self) -> None:
        self._connection.delete(f"{ApiPath.image}/{self.id}")


class Frame(Image):
    def __init__(
        self,
        _connection,
        id: str,
        video_id: str,
        scene_id: str,
        url: str,
        frame_time: float,
        description: str,
    ):
        super().__init__(_connection=_connection, id=id, collection_id=None, url=url)
        self.scene_id = scene_id
        self.video_id = video_id
        self.frame_time = frame_time
        self.description = description

    def __repr__(self) -> str:
        return (
            f"Frame("
            f"id={self.id}, "
            f"video_id={self.video_id}, "
            f"scene_id={self.scene_id}, "
            f"url={self.url}, "
            f"frame_time={self.frame_time}, "
            f"description={self.description})"
        )

    def to_json(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "scene_id": self.scene_id,
            "url": self.url,
            "frame_time": self.frame_time,
            "description": self.description,
        }
