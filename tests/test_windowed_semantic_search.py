"""Thin native window contract. No runtime patch or network dependencies."""

from copy import deepcopy

import pytest
from videodb import WindowInfo
from videodb.collection import Collection
from videodb.search import SearchResult
from videodb.video import Video


class FakeConnection:
    def __init__(self, response=None):
        self.calls = []
        self.response = response or {"results": []}

    def post(self, path, data):
        self.calls.append((path, deepcopy(data)))
        return deepcopy(self.response)


@pytest.mark.parametrize("cls,scope", [(Collection, "collection"), (Video, "video")])
def test_no_window_snapshot(cls, scope):
    conn = FakeConnection()
    obj = cls(conn, id="test", **({"collection_id": "c"} if cls is Video else {}))
    result = obj.semantic_search("tap", ["episodes"], 10, 0.2, [], ["source"], ["idx"])
    assert conn.calls == [
        (
            f"{scope}/test/semantic-search",
            {
                "query": "tap",
                "index_names": ["episodes"],
                "index_ids": ["idx"],
                "top_k": 10,
                "score_threshold": 0.2,
                "filter": [],
                "return_fields": ["source"],
            },
        )
    ]
    assert result.window_plan is None


@pytest.mark.parametrize(
    "window", ["moment", "span", "session", "auto", {"min_seconds": 10, "max_seconds": 20}]
)
@pytest.mark.parametrize("cls,scope", [(Collection, "collection"), (Video, "video")])
def test_window_sent_once_without_fallback(window, cls, scope):
    conn = FakeConnection()
    result = cls(conn, id="test", **({"collection_id": "c"} if cls is Video else {})).semantic_search(
        "tap", window=window
    )
    assert len(conn.calls) == 1
    assert conn.calls[0][0] == f"{scope}/test/semantic-search"
    assert conn.calls[0][1]["window"] == window
    assert result.window_plan is None  # An older server cannot be mistaken for native support.


def test_native_grouped_response_and_rank():
    info = {
        "level": "moment",
        "level_seconds": 5,
        "merged_from": 2,
        "seconds": 8,
        "coverage": 0.75,
        "hit_scene_ids": ["s1", "s2"],
        "future_field": "ignored",
    }
    doc = {
        "start": 0,
        "end": 8,
        "text": "tap",
        "score": 0.9,
        "window": info,
        "metadata": {"source": "epic"},
        "scene_index_id": "idx",
        "scene_index_name": "episodes",
    }
    groups = [
        {"collection_id": "c", "video_id": vid, "length": 300, "title": "Kitchen", "docs": [doc]}
        for vid in ["a", "b", "a"]
    ]
    conn = FakeConnection({"results": groups, "window_plan": {"level": "moment", "how": "explicit"}})
    result = Collection(conn, "c").semantic_search("tap", window="moment")
    assert [s.video_id for s in result.shots] == ["a", "b", "a"]
    assert result.window_plan == {"level": "moment", "how": "explicit"}
    shot = result.shots[0]
    assert isinstance(shot.window, WindowInfo)
    assert shot.window.hit_scene_ids == ["s1", "s2"]
    assert shot.window.to_dict()["merged_from"] == 2
    assert shot.metadata == {"source": "epic"}
    assert shot.scene_index_id == "idx" and shot.video_title == "Kitchen"
    assert shot.search_score == 0.9 and len(conn.calls) == 1


def test_old_shots_and_warnings():
    with pytest.warns(UserWarning, match="window metadata unavailable"):
        result = SearchResult(
            FakeConnection(),
            results=[{"video_id": "a", "docs": [{"start": 0, "end": 3}]}],
            warnings=[{"code": "window_test_warning", "message": "window metadata unavailable"}],
        )
    assert result.shots[0].window is None
    assert result.window_plan is None


def test_keyword_only_parameter():
    with pytest.raises(TypeError):
        Collection(FakeConnection(), "c").semantic_search("q", None, 10, None, None, None, None, "moment")
