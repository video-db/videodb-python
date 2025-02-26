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
    """Connection class to interact with the VideoDB"""

    def __init__(self, api_key: str, base_url: str) -> None:
        """Initializes a new instance of the Connection class with specified API credentials.

        :param api_key: API key for authentication
        :param str base_url: (optional) Base URL of the VideoDB API
        :raise ValueError: If the API key is not provided
        :return: :class:`Connection <Connection>` object, to interact with the VideoDB
        :rtype: :class:`videodb.client.Connection`
        """
        self.api_key = api_key
        self.base_url = base_url
        self.collection_id = "default"
        super().__init__(api_key=api_key, base_url=base_url, version=__version__)

    def get_collection(self, collection_id: Optional[str] = "default") -> Collection:
        """Get a collection object by its ID.

        :param collection_id: ID of the collection
        :return: :class:`Collection <Collection>` object
        :rtype: :class:`videodb.collection.Collection`
        """
        collection_data = self.get(path=f"{ApiPath.collection}/{collection_id}")
        self.collection_id = collection_data.get("id", "default")
        return Collection(
            self,
            self.collection_id,
            collection_data.get("name"),
            collection_data.get("description"),
            collection_data.get("is_public", False),
        )

    def get_collections(self) -> List[Collection]:
        """Get a list of all collections.

        :return: List of :class:`Collection <Collection>` objects
        :rtype: list[:class:`videodb.collection.Collection`]
        """
        collections_data = self.get(path=ApiPath.collection)
        return [
            Collection(
                self,
                collection.get("id"),
                collection.get("name"),
                collection.get("description"),
                collection.get("is_public", False),
            )
            for collection in collections_data.get("collections")
        ]

    def create_collection(
        self, name: str, description: str, is_public: bool = False
    ) -> Collection:
        """Create a new collection.

        :param name: Name of the collection
        :param description: Description of the collection
        :param is_public: Make collection public
        :return: :class:`Collection <Collection>` object
        :rtype: :class:`videodb.collection.Collection`
        """
        collection_data = self.post(
            path=ApiPath.collection,
            data={
                "name": name,
                "description": description,
                "is_public": is_public,
            },
        )
        self.collection_id = collection_data.get("id", "default")
        return Collection(
            self,
            collection_data.get("id"),
            collection_data.get("name"),
            collection_data.get("description"),
            collection_data.get("is_public", False),
        )

    def update_collection(self, id: str, name: str, description: str) -> Collection:
        """Update an existing collection.

        :param str id: ID of the collection
        :param name: Name of the collection
        :param description: Description of the collection
        :return: :class:`Collection <Collection>` object
        :rtype: :class:`videodb.collection.Collection`
        """
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
            collection_data.get("is_public", False),
        )

    def check_usage(self) -> dict:
        """Check the usage.

        :return: Usage data
        :rtype: dict
        """
        return self.get(path=f"{ApiPath.billing}/{ApiPath.usage}")

    def get_invoices(self) -> List[dict]:
        """Get a list of all invoices.

        :return: List of invoices
        :rtype: list of dict
        """
        return self.get(path=f"{ApiPath.billing}/{ApiPath.invoices}")

    def download(self, stream_link: str, name: str) -> dict:
        return self.post(
            path=f"{ApiPath.download}",
            data={
                "stream_link": stream_link,
                "name": name,
            },
        )

    def upload(
        self,
        file_path: str = None,
        url: str = None,
        media_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Union[Video, Audio, Image, None]:
        """Upload a file.

        :param file_path: Path to the file to upload
        :param url: URL of the file to upload
        :param MediaType media_type:(optional):class:`MediaType <MediaType>` object
        :param name:(optional) Name of the file
        :param description:(optional) Description of the file
        :param callback_url:(optional) URL to receive the callback
        :return: :class:`Video <Video>`, or :class:`Audio <Audio>`, or :class:`Image <Image>` object
        :rtype: Union[ :class:`videodb.video.Video`, :class:`videodb.audio.Audio`, :class:`videodb.image.Image`]
        """
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
