from videodb._constants import ApiPath, MeetingStatus

from videodb.exceptions import (
    VideodbError,
)

DEFAULT_MEETING_TIMEOUT = 14400  # 4 hours
DEFAULT_POLLING_INTERVAL = 120  # 2 minutes


class Meeting:
    """Meeting class representing a meeting recording bot.

    :ivar str id: Unique identifier for the meeting
    :ivar str collection_id: ID of the collection this meeting belongs to
    :ivar str bot_name: Name of the meeting recording bot
    :ivar str meeting_title: Title of the meeting
    :ivar str meeting_url: URL of the meeting
    :ivar str status: Current status of the meeting
    :ivar str time_zone: Time zone of the meeting
    :ivar str video_id: ID of the recorded video
    :ivar dict speaker_timeline: Timeline of speakers in the meeting
    """

    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self._update_attributes(kwargs)

    def __repr__(self) -> str:
        return f"Meeting(id={self.id}, collection_id={self.collection_id}, meeting_title={self.meeting_title}, status={self.status}, bot_name={self.bot_name}, meeting_url={self.meeting_url})"

    def _update_attributes(self, data: dict) -> None:
        """Update instance attributes from API response data.

        :param dict data: Dictionary containing attribute data from API response
        :return: None
        :rtype: None
        """
        self.bot_name = data.get("bot_name")
        self.meeting_title = data.get("meeting_title")
        self.meeting_url = data.get("meeting_url")
        self.status = data.get("status")
        self.time_zone = data.get("time_zone")
        self.video_id = data.get("video_id")
        self.speaker_timeline = data.get("speaker_timeline")

    def refresh(self) -> "Meeting":
        """Refresh meeting data from the server.

        :return: The Meeting instance with updated data
        :rtype: Meeting
        :raises VideodbError: If the API request fails
        """
        response = self._connection.get(
            path=f"{ApiPath.collection}/{self.collection_id}/{ApiPath.meeting}/{self.id}"
        )

        if response:
            self._update_attributes(response)
        else:
            raise VideodbError(f"Failed to refresh meeting {self.id}")

        return self

    @property
    def is_active(self) -> bool:
        """Check if the meeting is currently active.

        :return: True if meeting is initializing or processing, False otherwise
        :rtype: bool
        """
        return self.status in [MeetingStatus.initializing, MeetingStatus.processing]

    @property
    def is_completed(self) -> bool:
        """Check if the meeting has completed.

        :return: True if meeting is done, False otherwise
        :rtype: bool
        """
        return self.status == MeetingStatus.done

    def wait_for_status(
        self,
        target_status: str,
        timeout: int = DEFAULT_MEETING_TIMEOUT,
        interval: int = DEFAULT_POLLING_INTERVAL,
    ) -> bool:
        """Wait for the meeting to reach a specific status.

        :param str target_status: The status to wait for
        :param int timeout: Maximum time to wait in seconds (default: 14400)
        :param int interval: Time between status checks in seconds (default: 120)
        :return: True if status reached, False if timeout
        :rtype: bool
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            self.refresh()
            if self.status == target_status:
                return True
            time.sleep(interval)

        return False
