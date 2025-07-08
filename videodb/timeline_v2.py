from typing import List, Optional, Union
from enum import Enum


class AssetType(str, Enum):
    video = "video"
    image = "image"
    audio = "audio"
    text = "text"


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


class TextAlignment(str, Enum):
    """Place the text in one of nine predefined positions of the background."""

    top = "top"
    top_right = "top_right"
    right = "right"
    bottom_right = "bottom_right"
    bottom = "bottom"
    bottom_left = "bottom_left"
    left = "left"
    top_left = "top_left"
    center = "center"


class HorizontalAlignment(str, Enum):
    """Horizontal text alignment options."""

    left = "left"
    center = "center"
    right = "right"


class VerticalAlignment(str, Enum):
    """Vertical text alignment options."""

    top = "top"
    center = "center"
    bottom = "bottom"


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
            "crop": self.crop.to_json(),
        }


class AudioAsset(BaseAsset):
    """The AudioAsset is used to create audio sequences from audio files. The src must be a publicly accessible URL to an audio resource"""

    type = AssetType.audio

    def __init__(self, id: str, trim: int = 0, volume: float = 1):
        self.id = id
        self.trim = trim
        self.volume = volume

    def to_json(self):
        return {
            "type": self.type,
            "id": self.id,
            "trim": self.trim,
            "volume": self.volume,
        }


class Font:
    """Font styling properties for text assets."""

    def __init__(
        self,
        family: str = "Clear Sans",
        size: int = 48,
        color: str = "#FFFFFF",
        opacity: float = 1.0,
        weight: Optional[int] = None,
    ):
        if size < 1:
            raise ValueError("size must be at least 1")
        if not (0.0 <= opacity <= 1.0):
            raise ValueError("opacity must be between 0.0 and 1.0")
        if weight is not None and not (100 <= weight <= 900):
            raise ValueError("weight must be between 100 and 900")

        self.family = family
        self.size = size
        self.color = color
        self.opacity = opacity
        self.weight = weight

    def to_json(self):
        data = {
            "family": self.family,
            "size": self.size,
            "color": self.color,
            "opacity": self.opacity,
        }
        if self.weight is not None:
            data["weight"] = self.weight
        return data


class Border:
    """Text border properties."""

    def __init__(self, color: str = "#000000", width: float = 0.0):
        if width < 0.0:
            raise ValueError("width must be non-negative")
        self.color = color
        self.width = width

    def to_json(self):
        return {
            "color": self.color,
            "width": self.width,
        }


class Shadow:
    """Text shadow properties."""

    def __init__(self, color: str = "#000000", x: float = 0.0, y: float = 0.0):
        if x < 0.0:
            raise ValueError("x must be non-negative")
        if y < 0.0:
            raise ValueError("y must be non-negative")
        self.color = color
        self.x = x
        self.y = y

    def to_json(self):
        return {
            "color": self.color,
            "x": self.x,
            "y": self.y,
        }


class Background:
    """Text background styling properties."""

    def __init__(
        self,
        width: float = 0.0,
        height: float = 0.0,
        color: str = "#000000",
        border_width: float = 0.0,
        opacity: float = 1.0,
        text_alignment: TextAlignment = TextAlignment.center,
    ):
        if width < 0.0:
            raise ValueError("width must be non-negative")
        if height < 0.0:
            raise ValueError("height must be non-negative")
        if border_width < 0.0:
            raise ValueError("border_width must be non-negative")
        if not (0.0 <= opacity <= 1.0):
            raise ValueError("opacity must be between 0.0 and 1.0")

        self.width = width
        self.height = height
        self.color = color
        self.border_width = border_width
        self.opacity = opacity
        self.text_alignment = text_alignment

    def to_json(self):
        return {
            "width": self.width,
            "height": self.height,
            "color": self.color,
            "border_width": self.border_width,
            "opacity": self.opacity,
            "text_alignment": self.text_alignment.value,
        }


class Alignment:
    """Text alignment properties."""

    def __init__(
        self,
        horizontal: HorizontalAlignment = HorizontalAlignment.center,
        vertical: VerticalAlignment = VerticalAlignment.center,
    ):
        self.horizontal = horizontal
        self.vertical = vertical

    def to_json(self):
        return {
            "horizontal": self.horizontal.value,
            "vertical": self.vertical.value,
        }


class TextAsset(BaseAsset):
    """The TextAsset is used to create text sequences from text strings with full control over the text styling and positioning."""

    type = AssetType.text

    def __init__(
        self,
        text: str,
        font: Optional[Font] = None,
        border: Optional[Border] = None,
        shadow: Optional[Shadow] = None,
        background: Optional[Background] = None,
        alignment: Optional[Alignment] = None,
        tabsize: int = 4,
        line_spacing: float = 0,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        if tabsize < 1:
            raise ValueError("tabsize must be at least 1")
        if line_spacing < 0.0:
            raise ValueError("line_spacing must be non-negative")
        if width is not None and width < 1:
            raise ValueError("width must be at least 1")
        if height is not None and height < 1:
            raise ValueError("height must be at least 1")

        self.text = text
        self.font = font if font is not None else Font()
        self.border = border
        self.shadow = shadow
        self.background = background
        self.alignment = alignment if alignment is not None else Alignment()
        self.tabsize = tabsize
        self.line_spacing = line_spacing
        self.width = width
        self.height = height

    def to_json(self):
        data = {
            "type": self.type,
            "text": self.text,
            "font": self.font.to_json(),
            "alignment": self.alignment.to_json(),
            "tabsize": self.tabsize,
            "line_spacing": self.line_spacing,
        }
        if self.border:
            data["border"] = self.border.to_json()
        if self.shadow:
            data["shadow"] = self.shadow.to_json()
        if self.background:
            data["background"] = self.background.to_json()
        if self.width is not None:
            data["width"] = self.width
        if self.height is not None:
            data["height"] = self.height

        return data


AnyAsset = Union[VideoAsset, ImageAsset, AudioAsset, TextAsset]


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
