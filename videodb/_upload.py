import requests

from typing import Optional
from urllib.parse import urlparse
from requests import HTTPError
import os


from videodb._constants import (
    ApiPath,
)

from videodb.exceptions import (
    VideodbError,
)


def _is_url(path: str) -> bool:
    parsed = urlparse(path)
    return all([parsed.scheme in ("http", "https"), parsed.netloc])


def upload(
    _connection,
    source: str | None = None,
    media_type: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    callback_url: Optional[str] = None,
    file_path: str | None = None,
    url: str | None = None,
) -> dict:
    """Upload a file or URL.

    ``source`` can be used as a generic argument which accepts either a local
    file path or a URL. ``file_path`` and ``url`` remain for backward
    compatibility and should not be used together with ``source``.
    """
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
            name = file_path.split("/")[-1].split(".")[0] if not name else name
            upload_url_data = _connection.get(
                path=f"{ApiPath.collection}/{_connection.collection_id}/{ApiPath.upload_url}",
                params={"name": name},
            )
            upload_url = upload_url_data.get("upload_url")
            with open(file_path, "rb") as file:
                files = {"file": (name, file)}
                response = requests.post(upload_url, files=files)
                response.raise_for_status()
                url = upload_url

        except FileNotFoundError as e:
            raise VideodbError("File not found", cause=e)

        except HTTPError as e:
            raise VideodbError("Error while uploading file", cause=e)

    upload_data = _connection.post(
        path=f"{ApiPath.collection}/{_connection.collection_id}/{ApiPath.upload}",
        data={
            "url": url,
            "name": name,
            "description": description,
            "callback_url": callback_url,
            "media_type": media_type,
        },
    )
    return upload_data
