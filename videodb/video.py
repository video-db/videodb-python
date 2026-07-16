from typing import Literal, Optional, Union, List, Dict, Tuple, Any
from videodb._utils._video import play_stream, build_iframe_embed_code
from videodb._constants import (
    ApiPath,
    IndexType,
    ReframeMode,
    SceneExtractionType,
    SearchType,
    Segmenter,
    SegmentationType,
    SubtitleStyle,
    Workflows,
)
from videodb.image import Image, Frame
from videodb.index import Index
from videodb.understanding import Understanding, normalize_understanding_analyzers
from videodb.scene import Scene, SceneCollection
from videodb.search import AskResponse, SearchFactory, SearchResponse, SearchResult, warn_legacy_search_once
from videodb.shot import Shot

_VALID_SEGMENTERS = {Segmenter.word, Segmenter.sentence, Segmenter.time}


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

    def update(self, name: Optional[str] = None) -> None:
        """Update the video's metadata.

        :param str name: (optional) New name for the video
        """
        data = {}
        if name is not None:
            data["name"] = name
        if not data:
            return
        response_data = self._connection.patch(
            path=f"{ApiPath.video}/{self.id}",
            data=data,
        )
        if name is not None:
            self.name = response_data.get("name", name)

    def search(
        self,
        query: str,
        *args,
        config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[SearchResponse, SearchResult]:
        """Search this video.

        New search is used by default. Calls that use legacy-shaped parameters are
        routed to :meth:`legacy_search` with a warning.
        """
        old_params = {
            "search_type",
            "index_type",
            "result_threshold",
            "dynamic_score_percentage",
            "scene_index_id",
            "index_id",
            "algorithm",
            "sort_docs_on",
            "namespace",
        }
        new_params = {
            "top_k",
            "mode",
            "return_fields",
            "include_clip",
            "session_id",
            "config",
        }
        unsupported_params = {"index_name", "index_names", "index_id", "index_ids"}

        if config is not None:
            kwargs["config"] = config

        if args:
            legacy_arg_names = [
                "search_type",
                "index_type",
                "result_threshold",
                "score_threshold",
                "dynamic_score_percentage",
                "filter",
            ]
            for name, value in zip(legacy_arg_names, args):
                kwargs.setdefault(name, value)

        has_old = bool(args) or any(k in kwargs and kwargs[k] is not None for k in old_params)
        has_new = any(k in kwargs and kwargs[k] is not None for k in new_params)
        has_unsupported = any(k in kwargs and kwargs[k] is not None for k in unsupported_params)

        if kwargs.get("deepsearch_config") is not None:
            raise ValueError("deepsearch_config is internal and cannot be passed to search().")
        if has_old and (has_new or has_unsupported):
            raise ValueError(
                "Cannot mix legacy search params with new search params. "
                "Use search(...) for new search or legacy_search(...) for legacy search."
            )
        if has_unsupported:
            raise ValueError(
                "index_name/index_names/index_id/index_ids are not supported in search(). "
                "Use semantic_search(), query(), or aggregate() for index-specific calls."
            )

        if has_old:
            warn_legacy_search_once()
            return self.legacy_search(query=query, **kwargs)

        return self._new_search(query=query, **kwargs)

    def _new_search(self, query: str, **kwargs) -> SearchResponse:
        payload = {"query": query, **{k: v for k, v in kwargs.items() if v is not None}}
        search_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.search}/v2",
            data=payload,
            show_progress=True,
        )
        return SearchResponse(self._connection, **search_data)

    def ask(
        self,
        question: str,
        top_k: int = 15,
        mode: str = "default",
        include_sources: bool = False,
    ) -> AskResponse:
        ask_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.ask}",
            data={
                "question": question,
                "top_k": top_k,
                "mode": mode,
                "include_sources": include_sources,
            },
            show_progress=True,
        )
        return AskResponse(self._connection, **ask_data)

    def semantic_search(
        self,
        query: str,
        index_names: Optional[Union[List[str], str]] = None,
        top_k: int = 10,
        score_threshold: Optional[float] = None,
        filter: Optional[Union[List, Dict]] = None,
        return_fields: Optional[Union[List, Dict, str]] = None,
        index_ids: Optional[Union[List[str], str]] = None,
    ) -> SearchResult:
        search_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.semantic_search}",
            data={
                "query": query,
                "index_names": index_names,
                "index_ids": index_ids,
                "top_k": top_k,
                "score_threshold": score_threshold,
                "filter": filter,
                "return_fields": return_fields,
            },
        )
        return SearchResult(self._connection, **search_data)

    def query(
        self,
        index_name: Optional[str] = None,
        filter: Optional[Union[List, Dict]] = None,
        limit: int = 100,
        return_fields: Optional[Union[List, Dict, str]] = None,
        sort: Optional[Union[str, List[Tuple[str, str]]]] = None,
        index_id: Optional[str] = None,
    ) -> SearchResult:
        query_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.query}",
            data={
                "index_name": index_name,
                "index_id": index_id,
                "filter": filter,
                "limit": limit,
                "return_fields": return_fields,
                "sort": sort,
            },
        )
        return SearchResult(self._connection, **query_data)

    def aggregate(
        self,
        index_name: Optional[str] = None,
        filter: Optional[Union[List, Dict]] = None,
        group_by: Optional[str] = None,
        metric: str = "count",
        limit: int = 100,
        sort: Optional[Union[str, List[Tuple[str, str]]]] = None,
        index_id: Optional[str] = None,
    ) -> Union[Dict, List[Dict]]:
        return self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.aggregate}",
            data={
                "index_name": index_name,
                "index_id": index_id,
                "filter": filter,
                "group_by": group_by,
                "metric": metric,
                "limit": limit,
                "sort": sort,
            },
        )

    def legacy_search(
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
        if kwargs.get("scene_index_id") is None and kwargs.get("index_id") is not None:
            kwargs["scene_index_id"] = kwargs.get("index_id")
        kwargs.pop("index_id", None)
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
        self.stream_url = stream_data.get("stream_url")
        self.player_url = stream_data.get("player_url")
        return self.stream_url

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
        if segmenter not in _VALID_SEGMENTERS:
            raise ValueError(
                f"Invalid segmenter '{segmenter}'. "
                f"Must be one of: {', '.join(sorted(_VALID_SEGMENTERS))}"
            )
        if start is not None and start < 0:
            raise ValueError(f"start must be non-negative, got {start}")
        if end is not None and end < 0:
            raise ValueError(f"end must be non-negative, got {end}")
        if start is not None and end is not None and start > end:
            raise ValueError(
                f"start ({start}) must be less than or equal to end ({end})"
            )
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

        :param int start: Start time in seconds (must be >= 0 and <= end)
        :param int end: End time in seconds (must be >= 0 and >= start)
        :param Segmenter segmenter: How to split the transcript into segments.
            Must be one of :attr:`Segmenter.word` (default, one segment per word),
            :attr:`Segmenter.sentence` (one segment per sentence), or
            :attr:`Segmenter.time` (fixed-duration segments controlled by *length*)
        :param int length: Duration in seconds for each segment when
            *segmenter* is :attr:`Segmenter.time` (default 1)
        :param bool force: Force re-fetch transcript from the server,
            bypassing the local cache
        :raises ValueError: If *segmenter* is not a valid value, or if
            *start*/*end* are negative or *start* > *end*
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
    ) -> str:
        """Get plain text transcript for the video.

        :param int start: Start time in seconds to get transcript from
        :param int end: End time in seconds to get transcript until
        :param bool force: Force fetch new transcript
        :return: Full transcript text as string
        :rtype: str
        """
        self._fetch_transcript(start=start, end=end)
        return self.transcript_text

    def generate_transcript(
        self,
        force: bool = None,
        language_code: Optional[str] = None,
    ) -> str:
        """Generate transcript for the video.

        :param bool force: Force generate new transcript
        :param str language_code: (optional) Language code for transcription.
            Use ISO 639-1 codes (e.g., "en", "hi", "fr") or regional
            variants with underscores (e.g., "en_us", "en_uk", "en_au").
            Defaults to "en_us" if not specified.
        :return: Full transcript text as string
        :rtype: str
        """
        transcript_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.transcription}",
            data={
                "force": True if force else False,
                "language_code": language_code,
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
        segmentation_type: Optional[SegmentationType] = SegmentationType.sentence,
        force: bool = False,
        callback_url: str = None,
    ) -> None:
        """Semantic indexing of spoken words in the video.

        :param str language_code: (optional) Language code for transcription.
            Use ISO 639-1 codes (e.g., "en", "hi", "fr") or regional
            variants with underscores (e.g., "en_us", "en_uk", "en_au").
            Defaults to "en_us" if not specified.
        :param SegmentationType segmentation_type: (optional) Segmentation type used for indexing, :class:`SegmentationType <SegmentationType>` object
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
                "segmentation_type": segmentation_type,
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

    def index_visuals(
        self,
        prompt: Optional[str] = None,
        batch_config: Optional[Dict] = None,
        model_name: Optional[str] = None,
        model_config: Optional[Dict] = None,
        name: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Optional[str]:
        """Index visuals (scenes) from the video.

        :param str prompt: Prompt for scene description
        :param dict batch_config: Frame extraction config with keys:
            - "type": Extraction type ("time" or "shot"). Default is "time".
            - "value": Window size in seconds (for time) or threshold (for shot). Default is 10.
            - "frame_count": Number of frames to extract per window. Default is 1.
            - "select_frames": Which frames to select (e.g., ["first", "middle", "last"]). Default is ["first"].
        :param str model_name: Name of the model
        :param dict model_config: Configuration for the model
        :param str name: Name of the visual index
        :param str callback_url: URL to receive the callback (optional)
        :return: The scene index id
        :rtype: str
        """
        if batch_config is not None:
            extraction_type = batch_config.get("type")
            if extraction_type == "shot":
                extraction_type = SceneExtractionType.shot_based
                extraction_config = {
                    "threshold": batch_config.get("value"),
                    "frame_count": batch_config.get("frame_count"),
                }
            else:
                extraction_type = SceneExtractionType.time_based
                extraction_config = {
                    "time": batch_config.get("value"),
                    "frame_count": batch_config.get("frame_count"),
                    "select_frames": batch_config.get("select_frames"),
                }
        else:
            extraction_type = None
            extraction_config = None

        scenes_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            data={
                "extraction_type": extraction_type,
                "extraction_config": extraction_config,
                "prompt": prompt,
                "model_name": model_name,
                "model_config": model_config or {},
                "name": name,
                "callback_url": callback_url,
            },
        )
        if not scenes_data:
            return None
        return scenes_data.get("scene_index_id")

    def index_audio(
        self,
        prompt: Optional[str] = None,
        model_name: Optional[str] = None,
        model_config: Optional[Dict] = None,
        language_code: Optional[str] = None,
        batch_config: Optional[Dict] = None,
        name: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> Optional[str]:
        """Index audio by processing transcript segments through an LLM.

        Segments the video transcript, processes each segment with the given
        prompt using the specified model, and indexes the results as scene
        records for semantic search.

        :param str prompt: (optional) Prompt for processing transcript segments
        :param str model_name: (optional) LLM tier to use (e.g. "basic", "pro", "ultra")
        :param dict model_config: (optional) Model configuration
        :param str language_code: (optional) Language code for transcription.
            Use ISO 639-1 codes (e.g., "en", "hi", "fr") or regional
            variants with underscores (e.g., "en_us", "en_uk", "en_au").
            Defaults to "en_us" if not specified.
        :param dict batch_config: (optional) Segmentation config with keys:
            - "type": Segmentation type ("word", "sentence", or "time")
            - "value": Segment length (words, sentences, or seconds)
            Defaults to {"type": "word", "value": 10}
        :param str name: (optional) Name for the scene index
        :param str callback_url: (optional) URL to receive the callback
        :return: The scene index id
        :rtype: str
        """
        if batch_config is not None:
            extraction_config = {
                "segmenter": batch_config.get("type"),
                "segmentation_value": batch_config.get("value"),
            }
        else:
            extraction_config = None

        scenes_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.index}/{ApiPath.scene}",
            data={
                "extraction_type": SceneExtractionType.transcript,
                "extraction_config": extraction_config,
                "prompt": prompt,
                "model_name": model_name,
                "model_config": model_config,
                "language_code": language_code,
                "name": name,
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

    def understand(
        self,
        analyzers: List[Dict[str, Any]],
        segmentation: Optional[Dict[str, Any]] = None,
        sampling: Optional[Dict[str, Any]] = None,
        transform: Optional[Dict[str, Any]] = None,
        audio_chunking: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None,
        **kwargs,
    ) -> Understanding:
        """Create an understanding run for this video.

        :param list analyzers: Analyzer definitions. The SDK accepts friendly
            analyzer type ``spoken_words`` and maps it to the server analyzer.
        :param dict segmentation: Optional run-level segmentation config
        :param dict sampling: Optional run-level sampling config
        :param dict transform: Optional run-level transform config
        :param dict audio_chunking: Optional run-level audio chunking config
        :param str callback_url: Optional URL called when the run completes
        :return: :class:`Understanding <videodb.understanding.Understanding>` object
        """
        normalized_analyzers = normalize_understanding_analyzers(analyzers)
        payload = {"analyzers": normalized_analyzers}
        optional_fields = {
            "segmentation": segmentation,
            "sampling": sampling,
            "transform": transform,
            "audio_chunking": audio_chunking,
            "callback_url": callback_url,
            **kwargs,
        }
        payload.update({key: value for key, value in optional_fields.items() if value is not None})

        data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.understand}",
            data=payload,
        ) or {}
        data.setdefault(
            "analyzers",
            [
                {
                    "name": analyzer.get("name"),
                    "type": analyzer.get("type"),
                    "status": "pending",
                }
                for analyzer in normalized_analyzers
            ],
        )
        data.setdefault("video_id", self.id)
        data.setdefault("collection_id", self.collection_id)
        return Understanding(self._connection, **data)

    def get_understanding(self, understanding_id: str) -> Understanding:
        """Get an understanding run by id.

        :param str understanding_id: Understanding run id
        :return: :class:`Understanding <videodb.understanding.Understanding>` object
        """
        if not understanding_id:
            raise ValueError("understanding_id is required")
        data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.understand}/{understanding_id}"
        ) or {}
        data.setdefault("video_id", self.id)
        data.setdefault("collection_id", self.collection_id)
        data.setdefault("understanding_id", understanding_id)
        return Understanding(self._connection, **data)

    def list_understandings(self) -> List[Understanding]:
        """List understanding runs for this video."""
        data = self._connection.get(path=f"{ApiPath.video}/{self.id}/{ApiPath.understand}")
        results = (data or {}).get("understanding_results") or []
        understandings = []
        for item in results:
            data = dict(item)
            data.setdefault("video_id", self.id)
            data.setdefault("collection_id", self.collection_id)
            understandings.append(Understanding(self._connection, **data))
        return understandings

    def delete_understanding(self, understanding_id: str) -> None:
        """Delete an understanding run."""
        if not understanding_id:
            raise ValueError("understanding_id is required")
        self._connection.delete(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.understand}/{understanding_id}"
        )

    @staticmethod
    def _format_index_source(source: Union[object, Dict]) -> Dict:
        """Format an index *source* into the request payload.

        Exactly two source kinds are supported:

          - an :class:`UnderstandingAnalyzer <videodb.understanding.UnderstandingAnalyzer>`
            (anything exposing ``to_index_source()``) — serialized as a light reference
            ``{understanding_id, analyzer_id, ...}``; the server re-fetches the analyzer
            output from its own store, so scenes never round-trip through the client
          - a dict carrying either ``scenes`` (user-provided temporal records) or an
            ``understanding_id`` reference (optionally with ``analyzer_id`` /
            ``analyzer_type``), passed through as-is
          - a bare list of temporal record dicts — sugar for ``{"scenes": [...]}``

        :param source: The analyzer object, source dict, or list of temporal records
        :raises ValueError: If the source is missing or of an unsupported type
        :return: The serialized ``source`` payload
        :rtype: dict
        """
        if source is None:
            raise ValueError("source is required")

        # Analyzer (or any object that knows how to reference itself).
        if hasattr(source, "to_index_source"):
            return source.to_index_source()

        # A bare list can only mean temporal records — canonicalize to the dict form.
        if isinstance(source, list):
            return {"scenes": source}

        if isinstance(source, dict):
            if isinstance(source.get("scenes"), list) or source.get("understanding_id"):
                return source
            raise ValueError(
                "source dict must carry 'scenes' (temporal records) or an "
                "'understanding_id' reference"
            )

        raise ValueError(
            "source must be an analyzer object, a dict with 'scenes' or "
            "'understanding_id', or a list of temporal records — got "
            + type(source).__name__
        )

    def _format_index(self, index_data: dict) -> Index:
        index_data = dict(index_data)
        video_id = index_data.pop("video_id", None) or self.id
        collection_id = index_data.pop("collection_id", None) or self.collection_id
        return Index(
            self._connection,
            video_id=video_id,
            collection_id=collection_id,
            **index_data,
        )

    def index(
        self,
        source: Union[object, Dict, List],
        name: Optional[str] = None,
        use_for: Optional[List[str]] = None,
        fields: Optional[Dict[str, List[str]]] = None,
        callback_url: Optional[str] = None,
    ) -> Optional[Index]:
        """Create a retrieval-ready index from an understanding artifact.

        Turns an understanding artifact (or user-provided temporal records) into an
        index that declares retrieval capabilities (``use_for``) and field-level
        indexing configuration (``fields``).

        :param source: An :class:`UnderstandingAnalyzer` object (indexed by reference —
            scenes never leave the server), or a dict carrying ``scenes`` (temporal
            records) or an ``understanding_id`` reference
        :param str name: (optional) User-facing index name. Defaults to the
            artifact/source name on the server.
        :param list use_for: (optional) Retrieval capabilities to enable, any of
            :attr:`IndexCapability.semantic <videodb.IndexCapability.semantic>`,
            :attr:`IndexCapability.query <videodb.IndexCapability.query>`,
            :attr:`IndexCapability.aggregate <videodb.IndexCapability.aggregate>`.
            Defaults to the artifact's defaults on the server.
        :param dict fields: (optional) Field-level indexing configuration mapping
            field groups (``semantic``, ``text``, ``filter``, ``aggregate``,
            ``sort``) to lists of field names
        :param str callback_url: (optional) URL called when indexing completes
        :raises ValueError: If ``source`` is missing or of an unsupported type
        :raises InvalidRequestError: If the index creation fails
        :return: The created index, :class:`Index <Index>` object
        :rtype: :class:`videodb.index.Index`
        """
        index_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.indexes}",
            data={
                "source": self._format_index_source(source),
                "name": name,
                "use_for": use_for,
                "fields": fields,
                "callback_url": callback_url,
            },
        )
        if not index_data:
            return None
        return self._format_index(index_data)

    def get_index(
        self, index_id: Optional[str] = None, name: Optional[str] = None
    ) -> Optional[Index]:
        """Get an index manifest by its ID or name.

        :param str index_id: (optional) The id of the index
        :param str name: (optional) The name of the index
        :raises ValueError: If neither ``index_id`` nor ``name`` is provided
        :return: The index, :class:`Index <Index>` object
        :rtype: :class:`videodb.index.Index`
        """
        if not index_id and not name:
            raise ValueError("Either index_id or name is required")
        params = {"collection_id": self.collection_id}
        if index_id:
            path = f"{ApiPath.video}/{self.id}/{ApiPath.indexes}/{index_id}"
        else:
            path = f"{ApiPath.video}/{self.id}/{ApiPath.indexes}"
            params["name"] = name
        index_data = self._connection.get(path=path, params=params)
        if not index_data:
            return None
        return self._format_index(index_data)

    def list_indexes(self, use_for: Optional[str] = None) -> List[Index]:
        """List all the indexes of the video.

        :param str use_for: (optional) Filter by retrieval capability, any of
            :attr:`IndexCapability.semantic <videodb.IndexCapability.semantic>`,
            :attr:`IndexCapability.query <videodb.IndexCapability.query>`,
            :attr:`IndexCapability.aggregate <videodb.IndexCapability.aggregate>`
        :return: List of :class:`Index <Index>` objects
        :rtype: list[:class:`videodb.index.Index`]
        """
        params = {"collection_id": self.collection_id}
        if use_for is not None:
            params["use_for"] = use_for
        index_data = self._connection.get(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.indexes}",
            params=params,
        )
        return [self._format_index(index) for index in index_data.get("indexes", [])]

    def delete_index(self, index_id: str) -> None:
        """Delete an index.

        Removes the index's retrieval structures. It does not delete the original
        video or stored understanding artifacts.

        :param str index_id: The id of the index to be deleted
        :raises ValueError: If ``index_id`` is not provided
        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        if not index_id:
            raise ValueError("index_id is required")
        self._connection.delete(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.indexes}/{index_id}",
            params={"collection_id": self.collection_id},
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

    def clip(
            self,
            prompt: str,
            content_type: Literal["spoken", "visual", "multimodal"],
            model_name: Literal["basic", "pro", "ultra"],
        ) -> SearchResult:
            """Generate a clip from the video using a prompt.
            :param str prompt: Prompt to generate the clip
            :param str content_type: Content type for the clip. Valid options: "spoken", "visual", "multimodal"
            :param str model_name: Model tier for generation. Valid options: "basic", "pro", "ultra"
            :return: The search result of the generated clip
            :rtype: :class:`SearchResult <SearchResult>`
            """

            clip_data = self._connection.post(
                path=f"{ApiPath.video}/{self.id}/{ApiPath.clip}",
                data={
                    "prompt": prompt,
                    "content_type": content_type,
                    "model_name": model_name,
                },
            )
            return SearchResult(self._connection, **clip_data)

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

    def get_embed_code(
        self,
        width: str = "100%",
        height: int = 405,
        title: str = "VideoDB Player",
        allow_fullscreen: bool = True,
        auto_generate: bool = True,
    ) -> str:
        """Generate an HTML iframe embed code for the video.

        :param str width: Width of the iframe (default: "100%")
        :param int height: Height of the iframe in pixels (default: 405)
        :param str title: Title attribute for the iframe (default: "VideoDB Player")
        :param bool allow_fullscreen: Whether to allow fullscreen (default: True)
        :param bool auto_generate: If True and player_url is missing, auto-generate it (default: True)
        :return: HTML iframe string
        :rtype: str
        :raises ValueError: If player_url is not available
        """
        if not self.player_url and auto_generate:
            self.generate_stream()

        if not self.player_url:
            raise ValueError(
                "player_url not available. Call generate_stream() first or set auto_generate=True."
            )

        return build_iframe_embed_code(
            player_url=self.player_url,
            width=width,
            height=height,
            title=title,
            allow_fullscreen=allow_fullscreen,
        )

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

    def reframe(
        self,
        start: Optional[float] = None,
        end: Optional[float] = None,
        target: Union[str, Dict[str, int]] = "vertical",
        mode: str = ReframeMode.smart,
        callback_url: Optional[str] = None,
    ) -> Optional["Video"]:
        """Reframe video to a new aspect ratio with optional object tracking.

        :param float start: Start time in seconds (optional)
        :param float end: End time in seconds (optional)
        :param Union[str, dict] target: Target format - preset string (e.g., "vertical", "square", "landscape") or {"width": int, "height": int}
        :param str mode: Reframing mode - "simple" or "smart" (default: "smart")
        :param str callback_url: URL to receive callback when processing completes (optional)
        :raises InvalidRequestError: If the reframe request fails
        :return: :class:`Video <Video>` object if no callback_url, None otherwise
        :rtype: Optional[:class:`videodb.video.Video`]
        """
        reframe_data = self._connection.post(
            path=f"{ApiPath.video}/{self.id}/{ApiPath.reframe}",
            data={
                "start": start,
                "end": end,
                "target": target,
                "mode": mode,
                "callback_url": callback_url,
            },
        )

        if callback_url:
            return None

        if reframe_data:
            return Video(self._connection, **reframe_data)

    def smart_vertical_reframe(
        self,
        start: Optional[float] = None,
        end: Optional[float] = None,
        callback_url: Optional[str] = None,
    ) -> Optional["Video"]:
        """Convenience method for object-aware vertical reframing.

        Equivalent to calling reframe(target="vertical", mode="smart").

        :param float start: Start time in seconds (optional)
        :param float end: End time in seconds (optional)
        :param str callback_url: URL to receive callback when processing completes (optional)
        :return: :class:`Video <Video>` object if no callback_url, None otherwise
        :rtype: Optional[:class:`videodb.video.Video`]
        """
        return self.reframe(
            start=start,
            end=end,
            target="vertical",
            mode=ReframeMode.smart,
            callback_url=callback_url,
        )

    def download(self, name: Optional[str] = None) -> dict:
        """Download the video from its stream URL.

        :param str name: Name for the downloaded file (optional, defaults to video name)
        :raises InvalidRequestError: If the download request fails
        :return: Download response data
        :rtype: dict
        """
        if not self.stream_url:
            raise ValueError("Video does not have a stream_url")

        download_name = name or self.name or f"video_{self.id}"
        return self._connection.download(self.stream_url, download_name)
