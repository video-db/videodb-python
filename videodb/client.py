import logging

from typing import (
    Optional,
    Union,
    List,
)
from videodb.__about__ import __version__
from videodb._constants import (
    ApiPath,
    TranscodeMode,
    VideoConfig,
    AudioConfig,
)

from videodb.collection import Collection
from videodb._utils._http_client import HttpClient
from videodb.video import Video
from videodb.audio import Audio
from videodb.image import Image
from videodb.meeting import Meeting

from videodb._upload import (
    upload,
)

logger = logging.getLogger(__name__)


class Connection(HttpClient):
    """Connection class to interact with the VideoDB"""

    def __init__(self, api_key: str, base_url: str, **kwargs) -> "Connection":
        """Initializes a new instance of the Connection class with specified API credentials.

        Note: Users should not initialize this class directly.
        Instead use :meth:`videodb.connect() <videodb.connect>`

        :param str api_key: API key for authentication
        :param str base_url: Base URL of the VideoDB API
        :raise ValueError: If the API key is not provided
        :return: :class:`Connection <Connection>` object, to interact with the VideoDB
        :rtype: :class:`videodb.client.Connection`
        """
        self.api_key = api_key
        self.base_url = base_url
        self.collection_id = "default"
        super().__init__(
            api_key=api_key, base_url=base_url, version=__version__, **kwargs
        )

    def get_collection(self, collection_id: Optional[str] = "default") -> Collection:
        """Get a collection object by its ID.

        :param str collection_id: ID of the collection (optional, default: "default")
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

        :param str name: Name of the collection
        :param str description: Description of the collection
        :param bool is_public: Make collection public (optional, default: False)
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
        :param str name: Name of the collection
        :param str description: Description of the collection
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
        :rtype: list[dict]
        """
        return self.get(path=f"{ApiPath.billing}/{ApiPath.invoices}")

    def create_event(self, event_prompt: str, label: str):
        """Create an rtstream event.

        :param str event_prompt: Prompt for the event
        :param str label: Label for the event
        :return: Event ID
        :rtype: str
        """
        event_data = self.post(
            f"{ApiPath.rtstream}/{ApiPath.event}",
            data={"event_prompt": event_prompt, "label": label},
        )

        return event_data.get("event_id")

    def list_events(self):
        """List all rtstream events.

        :return: List of events
        :rtype: list[dict]
        """
        event_data = self.get(f"{ApiPath.rtstream}/{ApiPath.event}")
        return event_data.get("events", [])

    def download(self, stream_link: str, name: str) -> dict:
        """Download a file from a stream link.

        :param stream_link: URL of the stream to download
        :param name: Name to save the downloaded file as
        :return: Download response data
        :rtype: dict
        """
        return self.post(
            path=f"{ApiPath.download}",
            data={
                "stream_link": stream_link,
                "name": name,
            },
        )

    def youtube_search(
        self,
        query: str,
        result_threshold: Optional[int] = 10,
        duration: str = "medium",
    ) -> List[dict]:
        """Search for a query on YouTube.

        :param str query: Query to search for
        :param int result_threshold: Number of results to return (optional)
        :param str duration: Duration of the video (optional)
        :return: List of YouTube search results
        :rtype: List[dict]
        """
        search_data = self.post(
            path=f"{ApiPath.collection}/{self.collection_id}/{ApiPath.search}/{ApiPath.web}",
            data={
                "query": query,
                "result_threshold": result_threshold,
                "platform": "youtube",
                "duration": duration,
            },
        )
        return search_data.get("results")

    def transcode(
        self,
        source: str,
        callback_url: str,
        mode: TranscodeMode = TranscodeMode.economy,
        video_config: VideoConfig = VideoConfig(),
        audio_config: AudioConfig = AudioConfig(),
    ) -> None:
        """Transcode the video

        :param str source: URL of the video to transcode, preferably a downloadable URL
        :param str callback_url: URL to receive the callback
        :param TranscodeMode mode: Mode of the transcoding
        :param VideoConfig video_config: Video configuration (optional)
        :param AudioConfig audio_config: Audio configuration (optional)
        :return: Transcode job ID
        :rtype: str
        """
        job_data = self.post(
            path=f"{ApiPath.transcode}",
            data={
                "source": source,
                "callback_url": callback_url,
                "mode": mode,
                "video_config": video_config.__dict__,
                "audio_config": audio_config.__dict__,
            },
        )
        return job_data.get("job_id")

    def get_transcode_details(self, job_id: str) -> dict:
        """Get the details of a transcode job.

        :param str job_id: ID of the transcode job
        :return: Details of the transcode job
        :rtype: dict
        """
        return self.get(path=f"{ApiPath.transcode}/{job_id}")

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
        """Upload a file.

        :param str source: Local path or URL of the file to upload (optional)
        :param MediaType media_type: MediaType object (optional)
        :param str name: Name of the file (optional)
        :param str description: Description of the file (optional)
        :param str callback_url: URL to receive the callback (optional)
        :param str file_path: Path to the file to upload (optional)
        :param str url: URL of the file to upload (optional)
        :return: :class:`Video <Video>`, or :class:`Audio <Audio>`, or :class:`Image <Image>` object
        :rtype: Union[ :class:`videodb.video.Video`, :class:`videodb.audio.Audio`, :class:`videodb.image.Image`]
        """
        upload_data = upload(
            self,
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
            return Video(self, **upload_data)
        elif media_id.startswith("a-"):
            return Audio(self, **upload_data)
        elif media_id.startswith("img-"):
            return Image(self, **upload_data)

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
        """Record a meeting and upload it to the default collection.

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

        response = self.post(
            path=f"{ApiPath.collection}/default/{ApiPath.meeting}/{ApiPath.record}",
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
        return Meeting(self, id=meeting_id, collection_id="default", **response)

    def get_meeting(self, meeting_id: str) -> Meeting:
        """Get a meeting by its ID.

        :param str meeting_id: ID of the meeting
        :return: :class:`Meeting <Meeting>` object
        :rtype: :class:`videodb.meeting.Meeting`
        """
        meeting = Meeting(self, id=meeting_id, collection_id="default")
        meeting.refresh()
        return meeting
