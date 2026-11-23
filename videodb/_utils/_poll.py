"""Polling helpers shared by every wait loop in the SDK.

Cadence precedence, highest first:

1. an explicit ``poll_interval`` from the caller;
2. the server's hint, ``retry_after`` in the response body or the
   ``Retry-After`` header, clamped to the configured band;
3. the SDK's own flat cadence.

Jitter is off by default and can be enabled per schedule.
"""

import logging
import random
import time

from typing import Any, Optional

from videodb._constants import PollDefaults
from videodb.exceptions import JobTimeoutError

logger = logging.getLogger(__name__)


def _coerce(value) -> Optional[float]:
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return None
    if seconds < 0:
        return None
    return seconds


def retry_after_from(source: Any) -> Optional[float]:
    """Return the server's poll hint in seconds, or None if it sent none.

    ``source`` may be a decoded response body (``dict``) or anything with a
    ``headers`` mapping, such as a :class:`requests.Response`.
    """
    if source is None:
        return None

    if isinstance(source, dict):
        for holder in (source, source.get("data")):
            if isinstance(holder, dict):
                seconds = _coerce(holder.get("retry_after"))
                if seconds is not None:
                    return seconds
        return None

    headers = getattr(source, "headers", None)
    if headers:
        try:
            return _coerce(headers.get("Retry-After"))
        except AttributeError:
            return None
    return None


def max_wait_from(source: Any) -> Optional[float]:
    """Return the server's advisory ceiling for this job kind, if any."""
    if not isinstance(source, dict):
        return None
    for holder in (source, source.get("data")):
        if isinstance(holder, dict):
            seconds = _coerce(holder.get("max_wait"))
            if seconds is not None:
                return seconds
    return None


class PollSchedule:
    """Decides how long to wait before the next status check.

    :param float interval: Force a fixed cadence (what ``poll_interval=``
        used to mean). ``None`` means follow the server hint, else
        ``first_interval``.
    :param float max_poll_time: Deadline in seconds. ``None`` uses
        ``default_max_poll_time`` (else the SDK default), which a server
        ``max_wait`` hint may extend; an explicit value is never extended.
    :param float first_interval: The loop's own cadence when the server
        sends no hint.
    :param float default_max_poll_time: The loop's own deadline when the
        caller passes none.
    """

    def __init__(
        self,
        interval: Optional[float] = None,
        max_poll_time: Optional[float] = None,
        first_interval: Optional[float] = None,
        factor: Optional[float] = None,
        max_interval: Optional[float] = None,
        min_interval: Optional[float] = None,
        jitter: Optional[float] = None,
        default_max_poll_time: Optional[float] = None,
    ) -> None:
        self.interval = _coerce(interval)
        self._deadline_explicit = max_poll_time is not None
        if max_poll_time is not None:
            self.max_poll_time = _coerce(max_poll_time)
        elif default_max_poll_time is not None:
            self.max_poll_time = float(default_max_poll_time)
        else:
            self.max_poll_time = PollDefaults.max_poll_time
        self.factor = factor if factor is not None else PollDefaults.factor
        self.max_interval = (
            max_interval if max_interval is not None else PollDefaults.max_interval
        )
        self.min_interval = (
            min_interval if min_interval is not None else PollDefaults.min_interval
        )
        self.jitter = jitter if jitter is not None else PollDefaults.jitter
        self._next = (
            first_interval
            if first_interval is not None
            else PollDefaults.first_interval
        )
        self._start = time.monotonic()
        self.polls = 0

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._start

    @property
    def remaining(self) -> float:
        return self.max_poll_time - self.elapsed

    @property
    def expired(self) -> bool:
        return self.remaining <= 0

    def observe(self, source: Any = None) -> None:
        """Adopt a server-advertised ceiling unless the caller set a deadline."""
        if self._deadline_explicit:
            return
        advertised = max_wait_from(source)
        if advertised and advertised > self.max_poll_time:
            logger.debug(
                "Extending poll deadline %.0fs -> %.0fs (server max_wait)",
                self.max_poll_time,
                advertised,
            )
            self.max_poll_time = advertised

    def next_delay(self, source: Any = None) -> float:
        """Seconds to wait before the next check."""
        self.observe(source)

        if self.interval is not None:
            delay = self.interval
        else:
            hint = retry_after_from(source)
            if hint is not None:
                delay = hint
            else:
                delay = self._next
                self._next = min(self._next * self.factor, self.max_interval)

        if self.jitter:
            delay *= 1 + random.uniform(-self.jitter, self.jitter)
        delay = max(self.min_interval, min(delay, self.max_interval))
        if self.remaining > 0:
            delay = min(delay, max(self.remaining, self.min_interval))
        return round(delay, 3)

    def sleep(self, source: Any = None) -> float:
        """Wait for the next check and return how long we waited."""
        delay = self.next_delay(source)
        self.polls += 1
        logger.debug(
            "Waiting %.1fs before next poll (%.0fs elapsed)", delay, self.elapsed
        )
        time.sleep(delay)
        return delay

    def raise_if_expired(
        self,
        what: str = "Job",
        output_url: Optional[str] = None,
        last_response: Any = None,
        job_id: Optional[str] = None,
    ) -> None:
        """Raise :class:`JobTimeoutError` once the deadline has passed."""
        self.observe(last_response)
        if not self.expired:
            return
        raise JobTimeoutError(
            f"{what} did not complete within {int(self.max_poll_time)}s "
            f"(polled {self.polls} times). The job is still running on "
            f"VideoDB; poll {output_url or 'its output_url'} to pick it up.",
            response=last_response,
            output_url=output_url,
            job_id=job_id,
        )
