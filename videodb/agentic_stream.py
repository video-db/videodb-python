import time

from typing import List, Optional

from videodb._constants import AgenticStreamRunStatus, ApiPath
from videodb.exceptions import VideodbError


class AgenticStreamRun:
    """AgenticStreamRun class representing a single execution of an agentic stream.

    :ivar str id: Unique identifier for the run
    :ivar str agentic_stream_id: ID of the parent agentic stream
    :ivar str collection_id: ID of the collection
    :ivar str status: Current status (queued/running/completed/failed/cancelled)
    :ivar dict config: Immutable config snapshot captured at run creation
    :ivar dict progress: Current progress ``{stage, percent, message}``
    :ivar str video_id: ID of the produced video (populated on completion)
    :ivar str stream_url: Stream URL of the produced video
    :ivar str player_url: Player URL of the produced video
    :ivar str thumbnail_url: Thumbnail URL of the produced video
    :ivar float duration: Duration of the produced video in seconds
    :ivar list events: Compiled clip list (populated on completion)
    :ivar str error: Error message when the run failed
    """

    def __init__(
        self, _connection, id: str, agentic_stream_id: str, collection_id: str, **kwargs
    ) -> None:
        self._connection = _connection
        self.id = id
        self.agentic_stream_id = agentic_stream_id
        self.collection_id = collection_id
        self._update_attributes(kwargs)

    def __repr__(self) -> str:
        return (
            f"AgenticStreamRun("
            f"id={self.id}, "
            f"agentic_stream_id={self.agentic_stream_id}, "
            f"collection_id={self.collection_id}, "
            f"status={self.status}, "
            f"progress={self.progress}, "
            f"config={self.config}, "
            f"video_id={self.video_id}, "
            f"stream_url={self.stream_url}, "
            f"player_url={self.player_url}, "
            f"thumbnail_url={self.thumbnail_url}, "
            f"duration={self.duration}, "
            f"events={self.events}, "
            f"error={self.error}, "
            f"callback_url={self.callback_url}, "
            f"callback_data={self.callback_data}, "
            f"created_at={self.created_at}, "
            f"updated_at={self.updated_at}, "
            f"completed_at={self.completed_at})"
        )

    def _update_attributes(self, data: dict) -> None:
        self.status = data.get("status")
        self.config = data.get("config")
        self.progress = data.get("progress")
        self.video_id = data.get("video_id")
        self.stream_url = data.get("stream_url")
        self.player_url = data.get("player_url")
        self.thumbnail_url = data.get("thumbnail_url")
        self.duration = data.get("duration")
        self.events = data.get("events")
        self.error = data.get("error")
        self.callback_url = data.get("callback_url")
        self.callback_data = data.get("callback_data")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")
        self.completed_at = data.get("completed_at")

    @property
    def _base_path(self) -> str:
        return (
            f"{ApiPath.collection}/{self.collection_id}/"
            f"{ApiPath.agentic_stream}/{self.agentic_stream_id}/"
            f"{ApiPath.runs}/{self.id}"
        )

    @property
    def is_complete(self) -> bool:
        """True if the run has reached a terminal status."""
        return self.status in AgenticStreamRunStatus.terminal

    @property
    def is_successful(self) -> bool:
        """True if the run completed successfully."""
        return self.status == AgenticStreamRunStatus.completed

    def refresh(self) -> "AgenticStreamRun":
        """Refresh run data from the server.

        :return: The updated run instance
        :rtype: AgenticStreamRun
        """
        response = self._connection.get(path=self._base_path)
        if response:
            self._update_attributes(response)
        else:
            raise VideodbError(f"Failed to refresh run {self.id}")
        return self

    def wait(self, timeout: int = 3600, poll_interval: int = 5) -> "AgenticStreamRun":
        """Block until the run reaches a terminal status.

        :param int timeout: Maximum seconds to wait (default 3600)
        :param int poll_interval: Seconds between polls (default 5)
        :return: The run instance in a terminal state
        :rtype: AgenticStreamRun
        :raises VideodbError: If the run failed or the timeout is exceeded
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            self.refresh()
            if self.is_complete:
                if self.status == AgenticStreamRunStatus.failed:
                    raise VideodbError(f"Run {self.id} failed: {self.error}")
                return self
            time.sleep(poll_interval)
        raise VideodbError(f"Run {self.id} did not complete within {timeout}s")

    def cancel(self) -> "AgenticStreamRun":
        """Cancel a queued or running run.

        :return: The updated run instance
        :rtype: AgenticStreamRun
        """
        response = self._connection.patch(
            path=f"{self._base_path}/{ApiPath.status}",
            data={"status": AgenticStreamRunStatus.cancelled},
        )
        if response:
            self._update_attributes(response)
        return self

    def get_events(self) -> List[dict]:
        """Get the user-facing event timeline of this run.

        :return: List of event dicts
        :rtype: List[dict]
        """
        response = self._connection.get(path=f"{self._base_path}/{ApiPath.events}")
        return (response or {}).get("events", [])

    def get_logs(self) -> List[dict]:
        """Get the debug logs of this run.

        :return: List of log dicts
        :rtype: List[dict]
        """
        response = self._connection.get(path=f"{self._base_path}/{ApiPath.logs}")
        return (response or {}).get("logs", [])


class AgenticStream:
    """AgenticStream class representing a persistent agent video pipeline.

    Note: Users should not initialize this class directly.
    Instead use :meth:`Collection.create_agentic_stream() <videodb.collection.Collection.create_agentic_stream>`

    :ivar str id: Unique identifier for the agentic stream
    :ivar str collection_id: ID of the collection this stream belongs to
    :ivar str name: Human-readable name
    :ivar str template_id: ID of the template this stream uses
    :ivar str prompt: Content instructions for the agent
    :ivar list sources: Keywords/URLs used for research each run
    """

    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self._update_attributes(kwargs)

    def __repr__(self) -> str:
        return (
            f"AgenticStream("
            f"id={self.id}, "
            f"collection_id={self.collection_id}, "
            f"name={self.name}, "
            f"template_id={self.template_id}, "
            f"prompt={self.prompt}, "
            f"sources={self.sources}, "
            f"max_duration={self.max_duration}, "
            f"voice={self.voice}, "
            f"language={self.language}, "
            f"aspect_ratio={self.aspect_ratio}, "
            f"captions={self.captions}, "
            f"model={self.model}, "
            f"callback_url={self.callback_url}, "
            f"callback_data={self.callback_data}, "
            f"status={self.status}, "
            f"created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )

    def _update_attributes(self, data: dict) -> None:
        self.name = data.get("name")
        self.template_id = data.get("template_id")
        self.prompt = data.get("prompt")
        self.sources = data.get("sources")
        self.max_duration = data.get("max_duration")
        self.voice = data.get("voice")
        self.language = data.get("language")
        self.aspect_ratio = data.get("aspect_ratio")
        self.captions = data.get("captions")
        self.model = data.get("model")
        self.callback_url = data.get("callback_url")
        self.callback_data = data.get("callback_data")
        self.status = data.get("status")
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")

    @property
    def _base_path(self) -> str:
        return (
            f"{ApiPath.collection}/{self.collection_id}/"
            f"{ApiPath.agentic_stream}/{self.id}"
        )

    def refresh(self) -> "AgenticStream":
        """Refresh stream data from the server.

        :return: The updated stream instance
        :rtype: AgenticStream
        """
        response = self._connection.get(path=f"{self._base_path}/")
        if response:
            self._update_attributes(response)
        else:
            raise VideodbError(f"Failed to refresh agentic stream {self.id}")
        return self

    def update(self, **kwargs) -> "AgenticStream":
        """Update stream fields.

        :param kwargs: Fields to update (name, template_id, prompt, sources, max_duration,
            voice, language, aspect_ratio, captions, model, callback_url,
            callback_data)
        :return: The updated stream instance
        :rtype: AgenticStream
        """
        response = self._connection.patch(path=f"{self._base_path}/", data=kwargs)
        if response:
            self._update_attributes(response)
        return self

    def delete(self) -> None:
        """Delete the agentic stream.

        Existing runs, output videos, and schedules are not deleted.
        Delete any associated schedules separately.

        :return: None
        :rtype: None
        """
        self._connection.delete(path=f"{self._base_path}/")

    def run_now(
        self,
        callback_url: Optional[str] = None,
        callback_data: Optional[dict] = None,
    ) -> AgenticStreamRun:
        """Trigger an on-demand run of this stream.

        :param str callback_url: (optional) Per-run webhook override
        :param dict callback_data: (optional) Per-run callback data override
        :return: The created run
        :rtype: AgenticStreamRun
        """
        data = {}
        if callback_url is not None:
            data["callback_url"] = callback_url
        if callback_data is not None:
            data["callback_data"] = callback_data
        response = self._connection.post(
            path=f"{self._base_path}/{ApiPath.runs}", data=data
        )
        if not response:
            raise VideodbError("Failed to trigger run")
        return AgenticStreamRun(
            self._connection,
            id=response.get("id"),
            agentic_stream_id=self.id,
            collection_id=self.collection_id,
            **{k: v for k, v in response.items()
               if k not in ("id", "agentic_stream_id", "collection_id")},
        )

    def list_runs(self) -> List[AgenticStreamRun]:
        """List runs of this stream, most recent first.

        :return: List of runs
        :rtype: List[AgenticStreamRun]
        """
        response = self._connection.get(path=f"{self._base_path}/{ApiPath.runs}")
        runs = (response or {}).get("runs", [])
        return [
            AgenticStreamRun(
                self._connection,
                id=run.get("id"),
                agentic_stream_id=self.id,
                collection_id=self.collection_id,
                **{k: v for k, v in run.items()
                   if k not in ("id", "agentic_stream_id", "collection_id")},
            )
            for run in runs
        ]

    def get_run(self, run_id: str) -> AgenticStreamRun:
        """Get a run by its ID.

        :param str run_id: ID of the run
        :return: The run
        :rtype: AgenticStreamRun
        """
        response = self._connection.get(
            path=f"{self._base_path}/{ApiPath.runs}/{run_id}"
        )
        if not response:
            raise VideodbError(f"Run {run_id} not found")
        return AgenticStreamRun(
            self._connection,
            id=response.get("id"),
            agentic_stream_id=self.id,
            collection_id=self.collection_id,
            **{k: v for k, v in response.items()
               if k not in ("id", "agentic_stream_id", "collection_id")},
        )
