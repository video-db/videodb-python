"""Submitting a timeline for NLE export, and following the job.

The SDK is a pure HTTP client, so all of this is provable against a stub
connection — no network, no platform, no credentials.

The shape mirrors ``Timeline.generate_stream``, which is the established way this
SDK asks the platform to do something with a timeline: serialize ``to_json()``,
POST it inline, and fall back to uploading the JSON when it exceeds
``MAX_PAYLOAD_SIZE``. Export is the same question as render — "here is a timeline,
produce an artifact" — so it is the same shape, and the payload-size fallback
comes along for free rather than being rediscovered the first time somebody
exports a long timeline.
"""

import pytest

from videodb.editor import MAX_PAYLOAD_SIZE, Timeline
from videodb.exceptions import (
    InvalidRequestError,
    RequestTimeoutError,
    VideodbError,
)
from videodb.export import ExportJob


class StubConnection:
    """Records requests and replays scripted responses."""

    def __init__(self, *responses):
        self._responses = list(responses)
        self.posts = []
        self.gets = []

    def post(self, path, data=None, **kwargs):
        self.posts.append({"path": path, "data": data})
        return self._next()

    def get(self, path, params=None, **kwargs):
        self.gets.append({"path": path, "params": params})
        return self._next()

    def _next(self):
        return self._responses.pop(0) if self._responses else {}


def _timeline(conn):
    """A bare timeline is enough here.

    These tests are about the request export() builds, not about how tracks are
    assembled — to_json() produces the same envelope either way, and a populated
    track would couple them to Track's API for nothing.
    """
    return Timeline(conn)


SUBMITTED = {"job_id": "exp_abc123def456", "timeline_id": "tl-9", "status": "queued", "progress": 0}


# ------------------------------------------------------------------- submit


def test_export_posts_the_timeline_inline():
    """The same payload shape generate_stream sends, to a path under `editor`."""
    conn = StubConnection(SUBMITTED)
    _timeline(conn).export()
    assert conn.posts[0]["path"] == "editor/export"
    assert "timeline" in conn.posts[0]["data"]


def test_export_returns_a_job_without_waiting():
    """An export is minutes of downloads and encoding. A call that blocked by
    default would make every caller discover that the hard way."""
    conn = StubConnection(SUBMITTED)
    job = _timeline(conn).export()
    assert isinstance(job, ExportJob)
    assert job.id == "exp_abc123def456"
    assert job.status == "queued"


def test_the_format_is_named_rather_than_assumed():
    """So a second format is additive rather than a breaking change."""
    conn = StubConnection(SUBMITTED)
    _timeline(conn).export()
    assert conn.posts[0]["data"]["format"] == "nle"


def test_optional_fields_are_omitted_rather_than_sent_as_null():
    """A null `name` is not the same as no name — the service falls back to the
    timeline id when the key is absent, and to nothing when it is null."""
    conn = StubConnection(SUBMITTED)
    _timeline(conn).export()
    data = conn.posts[0]["data"]
    assert "name" not in data
    assert "client_ref" not in data
    assert "timeline_id" not in data


def test_supplied_fields_are_forwarded():
    conn = StubConnection(SUBMITTED)
    _timeline(conn).export(name="Demo cut", client_ref="ours-1", timeline_id="tl-9")
    data = conn.posts[0]["data"]
    assert data["name"] == "Demo cut"
    assert data["client_ref"] == "ours-1"
    assert data["timeline_id"] == "tl-9"


def test_a_large_timeline_is_uploaded_rather_than_posted_inline(monkeypatch):
    """The reason to mirror generate_stream rather than invent a shape.

    A long timeline can exceed the request body limit, and posting it inline
    then fails with nothing useful in the response. generate_stream already
    solved this by uploading and referencing by URL; export inherits it.
    """
    conn = StubConnection(SUBMITTED)
    timeline = _timeline(conn)
    monkeypatch.setattr(
        Timeline, "_upload_timeline_data", lambda self, json_str: "https://x/timeline.json"
    )
    monkeypatch.setattr("videodb.editor.MAX_PAYLOAD_SIZE", 1)
    timeline.export()
    data = conn.posts[0]["data"]
    assert data["timeline_url"] == "https://x/timeline.json"
    assert "timeline" not in data


def test_the_inline_threshold_is_the_one_the_render_path_uses():
    """Two different thresholds would mean a timeline that renders and does not
    export, for no reason a caller could discover."""
    assert MAX_PAYLOAD_SIZE == 100 * 1024


def test_a_response_without_a_job_id_is_an_error_not_a_broken_job():
    """A job object with no id cannot be polled, refreshed or downloaded. Failing
    at the call site names the problem; returning one defers it to whichever
    attribute is touched first."""
    conn = StubConnection({"status": "queued"})
    with pytest.raises(InvalidRequestError, match="job_id"):
        _timeline(conn).export()


# -------------------------------------------------------------- following it


def test_refresh_reads_the_job_and_updates_in_place():
    conn = StubConnection({"job_id": "exp_a", "status": "rendering", "progress": 40})
    job = ExportJob(conn, job_id="exp_a", timeline_id="tl-9", status="queued", progress=0)
    job.refresh()
    assert conn.gets[0]["path"] == "editor/export/tl-9/exp_a"
    assert job.status == "rendering"
    assert job.progress == 40


def test_done_and_failed_describe_the_two_terminal_states():
    conn = StubConnection()
    assert ExportJob(conn, job_id="a", timeline_id="tl-9", status="done").done is True
    assert ExportJob(conn, job_id="a", timeline_id="tl-9", status="error").failed is True
    assert ExportJob(conn, job_id="a", timeline_id="tl-9", status="rendering").done is False
    assert ExportJob(conn, job_id="a", timeline_id="tl-9", status="rendering").failed is False


def test_an_unknown_status_is_neither_done_nor_failed():
    """The platform's status vocabulary can grow. Reporting an unrecognised
    status as done would have a caller download an artifact that is not there."""
    job = ExportJob(StubConnection(), job_id="a", timeline_id="tl-9", status="transmogrifying")
    assert job.done is False
    assert job.failed is False


def test_wait_polls_until_terminal():
    conn = StubConnection(
        {"job_id": "exp_a", "status": "rendering", "progress": 10},
        {"job_id": "exp_a", "status": "packaging", "progress": 80},
        {"job_id": "exp_a", "status": "done", "progress": 100},
    )
    job = ExportJob(conn, job_id="exp_a", timeline_id="tl-9", status="queued")
    job.wait(poll_interval=0)
    assert job.status == "done"
    assert len(conn.gets) == 3


def test_wait_returns_on_a_failed_job_rather_than_polling_forever():
    conn = StubConnection({"job_id": "exp_a", "status": "error"})
    job = ExportJob(conn, job_id="exp_a", timeline_id="tl-9", status="queued")
    assert job.wait(poll_interval=0).failed is True


def test_wait_gives_up_and_says_so():
    """Silently returning a still-running job would have the caller treat an
    unfinished export as finished."""
    conn = StubConnection(*[{"job_id": "exp_a", "status": "rendering"}] * 50)
    job = ExportJob(conn, job_id="exp_a", timeline_id="tl-9", status="queued")
    with pytest.raises(RequestTimeoutError):
        job.wait(timeout=0, poll_interval=0)


def test_download_url_is_a_method_because_the_link_expires():
    """A property invites caching, and what would be cached is a signed URL with
    a short life. Minted per call, never stored on the job."""
    conn = StubConnection({"download_url": "https://storage/bundle.zip?sig=1"})
    job = ExportJob(conn, job_id="exp_a", timeline_id="tl-9", status="done")
    assert job.download_url() == "https://storage/bundle.zip?sig=1"
    assert not hasattr(job, "_download_url")


def test_download_url_refuses_before_the_job_is_done():
    """There is nothing to sign yet, and a 410 from the platform is a worse
    explanation than the one available here."""
    job = ExportJob(StubConnection(), job_id="exp_a", status="rendering")
    with pytest.raises(InvalidRequestError, match="not finished"):
        job.download_url()


def test_the_fidelity_summary_reaches_the_caller():
    """An export that dropped the user's colour grades is not a plain success,
    and a client that cannot see that reports it as one."""
    conn = StubConnection(
        {
            "job_id": "exp_a",
            "status": "done",
            "fidelity": {"counts": {"carried": 11, "dropped": 1}, "missing_media": []},
        }
    )
    job = ExportJob(conn, job_id="exp_a", timeline_id="tl-9", status="queued")
    job.refresh()
    assert job.fidelity["counts"]["dropped"] == 1


def test_a_job_read_back_is_addressed_under_its_timeline():
    """The read is addressed under the timeline that produced the job — the
    path shape the API defines."""
    conn = StubConnection({"job_id": "exp_a", "status": "done"})
    ExportJob(conn, job_id="exp_a", timeline_id="tl-9").refresh()
    assert conn.gets[0]["path"] == "editor/export/tl-9/exp_a"


def test_a_job_without_a_timeline_says_so_rather_than_guessing():
    """A submit response that carried no timeline_id yields a job that cannot be
    read back. Failing with that sentence beats a 404 from a malformed path."""
    job = ExportJob(StubConnection(), job_id="exp_a")
    with pytest.raises(InvalidRequestError, match="timeline_id"):
        job.refresh()


def test_the_submitted_job_remembers_its_timeline():
    conn = StubConnection(SUBMITTED)
    assert _timeline(conn).export().timeline_id == "tl-9"


def test_download_url_raises_rather_than_returning_none():
    """The method is annotated `-> str`, so a caller reasonably treats the
    result as one. Returning None pushes the failure into whatever it is handed
    to — an opener, an HTTP call, a log line reading "None" — by which point
    nothing points back at the export that had no bundle.
    """
    conn = StubConnection({})  # a download response carrying no URL
    job = ExportJob(conn, SUBMITTED["job_id"], timeline_id=SUBMITTED["timeline_id"],
                    status="done")

    with pytest.raises(InvalidRequestError, match="no download URL"):
        job.download_url()


def test_every_export_failure_is_a_videodb_error():
    """The package promises `except VideodbError` catches SDK failures, and
    GenerationJob keeps that promise — a sibling raising builtins alongside it
    means the documented catch-all handles one job type and crashes on the
    other. Public surface: the types must be right at first release."""
    job = ExportJob(StubConnection(), job_id="exp_a")
    with pytest.raises(VideodbError):
        job.refresh()  # no timeline_id
    slow = StubConnection(*[{"job_id": "exp_a", "status": "rendering"}] * 5)
    running = ExportJob(slow, job_id="exp_a", timeline_id="tl-9")
    with pytest.raises(VideodbError):
        running.wait(timeout=0, poll_interval=0)


def test_a_submit_answering_id_instead_of_job_id_still_makes_a_job():
    """GenerationJob.from_data accepts either key, and endpoints have answered
    with both shapes. A submit that hard-fails AFTER the job was created costs
    the user a running export they cannot see."""
    conn = StubConnection({"id": "exp_b", "timeline_id": "tl-9", "status": "queued"})
    job = _timeline(conn).export()
    assert job.id == "exp_b"


def test_job_id_is_an_alias_for_id():
    """GenerationJob exposes both spellings; a caller moving between the two
    job types should not need to remember which one this is."""
    job = ExportJob(StubConnection(), job_id="exp_a")
    assert job.job_id == "exp_a"


def test_the_export_annotation_resolves():
    """`-> "ExportJob"` with no import in scope breaks every annotation
    resolver (typeguard, sphinx, pydantic) that calls get_type_hints on a
    public method."""
    import typing

    hints = typing.get_type_hints(Timeline.export)
    assert hints["return"].__name__ == "ExportJob"
