from typing import List

from videodb._constants import ApiPath

from videodb.image import Frame


class Scene:
    def __init__(
        self,
        video_id: str,
        start: float,
        end: float,
        description: str,
        id: str = None,
        frames: List[Frame] = [],
    ):
        self.id = id
        self.video_id = video_id
        self.start = start
        self.end = end
        self.frames: List[Frame] = frames
        self.description = description

    def __repr__(self) -> str:
        return (
            f"Scene("
            f"id={self.id}, "
            f"video_id={self.video_id}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"frames={self.frames}, "
            f"description={self.description})"
        )

    def to_json(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "start": self.start,
            "end": self.end,
            "frames": [frame.to_json() for frame in self.frames],
            "description": self.description,
        }


class SceneCollection:
    def __init__(
        self,
        _connection,
        id: str,
        video_id: str,
        config: dict,
        scenes: List[Scene],
    ) -> None:
        self._connection = _connection
        self.id = id
        self.video_id = video_id
        self.config: dict = config
        self.scenes: List[Scene] = scenes

    def __repr__(self) -> str:
        return (
            f"SceneCollection("
            f"id={self.id}, "
            f"video_id={self.video_id}, "
            f"config={self.config}, "
            f"scenes={self.scenes})"
        )

    def delete(self) -> None:
        self._connection.delete(
            path=f"{ApiPath.video}/{self.video_id}/{ApiPath.scenes}/{self.id}"
        )
