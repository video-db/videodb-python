from typing import Optional, Union, List, Dict, Tuple, Any
from videodb._utils._video import play_stream
from videodb._constants import (
    ApiPath,
    IndexType,
    SceneExtractionType,
    SearchType,
    Segmenter,
    SubtitleStyle,
    Workflows,
)
from videodb.image import Image, Frame
from videodb.scene import Scene, SceneCollection
from videodb.search import SearchFactory, SearchResult
from videodb.shot import Shot


class Video:
    """Video class to interact with the Video

    :ivar str id: Unique identifier for the video
    :ivar str collection_id: ID of the collection this video belongs to
    :ivar str stream_url: URL to stream the video
    :ivar str player_url: URL to play the video in a player
    :ivar str name: Name of the video file
    :ivar str description: Description of the video
    :ivar str thumbnail_url: URL of the video thumbnail
    :ivar float length: Duration of the video in seconds
    :ivar list transcript: Timestamped transcript segments
    :ivar str transcript_text: Full transcript text
    :ivar list scenes: List of scenes in the video
    """

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
        index_type: Optional[str] = IndexType.spoken_word,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[float] = None,
        dynamic_score_percentage: Optional[float] = None,
        filter: List[Dict[str, Any]] = [],
        **kwargs,
    ) -> SearchResult:
        """Search for a query in the video.

        :param str query: Query to search for.
        :param SearchType search_type: (optional) Type of search to perform :class:`SearchType <SearchType>` object
        :param IndexType index_type: (optional) Type of index to search :class:`IndexType <IndexType>` object
        :param int result_threshold: (optional) Number of results to return
        :param float score_threshold: (optional) Threshold score for the search
        :param float dynamic_score_percentage: (optional) Percentage of dynamic score to consider
        :raise SearchError: If the search fails
        :return: :class:`SearchResult <SearchResult>` object
        :rtype: :class:`videodb.search.SearchResult`
        """
        search = SearchFactory(self._connection).get_search(search_type)
        return search.search_inside_video(
            video_id=self.id,
            query=query,
            search_type=search_type,
            index_type=index_type,
            result_threshold=result_threshold,
            score_threshold=score_threshold,
            dynamic_score_percentage=dynamic_score_percentage,
            filter=filter,
            **kwargs,
        )

    def delete(self) -> None:
        """Delete the video.

        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        self._connection.delete(path=f"{ApiPath.video}/{self.id}")

    def remove_storage(self) -> None:
        """Remove the video storage.

        :raises InvalidRequestError: If the storage removal fails
        :return: None if the removal is successful
        :rtype: None
        """
        self._connection.delete(path=f"{ApiPath.video}/{self.id}/{ApiPath.storage}")

    def generate_stream(
        self, timeline: Optional[List[Tuple[float, float]]] = None
    ) -> str:
        """Generate the stream url of the video.

        :param List[Tuple[float, float]] timeline: (optional) The timeline of the video to be streamed in the format [(start, end)]
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

    def generate_thumbnail(self, time: Optional[float] = None) -> Union[str, Image]:
        """Generate the thumbnail of the video.

        :param float time: (optional) The time of the video to generate the thumbnail
        :returns: :class:`Image <Image>` object if time is provided else the thumbnail url
        :rtype: Union[str, :class:`videodb.image.Image`]
        """
        if self.thumbnail_url and not time:
            return self.thumbnail_url

        if time:
            thumbnail_data = self._connection.post(
                path=f"{ApiPath.video}/{self.id}/{ApiPath.thumbnail}",
                data={
                    "time": time,
                },
            )
            return Image(self._connection, **thumbnail_data)

        thumbnail_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.thumbnail}"
        )
        self.thumbnail_url = thumbnail_data.get("thumbnail_url")
        return self.thumbnail_url

    def get_thumbnails(self) -> List[Image]:
        """Get all the thumbnails of the video.

        :return: List of :class:`Image <Image>` objects
        :rtype: List[:class:`videodb.image.Image`]
        """
        thumbnails_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.thumbnails}"
        )
        return [Image(self._connection, **thumbnail) for thumbnail in thumbnails_data]

    def _fetch_transcript(
        self,
        start: int = None,
        end: int = None,
        segmenter: str = Segmenter.word,
        length: int = 1,
        force: bool = None,
    ) -> None:
        if (
            self.transcript
            and not start
            and not end
            and not segmenter
            and not length
            and not force
        ):
            return
        transcript_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.transcription}",
            params={
                "start": start,
                "end": end,
                "segmenter": segmenter,
                "length": length,
                "force": "true" if force else "false",
            },
            show_progress=True,
        )
        self.transcript = transcript_data.get("word_timestamps", [])
        self.transcript_text = transcript_data.get("text", "")

    def get_transcript(
        self,
        start: int = None,
        end: int = None,
        segmenter: Segmenter = Segmenter.word,
        length: int = 1,
        force: bool = None,
    ) -> List[Dict[str, Union[float, str]]]:
        """Get timestamped transcript segments for the video.

        :param int start: Start time in seconds
        :param int end: End time in seconds
        :param Segmenter segmenter: Segmentation type (:class:`Segmenter.word`,
            :class:`Segmenter.sentence`, :class:`Segmenter.time`)
        :param int length: Length of segments when using time segmenter
        :param bool force: Force fetch new transcript
        :return: List of dicts with keys: start (float), end (float), text (str)
        :rtype: List[Dict[str, Union[float, str]]]
        """
        self._fetch_transcript(
            start=start, end=end, segmenter=segmenter, length=length, force=force
        )
        return self.transcript

    def get_transcript_text(
        self,
        start: int = None,
        end: int = None,
        segmenter: str = Segmenter.word,
        length: int = 1,
        force: bool = None,
    ) -> str:
        """Get plain text transcript for the video.

        :param int start: Start time in seconds to get transcript from
        :param int end: End time in seconds to get transcript until
        :param bool force: Force fetch new transcript
        :return: Full transcript text as string
        :rtype: str
        """
        self._fetch_transcript(
            start=start, end=end, segmenter=segmenter, length=length, force=force
        )
        return self.transcript_text

    def generate_transcript(
        self,
        force: bool = None,
    ) -> str:
        """Generate transcript for the video.

        :param bool force: Force generate new transcript
        :return: Full transcript text as string
        :rtype: str
        """
        transcript_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.transcription}",
            data={
                "force": True if force else False,
            },
        )
        transcript = transcript_data.get("word_timestamps", [])
        if transcript:
            return {
                "success": True,
                "message": "Transcript generated successfully",
            }
        return transcript_data

    def translate_transcript(
        self,
        language: str,
        additional_notes: str = "",
        callback_url: Optional[str] = None,
    ) -> List[dict]:
        """Translate transcript of a video to a given language.

        :param str language: Language to translate the transcript
        :param str additional_notes: Additional notes for the style of language
        :param str callback_url: URL to receive the callback (optional)
        :return: List of translated transcript
        :rtype: List[dict]
        """
        translate_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.collection_id}/{ApiPath.video}/{self.id}/{ApiPath.translate}",
            data={
                "language": language,
                "additional_notes": additional_notes,
                "callback_url": callback_url,
            },
        )
        if translate_data:
            return translate_data.get("translated_transcript")

    def index_spoken_words(
        self,
        language_code: Optional[str] = None,
        force: bool = False,
        callback_url: str = None,
    ) -> None:
        """Semantic indexing of spoken words in the video.

        :param str language_code: (optional) Language code of the video
        :param bool force: (optional) Force to index the video
        :param str callback_url: (optional) URL to receive the callback
        :raises InvalidRequestError: If the video is already indexed
        :return: None if the indexing is successful
        :rtype: None
        """
        self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}",
            data={
                "index_type": IndexType.spoken_word,
                "language_code": language_code,
                "force": force,
                "callback_url": callback_url,
            },
            show_progress=True,
        )

    def get_scenes(self) -> Union[list, None]:
        """
        .. deprecated:: 0.2.0
        Use :func:`list_scene_index` and :func:`get_scene_index` instead.

        Get the scenes of the video.

        :return: The scenes of the video
        :rtype: list
        """
        if self.scenes:
            return self.scenes
        scene_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}",
            params={
                "index_type": IndexType.scene,
            },
        )
        self.scenes = scene_data
        return scene_data if scene_data else None

    def _format_scene_collection(self, scene_collection_data: dict) -> SceneCollection:
        scenes = []
        for scene in scene_collection_data.get("scenes", []):
            frames = []
            for frame in scene.get("frames", []):
                frame = Frame(
                    self._connection,
                    frame.get("frame_id"),
                    self.id,
                    scene.get("scene_id"),
                    frame.get("url"),
                    frame.get("frame_time"),
                    frame.get("description"),
                )
                frames.append(frame)
            scene = Scene(
                video_id=self.id,
                start=scene.get("start"),
                end=scene.get("end"),
                description=scene.get("description"),
                id=scene.get("scene_id"),
                frames=frames,
                metadata=scene.get("metadata", {}),
                connection=self._connection,
            )
            scenes.append(scene)

        return SceneCollection(
            self._connection,
            scene_collection_data.get("scene_collection_id"),
            self.id,
            scene_collection_data.get("config", {}),
            scenes,
        )

    def extract_scenes(
        self,
        extraction_type: SceneExtractionType = SceneExtractionType.shot_based,
        extraction_config: dict = {},
        force: bool = False,
        callback_url: str = None,
    ) -> Optional[SceneCollection]:
        """Extract the scenes of the video.

        :param SceneExtractionType extraction_type: (optional) The type of extraction, :class:`SceneExtractionType <SceneExtractionType>` object
        :param dict extraction_config: (optional) Dictionary of configuration parameters to control how scenes are extracted.
            For time-based extraction (extraction_type=time_based):\n
                - "time" (int, optional): Interval in seconds at which scenes are
                  segmented. Default is 10 (i.e., every 10 seconds forms a new scene).
                - "frame_count" (int, optional): Number of frames to extract per
                  scene. Default is 1.
                - "select_frames" (List[str], optional): Which frames to select from
                  each segment. Possible values include "first", "middle", and "last".
                  Default is ["first"].

            For shot-based extraction (extraction_type=shot_based):\n
                - "threshold" (int, optional): Sensitivity for detecting scene changes
                  (camera shots). The higher the threshold, the fewer scene splits.
                  Default is 20.
                - "frame_count" (int, optional): Number of frames to extract from
                  each detected shot. Default is 1.
        :param bool force: (optional) Force to extract the scenes
        :param str callback_url: (optional) URL to receive the callback
        :raises InvalidRequestError: If the extraction fails
        :return: The scene collection, :class:`SceneCollection <SceneCollection>` object
        :rtype: :class:`videodb.scene.SceneCollection`
        """
        scenes_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.scenes}",
            data={
                "extraction_type": extraction_type,
                "extraction_config": extraction_config,
                "force": force,
                "callback_url": callback_url,
            },
        )
        if not scenes_data:
            return None
        return self._format_scene_collection(scenes_data.get("scene_collection"))

    def get_scene_collection(self, collection_id: str) -> Optional[SceneCollection]:
        """Get the scene collection.

        :param str collection_id: The id of the scene collection
        :return: The scene collection
        :rtype: :class:`videodb.scene.SceneCollection`
        """
        if not collection_id:
            raise ValueError("collection_id is required")
        scenes_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.scenes}/{collection_id}",
            params={"collection_id": self.collection_id},
        )
        if not scenes_data:
            return None
        return self._format_scene_collection(scenes_data.get("scene_collection"))

    def list_scene_collection(self):
        """List all the scene collections.

        :return: The scene collections
        :rtype: list
        """
        scene_collections_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.scenes}",
            params={"collection_id": self.collection_id},
        )
        return scene_collections_data.get("scene_collections", [])

    def delete_scene_collection(self, collection_id: str) -> None:
        """Delete the scene collection.

        :param str collection_id: The id of the scene collection to be deleted
        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        if not collection_id:
            raise ValueError("collection_id is required")
        self._connection.delete(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.scenes}/{collection_id}"
        )

    def index_scenes(
        self,
        extraction_type: SceneExtractionType = SceneExtractionType.shot_based,
        extraction_config: Dict = {},
        prompt: Optional[str] = None,
        metadata: Dict = {},
        model_name: Optional[str] = None,
        model_config: Optional[Dict] = None,
        name: Optional[str] = None,
        scenes: Optional[List[Scene]] = None,
        callback_url: Optional[str] = None,
    ) -> Optional[str]:
        """Index the scenes of the video.

        :param SceneExtractionType extraction_type: (optional) The type of extraction, :class:`SceneExtractionType <SceneExtractionType>` object
        :param dict extraction_config: (optional) Dictionary of configuration parameters to control how scenes are extracted.
            For time-based extraction (extraction_type=time_based):\n
                - "time" (int, optional): Interval in seconds at which scenes are
                  segmented. Default is 10 (i.e., every 10 seconds forms a new scene).
                - "frame_count" (int, optional): Number of frames to extract per
                  scene. Default is 1.
                - "select_frames" (List[str], optional): Which frames to select from
                  each segment. Possible values include "first", "middle", and "last".
                  Default is ["first"].

            For shot-based extraction (extraction_type=shot_based):\n
                - "threshold" (int, optional): Sensitivity for detecting scene changes
                  (camera shots). The higher the threshold, the fewer scene splits.
                  Default is 20.
                - "frame_count" (int, optional): Number of frames to extract from
                  each detected shot. Default is 1.
        :param str prompt: (optional) The prompt for the extraction
        :param str model_name: (optional) The model name for the extraction
        :param dict model_config: (optional) The model configuration for the extraction
        :param str name: (optional) The name of the scene index
        :param list[Scene] scenes: (optional) The scenes to be indexed, List of :class:`Scene <Scene>` objects
        :param str callback_url: (optional) The callback url
        :raises InvalidRequestError: If the index fails or index already exists
        :return: The scene index id
        :rtype: str
        """
        scenes_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            data={
                "extraction_type": extraction_type,
                "extraction_config": extraction_config,
                "prompt": prompt,
                "metadata": metadata,
                "model_name": model_name,
                "model_config": model_config,
                "name": name,
                "scenes": [scene.to_json() for scene in scenes] if scenes else None,
                "callback_url": callback_url,
            },
        )
        if not scenes_data:
            return None
        return scenes_data.get("scene_index_id")

    def list_scene_index(self) -> List:
        """List all the scene indexes.

        :return: The scene indexes
        :rtype: list
        """
        index_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            params={"collection_id": self.collection_id},
        )
        return index_data.get("scene_indexes", [])

    def get_scene_index(self, scene_index_id: str) -> Optional[List]:
        """Get the scene index.

        :param str scene_index_id: The id of the scene index
        :return: The scene index records
        :rtype: list
        """
        index_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}/{ApiPath.scene}/{scene_index_id}",
            params={"collection_id": self.collection_id},
        )
        if not index_data:
            return None
        return index_data.get("scene_index_records", [])

    def delete_scene_index(self, scene_index_id: str) -> None:
        """Delete the scene index.

        :param str scene_index_id: The id of the scene index to be deleted
        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        if not scene_index_id:
            raise ValueError("scene_index_id is required")
        self._connection.delete(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}/{ApiPath.scene}/{scene_index_id}"
        )

    def add_subtitle(self, style: SubtitleStyle = SubtitleStyle()) -> str:
        """Add subtitles to the video.

        :param SubtitleStyle style: (optional) The style of the subtitles, :class:`SubtitleStyle <SubtitleStyle>` object
        :return: The stream url of the video with subtitles
        :rtype: str
        """
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
        """Open the player url in the browser/iframe and return the stream url.

        :return: The player url
        :rtype: str
        """
        return play_stream(self.stream_url)

    def get_meeting(self):
        """Get meeting information associated with the video.

        :return: :class:`Meeting <Meeting>` object if meeting is associated, None otherwise
        :rtype: Optional[:class:`videodb.meeting.Meeting`]
        :raises InvalidRequestError: If the API request fails
        """
        # TODO: Add type check for Meeting
        from videodb.meeting import Meeting

        meeting_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.meeting}"
        )
        if meeting_data:
            return Meeting(
                self._connection,
                id=meeting_data.get("meeting_id"),
                collection_id=self.collection_id,
                **meeting_data,
            )
        return None
