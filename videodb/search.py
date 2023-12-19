from abc import ABC, abstractmethod
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
        self.text_summary = None
        self.stream = None
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

    def get_shots(self) -> List[Shot]:
        return self.shots

    def compile(self) -> str:
        """Compile the search result shots into a stream link

        :raises SearchError: If no shots are found in the search results
        :return: The stream link
        :rtype: str
        """
        if self.stream:
            return self.stream
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
            self.stream = compile_data.get("stream_link")
            return self.stream

        else:
            raise SearchError("No shots found in search results to compile")


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
        score_threshold: Optional[int] = None,
        dynamic_score_percentage: Optional[int] = None,
    ):
        search_data = self._connection.post(
            path=f"{ApiPath.video}/{video_id}/{ApiPath.search}",
            data={
                "type": SearchType.semantic,
                "query": query,
                "score_threshold": score_threshold
                or SemanticSearchDefaultValues.score_threshold,
                "result_threshold": result_threshold
                or SemanticSearchDefaultValues.result_threshold,
            },
        )
        return SearchResult(self._connection, **search_data)

    def search_inside_collection(
        self,
        collection_id: str,
        query: str,
        result_threshold: Optional[int] = None,
        score_threshold: Optional[int] = None,
        dynamic_score_percentage: Optional[int] = None,
    ):
        search_data = self._connection.post(
            path=f"{ApiPath.collection}/{collection_id}/{ApiPath.search}",
            data={
                "type": SearchType.semantic,
                "query": query,
                "score_threshold": score_threshold
                or SemanticSearchDefaultValues.score_threshold,
                "result_threshold": result_threshold
                or SemanticSearchDefaultValues.result_threshold,
            },
        )
        return SearchResult(self._connection, **search_data)


search_type = {SearchType.semantic: SemanticSearch}


class SearchFactory:
    def __init__(self, _connection):
        self._connection = _connection

    def get_search(self, type: str):
        if type not in search_type:
            raise SearchError(
                f"Invalid search type: {type}. Valid search types are: {list(search_type.keys())}"
            )
        return search_type[type](self._connection)
