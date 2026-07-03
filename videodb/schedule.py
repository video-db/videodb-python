from videodb._constants import ApiPath
from videodb.exceptions import VideodbError


class Schedule:
    """Schedule class representing a time-based trigger for agentic stream runs.

    Note: Users should not initialize this class directly.
    Instead use :meth:`Connection.create_schedule() <videodb.client.Connection.create_schedule>`

    :ivar str id: Unique identifier for the schedule
    :ivar str target_type: Type of the scheduled target (``agentic_stream``)
    :ivar str target_id: ID of the target agentic stream
    :ivar str collection_id: ID of the target's collection
    :ivar str trigger: EventBridge cron expression, e.g. ``"0 9 * * ? *"``
    :ivar str timezone: IANA timezone name the cron runs in (default ``UTC``)
    :ivar str status: ``active`` or ``paused``
    """

    def __init__(self, _connection, id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self._update_attributes(kwargs)

    def __repr__(self) -> str:
        return (
            f"Schedule("
            f"id={self.id}, "
            f"target_id={self.target_id}, "
            f"trigger={self.trigger}, "
            f"status={self.status})"
        )

    def _update_attributes(self, data: dict) -> None:
        self.target_type = data.get("target_type")
        self.target_id = data.get("target_id")
        self.collection_id = data.get("collection_id")
        self.trigger = data.get("trigger")
        self.timezone = data.get("timezone")
        self.status = data.get("status")
        self.callback_url = data.get("callback_url")
        self.callback_data = data.get("callback_data")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")

    def refresh(self) -> "Schedule":
        """Refresh schedule data from the server.

        :return: The updated schedule instance
        :rtype: Schedule
        """
        response = self._connection.get(path=f"{ApiPath.schedule}/{self.id}/")
        if response:
            self._update_attributes(response)
        else:
            raise VideodbError(f"Failed to refresh schedule {self.id}")
        return self

    def delete(self) -> None:
        """Delete the schedule. In-flight runs are unaffected.

        :return: None
        :rtype: None
        """
        self._connection.delete(path=f"{ApiPath.schedule}/{self.id}/")

    def enable(self) -> "Schedule":
        """Resume a paused schedule.

        :return: The updated schedule instance
        :rtype: Schedule
        """
        response = self._connection.patch(
            path=f"{ApiPath.schedule}/{self.id}/{ApiPath.status}",
            data={"status": "active"},
        )
        if response:
            self._update_attributes(response)
        return self

    def disable(self) -> "Schedule":
        """Pause the schedule. Future triggers stop; the record is kept.

        :return: The updated schedule instance
        :rtype: Schedule
        """
        response = self._connection.patch(
            path=f"{ApiPath.schedule}/{self.id}/{ApiPath.status}",
            data={"status": "paused"},
        )
        if response:
            self._update_attributes(response)
        return self
