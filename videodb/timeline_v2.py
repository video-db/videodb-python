from typing import List, Optional, Union
from enum import Enum


class AssetType(str, Enum):
    video = "video"
    image = "image"


class Fit(str, Enum):
    crop = "crop"
    cover = "cover"
    contain = "contain"


class Position(str, Enum):
    top = "top"
    bottom = "bottom"
    left = "left"
    right = "right"
    center = "center"
    top_left = "top-left"
    top_right = "top-right"
    bottom_left = "bottom-left"
    bottom_right = "bottom-right"


class Filter(str, Enum):
    """A filter effect to apply to the Clip."""

    blur = "blur"
    boost = "boost"
    contrast = "contrast"
    darken = "darken"
    greyscale = "greyscale"
    lighten = "lighten"
    muted = "muted"
    negative = "negative"


class Offset:
    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    def to_json(self):
        return {
            "x": self.x,
            "y": self.y,
        }


class Crop:
    def __init__(self, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0):
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left

    def to_json(self):
        return {
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "left": self.left,
        }


class Transition:
    def __init__(self, in_: str = None, out: str = None):
        self.in_ = in_
        self.out = out

    def to_json(self):
        return {
            "in": self.in_,
            "out": self.out,
        }


class BaseAsset:
    """The type of asset to display for the duration of the Clip."""

    type: AssetType


class VideoAsset(BaseAsset):
    """The VideoAsset is used to create video sequences from video files. The src must be a publicly accessible URL to a video resource"""

    type = AssetType.video

    def __init__(
        self,
        id: str,
        trim: int = 0,
        volume: float = 1,
        crop: Optional[Crop] = None,
    ):
        if trim < 0:
            raise ValueError("trim must be non-negative")
        if not (0 <= volume <= 2):
            raise ValueError("volume must be between 0 and 2")

        self.id = id
        self.trim = trim
        self.volume = volume
        self.crop = crop if crop is not None else Crop()

    def to_json(self):
        return {
            "type": self.type,
            "id": self.id,
            "trim": self.trim,
            "volume": self.volume,
            "crop": self.crop.to_json(),
        }


class ImageAsset(BaseAsset):
    """The ImageAsset is used to create video from images to compose an image. The src must be a publicly accessible URL to an image resource such as a jpg or png file."""

    type = AssetType.image

    def __init__(self, id: str, trim: int = 0, crop: Optional[Crop] = None):
        if trim < 0:
            raise ValueError("trim must be non-negative")

        self.id = id
        self.trim = trim
        self.crop = crop if crop is not None else Crop()

    def to_json(self):
        return {
            "type": self.type,
            "id": self.id,
            "trim": self.trim,
            "crop": self.crop.to_json(),
        }


AnyAsset = Union[VideoAsset, ImageAsset]


class Clip:
    """A clip is a container for a specific type of asset, i.e. a title, image, video, audio or html. You use a Clip to define when an asset will display on the timeline, how long it will play for and transitions, filters and effects to apply to it."""

    def __init__(
        self,
        asset: AnyAsset,
        start: Union[float, int],
        length: Union[float, int],
        transition: Optional[Transition] = None,
        effect: Optional[str] = None,
        filter: Optional[Filter] = None,
        scale: float = 1,
        opacity: float = 1,
        fit: Optional[Fit] = Fit.crop,
        position: Position = Position.center,
        offset: Optional[Offset] = None,
    ):
        if start < 0:
            raise ValueError("start must be non-negative")
        if length <= 0:
            raise ValueError("length must be positive")
        if not (0 <= scale <= 10):
            raise ValueError("scale must be between 0 and 10")
        if not (0 <= opacity <= 1):
            raise ValueError("opacity must be between 0 and 1")

        self.asset = asset
        self.start = start
        self.length = length
        self.transition = transition
        self.effect = effect
        self.filter = filter
        self.scale = scale
        self.opacity = opacity
        self.fit = fit
        self.position = position
        self.offset = offset if offset is not None else Offset()

    def to_json(self):
        json = {
            "asset": self.asset.to_json(),
            "start": self.start,
            "length": self.length,
            "effect": self.effect,
            "scale": self.scale,
            "opacity": self.opacity,
            "fit": self.fit,
            "position": self.position,
            "offset": self.offset.to_json(),
        }

        if self.transition:
            json["transition"] = self.transition.to_json()
        if self.filter:
            json["filter"] = self.filter.value

        return json


class Track:
    def __init__(self, clips: List[Clip] = []):
        self.clips = clips

    def add_clip(self, clip: Clip):
        self.clips.append(clip)

    def to_json(self):
        return {
            "clips": [clip.to_json() for clip in self.clips],
        }


class TimelineV2:
    def __init__(self, connection):
        self.connection = connection
        self.background: str = "#000000"
        self.resolution: str = "1280x720"
        self.tracks: List[Track] = []
        self.stream_url = None
        self.player_url = None

    def add_track(self, track: Track):
        self.tracks.append(track)

    def add_clip(self, track_index: int, clip: Clip):
        self.tracks[track_index].clips.append(clip)

    def to_json(self):
        return {
            "timeline": {
                "background": self.background,
                "resolution": self.resolution,
                "tracks": [track.to_json() for track in self.tracks],
            }
        }

    def generate_stream(self):
        stream_data = self.connection.post(
            path="timeline_v2",
            data=self.to_json(),
        )
        self.stream_url = stream_data.get("stream_url")
        self.player_url = stream_data.get("player_url")
        return stream_data.get("stream_url", None)
