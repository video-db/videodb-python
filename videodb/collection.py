import logging

from typing import Optional, Union, List, Dict, Any, Literal
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
from videodb.meeting import Meeting
from videodb.rtstream import RTStream
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
        self, url: str, name: str, sample_rate: int = None
    ) -> RTStream:
        """Connect to an rtstream.

        :param str url: URL of the rtstream
        :param str name: Name of the rtstream
        :param int sample_rate: Sample rate of the rtstream (optional)
        :return: :class:`RTStream <RTStream>` object
        """
        rtstream_data = self._connection.post(
            path=f"{ApiPath.rtstream}",
            data={
                "collection_id": self.id,
                "url": url,
                "name": name,
                "sample_rate": sample_rate,
            },
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

    def list_rtstreams(self) -> List[RTStream]:
        """List all rtstreams in the collection.

        :return: List of :class:`RTStream <RTStream>` objects
        :rtype: List[:class:`videodb.rtstream.RTStream`]
        """
        rtstreams_data = self._connection.get(
            path=f"{ApiPath.rtstream}",
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
    ) -> Image:
        """Generate an image from a prompt.

        :param str prompt: Prompt for the image generation
        :param str aspect_ratio: Aspect ratio of the image (optional)
        :param str callback_url: URL to receive the callback (optional)
        :return: :class:`Image <Image>` object
        :rtype: :class:`videodb.image.Image`
        """
        image_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.generate}/{ApiPath.image}",
            data={
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "callback_url": callback_url,
            },
        )
        if image_data:
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
    ) -> Audio:
        """Generate voice from text.

        :param str text: Text to convert to voice
        :param str voice_name: Name of the voice to use
        :param dict config: Configuration for the voice generation
        :param str callback_url: URL to receive the callback (optional)
        :return: :class:`Audio <Audio>` object
        :rtype: :class:`videodb.audio.Audio`
        """
        audio_data = self._connection.post(
            path=f"{ApiPath.collection}/{self.id}/{ApiPath.generate}/{ApiPath.audio}",
            data={
                "text": text,
                "audio_type": "voice",
                "voice_name": voice_name,
                "config": config,
                "callback_url": callback_url,
            },
        )
        if audio_data:
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
        :param str language_code: Language code to dub the video to
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
    ) -> SearchResult:
        """Search for a query in the collection.

        :param str query: Query to search for
        :param SearchType search_type: Type of search to perform (optional)
        :param IndexType index_type: Type of index to search (optional)
        :param int result_threshold: Number of results to return (optional)
        :param float score_threshold: Threshold score for the search (optional)
        :param float dynamic_score_percentage: Percentage of dynamic score to consider (optional)
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
