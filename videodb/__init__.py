"""Videodb API client library"""

import os
import logging

from typing import Optional
from videodb._utils._video import play_stream
from videodb._constants import (
    VIDEO_DB_API,
    IndexType,
    SceneExtractionType,
    MediaType,
    SearchType,
    Segmenter,
    SubtitleAlignment,
    SubtitleBorderStyle,
    SubtitleStyle,
    TextStyle,
    TranscodeMode,
    ResizeMode,
    VideoConfig,
    AudioConfig,
    ReframeMode,
    SegmentationType,
)
from videodb.client import Connection
from videodb.capture_session import CaptureSession
from videodb.websocket_client import WebSocketConnection
from videodb.capture import CaptureClient, Channel, AudioChannel, VideoChannel, Channels

__all__ = [
    "connect",
    "CaptureSession",
    "WebSocketConnection",
    "CaptureClient",
    "Channel",
    "AudioChannel",
    "VideoChannel",
    "Channels",
]
from videodb.exceptions import (
    VideodbError,
    AuthenticationError,
    InvalidRequestError,
    SearchError,
)

logger: logging.Logger = logging.getLogger("videodb")


__all__ = [
    "VideodbError",
    "AuthenticationError",
    "InvalidRequestError",
    "IndexType",
    "SearchError",
    "play_stream",
    "MediaType",
    "SearchType",
    "SubtitleAlignment",
    "SubtitleBorderStyle",
    "SubtitleStyle",
    "TextStyle",
    "SceneExtractionType",
    "Segmenter",
    "TranscodeMode",
    "ResizeMode",
    "VideoConfig",
    "AudioConfig",
    "ReframeMode",
    "SegmentationType",
]


def connect(
    api_key: str = None,
    session_token: str = None,
    base_url: Optional[str] = VIDEO_DB_API,
    log_level: Optional[int] = logging.INFO,
    **kwargs,
) -> Connection:
    """A client for interacting with a videodb via REST API

    :param str api_key: The api key to use for authentication
    :param str session_token: The session token to use for authentication (alternative to api_key)
    :param str base_url: (optional) The base url to use for the api
    :param int log_level: (optional) The log level to use for the logger
    :return: A connection object
    :rtype: videodb.client.Connection
    """

    logger.setLevel(log_level)

    # Determine which token to use
    if api_key is None and session_token is None:
        api_key = os.environ.get("VIDEO_DB_API_KEY")

    if api_key is None and session_token is None:
        raise AuthenticationError(
            "No authentication provided. Set an API key (VIDEO_DB_API_KEY) or provide api_key/session_token as an argument."
        )

    return Connection(api_key=api_key, session_token=session_token, base_url=base_url, **kwargs)
