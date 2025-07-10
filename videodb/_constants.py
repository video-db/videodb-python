"""Constants used in the videodb package."""

from typing import Union
from dataclasses import dataclass

VIDEO_DB_API: str = "https://api.videodb.io"


class MediaType:
    video = "video"
    audio = "audio"
    image = "image"


class SearchType:
    semantic = "semantic"
    keyword = "keyword"
    scene = "scene"
    llm = "llm"


class IndexType:
    spoken_word = "spoken_word"
    scene = "scene"


class SceneExtractionType:
    shot_based = "shot"
    time_based = "time"


class Workflows:
    add_subtitles = "add_subtitles"


class SemanticSearchDefaultValues:
    result_threshold = 5
    score_threshold = 0.2


class Segmenter:
    time = "time"
    word = "word"
    sentence = "sentence"


class ApiPath:
    collection = "collection"
    upload = "upload"
    video = "video"
    audio = "audio"
    image = "image"
    stream = "stream"
    thumbnail = "thumbnail"
    thumbnails = "thumbnails"
    upload_url = "upload_url"
    transcription = "transcription"
    index = "index"
    search = "search"
    compile = "compile"
    workflow = "workflow"
    timeline = "timeline"
    delete = "delete"
    billing = "billing"
    usage = "usage"
    invoices = "invoices"
    scenes = "scenes"
    scene = "scene"
    frame = "frame"
    describe = "describe"
    storage = "storage"
    download = "download"
    title = "title"
    rtstream = "rtstream"
    status = "status"
    event = "event"
    alert = "alert"
    generate_url = "generate_url"
    generate = "generate"
    text = "text"
    web = "web"
    translate = "translate"
    dub = "dub"
    transcode = "transcode"
    meeting = "meeting"
    record = "record"


class Status:
    processing = "processing"
    in_progress = "in progress"


class MeetingStatus:
    initializing = "initializing"
    processing = "processing"
    done = "done"


class HttpClientDefaultValues:
    max_retries = 1
    timeout = 30
    backoff_factor = 0.1
    status_forcelist = [502, 503, 504]


class MaxSupported:
    fade_duration = 5


class SubtitleBorderStyle:
    no_border = 1
    opaque_box = 3
    outline = 4


class SubtitleAlignment:
    bottom_left = 1
    bottom_center = 2
    bottom_right = 3
    middle_left = 9
    middle_center = 10
    middle_right = 11
    top_left = 5
    top_center = 6
    top_right = 7


@dataclass
class SubtitleStyle:
    font_name: str = "Arial"
    font_size: float = 18
    primary_colour: str = "&H00FFFFFF"  # white
    secondary_colour: str = "&H000000FF"  # blue
    outline_colour: str = "&H00000000"  # black
    back_colour: str = "&H00000000"  # black
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike_out: bool = False
    scale_x: float = 1.0
    scale_y: float = 1.0
    spacing: float = 0
    angle: float = 0
    border_style: int = SubtitleBorderStyle.outline
    outline: float = 1.0
    shadow: float = 0.0
    alignment: int = SubtitleAlignment.bottom_center
    margin_l: int = 10
    margin_r: int = 10
    margin_v: int = 10


@dataclass
class TextStyle:
    fontsize: int = 24
    fontcolor: str = "black"
    fontcolor_expr: str = ""
    alpha: float = 1.0
    font: str = "Sans"
    box: bool = True
    boxcolor: str = "white"
    boxborderw: str = "10"
    boxw: int = 0
    boxh: int = 0
    line_spacing: int = 0
    text_align: str = "T"
    y_align: str = "text"
    borderw: int = 0
    bordercolor: str = "black"
    expansion: str = "normal"
    basetime: int = 0
    fix_bounds: bool = False
    text_shaping: bool = True
    shadowcolor: str = "black"
    shadowx: int = 0
    shadowy: int = 0
    tabsize: int = 4
    x: Union[str, int] = "(main_w-text_w)/2"
    y: Union[str, int] = "(main_h-text_h)/2"


class TranscodeMode:
    lightning = "lightning"
    economy = "economy"


class ResizeMode:
    crop = "crop"
    fit = "fit"
    pad = "pad"


@dataclass
class VideoConfig:
    resolution: int = None
    quality: int = 23
    framerate: int = None
    aspect_ratio: str = None
    resize_mode: str = ResizeMode.crop


@dataclass
class AudioConfig:
    mute: bool = False
