import time
from typing import Any, Dict, List, Optional

from videodb._constants import (
    ApiPath,
    ANALYZER_TERMINAL_STATUSES,
    UNDERSTANDING_TERMINAL_STATUSES,
)

class UnderstandingAnalyzer:
    """Analyzer status and output handle for one analyzer in an understanding run."""

    def __init__(
        self,
        understanding: "Understanding",
        id: Optional[str] = None,
        name: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.understanding = understanding
        self.id = id
        self.name = name
        self.type = type
        self.status = status
        self.extra = kwargs

    def __repr__(self) -> str:
        return (
            f"UnderstandingAnalyzer("
            f"id={self.id}, "
            f"name={self.name}, "
            f"type={self.type}, "
            f"status={self.status})"
        )

    def __getitem__(self, key):
        return self.__dict__[key]

    @property
    def is_complete(self) -> bool:
        """Return True when the analyzer is in a terminal status."""
        return self.status in ANALYZER_TERMINAL_STATUSES

    @property
    def is_successful(self) -> bool:
        """Return True when the analyzer completed successfully."""
        return self.status == "done"

    def refresh(self) -> "UnderstandingAnalyzer":
        """Refresh this analyzer's status from the API."""
        analyzer = self.understanding.get_analyzer(self.name or self.id, refresh=True)
        self.id = analyzer.id
        self.name = analyzer.name
        self.type = analyzer.type
        self.status = analyzer.status
        self.extra = analyzer.extra
        return self

    def wait_until_complete(
        self,
        timeout: int = 1800,
        poll_interval: int = 10,
    ) -> "UnderstandingAnalyzer":
        """Poll this analyzer until it reaches a terminal status.

        :param int timeout: Maximum time to wait, in seconds
        :param int poll_interval: Seconds between status checks
        :raises TimeoutError: If the analyzer does not complete before timeout
        :return: This analyzer with refreshed status
        """
        deadline = time.time() + timeout
        while True:
            self.refresh()
            if self.is_complete:
                return self
            if time.time() >= deadline:
                raise TimeoutError(
                    f"Analyzer {self.name or self.id} did not complete within {timeout}s"
                )
            time.sleep(poll_interval)

    def get_output(self) -> Any:
        """Return this analyzer's output.

        The current API returns the analyzer's segments output.
        """
        identifier = self.name or self.id
        if not identifier:
            raise ValueError("Analyzer id or name is required")
        return self.understanding.get_analyzer_output(identifier)

    def to_index_source(self) -> Dict:
        """Serialize this analyzer as an index ``source`` reference.

        Sends only identifiers — the server re-fetches the analyzer's output from its
        own store, so scenes never round-trip through the client:

            for analyzer in understanding.list_analyzers():
                if analyzer.is_successful:
                    video.index(name=analyzer.name, source=analyzer)

        :raises ValueError: If the analyzer has no id or its understanding id is unknown
        """
        understanding_id = getattr(self.understanding, "id", None)
        if not understanding_id or not self.id:
            raise ValueError("analyzer source requires understanding id and analyzer id")
        # ids + type — the server's analyzer record stays the source of truth for the
        return {
            "understanding_id": understanding_id,
            "analyzer_id": self.id,
            "analyzer_type": self.type,
        }


class Understanding:
    """A video understanding run.

    Use :meth:`list_analyzers` or :meth:`get_analyzer` to inspect analyzers and
    fetch analyzer outputs.
    """

    def __init__(
        self,
        _connection,
        video_id: str,
        collection_id: Optional[str] = None,
        understanding_id: Optional[str] = None,
        id: Optional[str] = None,
        status: Optional[str] = None,
        analyzers: Optional[List[Dict[str, Any]]] = None,
        output_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        self._connection = _connection
        self.video_id = video_id
        self.collection_id = collection_id
        self.id = understanding_id or id
        self.status = status
        self.output_url = output_url
        self.extra = kwargs
        self.analyzers = [self.create_analyzer(item) for item in (analyzers or [])]

    def __repr__(self) -> str:
        return (
            f"Understanding("
            f"id={self.id}, "
            f"video_id={self.video_id}, "
            f"status={self.status}, "
            f"analyzers={len(self.analyzers)})"
        )

    def __getitem__(self, key):
        return self.__dict__[key]

    @property
    def is_complete(self) -> bool:
        """Return True when the understanding run is in a terminal status."""
        return self.status in UNDERSTANDING_TERMINAL_STATUSES

    @property
    def is_successful(self) -> bool:
        """Return True when the understanding run completed successfully."""
        return self.status == "done"

    def create_analyzer(self, data: Dict[str, Any]) -> UnderstandingAnalyzer:
        return UnderstandingAnalyzer(self, **(data or {}))

    def update_from_response(self, data: Dict[str, Any]) -> "Understanding":
        data = data or {}
        self.status = data.get("status", self.status)
        if data.get("understanding_id") or data.get("id"):
            self.id = data.get("understanding_id") or data.get("id")
        if data.get("video_id"):
            self.video_id = data.get("video_id")
        if data.get("collection_id"):
            self.collection_id = data.get("collection_id")
        if data.get("output_url"):
            self.output_url = data.get("output_url")
        if "analyzers" in data:
            self.analyzers = [self.create_analyzer(item) for item in data.get("analyzers") or []]
        return self

    def refresh(self) -> "Understanding":
        """Refresh understanding and analyzer statuses from the API."""
        data = self._connection.get(
            path=f"{ApiPath.video}/{self.video_id}/{ApiPath.understand}/{self.id}"
        )
        return self.update_from_response(data)

    def wait_until_complete(
        self,
        timeout: int = 1800,
        poll_interval: int = 10,
    ) -> "Understanding":
        """Poll this understanding until it reaches a terminal status.

        Terminal statuses are ``done`` and ``failed``.

        :param int timeout: Maximum time to wait, in seconds
        :param int poll_interval: Seconds between status checks
        :raises TimeoutError: If the run does not complete before timeout
        :return: This understanding with refreshed status
        """
        deadline = time.time() + timeout
        while True:
            self.refresh()
            if self.is_complete:
                return self
            if time.time() >= deadline:
                raise TimeoutError(f"Understanding {self.id} did not complete within {timeout}s")
            time.sleep(poll_interval)

    def list_analyzers(self) -> List[UnderstandingAnalyzer]:
        """Return analyzers in this understanding run."""
        return list(self.analyzers)

    def get_analyzer(self, name_or_id: str, refresh: bool = False) -> UnderstandingAnalyzer:
        """Return an analyzer by user-facing name or internal analyzer id.

        :param str name_or_id: Analyzer name returned by the API, or an internal id such as ``"an_..."``
        :param bool refresh: When True, fetch the latest analyzer status first
        :raises ValueError: If no analyzer matches
        :return: :class:`UnderstandingAnalyzer <UnderstandingAnalyzer>` object
        """
        if refresh:
            data = self._connection.get(
                path=f"{ApiPath.video}/{self.video_id}/{ApiPath.understand}/{self.id}",
                params={"analyzer": name_or_id},
            ) or {}
            self.status = data.get("status", self.status)
            analyzer_data = (data.get("analyzers") or [None])[0]
            if analyzer_data:
                refreshed = self.create_analyzer(analyzer_data)
                for index, analyzer in enumerate(self.analyzers):
                    if analyzer.name == refreshed.name or analyzer.id == refreshed.id:
                        self.analyzers[index] = refreshed
                        return refreshed
                self.analyzers.append(refreshed)
                return refreshed

        for analyzer in self.analyzers:
            if analyzer.name == name_or_id or analyzer.id == name_or_id:
                return analyzer
        raise ValueError(f"Analyzer not found: {name_or_id}")

    def get_analyzer_output(self, name_or_id: str) -> Any:
        """Return output for an analyzer by name or id."""
        return self._connection.get(
            path=(
                f"{ApiPath.video}/{self.video_id}/{ApiPath.understand}/{self.id}"
                f"/analyzers/{name_or_id}/output"
            )
        )

    def delete(self) -> None:
        """Delete this understanding run."""
        self._connection.delete(
            path=f"{ApiPath.video}/{self.video_id}/{ApiPath.understand}/{self.id}"
        )


def normalize_understanding_analyzers(analyzers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize analyzer payloads to the server contract.

    The public SDK accepts friendly analyzer types like ``spoken_words``. Names
    remain optional; the server assigns a unique name and id when omitted. Use
    explicit names when another analyzer references one through ``inputs``.
    """
    if not isinstance(analyzers, list) or not analyzers:
        raise ValueError("analyzers must be a non-empty list")

    normalized = []
    names = set()

    for index, analyzer in enumerate(analyzers):
        if not isinstance(analyzer, dict):
            raise ValueError(f"analyzers[{index}] must be a dict")
        if not analyzer.get("type"):
            raise ValueError(f"analyzers[{index}].type is required")

        item = dict(analyzer)
        name = item.get("name")
        if name:
            if name in names:
                raise ValueError(f"Duplicate analyzer name: {name}")
            names.add(name)

        normalized.append(item)

    return normalized
