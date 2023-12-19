from videodb._constants import (
    ApiPath,
    SearchType,
    IndexType,
    Workflows,
)
from videodb.search import SearchFactory, SearchResult
from videodb.shot import Shot
from typing import Optional


class Video:
    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self.stream_link = kwargs.get("stream_link", None)
        self.name = kwargs.get("name", None)
        self.description = kwargs.get("description", None)
        self.thumbnail = kwargs.get("thumbnail", None)
        self.length = float(kwargs.get("length", 0.0))
        self.transcript = kwargs.get("transcript", None)
        self.transcript_text = kwargs.get("transcript_text", None)

    def __repr__(self) -> str:
        return (
            f"Video("
            f"id={self.id}, "
            f"collection_id={self.collection_id}, "
            f"stream_link={self.stream_link}, "
            f"name={self.name}, "
            f"description={self.description}, "
            f"thumbnail={self.thumbnail}, "
            f"length={self.length})"
        )

    def __getitem__(self, key):
        return self.__dict__[key]

    def search(
        self,
        query: str,
        search_type: Optional[str] = SearchType.semantic,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[int] = None,
        dynamic_score_percentage: Optional[int] = None,
    ) -> SearchResult:
        search = SearchFactory(self._connection).get_search(search_type)
        return search.search_inside_video(
            self.id,
            query,
            result_threshold,
            score_threshold,
            dynamic_score_percentage,
        )

    def delete(self) -> None:
        """Delete the video

        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        self._connection.delete(path=f"{ApiPath.video}/{self.id}")

    def get_stream(self, timeline: Optional[list[tuple[int, int]]] = None) -> str:
        """Get the stream link of the video

        :param list timeline: The timeline of the video to be streamed. Defaults to None.
        :raises InvalidRequestError: If the get_stream fails
        :return: The stream link of the video
        :rtype: str
        """
        if not timeline and self.stream_link:
            return self.stream_link

        stream_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.stream}",
            data={
                "timeline": timeline,
                "length": self.length,
            },
        )
        return stream_data.get("stream_link")

    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail
        thumbnail_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.thumbnail}"
        )
        self.thumbnail = thumbnail_data.get("thumbnail")
        return self.thumbnail

    def _fetch_transcript(self, force: bool = False) -> None:
        if self.transcript and not force:
            return
        transcript_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.transcription}",
            params={"force": "true" if force else "false"},
        )
        self.transcript = transcript_data.get("word_timestamps", [])
        self.transcript_text = transcript_data.get("text", "")

    def get_transcript(self, force: bool = False) -> list[dict]:
        self._fetch_transcript(force)
        return self.transcript

    def get_transcript_text(self, force: bool = False) -> str:
        self._fetch_transcript(force)
        return self.transcript_text

    def index_spoken_words(self) -> None:
        """Symantic indexing of spoken words in the video

        :raises InvalidRequestError: If the video is already indexed
        :return: None if the indexing is successful
        :rtype: None
        """
        self._fetch_transcript()
        self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}",
            data={
                "index_type": IndexType.semantic,
            },
        )

    def add_subtitle(self) -> str:
        subtitle_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.workflow}",
            data={
                "type": Workflows.add_subtitles,
            },
        )
        return subtitle_data.get("stream_link")

    def insert_video(self, video, timestamp: float) -> str:
        """Insert a video into another video

        :param Video video: The video to be inserted
        :param float timestamp: The timestamp where the video should be inserted
        :raises InvalidRequestError: If the insert fails
        :return: The stream link of the inserted video
        :rtype: str
        """
        if timestamp > float(self.length):
            timestamp = float(self.length)

        pre_shot = Shot(self._connection, self.id, timestamp, "", 0, timestamp)
        inserted_shot = Shot(
            self._connection, video.id, video.length, "", 0, video.length
        )
        post_shot = Shot(
            self._connection,
            self.id,
            self.length - timestamp,
            "",
            timestamp,
            self.length,
        )
        all_shots = [pre_shot, inserted_shot, post_shot]

        compile_data = self._connection.post(
            path=f"{ApiPath.compile}",
            data=[
                {
                    "video_id": shot.video_id,
                    "collection_id": self.collection_id,
                    "shots": [(float(shot.start), float(shot.end))],
                }
                for shot in all_shots
            ],
        )
        stream_link = compile_data.get("stream_link")
        return stream_link
