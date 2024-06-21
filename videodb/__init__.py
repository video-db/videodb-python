"""Videodb API client library"""

import os
import logging

from typing import Optional
from videodb._utils._video import play_stream
from videodb._constants import (
    VIDEO_DB_API,
    SceneExtractionType,
    MediaType,
    SearchType,
    SubtitleAlignment,
    SubtitleBorderStyle,
    SubtitleStyle,
    TextStyle,
)
from videodb.client import Connection
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
    "SearchError",
    "play_stream",
    "MediaType",
    "SearchType",
    "SubtitleAlignment",
    "SubtitleBorderStyle",
    "SubtitleStyle",
    "TextStyle",
    "SceneExtractionType",
]


def connect(
    api_key: str = None,
    base_url: Optional[str] = VIDEO_DB_API,
    log_level: Optional[int] = logging.INFO,
) -> Connection:
    """A client for interacting with a videodb via REST API

    :param str api_key: The api key to use for authentication
    :param str base_url: (optional) The base url to use for the api
    :param int log_level: (optional) The log level to use for the logger
    :return: A connection object
    :rtype: videodb.client.Connection
    """

    logger.setLevel(log_level)
    if api_key is None:
        api_key = os.environ.get("VIDEO_DB_API_KEY")
    if api_key is None:
        raise AuthenticationError(
            "No API key provided. Set an API key either as an environment variable (VIDEO_DB_API_KEY) or pass it as an argument."
        )

    return Connection(api_key, base_url)
