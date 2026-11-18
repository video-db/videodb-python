import time

from videodb._constants import PollDefaults
from videodb._utils._poll import (
    JobTimeoutError,
    PollSchedule,
    max_wait_from,
    retry_after_from,
)


class _FakeResponse:
    def __init__(self, headers):
        self.headers = headers


def test_retry_after_from_body():
    assert retry_after_from({"retry_after": 3}) == 3.0
    assert retry_after_from({"data": {"retry_after": "4.5"}}) == 4.5


def test_retry_after_from_header():
    assert retry_after_from(_FakeResponse({"Retry-After": "7"})) == 7.0


def test_retry_after_absent_or_bad():
    assert retry_after_from(None) is None
    assert retry_after_from({}) is None
    assert retry_after_from({"retry_after": "soon"}) is None
    assert retry_after_from({"retry_after": -5}) is None
    assert retry_after_from(_FakeResponse({})) is None


def test_server_hint_wins_and_is_clamped():
    s = PollSchedule(jitter=0)
    assert s.next_delay({"retry_after": 12}) == 12.0
    # a wild hint is clamped into the sane band rather than trusted blindly
    assert s.next_delay({"retry_after": 9999}) == PollDefaults.max_interval
    assert s.next_delay({"retry_after": 0}) == PollDefaults.min_interval


def test_explicit_interval_wins_over_backoff():
    s = PollSchedule(interval=5, jitter=0)
    assert s.next_delay({"retry_after": 30}) == 5.0
    assert s.next_delay() == 5.0


def test_backoff_when_server_sends_no_hint():
    s = PollSchedule(first_interval=2, factor=2, max_interval=10, jitter=0)
    assert [s.next_delay() for _ in range(5)] == [2.0, 4.0, 8.0, 10.0, 10.0]


def test_jitter_stays_within_band():
    s = PollSchedule(interval=10, jitter=0.2)
    delays = [s.next_delay() for _ in range(200)]
    assert all(8.0 <= d <= 12.0 for d in delays)
    assert len(set(delays)) > 1


def test_server_max_wait_extends_the_deadline():
    s = PollSchedule(max_poll_time=60, jitter=0)
    s.next_delay({"retry_after": 1, "data": {"max_wait": 900}})
    assert s.max_poll_time == 900
    # a smaller advisory ceiling never shortens what the caller asked for
    s.next_delay({"data": {"max_wait": 10}})
    assert s.max_poll_time == 900


def test_delay_never_overshoots_the_deadline():
    s = PollSchedule(max_poll_time=3, interval=30, jitter=0)
    assert s.next_delay() <= 3.0


def test_not_expired_does_not_raise():
    PollSchedule(max_poll_time=60).raise_if_expired(what="Job")


def test_timeout_carries_the_job_handle():
    s = PollSchedule(max_poll_time=0)
    time.sleep(0.01)
    try:
        s.raise_if_expired(
            what="Job j-1",
            output_url="https://api.videodb.io/async-response/j-1",
            job_id="j-1",
        )
    except JobTimeoutError as e:
        assert e.output_url.endswith("j-1")
        assert e.job_id == "j-1"
        assert "still running" in str(e)
    else:
        raise AssertionError("expected JobTimeoutError")
