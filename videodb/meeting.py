from videodb._constants import ApiPath

from videodb.exceptions import (
    VideodbError,
)


class Meeting:
    """Meeting class representing a meeting recording bot."""

    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self._update_attributes(kwargs)

    def __repr__(self) -> str:
        return f"Meeting(id={self.id}, collection_id={self.collection_id}, name={self.name}, status={self.status}, bot_name={self.bot_name})"

    def _update_attributes(self, data: dict) -> None:
        """Update instance attributes from API response data."""
        self.bot_name = data.get("bot_name")
        self.name = data.get("meeting_name")
        self.meeting_url = data.get("meeting_url")
        self.status = data.get("status")
        self.time_zone = data.get("time_zone")

    def refresh(self) -> "Meeting":
        """Refresh meeting data from the server.

        Returns:
            self: The Meeting instance with updated data

        Raises:
            APIError: If the API request fails
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
        """Check if the meeting is currently active."""
        return self.status in ["initializing", "processing"]

    @property
    def is_completed(self) -> bool:
        """Check if the meeting has completed."""
        return self.status in ["done"]

    def wait_for_status(
        self, target_status: str, timeout: int = 14400, interval: int = 120
    ) -> bool:
        """Wait for the meeting to reach a specific status.

        Args:
            target_status: The status to wait for
            timeout: Maximum time to wait in seconds
            interval: Time between status checks in seconds

        Returns:
            bool: True if status reached, False if timeout
        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout:
            self.refresh()
            if self.status == target_status:
                return True
            time.sleep(interval)

        return False
