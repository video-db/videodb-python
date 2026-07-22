import os
from typing import Optional, Union
from urllib.parse import urlparse

import requests
from requests import HTTPError


from videodb._constants import (
    ApiPath,
)

from videodb.exceptions import (
    VideodbError,
)


def _is_url(path: str) -> bool:
    parsed = urlparse(path)
    return all([parsed.scheme in ("http", "https"), parsed.netloc])


def upload_bytes(
    _connection,
    content: Union[str, bytes],
    name: str,
    content_type: str = "application/octet-stream",
    collection_id: Optional[str] = None,
) -> str:
    """Upload in-memory content using a presigned upload URL and return the object URL."""
    collection_id = collection_id or _connection.collection_id
    upload_url_data = _connection.get(
        path=f"{ApiPath.collection}/{collection_id}/{ApiPath.upload_url}",
        params={"name": name},
    )
    upload_url = upload_url_data.get("upload_url")

    try:
        files = {"file": (name, content, content_type)}
        response = requests.post(upload_url, files=files)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise VideodbError("Error while uploading content", cause=e)

    return upload_url


def upload(
    _connection,
    source: Optional[str] = None,
    media_type: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    callback_url: Optional[str] = None,
    file_path: Optional[str] = None,
    url: Optional[str] = None,
    collection_id: Optional[str] = None,
) -> dict:
    """Upload a file or URL.

    :param _connection: Connection object for API calls
    :param str source: Local path or URL of the file to be uploaded
    :param str media_type: MediaType object (optional)
    :param str name: Name of the file (optional)
    :param str description: Description of the file (optional)
    :param str callback_url: URL to receive the callback (optional)
    :param str file_path: Path to the file to be uploaded
    :param str url: URL of the file to be uploaded
    :param str collection_id: ID of the collection to upload to (optional)
    :return: Dictionary containing upload response data
    :rtype: dict
    """
    collection_id = collection_id or _connection.collection_id

    if source and (file_path or url):
        raise VideodbError("source cannot be used with file_path or url")

    if source and not file_path and not url:
        if _is_url(source):
            url = source
        else:
            file_path = source
    if file_path and not url and _is_url(file_path):
        url = file_path
        file_path = None

    if not file_path and url and not _is_url(url) and os.path.exists(url):
        file_path = url
        url = None

    if not file_path and not url:
        raise VideodbError("Either file_path or url is required")
    if file_path and url:
        raise VideodbError("Only one of file_path or url is allowed")

    if file_path:
        try:
            name = os.path.splitext(os.path.basename(file_path))[0] if not name else name
            with open(file_path, "rb") as file:
                url = upload_bytes(
                    _connection=_connection,
                    content=file,
                    name=name,
                    collection_id=collection_id,
                )

        except FileNotFoundError as e:
            raise VideodbError("File not found", cause=e)

        except HTTPError as e:
            raise VideodbError("Error while uploading file", cause=e)

    upload_data = _connection.post(
        path=f"{ApiPath.collection}/{collection_id}/{ApiPath.upload}",
        data={
            "url": url,
            "name": name,
            "description": description,
            "callback_url": callback_url,
            "media_type": media_type,
        },
    )
    return upload_data
