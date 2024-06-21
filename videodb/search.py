from abc import ABC, abstractmethod
from videodb._utils._video import play_stream
from videodb._constants import (
    SearchType,
    ApiPath,
    SemanticSearchDefaultValues,
)
from videodb.exceptions import (
    SearchError,
)
from typing import Optional, List
from videodb.shot import Shot


class SearchResult:
    def __init__(self, _connection, **kwargs):
        self._connection = _connection
        self.shots = []
        self.stream_url = None
        self.player_url = None
        self.collection_id = "default"
        self._results = kwargs.get("results", [])
        self._format_results()

    def _format_results(self):
        for result in self._results:
            self.collection_id = result.get("collection_id")
            for doc in result.get("docs"):
                self.shots.append(
                    Shot(
                        self._connection,
                        result.get("video_id"),
                        result.get("length"),
                        result.get("title"),
                        doc.get("start"),
                        doc.get("end"),
                        doc.get("text"),
                        doc.get("score"),
                    )
                )

    def __repr__(self) -> str:
        return (
            f"SearchResult("
            f"collection_id={self.collection_id}, "
            f"stream_url={self.stream_url}, "
            f"player_url={self.player_url}, "
            f"shots={self.shots})"
        )

    def get_shots(self) -> List[Shot]:
        return self.shots

    def compile(self) -> str:
        """Compile the search result shots into a stream url

        :raises SearchError: If no shots are found in the search results
        :return: The stream url
        :rtype: str
        """
        if self.stream_url:
            return self.stream_url
        elif self.shots:
            compile_data = self._connection.post(
                path=f"{ApiPath.compile}",
                data=[
                    {
                        "video_id": shot.video_id,
                        "collection_id": self.collection_id,
                        "shots": [(shot.start, shot.end)],
                    }
                    for shot in self.shots
                ],
            )
            self.stream_url = compile_data.get("stream_url")
            self.player_url = compile_data.get("player_url")
            return self.stream_url

        else:
            raise SearchError("No shots found in search results to compile")

    def play(self) -> str:
        """Generate a stream url for the shot and open it in the default browser

        :return: The stream url
        :rtype: str
        """
        self.compile()
        return play_stream(self.stream_url)


class Search(ABC):
    """Search interface inside video or collection"""

    @abstractmethod
    def search_inside_video(self, *args, **kwargs):
        pass

    @abstractmethod
    def search_inside_collection(self, *args, **kwargs):
        pass


class SemanticSearch(Search):
    def __init__(self, _connection):
        self._connection = _connection

    def search_inside_video(
        self,
        video_id: str,
        query: str,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[float] = None,
        dynamic_score_percentage: Optional[float] = None,
        **kwargs,
    ):
        search_data = self._connection.post(
            path=f"{ApiPath.video}/{video_id}/{ApiPath.search}",
            data={
                "index_type": SearchType.semantic,
                "query": query,
                "score_threshold": score_threshold
                or SemanticSearchDefaultValues.score_threshold,
                "result_threshold": result_threshold
                or SemanticSearchDefaultValues.result_threshold,
                "dynamic_score_percentage": dynamic_score_percentage,
                **kwargs,
            },
        )
        return SearchResult(self._connection, **search_data)

    def search_inside_collection(
        self,
        collection_id: str,
        query: str,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[float] = None,
        dynamic_score_percentage: Optional[float] = None,
        **kwargs,
    ):
        search_data = self._connection.post(
            path=f"{ApiPath.collection}/{collection_id}/{ApiPath.search}",
            data={
                "index_type": SearchType.semantic,
                "query": query,
                "score_threshold": score_threshold
                or SemanticSearchDefaultValues.score_threshold,
                "result_threshold": result_threshold
                or SemanticSearchDefaultValues.result_threshold,
                "dynamic_score_percentage": dynamic_score_percentage,
                **kwargs,
            },
        )
        return SearchResult(self._connection, **search_data)


class KeywordSearch(Search):
    def __init__(self, _connection):
        self._connection = _connection

    def search_inside_video(
        self,
        video_id: str,
        query: str,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[float] = None,
        dynamic_score_percentage: Optional[float] = None,
        **kwargs,
    ):
        search_data = self._connection.post(
            path=f"{ApiPath.video}/{video_id}/{ApiPath.search}",
            data={
                "index_type": SearchType.keyword,
                "query": query,
                "score_threshold": score_threshold,
                "result_threshold": result_threshold,
            },
        )
        return SearchResult(self._connection, **search_data)

    def search_inside_collection(self, **kwargs):
        raise NotImplementedError("Keyword search will be implemented in the future")


class SceneSearch(Search):
    def __init__(self, _connection):
        self._connection = _connection

    def search_inside_video(
        self,
        video_id: str,
        query: str,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[float] = None,
        dynamic_score_percentage: Optional[float] = None,
        **kwargs,
    ):
        search_data = self._connection.post(
            path=f"{ApiPath.video}/{video_id}/{ApiPath.search}",
            data={
                "index_type": SearchType.scene,
                "query": query,
                "score_threshold": score_threshold,
                "result_threshold": result_threshold,
                "dynamic_score_percentage": dynamic_score_percentage,
                **kwargs,
            },
        )
        return SearchResult(self._connection, **search_data)

    def search_inside_collection(self, **kwargs):
        raise NotImplementedError("Scene search will be implemented in the future")


search_type = {
    SearchType.semantic: SemanticSearch,
    SearchType.keyword: KeywordSearch,
    SearchType.scene: SceneSearch,
}


class SearchFactory:
    def __init__(self, _connection):
        self._connection = _connection

    def get_search(self, type: str):
        if type not in search_type:
            raise SearchError(
                f"Invalid search type: {type}. Valid search types are: {list(search_type.keys())}"
            )
        return search_type[type](self._connection)
