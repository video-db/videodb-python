import logging

from typing import (
    Optional,
    Union,
    List,
)
from videodb._upload import (
    upload,
)
from videodb._constants import (
    ApiPath,
    SearchType,
)
from videodb.video import Video
from videodb.audio import Audio
from videodb.image import Image
from videodb.search import SearchFactory, SearchResult

logger = logging.getLogger(__name__)


class Collection:
    def __init__(self, _connection, id: str, name: str = None, description: str = None):
        self._connection = _connection
        self.id = id
        self.name = name
        self.description = description

    def __repr__(self) -> str:
        return (
            f"Collection("
            f"id={self.id}, "
            f"name={self.name}, "
            f"description={self.description})"
        )

    def get_videos(self) -> List[Video]:
        videos_data = self._connection.get(
            path=f"{ApiPath.video}",
            params={"collection_id": self.id},
        )
        return [Video(self._connection, **video) for video in videos_data.get("videos")]

    def get_video(self, video_id: str) -> Video:
        video_data = self._connection.get(
            path=f"{ApiPath.video}/{video_id}", params={"collection_id": self.id}
        )
        return Video(self._connection, **video_data)

    def delete_video(self, video_id: str) -> None:
        """Delete the video

        :param str video_id: The id of the video to be deleted
        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        return self._connection.delete(
            path=f"{ApiPath.video}/{video_id}", params={"collection_id": self.id}
        )

    def get_audios(self) -> List[Audio]:
        audios_data = self._connection.get(
            path=f"{ApiPath.audio}",
            params={"collection_id": self.id},
        )
        return [Audio(self._connection, **audio) for audio in audios_data.get("audios")]

    def get_audio(self, audio_id: str) -> Audio:
        audio_data = self._connection.get(
            path=f"{ApiPath.audio}/{audio_id}", params={"collection_id": self.id}
        )
        return Audio(self._connection, **audio_data)

    def delete_audio(self, audio_id: str) -> None:
        return self._connection.delete(
            path=f"{ApiPath.audio}/{audio_id}", params={"collection_id": self.id}
        )

    def get_images(self) -> List[Image]:
        images_data = self._connection.get(
            path=f"{ApiPath.image}",
            params={"collection_id": self.id},
        )
        return [Image(self._connection, **image) for image in images_data.get("images")]

    def get_image(self, image_id: str) -> Image:
        image_data = self._connection.get(
            path=f"{ApiPath.image}/{image_id}", params={"collection_id": self.id}
        )
        return Image(self._connection, **image_data)

    def delete_image(self, image_id: str) -> None:
        return self._connection.delete(
            path=f"{ApiPath.image}/{image_id}", params={"collection_id": self.id}
        )

    def search(
        self,
        query: str,
        search_type: Optional[str] = SearchType.semantic,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[float] = None,
        dynamic_score_percentage: Optional[float] = None,
    ) -> SearchResult:
        search = SearchFactory(self._connection).get_search(search_type)
        return search.search_inside_collection(
            collection_id=self.id,
            query=query,
            result_threshold=result_threshold,
            score_threshold=score_threshold,
            dynamic_score_percentage=dynamic_score_percentage,
        )

    def upload(
        self,
        file_path: str = None,
        url: Optional[str] = None,
        media_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Union[Video, Audio, Image, None]:
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
