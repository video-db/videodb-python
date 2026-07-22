import warnings

from videodb.collection import Collection
from videodb.video import Video
import videodb.search as search_module


class FakeConnection:
    def __init__(self, response=None):
        self.posts = []
        self.response = response or {"results": []}

    def post(self, path, data=None, **kwargs):
        self.posts.append({"path": path, "data": data or {}, "kwargs": kwargs})
        return self.response


def setup_function():
    search_module._RESPONSE_WARNING_EMITTED.clear()


def test_video_search_routes_stitch_rerank_options_to_legacy_endpoint_without_local_warning():
    conn = FakeConnection()
    video = Video(conn, id="video-1", collection_id="collection-1")

    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter("always")
        result = video.search(
            "find moments",
            stitch=False,
            rerank=True,
            rerank_params={"top_k": 3},
        )

    assert len(emitted) == 0
    assert result.warnings == []
    assert len(conn.posts) == 1
    assert conn.posts[0]["path"] == "video/video-1/search"
    assert conn.posts[0]["data"]["stitch"] is False
    assert conn.posts[0]["data"]["rerank"] is True
    assert conn.posts[0]["data"]["rerank_params"] == {"top_k": 3}


def test_collection_search_routes_stitch_rerank_options_to_legacy_endpoint():
    conn = FakeConnection()
    collection = Collection(conn, id="collection-1")

    collection.search(
        "find moments",
        stitch=False,
        rerank=True,
        rerank_params={"rank_fields": ["text"]},
    )

    assert len(conn.posts) == 1
    assert conn.posts[0]["path"] == "collection/collection-1/search"
    assert conn.posts[0]["data"]["stitch"] is False
    assert conn.posts[0]["data"]["rerank"] is True
    assert conn.posts[0]["data"]["rerank_params"] == {"rank_fields": ["text"]}


def test_video_search_still_routes_to_v2_when_no_legacy_params_are_present():
    conn = FakeConnection({"response_type": "shots", "results": []})
    video = Video(conn, id="video-1", collection_id="collection-1")

    video.search("find moments")

    assert len(conn.posts) == 1
    assert conn.posts[0]["path"] == "video/video-1/search/v2"
    assert conn.posts[0]["data"] == {"query": "find moments"}
