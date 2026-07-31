"""Following an NLE export job.

An export is minutes of multi-gigabyte downloads and encoding, so it cannot be a
synchronous call. :meth:`videodb.editor.Timeline.export` submits and returns one
of these immediately; the caller polls, or calls :meth:`ExportJob.wait`.

Two shape decisions worth stating, because both are easy to get backwards.

**``download_url`` is a method, not a property.** What it returns is a signed URL
with a short life. A property invites caching, and a cached signed URL is a link
that works in testing and 403s a day later. It is minted per call and never held
on the job.

**``done`` and ``failed`` are both False for a status this client does not
recognise.** The platform's vocabulary can grow, and reporting an unknown status
as done would have a caller fetch an artifact that does not exist. Waiting on a
status we cannot interpret is the recoverable mistake.
"""

import time
from typing import Optional

from videodb._constants import ApiPath

#: Statuses that mean the job is over.
DONE = "done"
ERROR = "error"
TERMINAL_STATUSES = (DONE, ERROR)

#: Default ceiling for :meth:`ExportJob.wait`, in seconds. Half an hour is
#: longer than an export is expected to take, so a wait that reaches it means
#: something is wrong rather than slow.
DEFAULT_WAIT_TIMEOUT = 1800

#: How often :meth:`ExportJob.wait` polls, in seconds. The job takes minutes;
#: polling faster than this costs requests and buys nothing.
DEFAULT_POLL_INTERVAL = 5


class ExportJob:
    """A submitted export.

    :ivar str id: The platform's job id
    :ivar str timeline_id: The timeline this export was made from
    :ivar str status: ``queued``, ``rendering``, ``converting``, ``packaging``,
        ``done`` or ``error``
    :ivar int progress: 0-100
    :ivar str stage: Human-readable label for the current stage
    :ivar str error: Failure message, when ``status`` is ``error``
    :ivar dict fidelity: What the bundle could and could not carry
    """

    def __init__(
        self,
        connection,
        job_id: str,
        timeline_id: Optional[str] = None,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        stage: Optional[str] = None,
        error: Optional[str] = None,
        fidelity: Optional[dict] = None,
        **kwargs,
    ) -> None:
        self.connection = connection
        self.id = job_id
        # Part of the address, not decoration. An export is read back under the
        # timeline that produced it, which is what scopes the read to its owner —
        # a job id alone would have to be trusted on its own.
        self.timeline_id = timeline_id
        self.status = status
        self.progress = progress
        self.stage = stage
        self.error = error
        self.fidelity = fidelity

    def __repr__(self) -> str:
        return f"ExportJob(id={self.id!r}, status={self.status!r}, progress={self.progress!r})"

    def _path(self) -> str:
        """Where this job lives. The timeline scopes the read to its owner."""
        if not self.timeline_id:
            raise ValueError(
                f"export {self.id} has no timeline_id, so it cannot be read back; "
                "it was built from a response that did not carry one"
            )
        return f"{ApiPath.editor}/export/{self.timeline_id}/{self.id}"

    @property
    def done(self) -> bool:
        """Whether the export finished successfully."""
        return self.status == DONE

    @property
    def failed(self) -> bool:
        """Whether the export ended in failure."""
        return self.status == ERROR

    @property
    def terminal(self) -> bool:
        """Whether the job is over, either way."""
        return self.status in TERMINAL_STATUSES

    def refresh(self) -> "ExportJob":
        """Re-read the job and update this object in place.

        :return: self, so it can be chained
        :rtype: :class:`ExportJob`
        """
        data = self.connection.get(path=self._path()) or {}
        self.status = data.get("status", self.status)
        self.progress = data.get("progress", self.progress)
        self.stage = data.get("stage", self.stage)
        self.error = data.get("error", self.error)
        if data.get("fidelity") is not None:
            self.fidelity = data["fidelity"]
        return self

    def wait(
        self,
        timeout: int = DEFAULT_WAIT_TIMEOUT,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> "ExportJob":
        """Poll until the job is over.

        Returns on failure as well as success — ``error`` is a terminal state, and
        polling a failed job forever is not more helpful than reporting it.

        :param int timeout: Seconds to wait before giving up
        :param int poll_interval: Seconds between polls
        :raises TimeoutError: if the job is still running when the budget runs out
        :return: self
        :rtype: :class:`ExportJob`
        """
        deadline = time.monotonic() + timeout
        while True:
            self.refresh()
            if self.terminal:
                return self
            if time.monotonic() >= deadline:
                # Raised rather than returned: a caller handed a still-running job
                # by a method named `wait` will treat it as finished.
                raise TimeoutError(
                    f"export {self.id} was still {self.status!r} after {timeout}s"
                )
            time.sleep(poll_interval)

    def download_url(self) -> str:
        """A signed URL for the bundle, minted for this call.

        Not cached and not stored on the job — see the module docstring.

        :raises ValueError: if the job has not finished
        :return: A URL valid for a limited time
        :rtype: str
        """
        if not self.done:
            raise ValueError(
                f"export {self.id} is not finished (status {self.status!r}); "
                "there is no bundle to download yet"
            )
        data = self.connection.get(path=f"{self._path()}/download") or {}
        url = data.get("download_url")
        if not url:
            # Returning None from something annotated -> str pushes the failure
            # into whatever the caller does with it — an opener, a request, a
            # log line reading "None" — and by then nothing points back here.
            raise ValueError(
                f"export {self.id} finished but no download URL was returned; "
                "the bundle may have expired"
            )
        return url


def job_from_response(connection, data: dict) -> ExportJob:
    """Build an :class:`ExportJob` from a submit response.

    A response without a ``job_id`` is an error rather than a job: an
    :class:`ExportJob` with no id cannot be refreshed, waited on or downloaded,
    so failing here names the problem instead of deferring it to whichever
    attribute the caller touches first.
    """
    job_id = (data or {}).get("job_id")
    if not job_id:
        raise ValueError(f"export response carried no job_id: {data!r}")
    return ExportJob(connection, **{**data, "job_id": job_id})
