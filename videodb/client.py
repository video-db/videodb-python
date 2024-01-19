import logging

from typing import (
    Optional,
    Union,
)

from videodb._constants import (
    ApiPath,
)

from videodb.collection import Collection
from videodb._utils._http_client import HttpClient
from videodb.video import Video
from videodb.audio import Audio

from videodb._upload import (
    upload,
)

logger = logging.getLogger(__name__)


class Connection(HttpClient):
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.collection_id = "default"
        super().__init__(api_key, base_url)

    def get_collection(self, collection_id: Optional[str] = "default") -> Collection:
        collection_data = self.get(path=f"{ApiPath.collection}/{collection_id}")
        self.collection_id = collection_data.get("id", "default")
        return Collection(
            self,
            self.collection_id,
            collection_data.get("name"),
            collection_data.get("description"),
        )

    def upload(
        self,
        file_path: str = None,
        url: str = None,
        media_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Union[Video, Audio, None]:
        upload_data = upload(
            self,
            file_path,
            url,
            media_type,
            name,
            description,
            callback_url,
        )
        if upload_data.get("id").startswith("m-"):
            return Video(self, **upload_data) if upload_data else None
        elif upload_data.get("id").startswith("a-"):
            return Audio(self, **upload_data) if upload_data else None
