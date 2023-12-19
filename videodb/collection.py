import logging

from typing import (
    Optional,
)
from videodb._upload import (
    upload,
)
from videodb._constants import (
    ApiPath,
    SearchType,
)
from videodb.video import Video
from videodb.search import SearchFactory, SearchResult

logger = logging.getLogger(__name__)


class Collection:
    def __init__(self, _connection, id: str, name: str = None, description: str = None):
        self._connection = _connection
        self.id = id
        self.name = name
        self.description = description

    def get_videos(self) -> list[Video]:
        videos_data = self._connection.get(path=f"{ApiPath.video}")
        return [Video(self._connection, **video) for video in videos_data.get("videos")]

    def get_video(self, video_id: str) -> Video:
        video_data = self._connection.get(path=f"{ApiPath.video}/{video_id}")
        return Video(self._connection, **video_data)

    def delete_video(self, video_id: str) -> None:
        """Delete the video

        :param str video_id: The id of the video to be deleted
        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        return self._connection.delete(path=f"{ApiPath.video}/{video_id}")

    def search(
        self,
        query: str,
        type: Optional[str] = SearchType.semantic,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[int] = None,
        dynamic_score_percentage: Optional[int] = None,
    ) -> SearchResult:
        search = SearchFactory(self._connection).get_search(type)
        return search.search_inside_collection(
            self.id,
            query,
            result_threshold,
            score_threshold,
            dynamic_score_percentage,
        )

    def upload(
        self,
        file_path: str = None,
        url: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Video:
        upload_data = upload(
            self._connection,
            file_path,
            url,
            name,
            description,
            callback_url,
        )
        return Video(self._connection, **upload_data) if upload_data else None
