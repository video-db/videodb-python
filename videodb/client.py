import logging

from typing import (
    Optional,
    Union,
    List,
)
from videodb.__about__ import __version__
from videodb._constants import (
    ApiPath,
)

from videodb.collection import Collection
from videodb._utils._http_client import HttpClient
from videodb.video import Video
from videodb.audio import Audio
from videodb.image import Image

from videodb._upload import (
    upload,
)

logger = logging.getLogger(__name__)


class Connection(HttpClient):
    def __init__(self, api_key: str, base_url: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.collection_id = "default"
        super().__init__(api_key=api_key, base_url=base_url, version=__version__)

    def get_collection(self, collection_id: Optional[str] = "default") -> Collection:
        collection_data = self.get(path=f"{ApiPath.collection}/{collection_id}")
        self.collection_id = collection_data.get("id", "default")
        return Collection(
            self,
            self.collection_id,
            collection_data.get("name"),
            collection_data.get("description"),
        )

    def get_collections(self) -> List[Collection]:
        collections_data = self.get(path=ApiPath.collection)
        return [
            Collection(
                self,
                collection.get("id"),
                collection.get("name"),
                collection.get("description"),
            )
            for collection in collections_data.get("collections")
        ]

    def create_collection(self, name: str, description: str) -> Collection:
        collection_data = self.post(
            path=ApiPath.collection,
            data={
                "name": name,
                "description": description,
            },
        )
        self.collection_id = collection_data.get("id", "default")
        return Collection(
            self,
            collection_data.get("id"),
            collection_data.get("name"),
            collection_data.get("description"),
        )

    def update_collection(self, id: str, name: str, description: str) -> Collection:
        collection_data = self.patch(
            path=f"{ApiPath.collection}/{id}",
            data={
                "name": name,
                "description": description,
            },
        )
        self.collection_id = collection_data.get("id", "default")
        return Collection(
            self,
            collection_data.get("id"),
            collection_data.get("name"),
            collection_data.get("description"),
        )

    def check_usage(self) -> dict:
        return self.get(path=f"{ApiPath.billing}/{ApiPath.usage}")

    def get_invoices(self) -> List[dict]:
        return self.get(path=f"{ApiPath.billing}/{ApiPath.invoices}")

    def upload(
        self,
        file_path: str = None,
        url: str = None,
        media_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Union[Video, Audio, Image, None]:
        upload_data = upload(
            self,
            file_path,
            url,
            media_type,
            name,
            description,
            callback_url,
        )
        media_id = upload_data.get("id", "")
        if media_id.startswith("m-"):
            return Video(self, **upload_data)
        elif media_id.startswith("a-"):
            return Audio(self, **upload_data)
        elif media_id.startswith("img-"):
            return Image(self, **upload_data)
