from typing import Optional, Union
from videodb._utils._video import play_stream
from videodb._constants import (
    ApiPath,
    IndexType,
    SceneModels,
    SearchType,
    SubtitleStyle,
    Workflows,
)
from videodb.search import SearchFactory, SearchResult
from videodb.shot import Shot


class Video:
    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self.stream_url = kwargs.get("stream_url", None)
        self.player_url = kwargs.get("player_url", None)
        self.name = kwargs.get("name", None)
        self.description = kwargs.get("description", None)
        self.thumbnail_url = kwargs.get("thumbnail_url", None)
        self.length = float(kwargs.get("length", 0.0))
        self.transcript = kwargs.get("transcript", None)
        self.transcript_text = kwargs.get("transcript_text", None)
        self.scenes = kwargs.get("scenes", None)

    def __repr__(self) -> str:
        return (
            f"Video("
            f"id={self.id}, "
            f"collection_id={self.collection_id}, "
            f"stream_url={self.stream_url}, "
            f"player_url={self.player_url}, "
            f"name={self.name}, "
            f"description={self.description}, "
            f"thumbnail_url={self.thumbnail_url}, "
            f"length={self.length})"
        )

    def __getitem__(self, key):
        return self.__dict__[key]

    def search(
        self,
        query: str,
        search_type: Optional[str] = SearchType.semantic,
        scene_model: Optional[str] = SceneModels.gemini_vision,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[int] = None,
        dynamic_score_percentage: Optional[int] = None,
    ) -> SearchResult:
        search = SearchFactory(self._connection).get_search(search_type)
        return search.search_inside_video(
            video_id=self.id,
            query=query,
            result_threshold=result_threshold,
            score_threshold=score_threshold,
            dynamic_score_percentage=dynamic_score_percentage,
            scene_model=scene_model,
        )

    def delete(self) -> None:
        """Delete the video

        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        self._connection.delete(path=f"{ApiPath.video}/{self.id}")

    def generate_stream(self, timeline: Optional[list[tuple[int, int]]] = None) -> str:
        """Generate the stream url of the video

        :param list timeline: The timeline of the video to be streamed. Defaults to None.
        :raises InvalidRequestError: If the get_stream fails
        :return: The stream url of the video
        :rtype: str
        """
        if not timeline and self.stream_url:
            return self.stream_url

        stream_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.stream}",
            data={
                "timeline": timeline,
                "length": self.length,
            },
        )
        return stream_data.get("stream_url", None)

    def generate_thumbnail(self):
        if self.thumbnail_url:
            return self.thumbnail_url
        thumbnail_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.thumbnail}"
        )
        self.thumbnail_url = thumbnail_data.get("thumbnail_url")
        return self.thumbnail_url

    def _fetch_transcript(self, force: bool = False) -> None:
        if self.transcript and not force:
            return
        transcript_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.transcription}",
            params={"force": "true" if force else "false"},
            show_progress=True,
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
        """Semantic indexing of spoken words in the video

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

    def index_scenes(
        self,
        scene_model: str = SceneModels.gpt4_vision,
        force: bool = False,
        prompt: str = None,
        threshold: float = None,
        min_scene_len: int = None,
        num_images: int = None,
        callback_url: str = None,
    ) -> None:
        self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}",
            data={
                "index_type": IndexType.scene,
                "model_name": scene_model,
                "force": force,
                "prompt": prompt,
                "threshold": threshold,
                "min_scene_len": min_scene_len,
                "num_images": num_images,
                "callback_url": callback_url,
            },
        )

    def get_scenes(
        self, scene_model: str = SceneModels.gpt4_vision
    ) -> Union[list, None]:
        if self.scenes:
            return self.scenes
        scene_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}",
            params={
                "index_type": IndexType.scene,
                "model_name": scene_model,
            },
        )
        self.scenes = scene_data
        return scene_data if scene_data else None

    def delete_scene_index(self, scene_model: str = SceneModels.gpt4_vision) -> None:
        self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}/{ApiPath.delete}",
            data={
                "index_type": IndexType.scene,
                "model_name": scene_model,
            },
        )
        self.scenes = None

    def add_subtitle(self, style: SubtitleStyle = SubtitleStyle()) -> str:
        if not isinstance(style, SubtitleStyle):
            raise ValueError("style must be of type SubtitleStyle")
        subtitle_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.workflow}",
            data={
                "type": Workflows.add_subtitles,
                "subtitle_style": style.__dict__,
            },
        )
        return subtitle_data.get("stream_url", None)

    def insert_video(self, video, timestamp: float) -> str:
        """Insert a video into another video

        :param Video video: The video to be inserted
        :param float timestamp: The timestamp where the video should be inserted
        :raises InvalidRequestError: If the insert fails
        :return: The stream url of the inserted video
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
        return compile_data.get("stream_url", None)

    def play(self) -> str:
        """Open the player url in the browser/iframe and return the stream url

        :return: The stream url
        :rtype: str
        """
        return play_stream(self.stream_url)
