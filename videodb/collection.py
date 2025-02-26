import logging

from typing import (
    Optional,
    Union,
    List,
    Dict,
    Any,
)
from videodb._upload import (
    upload,
)
from videodb._constants import (
    ApiPath,
    IndexType,
    SearchType,
)
from videodb.video import Video
from videodb.audio import Audio
from videodb.image import Image
from videodb.search import SearchFactory, SearchResult

logger = logging.getLogger(__name__)


class Collection:
    """Collection class to interact with the Collection"""

    def __init__(
        self,
        _connection,
        id: str,
        name: str = None,
        description: str = None,
        is_public: bool = False,
    ):
        self._connection = _connection
        self.id = id
        self.name = name
        self.description = description
        self.is_public = is_public

    def __repr__(self) -> str:
        return (
            f"Collection("
            f"id={self.id}, "
            f"name={self.name}, "
            f"description={self.description}), "
            f"is_public={self.is_public})"
        )

    def delete(self) -> None:
        """Delete the collection

        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        self._connection.delete(path=f"{ApiPath.collection}/{self.id}")

    def get_videos(self) -> List[Video]:
        """Get all the videos in the collection.

        :return: List of :class:`Video <Video>` objects
        :rtype: List[:class:`videodb.video.Video`]
        """
        videos_data = self._connection.get(
            path=f"{ApiPath.video}",
            params={"collection_id": self.id},
        )
        return [Video(self._connection, **video) for video in videos_data.get("videos")]

    def get_video(self, video_id: str) -> Video:
        """Get a video by its ID.

        :param str video_id: ID of the video
        :return: :class:`Video <Video>` object
        :rtype: :class:`videodb.video.Video`
        """
        video_data = self._connection.get(
            path=f"{ApiPath.video}/{video_id}", params={"collection_id": self.id}
        )
        return Video(self._connection, **video_data)

    def delete_video(self, video_id: str) -> None:
        """Delete the video.

        :param str video_id: The id of the video to be deleted
        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        return self._connection.delete(
            path=f"{ApiPath.video}/{video_id}", params={"collection_id": self.id}
        )

    def get_audios(self) -> List[Audio]:
        """Get all the audios in the collection.

        :return: List of :class:`Audio <Audio>` objects
        :rtype: List[:class:`videodb.audio.Audio`]
        """
        audios_data = self._connection.get(
            path=f"{ApiPath.audio}",
            params={"collection_id": self.id},
        )
        return [Audio(self._connection, **audio) for audio in audios_data.get("audios")]

    def get_audio(self, audio_id: str) -> Audio:
        """Get an audio by its ID.

        :param str audio_id: ID of the audio
        :return: :class:`Audio <Audio>` object
        :rtype: :class:`videodb.audio.Audio`
        """
        audio_data = self._connection.get(
            path=f"{ApiPath.audio}/{audio_id}", params={"collection_id": self.id}
        )
        return Audio(self._connection, **audio_data)

    def delete_audio(self, audio_id: str) -> None:
        """Delete the audio.

        :param str audio_id: The id of the audio to be deleted
        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        return self._connection.delete(
            path=f"{ApiPath.audio}/{audio_id}", params={"collection_id": self.id}
        )

    def get_images(self) -> List[Image]:
        """Get all the images in the collection.

        :return: List of :class:`Image <Image>` objects
        :rtype: List[:class:`videodb.image.Image`]
        """
        images_data = self._connection.get(
            path=f"{ApiPath.image}",
            params={"collection_id": self.id},
        )
        return [Image(self._connection, **image) for image in images_data.get("images")]

    def get_image(self, image_id: str) -> Image:
        """Get an image by its ID.

        :param str image_id: ID of the image
        :return: :class:`Image <Image>` object
        :rtype: :class:`videodb.image.Image`
        """
        image_data = self._connection.get(
            path=f"{ApiPath.image}/{image_id}", params={"collection_id": self.id}
        )
        return Image(self._connection, **image_data)

    def delete_image(self, image_id: str) -> None:
        """Delete the image.

        :param str image_id: The id of the image to be deleted
        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        return self._connection.delete(
            path=f"{ApiPath.image}/{image_id}", params={"collection_id": self.id}
        )

    def search(
        self,
        query: str,
        search_type: Optional[str] = SearchType.semantic,
        index_type: Optional[str] = IndexType.spoken_word,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[float] = None,
        dynamic_score_percentage: Optional[float] = None,
        filter: List[Dict[str, Any]] = [],
    ) -> SearchResult:
        """Search for a query in the collection.

        :param str query: Query to search for
        :param search_type:(optional) Type of search to perform :class:`SearchType <SearchType>` object
        :param index_type:(optional) Type of index to search :class:`IndexType <IndexType>` object
        :param int result_threshold:(optional) Number of results to return
        :param float score_threshold:(optional) Threshold score for the search
        :param float dynamic_score_percentage:(optional) Percentage of dynamic score to consider
        :raise SearchError: If the search fails
        :return: :class:`SearchResult <SearchResult>` object
        :rtype: :class:`videodb.search.SearchResult`
        """
        search = SearchFactory(self._connection).get_search(search_type)
        return search.search_inside_collection(
            collection_id=self.id,
            query=query,
            search_type=search_type,
            index_type=index_type,
            result_threshold=result_threshold,
            score_threshold=score_threshold,
            dynamic_score_percentage=dynamic_score_percentage,
            filter=filter,
        )

    def search_title(self, query) -> List[Video]:
        search_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.search}/{ApiPath.title}",
            data={
                "query": query,
                "search_type": SearchType.llm,
            },
        )
        return [
            {"video": Video(self._connection, **result.get("video"))}
            for result in search_data
        ]

    def upload(
        self,
        file_path: str = None,
        url: Optional[str] = None,
        media_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Union[Video, Audio, Image, None]:
        """Upload a file to the collection.

        :param str file_path: Path to the file to be uploaded
        :param str url: URL of the file to be uploaded
        :param MediaType media_type:(optional):class:`MediaType <MediaType>` object
        :param name:(optional) Name of the file
        :param description:(optional) Description of the file
        :param callback_url:(optional) URL to receive the callback
        :return: :class:`Video <Video>`, or :class:`Audio <Audio>`, or :class:`Image <Image>` object
        Union[ :class:`videodb.video.Video`, :class:`videodb.audio.Audio`, :class:`videodb.image.Image`]
        """
        upload_data = upload(
            self._connection,
            file_path,
            url,
            media_type,
            name,
            description,
            callback_url,
        )
        media_id = upload_data.get("id", "")
        if media_id.startswith("m-"):
            return Video(self._connection, **upload_data)
        elif media_id.startswith("a-"):
            return Audio(self._connection, **upload_data)
        elif media_id.startswith("img-"):
            return Image(self._connection, **upload_data)

    def make_public(self):
        self._connection.patch(
            path=f"{ApiPath.collection}/{self.id}", data={"is_public": True}
        )
        self.is_public = True

    def make_private(self):
        self._connection.patch(
            path=f"{ApiPath.collection}/{self.id}", data={"is_public": False}
        )
        self.is_public = False
