import copy
import logging
import uuid

from typing import Optional, Union

from videodb._constants import MaxSupported, TextStyle

logger = logging.getLogger(__name__)


def validate_max_supported(
    duration: Union[int, float], max_duration: Union[int, float], attribute: str = ""
) -> Union[int, float, None]:
    if duration is None:
        return 0
    if duration is not None and max_duration is not None and duration > max_duration:
        logger.warning(
            f"{attribute}: {duration} is greater than max supported: {max_duration}"
        )
    return duration


class MediaAsset:
    def __init__(self, asset_id: str) -> None:
        self.asset_id: str = asset_id

    def to_json(self) -> dict:
        return self.__dict__


class VideoAsset(MediaAsset):
    def __init__(
        self,
        asset_id: str,
        start: Optional[float] = 0,
        end: Optional[float] = None,
    ) -> None:
        super().__init__(asset_id)
        self.start: int = start
        self.end: Union[int, None] = end

    def to_json(self) -> dict:
        return copy.deepcopy(self.__dict__)

    def __repr__(self) -> str:
        return (
            f"VideoAsset("
            f"asset_id={self.asset_id}, "
            f"start={self.start}, "
            f"end={self.end})"
        )


class AudioAsset(MediaAsset):
    def __init__(
        self,
        asset_id: str,
        start: Optional[float] = 0,
        end: Optional[float] = None,
        disable_other_tracks: Optional[bool] = True,
        fade_in_duration: Optional[Union[int, float]] = 0,
        fade_out_duration: Optional[Union[int, float]] = 0,
    ):
        super().__init__(asset_id)
        self.start: int = start
        self.end: Union[int, None] = end
        self.disable_other_tracks: bool = disable_other_tracks
        self.fade_in_duration: Union[int, float] = validate_max_supported(
            fade_in_duration, MaxSupported.fade_duration, "fade_in_duration"
        )
        self.fade_out_duration: Union[int, float] = validate_max_supported(
            fade_out_duration, MaxSupported.fade_duration, "fade_out_duration"
        )

    def to_json(self) -> dict:
        return copy.deepcopy(self.__dict__)

    def __repr__(self) -> str:
        return (
            f"AudioAsset("
            f"asset_id={self.asset_id}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"disable_other_tracks={self.disable_other_tracks}, "
            f"fade_in_duration={self.fade_in_duration}, "
            f"fade_out_duration={self.fade_out_duration})"
        )


class ImageAsset(MediaAsset):
    def __init__(
        self,
        asset_id: str,
        width: Union[int, str] = 100,
        height: Union[int, str] = 100,
        x: Union[int, str] = 80,
        y: Union[int, str] = 20,
        duration: Optional[int] = None,
    ) -> None:
        super().__init__(asset_id)
        self.width = width
        self.height = height
        self.x = x
        self.y = y
        self.duration = duration

    def to_json(self) -> dict:
        return copy.deepcopy(self.__dict__)

    def __repr__(self) -> str:
        return (
            f"ImageAsset("
            f"asset_id={self.asset_id}, "
            f"width={self.width}, "
            f"height={self.height}, "
            f"x={self.x}, "
            f"y={self.y}, "
            f"duration={self.duration})"
        )


class TextAsset(MediaAsset):
    def __init__(
        self,
        text: str,
        duration: Optional[int] = None,
        style: TextStyle = TextStyle(),
    ) -> None:
        super().__init__(f"txt-{str(uuid.uuid4())}")
        self.text = text
        self.duration = duration
        self.style: TextStyle = style

    def to_json(self) -> dict:
        return {
            "text": copy.deepcopy(self.text),
            "asset_id": copy.deepcopy(self.asset_id),
            "duration": copy.deepcopy(self.duration),
            "style": copy.deepcopy(self.style.__dict__),
        }

    def __repr__(self) -> str:
        return (
            f"TextAsset("
            f"text={self.text}, "
            f"asset_id={self.asset_id}, "
            f"duration={self.duration}, "
            f"style={self.style})"
        )
