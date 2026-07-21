import time

from videodb._constants import ApiPath, SandboxStatus
from videodb.exceptions import InvalidRequestError, RequestTimeoutError

TERMINAL_STATUSES = (SandboxStatus.stopped, SandboxStatus.failed)


class Sandbox:
    """A persistent GPU compute pool for running inference jobs."""

    def __init__(self, _connection, sandbox_id=None, id=None, tier=None, status=None,
                 name=None, created_at=None, started_at=None, stopped_at=None, **kwargs):
        self._connection = _connection
        self.id = sandbox_id or id
        self.tier = tier
        self.status = status
        self.name = name
        self.created_at = created_at
        self.started_at = started_at
        self.stopped_at = stopped_at

    def __repr__(self):
        return f"Sandbox(id={self.id}, tier={self.tier}, status={self.status}, name={self.name})"

    def _update(self, data):
        if not data:
            return
        self.id = data.get("sandbox_id", data.get("id", self.id))
        self.tier = data.get("tier", self.tier)
        self.status = data.get("status", self.status)
        self.name = data.get("name", self.name)
        self.created_at = data.get("created_at", self.created_at)
        self.started_at = data.get("started_at", self.started_at)
        self.stopped_at = data.get("stopped_at", self.stopped_at)

    def refresh(self):
        """Fetch latest sandbox state from the server."""
        data = self._connection.get(path=f"{ApiPath.sandbox}/{self.id}")
        self._update(data or {})
        return self

    def wait_for_ready(self, timeout=300, interval=5):
        """Poll until the sandbox is active.

        :param int timeout: Maximum seconds to wait (default 300)
        :param int interval: Seconds between polls (default 5)
        :return: self
        :raises RequestTimeoutError: If timeout is exceeded
        :raises InvalidRequestError: If sandbox enters a terminal state
        """
        deadline = time.time() + timeout
        while True:
            self.refresh()
            if self.status == SandboxStatus.active:
                return self
            if self.status in TERMINAL_STATUSES:
                raise InvalidRequestError(
                    f"Sandbox {self.id} entered terminal state: {self.status}"
                )
            if time.time() >= deadline:
                raise RequestTimeoutError(
                    f"Sandbox {self.id} not ready within {timeout}s"
                )
            time.sleep(interval)

    def stop(self, grace=True):
        """Stop this sandbox.

        :param bool grace: Wait for running jobs to finish before teardown (default True)
        :return: self
        """
        data = self._connection.post(
            path=f"{ApiPath.sandbox}/{self.id}/stop",
            data={"grace": grace},
        )
        self._update(data.get("data", {}))
        return self

    def wait_for_stop(self, timeout=120, interval=5):
        """Poll until the sandbox is stopped.

        :param int timeout: Maximum seconds to wait (default 120)
        :param int interval: Seconds between polls (default 5)
        :return: self
        :raises RequestTimeoutError: If timeout is exceeded
        """
        deadline = time.time() + timeout
        while True:
            self.refresh()
            if self.status in TERMINAL_STATUSES:
                return self
            if time.time() >= deadline:
                raise RequestTimeoutError(
                    f"Sandbox {self.id} did not stop within {timeout}s"
                )
            time.sleep(interval)

    @property
    def is_active(self):
        return self.status == SandboxStatus.active

    @property
    def is_ready(self):
        return self.status in (SandboxStatus.provisioning, SandboxStatus.active)
