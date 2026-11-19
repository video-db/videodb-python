from unittest.mock import Mock

import pytest

from videodb.exceptions import JobTimeoutError, RequestTimeoutError
from videodb.understanding import Understanding


@pytest.mark.parametrize("analyzer_wait", [False, True])
@pytest.mark.parametrize("base_url", ["https://api.dev.videodb.io/", "https://api.videodb.io"])
@pytest.mark.parametrize("output_url", [None, "https://status.example.test/run"])
def test_timeout_carries_parent_run_handle(analyzer_wait, base_url, output_url):
    connection = Mock(base_url=base_url)
    response = {
        "status": "running",
        "analyzers": [{"id": "an_1", "name": "scene", "status": "running"}],
    }
    connection.get.return_value = response
    understanding = Understanding(
        connection,
        video_id="v_1",
        understanding_id="und_1",
        output_url=output_url,
        analyzers=response["analyzers"],
    )
    target = understanding.get_analyzer("scene") if analyzer_wait else understanding

    with pytest.raises(JobTimeoutError) as caught:
        target.wait_until_complete(timeout=0)

    error = caught.value
    expected_url = output_url or f"{base_url.rstrip('/')}/video/v_1/understand/und_1"
    assert error.job_id == "und_1"
    assert error.output_url == expected_url
    assert expected_url in str(error)
    assert error.response == response
    assert isinstance(error, TimeoutError)
    assert isinstance(error, RequestTimeoutError)
    connection.get.assert_called_once()

    response["status"] = "done"
    response["analyzers"][0]["status"] = "done"
    assert target.wait_until_complete(timeout=0) is target
