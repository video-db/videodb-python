import logging

from typing import Optional, Union, List, Dict, Any, Literal
from videodb._upload import (
    upload,
)
from videodb._constants import (
    ApiPath,
    IndexType,
    MediaType,
    SearchType,
    _InternalSearchType,
)
from videodb.video import Video
from videodb.audio import Audio
from videodb.image import Image
from videodb.job import GenerationJob
from videodb.voice_clone import VoiceClone
from videodb.meeting import Meeting
from videodb.capture_session import CaptureSession
from videodb.rtstream import RTStream, RTStreamSearchResult, RTStreamShot
from videodb.search import SearchFactory, SearchResult

logger = logging.getLogger(__name__)


class Collection:
    """Collection class to interact with the Collection.

    Note: Users should not initialize this class directly.
    Instead use :meth:`Connection.get_collection() <videodb.client.Connection.get_collection>`
    """

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

    def create_voice_clone(
        self,
        ref_audio_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        ref_text: Optional[str] = None,
        language: Optional[str] = None,
    ) -> VoiceClone:
        """Create a reusable voice clone from an audio in this collection.

        :param str ref_audio_id: Source audio ID to use as the voice reference.
        :param str name: Human-readable name (optional).
        :param str description: Description (optional).
        :param str ref_text: Text spoken in the reference audio (optional).
        :param str language: Language code, e.g. ``"en"`` (optional).
        :return: :class:`VoiceClone <VoiceClone>` object.
        :rtype: :class:`videodb.voice_clone.VoiceClone`
        """
        return self._connection.create_voice_clone(
            ref_audio_id=ref_audio_id,
            name=name,
            description=description,
            ref_text=ref_text,
            language=language,
            collection_id=self.id,
        )

    def get_voice_clone(self, voice_clone_id: str) -> VoiceClone:
        """Get a voice clone by ID."""
        return self._connection.get_voice_clone(voice_clone_id)

    def list_voice_clones(
        self,
        page: int = 1,
        page_size: int = 20,
        language: Optional[str] = None,
    ) -> List[VoiceClone]:
        """List user voice clones, optionally filtered by language."""
        return self._connection.list_voice_clones(
            page=page,
            page_size=page_size,
            language=language,
        )

    def delete_voice_clone(self, voice_clone_id: str) -> None:
        """Delete a voice clone by ID."""
        return self._connection.delete_voice_clone(voice_clone_id)

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

    def connect_rtstream(
        self,
        url: str,
        name: str,
        media_types: List[str] = None,
        sample_rate: int = None,
        store: bool = None,
        enable_transcript: bool = None,
        ws_connection_id: str = None,
    ) -> RTStream:
        """Connect to an rtstream.

        :param str url: URL of the rtstream
        :param str name: Name of the rtstream
        :param list media_types: List of media types to capture (default: [MediaType.video]).
            Valid values: :attr:`MediaType.audio`, :attr:`MediaType.video`
        :param int sample_rate: Sample rate of the rtstream (optional, server default: 30)
        :param bool store: Enable recording storage (optional, default: False).
            When True, the stream recording is stored and can be exported via :meth:`RTStream.export`.
        :param bool enable_transcript: Enable real-time transcription (optional)
        :param str ws_connection_id: WebSocket connection ID for receiving events (optional)
        :return: :class:`RTStream <RTStream>` object
        """
        if media_types is None:
            media_types = [MediaType.video]

        valid = {MediaType.audio, MediaType.video}
        invalid = set(media_types) - valid
        if invalid or not media_types:
            raise ValueError(
                f"Invalid media_types: {invalid}. Valid values: {MediaType.audio}, {MediaType.video}"
            )

        data = {
            "collection_id": self.id,
            "url": url,
            "name": name,
            "media_types": media_types,
        }
        if sample_rate is not None:
            data["sample_rate"] = sample_rate
        if store is not None:
            data["store"] = store
        if enable_transcript is not None:
            data["enable_transcript"] = enable_transcript
        if ws_connection_id is not None:
            data["ws_connection_id"] = ws_connection_id

        rtstream_data = self._connection.post(
            path=f"{ApiPath.rtstream}",
            data=data,
        )
        return RTStream(self._connection, **rtstream_data)

    def get_rtstream(self, id: str) -> RTStream:
        """Get an rtstream by its ID.

        :param str id: ID of the rtstream
        :return: :class:`RTStream <RTStream>` object
        :rtype: :class:`videodb.rtstream.RTStream`
        """
        rtstream_data = self._connection.get(
            path=f"{ApiPath.rtstream}/{id}",
        )
        return RTStream(self._connection, **rtstream_data)

    def list_rtstreams(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        status: Optional[str] = None,
        name: Optional[str] = None,
        ordering: Optional[str] = None,
    ) -> List[RTStream]:
        """List all rtstreams in the collection.

        :param int limit: Number of rtstreams to return (optional)
        :param int offset: Number of rtstreams to skip (optional)
        :param str status: Filter by status (optional)
        :param str name: Filter by name (optional)
        :param str ordering: Order results by field (optional)
        :return: List of :class:`RTStream <RTStream>` objects
        :rtype: List[:class:`videodb.rtstream.RTStream`]
        """
        params = {
            "limit": limit,
            "offset": offset,
            "status": status,
            "name": name,
            "ordering": ordering,
        }
        rtstreams_data = self._connection.get(
            path=f"{ApiPath.rtstream}",
            params={key: value for key, value in params.items() if value is not None},
        )
        return [
            RTStream(self._connection, **rtstream)
            for rtstream in rtstreams_data.get("results")
        ]

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: Optional[Literal["1:1", "9:16", "16:9", "4:3", "3:4"]] = "1:1",
        callback_url: Optional[str] = None,
        model_name: Optional[str] = None,
        config: Optional[dict] = None,
        sandbox_id: Optional[str] = None,
        wait: bool = False,
        poll_interval: int = 5,
        timeout: int = 600,
    ) -> Union[Image, GenerationJob]:
        """Generate an image from a prompt.

        :param str prompt: Prompt for the image generation
        :param str aspect_ratio: Aspect ratio of the image (optional, hosted models)
        :param str callback_url: URL to receive the callback (optional)
        :param str model_name: Model name. Use ``"black-forest-labs/FLUX.1-dev"`` for FLUX self-inference.
        :param dict config: Model configuration. Used by FLUX.
        :param str sandbox_id: ID of the sandbox to route the self-inference job to (optional).
        :param bool wait: If True, wait for self-inference jobs and return Image.
        :param int poll_interval: Seconds between job polls when wait=True.
        :param int timeout: Maximum seconds to wait when wait=True.
        :return: :class:`Image <Image>` or :class:`GenerationJob <GenerationJob>`
        :rtype: Union[:class:`videodb.image.Image`, :class:`videodb.job.GenerationJob`]
        """
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "callback_url": callback_url,
        }
        if model_name:
            payload["model_name"] = model_name
        if config is not None:
            payload["config"] = config
        if sandbox_id:
            payload["sandbox_id"] = sandbox_id

        image_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.generate}/{ApiPath.image}",
            data=payload,
        )
        if not image_data:
            return None
        if image_data.get("job_id"):
            job = GenerationJob.from_data(
                self._connection, image_data, result_type="image"
            )
            return job.wait(timeout=timeout, interval=poll_interval) if wait else job
        return Image(self._connection, **image_data)

    def generate_music(
        self, prompt: str, duration: int = 5, callback_url: Optional[str] = None
    ) -> Audio:
        """Generate music from a prompt.

        :param str prompt: Prompt for the music generation
        :param int duration: Duration of the music in seconds
        :param str callback_url: URL to receive the callback (optional)
        :return: :class:`Audio <Audio>` object
        :rtype: :class:`videodb.audio.Audio`
        """
        audio_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.generate}/{ApiPath.audio}",
            data={
                "prompt": prompt,
                "duration": duration,
                "audio_type": "music",
                "callback_url": callback_url,
            },
        )
        if audio_data:
            return Audio(self._connection, **audio_data)

    def generate_sound_effect(
        self,
        prompt: str,
        duration: int = 2,
        config: dict = {},
        callback_url: Optional[str] = None,
    ) -> Audio:
        """Generate sound effect from a prompt.

        :param str prompt: Prompt for the sound effect generation
        :param int duration: Duration of the sound effect in seconds
        :param dict config: Configuration for the sound effect generation
        :param str callback_url: URL to receive the callback (optional)
        :return: :class:`Audio <Audio>` object
        :rtype: :class:`videodb.audio.Audio`
        """
        audio_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.generate}/{ApiPath.audio}",
            data={
                "prompt": prompt,
                "duration": duration,
                "audio_type": "sound_effect",
                "config": config,
                "callback_url": callback_url,
            },
        )
        if audio_data:
            return Audio(self._connection, **audio_data)

    def generate_voice(
        self,
        text: str,
        voice_name: str = "Default",
        config: dict = {},
        callback_url: Optional[str] = None,
        model_name: str = "elevenlabs",
        sandbox_id: Optional[str] = None,
        voice_clone_id: Optional[str] = None,
        clone_voice_id: Optional[str] = None,
        wait: bool = False,
        poll_interval: int = 5,
        timeout: int = 600,
    ) -> Union[Audio, GenerationJob]:
        """Generate voice from text.

        :param str text: Text to convert to voice
        :param str voice_name: Name of the voice to use
        :param dict config: Configuration for the voice generation
        :param str callback_url: URL to receive the callback (optional)
        :param str model_name: Model name. Use ``"k2-fsa/OmniVoice"`` for OmniVoice.
        :param str sandbox_id: ID of the sandbox to route the self-inference job to (optional).
        :param str voice_clone_id: ID of a reusable voice clone to use for OmniVoice (optional).
        :param str clone_voice_id: Alias for ``voice_clone_id`` (optional).
        :param bool wait: If True, wait for self-inference jobs and return Audio.
        :param int poll_interval: Seconds between job polls when wait=True.
        :param int timeout: Maximum seconds to wait when wait=True.
        :return: :class:`Audio <Audio>` or :class:`GenerationJob <GenerationJob>`
        :rtype: Union[:class:`videodb.audio.Audio`, :class:`videodb.job.GenerationJob`]
        """
        if voice_clone_id and clone_voice_id and voice_clone_id != clone_voice_id:
            raise ValueError("voice_clone_id and clone_voice_id cannot both be different")
        resolved_voice_clone_id = voice_clone_id or clone_voice_id

        audio_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.generate}/{ApiPath.audio}",
            data={
                "text": text,
                "audio_type": "voice",
                "voice_name": voice_name,
                "model_name": model_name,
                "config": config,
                "callback_url": callback_url,
                "sandbox_id": sandbox_id,
                "voice_clone_id": resolved_voice_clone_id,
            },
        )
        if not audio_data:
            return None
        if audio_data.get("job_id"):
            job = GenerationJob.from_data(
                self._connection, audio_data, result_type="audio"
            )
            return job.wait(timeout=timeout, interval=poll_interval) if wait else job
        return Audio(self._connection, **audio_data)

    def generate_video(
        self,
        prompt: str,
        duration: float = 5,
        callback_url: Optional[str] = None,
    ) -> Video:
        """
        Generate a video from the given text prompt.

        This method sends a request to generate a video using the provided prompt,
        duration. If a callback URL is provided, the generation result will be sent to that endpoint asynchronously.

        :param str prompt: Text prompt used as input for video generation.

        :param float duration:
            Duration of the generated video in seconds.
            Must be an **integer value** (not a float) and must be **between 5 and 8 inclusive**.
            A `ValueError` will be raised if the validation fails.

        :param str callback_url:
            Optional URL to receive a callback once video generation is complete.

        :return:
            A `Video` object containing the generated video metadata and access details.

        :rtype:
            :class:`videodb.video.Video`
        """
        video_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.generate}/{ApiPath.video}",
            data={
                "prompt": prompt,
                "duration": duration,
                "callback_url": callback_url,
            },
        )
        if video_data:
            return Video(self._connection, **video_data)

    def generate_text(
        self,
        prompt: str,
        model_name: Literal["basic", "pro", "ultra"] = "basic",
        response_type: Literal["text", "json"] = "text",
    ) -> Union[str, dict]:
        """Generate text from a prompt using genai offering.

        :param str prompt: Prompt for the text generation
        :param str model_name: Model name to use ("basic", "pro" or "ultra")
        :param str response_type: Desired response type ("text" or "json")
        :return: Generated text response
        :rtype: Union[str, dict]
        """

        return self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.generate}/{ApiPath.text}",
            data={
                "prompt": prompt,
                "model_name": model_name,
                "response_type": response_type,
            },
        )

    def dub_video(
        self, video_id: str, language_code: str, callback_url: Optional[str] = None
    ) -> Video:
        """Dub a video.

        :param str video_id: ID of the video to dub
        :param str language_code: Language code to dub the video to.
            Use ISO 639-1 codes (e.g., "en", "hi", "fr") or regional
            variants with underscores (e.g., "en_us", "en_uk", "en_au").
        :param str callback_url: URL to receive the callback (optional)
        :return: :class:`Video <Video>` object
        :rtype: :class:`videodb.video.Video`
        """
        dub_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.generate}/{ApiPath.video}/{ApiPath.dub}",
            data={
                "video_id": video_id,
                "language_code": language_code,
                "callback_url": callback_url,
            },
        )
        if dub_data:
            return Video(self._connection, **dub_data)

    def search(
        self,
        query: str,
        search_type: Optional[str] = SearchType.semantic,
        index_type: Optional[str] = IndexType.spoken_word,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[float] = None,
        dynamic_score_percentage: Optional[float] = None,
        filter: List[Dict[str, Any]] = [],
        sort_docs_on: Optional[str] = None,
        namespace: Optional[str] = None,
        scene_index_id: Optional[str] = None,
    ) -> Union[SearchResult, RTStreamSearchResult]:
        """Search for a query in the collection.

        :param str query: Query to search for
        :param SearchType search_type: Type of search to perform (optional)
        :param IndexType index_type: Type of index to search (optional)
        :param int result_threshold: Number of results to return (optional)
        :param float score_threshold: Threshold score for the search (optional)
        :param float dynamic_score_percentage: Percentage of dynamic score to consider (optional)
        :param list filter: Additional metadata filters (optional)
        :param str sort_docs_on: Sort docs within each video by "score" or "start" (optional)
        :param str namespace: Search namespace (optional, "rtstream" to search RTStreams)
        :param str scene_index_id: Filter by specific scene index (optional)
        :raise SearchError: If the search fails
        :return: :class:`SearchResult <SearchResult>` or
            :class:`RTStreamSearchResult <videodb.rtstream.RTStreamSearchResult>` object
        :rtype: Union[:class:`videodb.search.SearchResult`,
            :class:`videodb.rtstream.RTStreamSearchResult`]
        """
        if namespace == "rtstream":
            data = {"query": query}
            if scene_index_id is not None:
                data["scene_index_id"] = scene_index_id
            if result_threshold is not None:
                data["result_threshold"] = result_threshold
            if score_threshold is not None:
                data["score_threshold"] = score_threshold
            if dynamic_score_percentage is not None:
                data["dynamic_score_percentage"] = dynamic_score_percentage
            if filter is not None:
                data["filter"] = filter

            search_data = self._connection.post(
                path=f"{ApiPath.rtstream}/{ApiPath.collection}/{self.id}/{ApiPath.search}",
                data=data,
            )
            results = search_data.get("results", [])
            shots = [
                RTStreamShot(
                    _connection=self._connection,
                    rtstream_id=result.get("rtstream_id") or result.get("id"),
                    rtstream_name=result.get("rtstream_name"),
                    start=result.get("start"),
                    end=result.get("end"),
                    text=result.get("text"),
                    search_score=result.get("score"),
                    scene_index_id=result.get("scene_index_id"),
                    scene_index_name=result.get("scene_index_name"),
                    metadata=result.get("metadata"),
                )
                for result in results
            ]
            return RTStreamSearchResult(collection_id=self.id, shots=shots)

        search = SearchFactory(self._connection).get_search(search_type)
        return search.search_inside_collection(
            collection_id=self.id,
            query=query,
            search_type=search_type,
            index_type=index_type,
            result_threshold=result_threshold,
            score_threshold=score_threshold,
            dynamic_score_percentage=dynamic_score_percentage,
            sort_docs_on=sort_docs_on,
            filter=filter,
        )

    def search_title(self, query) -> List[Video]:
        search_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.search}/{ApiPath.title}",
            data={
                "query": query,
                "search_type": _InternalSearchType.llm,
            },
        )
        return [
            {"video": Video(self._connection, **result.get("video"))}
            for result in search_data
        ]

    def upload(
        self,
        source: Optional[str] = None,
        media_type: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        callback_url: Optional[str] = None,
        file_path: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Union[Video, Audio, Image, None]:
        """Upload a file to the collection.

        :param str source: Local path or URL of the file to be uploaded
        :param MediaType media_type: MediaType object (optional)
        :param str name: Name of the file (optional)
        :param str description: Description of the file (optional)
        :param str callback_url: URL to receive the callback (optional)
        :param str file_path: Path to the file to be uploaded
        :param str url: URL of the file to be uploaded
        :return: :class:`Video <Video>`, or :class:`Audio <Audio>`, or :class:`Image <Image>` object
        :rtype: Union[ :class:`videodb.video.Video`, :class:`videodb.audio.Audio`, :class:`videodb.image.Image`]
        """
        upload_data = upload(
            self._connection,
            source,
            media_type=media_type,
            name=name,
            description=description,
            callback_url=callback_url,
            file_path=file_path,
            url=url,
            collection_id=self.id,
        )
        media_id = upload_data.get("id", "")
        if media_id.startswith("m-"):
            return Video(self._connection, **upload_data)
        elif media_id.startswith("a-"):
            return Audio(self._connection, **upload_data)
        elif media_id.startswith("img-"):
            return Image(self._connection, **upload_data)

    def make_public(self):
        """Make the collection public.

        :return: None
        :rtype: None
        """
        self._connection.patch(
            path=f"{ApiPath.collection}/{self.id}", data={"is_public": True}
        )
        self.is_public = True

    def make_private(self):
        """Make the collection private.

        :return: None
        :rtype: None
        """
        self._connection.patch(
            path=f"{ApiPath.collection}/{self.id}", data={"is_public": False}
        )
        self.is_public = False

    def record_meeting(
        self,
        meeting_url: str,
        bot_name: str = None,
        bot_image_url: str = None,
        meeting_title: str = None,
        callback_url: str = None,
        callback_data: Optional[dict] = None,
        time_zone: str = "UTC",
    ) -> Meeting:
        """Record a meeting and upload it to this collection.

        :param str meeting_url: Meeting url
        :param str bot_name: Name of the recorder bot
        :param str bot_image_url: URL of the recorder bot image
        :param str meeting_title: Name of the meeting
        :param str callback_url: URL to receive callback once recording is done
        :param dict callback_data: Data to be sent in the callback (optional)
        :param str time_zone: Time zone for the meeting (default ``UTC``)
        :return: :class:`Meeting <Meeting>` object representing the recording bot
        :rtype: :class:`videodb.meeting.Meeting`
        """
        if callback_data is None:
            callback_data = {}

        response = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.meeting}/{ApiPath.record}",
            data={
                "meeting_url": meeting_url,
                "bot_name": bot_name,
                "bot_image_url": bot_image_url,
                "meeting_title": meeting_title,
                "callback_url": callback_url,
                "callback_data": callback_data,
                "time_zone": time_zone,
            },
        )
        meeting_id = response.get("meeting_id")
        return Meeting(
            self._connection, id=meeting_id, collection_id=self.id, **response
        )

    def get_meeting(self, meeting_id: str) -> Meeting:
        """Get a meeting by its ID.

        :param str meeting_id: ID of the meeting
        :return: :class:`Meeting <Meeting>` object
        :rtype: :class:`videodb.meeting.Meeting`
        """
        meeting = Meeting(self._connection, id=meeting_id, collection_id=self.id)
        meeting.refresh()
        return meeting

    def create_capture_session(
        self,
        end_user_id: str,
        callback_url: str = None,
        ws_connection_id: str = None,
        metadata: dict = None,
    ) -> "CaptureSession":
        """Create a capture session.

        :param str end_user_id: ID of the end user
        :param str callback_url: URL to receive callback (optional)
        :param str ws_connection_id: WebSocket connection ID (optional)
        :param dict metadata: Custom metadata (optional)
        :return: :class:`CaptureSession <CaptureSession>` object
        :rtype: :class:`videodb.capture_session.CaptureSession`
        """
        data = {
            "end_user_id": end_user_id,
        }
        if callback_url:
            data["callback_url"] = callback_url
        if ws_connection_id:
            data["ws_connection_id"] = ws_connection_id
        if metadata:
            data["metadata"] = metadata

        response = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.capture}/{ApiPath.session}",
            data=data,
        )
        # Normalize rtstreams before passing to CaptureSession
        for rts in response.get("rtstreams", []):
            if isinstance(rts, dict):
                if "rtstream_id" in rts and "id" not in rts:
                    rts["id"] = rts.pop("rtstream_id")
                if "collection_id" not in rts:
                    rts["collection_id"] = self.id
        # Extract id and collection_id from response to avoid duplicate arguments
        session_id = response.pop("session_id", None) or response.pop("id", None)
        response.pop("collection_id", None)
        return CaptureSession(
            self._connection, id=session_id, collection_id=self.id, **response
        )

    def get_capture_session(self, session_id: str) -> "CaptureSession":
        """Get a capture session by its ID.

        :param str session_id: ID of the capture session
        :return: :class:`CaptureSession <CaptureSession>` object
        :rtype: :class:`videodb.capture_session.CaptureSession`
        """
        response = self._connection.get(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.capture}/{ApiPath.session}/{session_id}"
        )
        # Normalize rtstreams before passing to CaptureSession
        for rts in response.get("rtstreams", []):
            if isinstance(rts, dict):
                if "rtstream_id" in rts and "id" not in rts:
                    rts["id"] = rts.pop("rtstream_id")
                if "collection_id" not in rts:
                    rts["collection_id"] = self.id
        # Extract id and collection_id from response to avoid duplicate arguments
        response.pop("id", None)
        response.pop("collection_id", None)
        return CaptureSession(
            self._connection, id=session_id, collection_id=self.id, **response
        )

    def list_capture_sessions(self, status: str = None) -> list["CaptureSession"]:
        """List capture sessions.

        :param str status: Filter sessions by status (optional)
        :return: List of :class:`CaptureSession <CaptureSession>` objects
        :rtype: list[:class:`videodb.capture_session.CaptureSession`]
        """
        params = {}
        if status:
            params["status"] = status

        response = self._connection.get(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.capture}/{ApiPath.session}",
            params=params,
        )

        sessions = []
        for session_data in response.get("sessions", []):
            session_id = session_data.pop("id", None) or session_data.pop(
                "session_id", None
            )
            # Normalize rtstreams
            for rts in session_data.get("rtstreams", []):
                if isinstance(rts, dict):
                    if "rtstream_id" in rts and "id" not in rts:
                        rts["id"] = rts.pop("rtstream_id")
                    if "collection_id" not in rts:
                        rts["collection_id"] = self.id
            # Remove collection_id from data
            session_data.pop("collection_id", None)
            sessions.append(
                CaptureSession(
                    self._connection,
                    id=session_id,
                    collection_id=self.id,
                    **session_data,
                )
            )
        return sessions
