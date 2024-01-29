"""Constants used in the videodb package."""


VIDEO_DB_API: str = "https://api.videodb.io"


class MediaType:
    video = "video"
    audio = "audio"


class SearchType:
    semantic = "semantic"


class IndexType:
    semantic = "semantic"


class Workflows:
    add_subtitles = "add_subtitles"


class SemanticSearchDefaultValues:
    result_threshold = 5
    score_threshold = 0.2


class ApiPath:
    collection = "collection"
    upload = "upload"
    video = "video"
    audio = "audio"
    stream = "stream"
    thumbnail = "thumbnail"
    upload_url = "upload_url"
    transcription = "transcription"
    index = "index"
    search = "search"
    compile = "compile"
    workflow = "workflow"
    timeline = "timeline"


class Status:
    processing = "processing"
    in_progress = "in progress"


class HttpClientDefaultValues:
    max_retries = 1
    timeout = 30
    backoff_factor = 0.1
    status_forcelist = [502, 503, 504]


class MaxSupported:
    fade_duration = 5
