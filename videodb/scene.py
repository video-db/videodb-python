from typing import List

from videodb._constants import ApiPath

from videodb.image import Frame


class SceneExtractionConfig:
    def __init__(
        self,
        time: int = 5,
        threshold: int = 20,
        frame_count: int = 1,
        select_frame: str = "first",
    ):
        self.time = time
        self.threshold = threshold
        self.frame_count = frame_count
        self.select_frame = select_frame

    def __repr__(self) -> str:
        return (
            f"SceneExtractionConfig("
            f"time={self.time}, "
            f"threshold={self.threshold}, "
            f"frame_count={self.frame_count}, "
            f"select_frame={self.select_frame})"
        )


class Scene:
    def __init__(
        self,
        id: str,
        video_id: str,
        start: float,
        end: float,
        frames: List[Frame],
        description: str,
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
        config: SceneExtractionConfig,
        scenes: List[Scene],
    ) -> None:
        self._connection = _connection
        self.id = id
        self.video_id = video_id
        self.config: SceneExtractionConfig = config
        self.scenes: List[Scene] = scenes

    def __repr__(self) -> str:
        return (
            f"SceneCollection("
            f"id={self.id}, "
            f"video_id={self.video_id}, "
            f"config={self.config.__dict__}, "
            f"scenes={self.scenes})"
        )

    def delete(self) -> None:
        self._connection.delete(
            path=f"{ApiPath.video}/{self.video_id}/{ApiPath.scenes}/{self.id}"
        )
