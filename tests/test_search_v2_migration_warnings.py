import pytest

import videodb.search as search_module
from videodb.collection import Collection
from videodb.exceptions import SearchError
from videodb.video import Video


WARNING = {
    "code": "search_v2_migration_dual_read",
    "message": "search() now uses Search V2 and may also check older indexes during migration.",
    "docs": [{"label": "Search V2 search", "url": "https://example.test/search"}],
}
ASK_WARNING = {
    "code": "ask_requires_search_v2_index",
    "message": "ask() uses Search V2 indexes only.",
    "docs": [{"label": "Ask", "url": "https://example.test/ask"}],
}
SEMANTIC_WARNING = {
    "code": "semantic_search_v2_migration_dual_read",
    "message": "semantic_search() may also check older indexes during migration.",
    "docs": [{"label": "Semantic search", "url": "https://example.test/semantic"}],
}


class FakeConnection:
    def __init__(self):
        self.calls = []

    def post(self, path, data=None, **kwargs):
        self.calls.append((path, data or {}))
        if path == "compile":
            return {
                "stream_url": "https://stream.example.test/compiled.m3u8",
                "player_url": "https://player.example.test/watch?v=compiled",
            }
        if path.endswith("/ask"):
            return {"answer": "I do not have enough information to answer.", "sources": [], "warnings": [ASK_WARNING]}
        if path.endswith("/semantic-search"):
            return {"results": _results("semantic"), "warnings": [SEMANTIC_WARNING]}
        if path.endswith("/query"):
            return {"results": _results("query"), "warnings": [WARNING]}
        if path.endswith("/aggregate"):
            return {"results": [{"label": "object", "count": 2}], "warnings": [WARNING]}
        if path.endswith("/search/v2"):
            if (data or {}).get("mode") == "deepsearch":
                return {"response_type": "deepsearch", "results": _results("deepsearch"), "warnings": [WARNING]}
            return {"response_type": "shots", "results": _results("v2"), "warnings": [WARNING]}
        if path.endswith("/search"):
            return {"results": _results("legacy")}
        raise AssertionError(f"unexpected path: {path}")


class FakeCollectionConnection(FakeConnection):
    pass


def _results(text):
    return [
        {
            "collection_id": "c1",
            "video_id": "v1",
            "length": 30,
            "title": "video",
            "docs": [{"start": 1, "end": 3, "text": text, "score": 0.8}],
        }
    ]


@pytest.fixture(autouse=True)
def reset_warning_state():
    search_module._LEGACY_SEARCH_WARNING_EMITTED.clear()
    yield
    search_module._LEGACY_SEARCH_WARNING_EMITTED.clear()


def test_search_v2_server_warnings_are_emitted_and_exposed():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"search\(\) now uses Search V2") as emitted:
        response = video.search("find cars", filter={"legacy_key": "legacy_value"})

    assert len(emitted) == 1
    assert conn.calls[-1] == (
        "video/v1/search/v2",
        {"query": "find cars", "filter": {"legacy_key": "legacy_value"}},
    )
    assert response.warnings == [WARNING]
    assert response.results.warnings == [WARNING]
    assert response.shots[0].text == "v2"


def test_deepsearch_server_warnings_are_emitted_and_exposed_on_search_response():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"search\(\) now uses Search V2"):
        response = video.search("find cars", mode="deepsearch")

    assert conn.calls[-1] == ("video/v1/search/v2", {"query": "find cars", "mode": "deepsearch"})
    assert response.response_type == "deepsearch"
    assert response.warnings == [WARNING]
    assert response.results.warnings == [WARNING]


def test_ask_server_warnings_are_emitted_and_exposed_on_ask_response():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"ask\(\) uses Search V2 indexes only"):
        response = video.ask("what happened?")

    assert conn.calls[-1] == (
        "video/v1/ask",
        {"question": "what happened?", "top_k": 15, "mode": "default", "include_sources": False},
    )
    assert response.answer == "I do not have enough information to answer."
    assert response.warnings == [ASK_WARNING]


def test_search_response_compile_delegates_for_shots():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"search\(\) now uses Search V2"):
        response = video.search("find cars")

    assert response.compile() == "https://stream.example.test/compiled.m3u8"
    assert conn.calls[-1] == (
        "compile",
        [{"video_id": "v1", "collection_id": "c1", "shots": [(1, 3)]}],
    )
    assert response.results.stream_url == "https://stream.example.test/compiled.m3u8"


def test_search_response_play_delegates_for_shots(monkeypatch):
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")
    played = []

    monkeypatch.setattr(search_module, "play_stream", lambda url: played.append(url) or f"played:{url}")
    with pytest.warns(UserWarning, match=r"search\(\) now uses Search V2"):
        response = video.search("find cars")

    assert response.play() == "played:https://stream.example.test/compiled.m3u8"
    assert played == ["https://stream.example.test/compiled.m3u8"]


def test_search_response_embed_code_delegates_for_deepsearch():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"search\(\) now uses Search V2"):
        response = video.search("find cars", mode="deepsearch")

    html = response.get_embed_code(width="640", height=360, title="Result", allow_fullscreen=False)
    assert response.response_type == "deepsearch"
    assert 'src="https://player.example.test/embed?v=compiled"' in html
    assert 'width="640"' in html
    assert 'height="360"' in html
    assert 'title="Result"' in html
    assert "allowfullscreen" not in html


def test_search_response_media_helpers_raise_for_non_shot_response():
    response = search_module.SearchResponse(
        FakeConnection(),
        response_type="aggregate",
        results=[{"label": "car", "count": 2}],
    )

    with pytest.raises(SearchError, match="does not contain shot results"):
        response.compile()
    with pytest.raises(SearchError, match="does not contain shot results"):
        response.play()
    with pytest.raises(SearchError, match="does not contain shot results"):
        response.get_embed_code()


def test_semantic_search_accepts_plural_selectors_emits_and_exposes_warnings():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"semantic_search\(\) may also check older indexes"):
        response = video.semantic_search("find cars", index_names=["scene"], index_ids=["idx-v2"])

    assert conn.calls[-1] == (
        "video/v1/semantic-search",
        {
            "query": "find cars",
            "index_names": ["scene"],
            "index_ids": ["idx-v2"],
            "top_k": 10,
            "score_threshold": None,
            "filter": None,
            "return_fields": None,
        },
    )
    assert response.warnings == [SEMANTIC_WARNING]
    assert response.shots[0].text == "semantic"


def test_semantic_search_rejects_singular_selectors_in_sdk_signature():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.raises(TypeError, match="unexpected keyword argument 'index_name'"):
        video.semantic_search("find cars", index_name="scene")
    with pytest.raises(TypeError, match="unexpected keyword argument 'index_id'"):
        video.semantic_search("find cars", index_id="idx-old")
    assert conn.calls == []


def test_query_supports_singular_index_name_emits_and_exposes_warnings():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"search\(\) now uses Search V2"):
        response = video.query(index_name="scene")

    assert conn.calls[-1] == (
        "video/v1/query",
        {
            "index_name": "scene",
            "index_id": None,
            "filter": None,
            "limit": 100,
            "return_fields": None,
            "sort": None,
        },
    )
    assert response.warnings == [WARNING]
    assert response.shots[0].text == "query"


def test_query_supports_singular_index_id():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"search\(\) now uses Search V2"):
        response = video.query(index_id="idx-v2")

    assert conn.calls[-1][0] == "video/v1/query"
    assert conn.calls[-1][1]["index_name"] is None
    assert conn.calls[-1][1]["index_id"] == "idx-v2"
    assert response.warnings == [WARNING]


def test_query_rejects_plural_selectors_in_sdk_signature():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.raises(TypeError, match="unexpected keyword argument 'index_ids'"):
        video.query(index_ids=["idx-v2"])
    assert conn.calls == []


def test_aggregate_keeps_singular_index_name_emits_and_returns_raw_warning_payload():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"search\(\) now uses Search V2"):
        response = video.aggregate(index_name="scene")

    assert conn.calls[-1] == (
        "video/v1/aggregate",
        {
            "index_name": "scene",
            "index_id": None,
            "filter": None,
            "group_by": None,
            "metric": "count",
            "limit": 100,
            "sort": None,
        },
    )
    assert response["warnings"] == [WARNING]


def test_aggregate_keeps_singular_index_id():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"search\(\) now uses Search V2"):
        response = video.aggregate(index_id="idx-v2")

    assert conn.calls[-1][0] == "video/v1/aggregate"
    assert conn.calls[-1][1]["index_name"] is None
    assert conn.calls[-1][1]["index_id"] == "idx-v2"
    assert response["warnings"] == [WARNING]


def test_search_index_id_routes_video_to_legacy_with_python_warning_and_scene_index_id_mapping():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match="This search used legacy search because legacy parameters were provided") as emitted:
        response = video.search("find cars", index_id="old-scene-index")

    assert len(emitted) == 1
    assert conn.calls[-1][0] == "video/v1/search"
    assert conn.calls[-1][1]["scene_index_id"] == "old-scene-index"
    assert response.warnings == []
    assert response.shots[0].text == "legacy"


def test_search_index_id_routes_collection_to_legacy_with_python_warning_and_scene_index_id_mapping():
    conn = FakeCollectionConnection()
    collection = Collection(conn, id="c1")

    with pytest.warns(UserWarning, match="This search used legacy search because legacy parameters were provided"):
        response = collection.search("find cars", index_id="old-scene-index")

    assert conn.calls[-1][0] == "collection/c1/search"
    assert conn.calls[-1][1]["scene_index_id"] == "old-scene-index"
    assert response.warnings == []


def test_explicit_legacy_search_warns_once_and_uses_old_endpoint():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.warns(UserWarning, match=r"legacy_search\(\) searches older spoken-word and scene indexes only") as emitted:
        video.legacy_search("find cars")
        video.legacy_search("find people")

    assert len(emitted) == 1
    assert [call[0] for call in conn.calls] == ["video/v1/search", "video/v1/search"]


def test_search_rejects_mixed_legacy_and_v2_params_before_http():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.raises(ValueError, match="Cannot mix legacy search parameters with Search V2 parameters"):
        video.search("find cars", index_id="old-scene-index", top_k=5)
    assert conn.calls == []


def test_search_rejects_index_selectors_before_http():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.raises(ValueError, match=r"search\(\) chooses indexes automatically"):
        video.search("find cars", index_names=["scene"])
    with pytest.raises(ValueError, match=r"search\(\) chooses indexes automatically"):
        video.search("find cars", index_ids=["idx-v2"])
    assert conn.calls == []


def test_search_rejects_internal_deepsearch_config_before_http():
    conn = FakeConnection()
    video = Video(conn, id="v1", collection_id="c1")

    with pytest.raises(ValueError, match=r"deepsearch_config is not a public search\(\) option"):
        video.search("find cars", deepsearch_config={"internal": True})
    assert conn.calls == []
