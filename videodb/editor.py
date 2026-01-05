from typing import List, Optional, Union
from enum import Enum

from videodb._constants import ApiPath


class AssetType(str, Enum):
    """The type of asset to display for the duration of the Clip."""

    video = "video"
    image = "image"
    audio = "audio"
    text = "text"
    caption = "caption"


class Fit(str, Enum):
    """Set how the asset should be scaled to fit the viewport using one of the following options:

    crop (default) - scale the asset to fill the viewport while maintaining the aspect ratio. The asset will be cropped if it exceeds the bounds of the viewport.
    cover - stretch the asset to fill the viewport without maintaining the aspect ratio.
    contain - fit the entire asset within the viewport while maintaining the original aspect ratio.
    none - preserves the original asset dimensions and does not apply any scaling."""

    crop = "crop"
    cover = "cover"
    contain = "contain"
    none = None


class Position(str, Enum):
    """Place the asset in one of nine predefined positions of the viewport. This is most effective for when the asset is scaled and you want to position the element to a specific position."""

    top = "top"
    bottom = "bottom"
    left = "left"
    right = "right"
    center = "center"
    top_left = "top_left"
    top_right = "top_right"
    bottom_left = "bottom_left"
    bottom_right = "bottom_right"


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


class CaptionBorderStyle(str, Enum):
    """Border style properties for caption assets."""

    outline_and_shadow = "outline_and_shadow"
    opaque_box = "opaque_box"


class CaptionAlignment(str, Enum):
    """Caption alignment properties for caption assets."""

    bottom_left = "bottom_left"
    bottom_center = "bottom_center"
    bottom_right = "bottom_right"
    middle_left = "middle_left"
    middle_center = "middle_center"
    middle_right = "middle_right"
    top_left = "top_left"
    top_center = "top_center"
    top_right = "top_right"


class CaptionAnimation(str, Enum):
    """Caption animation properties for caption assets."""

    box_highlight = "box_highlight"
    color_highlight = "color_highlight"
    reveal = "reveal"
    karaoke = "karaoke"
    impact = "impact"
    supersize = "supersize"


class VerticalAlignment(str, Enum):
    """Vertical text alignment options."""

    top = "top"
    center = "center"
    bottom = "bottom"


class Offset:
    """Offset position for positioning elements on the viewport.

    :ivar float x: Horizontal offset value
    :ivar float y: Vertical offset value
    """

    def __init__(self, x: float = 0, y: float = 0):
        """Initialize an Offset instance.

        :param float x: Horizontal offset value (default: 0)
        :param float y: Vertical offset value (default: 0)
        """
        self.x = x
        self.y = y

    def to_json(self) -> dict:
        """Convert the offset to a JSON-serializable dictionary.

        :return: Dictionary containing offset properties
        :rtype: dict
        """
        return {
            "x": self.x,
            "y": self.y,
        }


class Crop:
    """Crop settings for trimming edges of an asset.

    :ivar int top: Number of pixels to crop from the top edge
    :ivar int right: Number of pixels to crop from the right edge
    :ivar int bottom: Number of pixels to crop from the bottom edge
    :ivar int left: Number of pixels to crop from the left edge
    """

    def __init__(self, top: int = 0, right: int = 0, bottom: int = 0, left: int = 0):
        """Initialize a Crop instance.

        :param int top: Pixels to crop from top (default: 0)
        :param int right: Pixels to crop from right (default: 0)
        :param int bottom: Pixels to crop from bottom (default: 0)
        :param int left: Pixels to crop from left (default: 0)
        """
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left

    def to_json(self) -> dict:
        """Convert the crop settings to a JSON-serializable dictionary.

        :return: Dictionary containing crop properties
        :rtype: dict
        """
        return {
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "left": self.left,
        }


class Transition:
    """Transition effect settings for clip entry and exit animations.

    :ivar str in_: The transition effect to apply when the clip enters
    :ivar str out: The transition effect to apply when the clip exits
    :ivar float duration: Duration of the transition effect in seconds
    """

    def __init__(self, in_: str = None, out: str = None, duration: int = 0.5):
        """Initialize a Transition instance.

        :param str in_: Entry transition effect name (default: None)
        :param str out: Exit transition effect name (default: None)
        :param float duration: Transition duration in seconds (default: 0.5)
        """
        self.in_ = in_
        self.out = out
        self.duration = duration

    def to_json(self) -> dict:
        """Convert the transition settings to a JSON-serializable dictionary.

        :return: Dictionary containing transition properties
        :rtype: dict
        """
        return {
            "in": self.in_,
            "out": self.out,
            "duration": self.duration,
        }


class BaseAsset:
    """The type of asset to display for the duration of the Clip."""

    type: AssetType


class VideoAsset(BaseAsset):
    """The VideoAsset is used to create video sequences from video files.

    The src must be a publicly accessible URL to a video resource.

    :ivar str id: Unique identifier for the video asset
    :ivar int start: Start time offset in seconds
    :ivar float volume: Audio volume level (0 to 5)
    :ivar Crop crop: Crop settings for the video
    """

    type = AssetType.video

    def __init__(
        self,
        id: str,
        start: int = 0,
        volume: float = 1,
        crop: Optional[Crop] = None,
    ):
        """Initialize a VideoAsset instance.

        :param str id: Unique identifier for the video asset
        :param int start: Start time offset in seconds (default: 0)
        :param float volume: Audio volume level between 0 and 5 (default: 1)
        :param Crop crop: (optional) Crop settings for the video
        :raises ValueError: If start is negative or volume is not between 0 and 5
        """
        if start < 0:
            raise ValueError("start must be non-negative")
        if not (0 <= volume <= 5):
            raise ValueError("volume must be between 0 and 5")

        self.id = id
        self.start = start
        self.volume = volume
        self.crop = crop if crop is not None else Crop()

    def to_json(self) -> dict:
        """Convert the video asset to a JSON-serializable dictionary.

        :return: Dictionary containing video asset properties
        :rtype: dict
        """
        return {
            "type": self.type,
            "id": self.id,
            "start": self.start,
            "volume": self.volume,
            "crop": self.crop.to_json(),
        }


class ImageAsset(BaseAsset):
    """The ImageAsset is used to create video from images.

    The src must be a publicly accessible URL to an image resource such as a jpg or png file.

    :ivar str id: Unique identifier for the image asset
    :ivar Crop crop: Crop settings for the image
    """

    type = AssetType.image

    def __init__(self, id: str, crop: Optional[Crop] = None):
        """Initialize an ImageAsset instance.

        :param str id: Unique identifier for the image asset
        :param Crop crop: (optional) Crop settings for the image
        """
        self.id = id
        self.crop = crop if crop is not None else Crop()

    def to_json(self) -> dict:
        """Convert the image asset to a JSON-serializable dictionary.

        :return: Dictionary containing image asset properties
        :rtype: dict
        """
        return {
            "type": self.type,
            "id": self.id,
            "crop": self.crop.to_json(),
        }


class AudioAsset(BaseAsset):
    """The AudioAsset is used to create audio sequences from audio files.

    The src must be a publicly accessible URL to an audio resource.

    :ivar str id: Unique identifier for the audio asset
    :ivar int start: Start time offset in seconds
    :ivar float volume: Audio volume level
    """

    type = AssetType.audio

    def __init__(self, id: str, start: int = 0, volume: float = 1):
        """Initialize an AudioAsset instance.

        :param str id: Unique identifier for the audio asset
        :param int start: Start time offset in seconds (default: 0)
        :param float volume: Audio volume level (default: 1)
        """
        self.id = id
        self.start = start
        self.volume = volume

    def to_json(self) -> dict:
        """Convert the audio asset to a JSON-serializable dictionary.

        :return: Dictionary containing audio asset properties
        :rtype: dict
        """
        return {
            "type": self.type,
            "id": self.id,
            "start": self.start,
            "volume": self.volume,
        }


class Font:
    """Font styling properties for text assets.

    :ivar str family: Font family name
    :ivar int size: Font size in pixels
    :ivar str color: Font color in hex format (e.g., "#FFFFFF")
    :ivar float opacity: Font opacity (0.0 to 1.0)
    :ivar int weight: (optional) Font weight (100 to 900)
    """

    def __init__(
        self,
        family: str = "Clear Sans",
        size: int = 48,
        color: str = "#FFFFFF",
        opacity: float = 1.0,
        weight: Optional[int] = None,
    ):
        """Initialize a Font instance.

        :param str family: Font family name (default: "Clear Sans")
        :param int size: Font size in pixels (default: 48)
        :param str color: Font color in hex format (default: "#FFFFFF")
        :param float opacity: Font opacity between 0.0 and 1.0 (default: 1.0)
        :param int weight: (optional) Font weight between 100 and 900
        :raises ValueError: If size < 1, opacity not in [0.0, 1.0], or weight not in [100, 900]
        """
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

    def to_json(self) -> dict:
        """Convert the font settings to a JSON-serializable dictionary.

        :return: Dictionary containing font properties
        :rtype: dict
        """
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
    """Text border properties.

    :ivar str color: Border color in hex format (e.g., "#000000")
    :ivar float width: Border width in pixels
    """

    def __init__(self, color: str = "#000000", width: float = 0.0):
        """Initialize a Border instance.

        :param str color: Border color in hex format (default: "#000000")
        :param float width: Border width in pixels (default: 0.0)
        :raises ValueError: If width is negative
        """
        if width < 0.0:
            raise ValueError("width must be non-negative")
        self.color = color
        self.width = width

    def to_json(self) -> dict:
        """Convert the border settings to a JSON-serializable dictionary.

        :return: Dictionary containing border properties
        :rtype: dict
        """
        return {
            "color": self.color,
            "width": self.width,
        }


class Shadow:
    """Text shadow properties.

    :ivar str color: Shadow color in hex format (e.g., "#000000")
    :ivar float x: Horizontal shadow offset in pixels
    :ivar float y: Vertical shadow offset in pixels
    """

    def __init__(self, color: str = "#000000", x: float = 0.0, y: float = 0.0):
        """Initialize a Shadow instance.

        :param str color: Shadow color in hex format (default: "#000000")
        :param float x: Horizontal shadow offset in pixels (default: 0.0)
        :param float y: Vertical shadow offset in pixels (default: 0.0)
        :raises ValueError: If x or y is negative
        """
        if x < 0.0:
            raise ValueError("x must be non-negative")
        if y < 0.0:
            raise ValueError("y must be non-negative")
        self.color = color
        self.x = x
        self.y = y

    def to_json(self) -> dict:
        """Convert the shadow settings to a JSON-serializable dictionary.

        :return: Dictionary containing shadow properties
        :rtype: dict
        """
        return {
            "color": self.color,
            "x": self.x,
            "y": self.y,
        }


class Background:
    """Text background styling properties.

    :ivar float width: Background width in pixels
    :ivar float height: Background height in pixels
    :ivar str color: Background color in hex format (e.g., "#000000")
    :ivar float border_width: Background border width in pixels
    :ivar float opacity: Background opacity (0.0 to 1.0)
    :ivar TextAlignment text_alignment: Text alignment within the background
    """

    def __init__(
        self,
        width: float = 0.0,
        height: float = 0.0,
        color: str = "#000000",
        border_width: float = 0.0,
        opacity: float = 1.0,
        text_alignment: TextAlignment = TextAlignment.center,
    ):
        """Initialize a Background instance.

        :param float width: Background width in pixels (default: 0.0)
        :param float height: Background height in pixels (default: 0.0)
        :param str color: Background color in hex format (default: "#000000")
        :param float border_width: Border width in pixels (default: 0.0)
        :param float opacity: Background opacity between 0.0 and 1.0 (default: 1.0)
        :param TextAlignment text_alignment: Text alignment position (default: TextAlignment.center)
        :raises ValueError: If width, height, or border_width is negative, or opacity not in [0.0, 1.0]
        """
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

    def to_json(self) -> dict:
        """Convert the background settings to a JSON-serializable dictionary.

        :return: Dictionary containing background properties
        :rtype: dict
        """
        return {
            "width": self.width,
            "height": self.height,
            "color": self.color,
            "border_width": self.border_width,
            "opacity": self.opacity,
            "text_alignment": self.text_alignment.value,
        }


class Alignment:
    """Text alignment properties.

    :ivar HorizontalAlignment horizontal: Horizontal text alignment
    :ivar VerticalAlignment vertical: Vertical text alignment
    """

    def __init__(
        self,
        horizontal: HorizontalAlignment = HorizontalAlignment.center,
        vertical: VerticalAlignment = VerticalAlignment.center,
    ):
        """Initialize an Alignment instance.

        :param HorizontalAlignment horizontal: Horizontal alignment (default: HorizontalAlignment.center)
        :param VerticalAlignment vertical: Vertical alignment (default: VerticalAlignment.center)
        """
        self.horizontal = horizontal
        self.vertical = vertical

    def to_json(self) -> dict:
        """Convert the alignment settings to a JSON-serializable dictionary.

        :return: Dictionary containing alignment properties
        :rtype: dict
        """
        return {
            "horizontal": self.horizontal.value,
            "vertical": self.vertical.value,
        }


class TextAsset(BaseAsset):
    """The TextAsset is used to create text sequences from text strings.

    Provides full control over the text styling and positioning.

    :ivar str text: The text content to display
    :ivar Font font: Font styling properties
    :ivar Border border: (optional) Text border properties
    :ivar Shadow shadow: (optional) Text shadow properties
    :ivar Background background: (optional) Text background properties
    :ivar Alignment alignment: Text alignment properties
    :ivar int tabsize: Tab character size in spaces
    :ivar float line_spacing: Space between lines
    :ivar int width: (optional) Text box width in pixels
    :ivar int height: (optional) Text box height in pixels
    """

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
        """Initialize a TextAsset instance.

        :param str text: The text content to display
        :param Font font: (optional) Font styling properties
        :param Border border: (optional) Text border properties
        :param Shadow shadow: (optional) Text shadow properties
        :param Background background: (optional) Text background properties
        :param Alignment alignment: (optional) Text alignment properties
        :param int tabsize: Tab character size in spaces (default: 4)
        :param float line_spacing: Space between lines (default: 0)
        :param int width: (optional) Text box width in pixels
        :param int height: (optional) Text box height in pixels
        :raises ValueError: If tabsize < 1, line_spacing < 0, width < 1, or height < 1
        """
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

    def to_json(self) -> dict:
        """Convert the text asset to a JSON-serializable dictionary.

        :return: Dictionary containing text asset properties
        :rtype: dict
        """
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


class FontStyling:
    """Font styling properties for caption assets.

    :ivar str name: Font family name
    :ivar int size: Font size in pixels
    :ivar bool bold: Whether text is bold
    :ivar bool italic: Whether text is italic
    :ivar bool underline: Whether text is underlined
    :ivar bool strikeout: Whether text has strikethrough
    :ivar float scale_x: Horizontal scale percentage
    :ivar float scale_y: Vertical scale percentage
    :ivar float spacing: Character spacing
    :ivar float angle: Text rotation angle in degrees
    """

    def __init__(
        self,
        name: str = "Clear Sans",
        size: int = 30,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strikeout: bool = False,
        scale_x: float = 100,
        scale_y: float = 100,
        spacing: float = 0.0,
        angle: float = 0.0,
    ):
        """Initialize a FontStyling instance.

        :param str name: Font family name (default: "Clear Sans")
        :param int size: Font size in pixels (default: 30)
        :param bool bold: Enable bold text (default: False)
        :param bool italic: Enable italic text (default: False)
        :param bool underline: Enable underlined text (default: False)
        :param bool strikeout: Enable strikethrough text (default: False)
        :param float scale_x: Horizontal scale percentage (default: 100)
        :param float scale_y: Vertical scale percentage (default: 100)
        :param float spacing: Character spacing (default: 0.0)
        :param float angle: Text rotation angle in degrees (default: 0.0)
        """
        self.name = name
        self.size = size
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strikeout = strikeout
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.spacing = spacing
        self.angle = angle

    def to_json(self) -> dict:
        """Convert the font styling to a JSON-serializable dictionary.

        :return: Dictionary containing font styling properties
        :rtype: dict
        """
        return {
            "font_name": self.name,
            "font_size": self.size,
            "bold": self.bold,
            "italic": self.italic,
            "underline": self.underline,
            "strikeout": self.strikeout,
            "scale_x": self.scale_x,
            "scale_y": self.scale_y,
            "spacing": self.spacing,
            "angle": self.angle,
        }


class BorderAndShadow:
    """Border and shadow properties for caption assets.

    :ivar CaptionBorderStyle style: Border style type
    :ivar int outline: Outline thickness in pixels
    :ivar str outline_color: Outline color in ASS format (e.g., "&H00000000")
    :ivar int shadow: Shadow depth in pixels
    """

    def __init__(
        self,
        style: CaptionBorderStyle = CaptionBorderStyle.outline_and_shadow,
        outline: int = 1,
        outline_color: str = "&H00000000",
        shadow: int = 0,
    ):
        """Initialize a BorderAndShadow instance.

        :param CaptionBorderStyle style: Border style type (default: CaptionBorderStyle.outline_and_shadow)
        :param int outline: Outline thickness in pixels (default: 1)
        :param str outline_color: Outline color in ASS format (default: "&H00000000")
        :param int shadow: Shadow depth in pixels (default: 0)
        """
        self.style = style
        self.outline = outline
        self.outline_color = outline_color
        self.shadow = shadow

    def to_json(self) -> dict:
        """Convert the border and shadow settings to a JSON-serializable dictionary.

        :return: Dictionary containing border and shadow properties
        :rtype: dict
        """
        return {
            "style": self.style.value,
            "outline": self.outline,
            "outline_color": self.outline_color,
            "shadow": self.shadow,
        }


class Positioning:
    """Positioning properties for caption assets.

    :ivar CaptionAlignment alignment: Caption alignment position
    :ivar int margin_l: Left margin in pixels
    :ivar int margin_r: Right margin in pixels
    :ivar int margin_v: Vertical margin in pixels
    """

    def __init__(
        self,
        alignment: CaptionAlignment = CaptionAlignment.bottom_center,
        margin_l: int = 30,
        margin_r: int = 30,
        margin_v: int = 30,
    ):
        """Initialize a Positioning instance.

        :param CaptionAlignment alignment: Caption alignment position (default: CaptionAlignment.bottom_center)
        :param int margin_l: Left margin in pixels (default: 30)
        :param int margin_r: Right margin in pixels (default: 30)
        :param int margin_v: Vertical margin in pixels (default: 30)
        """
        self.alignment = alignment
        self.margin_l = margin_l
        self.margin_r = margin_r
        self.margin_v = margin_v

    def to_json(self) -> dict:
        """Convert the positioning settings to a JSON-serializable dictionary.

        :return: Dictionary containing positioning properties
        :rtype: dict
        """
        return {
            "alignment": self.alignment.value,
            "margin_l": self.margin_l,
            "margin_r": self.margin_r,
            "margin_v": self.margin_v,
        }


class CaptionAsset(BaseAsset):
    """The CaptionAsset is used to create auto-generated or custom captions.

    Provides full styling and ASS (Advanced SubStation Alpha) subtitle format support.

    :ivar str src: Caption source ("auto" for auto-generated or base64 encoded ass string)
    :ivar FontStyling font: Font styling properties
    :ivar str primary_color: Primary text color in ASS format (e.g., "&H00FFFFFF")
    :ivar str secondary_color: Secondary text color in ASS format
    :ivar str back_color: Background color in ASS format
    :ivar BorderAndShadow border: Border and shadow properties
    :ivar Positioning position: Caption positioning properties
    :ivar CaptionAnimation animation: (optional) Caption animation effect
    """

    type = AssetType.caption

    def __init__(
        self,
        src: str = "auto",
        font: Optional[FontStyling] = None,
        primary_color: str = "&H00FFFFFF",
        secondary_color: str = "&H000000FF",
        back_color: str = "&H00000000",
        border: Optional[BorderAndShadow] = None,
        position: Optional[Positioning] = None,
        animation: Optional[CaptionAnimation] = None,
    ):
        """Initialize a CaptionAsset instance.

        :param str src: Caption source ("auto" for auto-generated or base64 encoded ass string)
        :param FontStyling font: (optional) Font styling properties
        :param str primary_color: Primary text color in ASS format (default: "&H00FFFFFF")
        :param str secondary_color: Secondary text color in ASS format (default: "&H000000FF")
        :param str back_color: Background color in ASS format (default: "&H00000000")
        :param BorderAndShadow border: (optional) Border and shadow properties
        :param Positioning position: (optional) Caption positioning properties
        :param CaptionAnimation animation: (optional) Caption animation effect
        """
        self.src = src
        self.font = font if font is not None else FontStyling()
        self.primary_color = primary_color
        self.secondary_color = secondary_color
        self.back_color = back_color
        self.border = border if border is not None else BorderAndShadow()
        self.position = position if position is not None else Positioning()
        self.animation = animation

    def to_json(self) -> dict:
        """Convert the caption asset to a JSON-serializable dictionary.

        :return: Dictionary containing caption asset properties
        :rtype: dict
        """
        data = {
            "type": self.type,
            "src": self.src,
            "font": self.font.to_json(),
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "back_color": self.back_color,
            "border": self.border.to_json(),
            "position": self.position.to_json(),
        }
        if self.animation:
            data["animation"] = self.animation.value
        return data


AnyAsset = Union[VideoAsset, ImageAsset, AudioAsset, TextAsset, CaptionAsset]


class Clip:
    """A clip is a container for a specific type of asset.

    Assets can be title, image, video, audio, or caption. Use a Clip to define
    when an asset will display on the timeline, how long it will play for,
    and transitions, filters and effects to apply to it.

    :ivar AnyAsset asset: The asset contained in this clip
    :ivar Union[float, int] duration: Duration of the clip in seconds
    :ivar Transition transition: (optional) Transition effects for the clip
    :ivar str effect: (optional) Effect to apply to the clip
    :ivar Filter filter: (optional) Filter to apply to the clip
    :ivar float scale: Scale factor (0 to 10)
    :ivar float opacity: Opacity level (0 to 1)
    :ivar Fit fit: How the asset should be scaled to fit the viewport
    :ivar Position position: Position of the asset in the viewport
    :ivar Offset offset: Offset position for fine-tuning placement
    :ivar int z_index: Z-index for layering order
    """

    def __init__(
        self,
        asset: AnyAsset,
        duration: Union[float, int],
        transition: Optional[Transition] = None,
        effect: Optional[str] = None,
        filter: Optional[Filter] = None,
        scale: float = 1,
        opacity: float = 1,
        fit: Optional[Fit] = Fit.crop,
        position: Position = Position.center,
        offset: Optional[Offset] = None,
        z_index: int = 0,
    ):
        """Initialize a Clip instance.

        :param AnyAsset asset: The asset to display (VideoAsset, ImageAsset, AudioAsset, TextAsset, or CaptionAsset)
        :param Union[float, int] duration: Duration of the clip in seconds
        :param Transition transition: (optional) Transition effects for entry/exit
        :param str effect: (optional) Effect name to apply
        :param Filter filter: (optional) Filter to apply to the clip
        :param float scale: Scale factor between 0 and 10 (default: 1)
        :param float opacity: Opacity level between 0 and 1 (default: 1)
        :param Fit fit: Asset scaling mode (default: Fit.crop)
        :param Position position: Asset position in viewport (default: Position.center)
        :param Offset offset: (optional) Fine-tune position offset
        :param int z_index: Layering order (default: 0)
        :raises ValueError: If scale not in [0, 10] or opacity not in [0, 1]
        """
        if not (0 <= scale <= 10):
            raise ValueError("scale must be between 0 and 10")
        if not (0 <= opacity <= 1):
            raise ValueError("opacity must be between 0 and 1")

        self.asset = asset
        self.duration = duration
        self.transition = transition
        self.effect = effect
        self.filter = filter
        self.scale = scale
        self.opacity = opacity
        self.fit = fit
        self.position = position
        self.offset = offset if offset is not None else Offset()
        self.z_index = z_index

    def to_json(self) -> dict:
        """Convert the clip to a JSON-serializable dictionary.

        :return: Dictionary containing clip properties
        :rtype: dict
        """
        json = {
            "asset": self.asset.to_json(),
            "duration": self.duration,
            "effect": self.effect,
            "scale": self.scale,
            "opacity": self.opacity,
            "fit": self.fit,
            "position": self.position,
            "offset": self.offset.to_json(),
            "z_index": self.z_index,
        }

        if self.transition:
            json["transition"] = self.transition.to_json()
        if self.filter:
            json["filter"] = self.filter.value

        return json


class TrackItem:
    """Wrapper class that positions a clip at a specific start time on a track.

    :ivar int start: Start time in seconds when the clip begins on the track
    :ivar Clip clip: The clip to be placed on the track
    """

    def __init__(self, start: int, clip: Clip):
        """Initialize a TrackItem instance.

        :param int start: Start time in seconds when the clip begins
        :param Clip clip: The clip to be placed on the track
        """
        self.start = start
        self.clip = clip

    def to_json(self) -> dict:
        """Convert the track item to a JSON-serializable dictionary.

        :return: Dictionary containing track item properties
        :rtype: dict
        """
        return {
            "start": self.start,
            "clip": self.clip.to_json(),
        }


class Track:
    """A track contains an array of clips.

    Tracks are layered on top of each other in the order in the array.
    The top most track will render on top of those below it.

    :ivar List[TrackItem] clips: List of clips on this track
    :ivar int z_index: Z-index for track layering order
    """

    def __init__(self, z_index: int = 0):
        """Initialize a Track instance.

        :param int z_index: Z-index for track layering order (default: 0)
        """
        self.clips: List[TrackItem] = []
        self.z_index: int = z_index

    def add_clip(self, start: int, clip: Clip) -> None:
        """Add a clip to the track at a specific start time.

        :param int start: Start time in seconds when the clip begins
        :param Clip clip: The clip to add to the track
        :return: None
        :rtype: None
        """
        self.clips.append(TrackItem(start, clip))

    def to_json(self) -> dict:
        """Convert the track to a JSON-serializable dictionary.

        :return: Dictionary containing track properties and clips
        :rtype: dict
        """
        return {
            "clips": [clip.to_json() for clip in self.clips],
            "z_index": self.z_index,
        }


class Timeline:
    """A timeline represents the contents of a video edit over time.

    A timeline consists of layers called tracks. Tracks are composed of titles,
    images, audio, html or video segments referred to as clips which are placed
    along the track at specific starting points and lasting for a specific
    amount of time.

    :ivar connection: API connection instance for making requests
    :ivar str background: Background color in hex format (e.g., "#000000")
    :ivar str resolution: Video resolution (e.g., "1280x720")
    :ivar List[Track] tracks: List of tracks in the timeline
    :ivar str stream_url: URL of the generated stream (populated after generate_stream)
    :ivar str player_url: URL of the video player (populated after generate_stream)
    """

    def __init__(self, connection):
        """Initialize a Timeline instance.

        :param connection: API connection instance for making requests
        """
        self.connection = connection
        self.background: str = "#000000"
        self.resolution: str = "1280x720"
        self.tracks: List[Track] = []
        self.stream_url = None
        self.player_url = None

    def add_track(self, track: Track) -> None:
        """Add a track to the timeline.

        :param Track track: The track to add to the timeline
        :return: None
        :rtype: None
        """
        self.tracks.append(track)

    def to_json(self) -> dict:
        """Convert the timeline to a JSON-serializable dictionary.

        :return: Dictionary containing timeline properties and tracks
        :rtype: dict
        """
        return {
            "timeline": {
                "background": self.background,
                "resolution": self.resolution,
                "tracks": [track.to_json() for track in self.tracks],
            }
        }

    def generate_stream(self) -> str:
        """Generate a stream from the timeline.

        Makes an API request to render the timeline and generate streaming URLs.
        Updates the stream_url and player_url instance variables.

        :return: The stream URL of the generated video
        :rtype: str
        """
        stream_data = self.connection.post(
            path=ApiPath.editor,
            data=self.to_json(),
        )
        self.stream_url = stream_data.get("stream_url")
        self.player_url = stream_data.get("player_url")
        return stream_data.get("stream_url", None)

    def download_stream(self, stream_url: str) -> dict:
        """Download a stream from the timeline.

        :param str stream_url: The URL of the stream to download
        :return: Dictionary containing download information
        :rtype: dict
        """
        return self.connection.post(
            path=f"{ApiPath.editor}/{ApiPath.download}", data={"stream_url": stream_url}
        )
