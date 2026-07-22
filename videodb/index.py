import time

from typing import List, Optional

from videodb._constants import ApiPath, INDEX_TERMINAL_STATUSES


class FieldSchema:
    """Schema details for a single indexed field.

    :ivar str type: Data type of the field (e.g. ``"string"``, ``"string_array"``, ``"number"``, ``"text"``, ``"boolean"``)
    :ivar list groups: Field groups this field belongs to (e.g. ``["semantic", "filter"]``)
    :ivar list operators: Filter operators supported by the field (for filterable fields)
    """

    def __init__(
        self,
        type: Optional[str] = None,
        groups: Optional[List[str]] = None,
        operators: Optional[List[str]] = None,
    ) -> None:
        self.type = type
        self.groups = groups or []
        self.operators = operators or []

    def __repr__(self) -> str:
        return (
            f"FieldSchema("
            f"type={self.type}, "
            f"groups={self.groups}, "
            f"operators={self.operators})"
        )

    def __getitem__(self, key):
        return self.__dict__[key]


class IndexRecord:
    """A single indexed record (one temporal scene of an index).

    :ivar str video_id: ID of the video the record belongs to
    :ivar str understanding_id: ID of the understanding run that produced the record
    :ivar str scene_id: ID of the scene within the artifact
    :ivar float start: Start time of the scene in seconds
    :ivar float end: End time of the scene in seconds
    :ivar dict data: Indexed field values for the scene
    :ivar str segment_id: Deprecated alias of ``scene_id``
    :ivar float start_sec: Deprecated alias of ``start``
    :ivar float end_sec: Deprecated alias of ``end``
    """

    def __init__(
        self,
        video_id: Optional[str] = None,
        understanding_id: Optional[str] = None,
        scene_id: Optional[str] = None,
        start: Optional[float] = None,
        end: Optional[float] = None,
        data: Optional[dict] = None,
        segment_id: Optional[str] = None,
        start_sec: Optional[float] = None,
        end_sec: Optional[float] = None,
    ) -> None:
        self.video_id = video_id
        self.understanding_id = understanding_id
        self.scene_id = scene_id if scene_id is not None else segment_id
        self.start = start if start is not None else start_sec
        self.end = end if end is not None else end_sec
        self.data = data or {}
        self.segment_id = self.scene_id
        self.start_sec = self.start
        self.end_sec = self.end

    def __repr__(self) -> str:
        return (
            f"IndexRecord("
            f"video_id={self.video_id}, "
            f"scene_id={self.scene_id}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"data={self.data})"
        )

    def __getitem__(self, key):
        return self.__dict__[key]


class RecordPage:
    """A page of indexed records returned by :meth:`Index.records`.

    :ivar list[IndexRecord] records: Records in this page
    :ivar str next_cursor: Cursor for the next page, ``None`` if there are no more records
    """

    def __init__(
        self,
        records: Optional[List[IndexRecord]] = None,
        next_cursor: Optional[str] = None,
    ) -> None:
        self.records = records or []
        self.next_cursor = next_cursor

    def __repr__(self) -> str:
        return (
            f"RecordPage(records={len(self.records)}, next_cursor={self.next_cursor})"
        )

    def __iter__(self):
        return iter(self.records)

    def __getitem__(self, key):
        return self.records[key]


class Index:
    """Index manifest for a retrieval-ready index built from an understanding artifact.

    Note: Users should not initialize this class directly.
    Instead use :meth:`Video.index() <videodb.video.Video.index>`,
    :meth:`Video.get_index() <videodb.video.Video.get_index>`, or
    :meth:`Video.list_indexes() <videodb.video.Video.list_indexes>`.

    :ivar str index_id: Unique identifier for the index
    :ivar str video_id: ID of the video this index belongs to
    :ivar str collection_id: ID of the collection this index belongs to
    :ivar str name: User-facing name of the index
    :ivar str status: Build status of the index (e.g. ``"building"``, ``"ready"``, ``"failed"``)
    :ivar list use_for: Retrieval capabilities the index supports
        (subset of ``"semantic"``, ``"query"``, ``"aggregate"``)
    :ivar source: Source artifact reference or records the index was built from
    :ivar int record_count: Number of records in the index
    :ivar dict fields: Field groups mapping (``semantic``, ``filter``,
        ``aggregate``, ``sort``) to lists of field names
    :ivar dict field_schema: Mapping of field name to :class:`FieldSchema <FieldSchema>`
    """

    def __init__(
        self, _connection, video_id: str, collection_id: str = None, **kwargs
    ) -> None:
        self._connection = _connection
        self.video_id = video_id
        self.collection_id = collection_id
        self.update_from_response(kwargs)

    def update_from_response(self, data: dict) -> "Index":
        data = data or {}
        self.index_id = data.get("index_id") or getattr(self, "index_id", None)
        self.name = data.get("name")
        self.status = data.get("status")
        self.error = data.get("error")
        self.use_for = data.get("use_for", [])
        self.source = data.get("source")
        self.record_count = data.get("record_count")
        self.fields = data.get("fields", {})
        self.field_schema = {
            field: FieldSchema(
                type=schema.get("type"),
                groups=schema.get("groups"),
                operators=schema.get("operators"),
            )
            for field, schema in (data.get("field_schema") or {}).items()
        }
        return self

    def __repr__(self) -> str:
        return (
            f"Index("
            f"index_id={self.index_id}, "
            f"video_id={self.video_id}, "
            f"name={self.name}, "
            f"status={self.status}, "
            + (f"error={self.error}, " if self.error else "")
            + f"use_for={self.use_for}, "
            f"record_count={self.record_count})"
        )

    def __getitem__(self, key):
        return self.__dict__[key]

    @property
    def is_complete(self) -> bool:
        """Return True when the index build is in a terminal status."""
        return self.status in INDEX_TERMINAL_STATUSES

    @property
    def is_successful(self) -> bool:
        """Return True when the index build completed successfully."""
        return self.status == "ready"

    def refresh(self) -> "Index":
        """Refresh the index manifest and build status from the API."""
        data = self._connection.get(
            path=f"{ApiPath.video}/{self.video_id}/{ApiPath.indexes}/{self.index_id}",
            params={"collection_id": self.collection_id}
            if self.collection_id
            else None,
        )
        return self.update_from_response(data)

    def wait_until_complete(
        self,
        timeout: int = 1800,
        poll_interval: int = 10,
    ) -> "Index":
        """Poll this index until it reaches a terminal status.

        Terminal statuses are ``ready`` and ``failed``.

        :param int timeout: Maximum time to wait, in seconds
        :param int poll_interval: Seconds between status checks
        :raises TimeoutError: If the build does not complete before timeout
        :return: This index with refreshed status
        """
        deadline = time.time() + timeout
        while True:
            self.refresh()
            if self.is_complete:
                return self
            if time.time() >= deadline:
                raise TimeoutError(f"Index {self.index_id} did not complete within {timeout}s")
            time.sleep(poll_interval)

    def records(self, limit: int = 20, cursor: Optional[str] = None) -> RecordPage:
        """Preview the records stored in the index.

        Intended for inspection and debugging. Records are paginated via a cursor.

        :param int limit: (optional) Maximum number of records to return (default: 20)
        :param str cursor: (optional) Cursor returned by a previous page to fetch the next page
        :return: A page of indexed records, :class:`RecordPage <RecordPage>` object
        :rtype: :class:`videodb.index.RecordPage`
        """
        params = {"limit": limit, "collection_id": self.collection_id}
        if cursor is not None:
            params["cursor"] = cursor
        records_data = self._connection.get(
            path=f"{ApiPath.video}/{self.video_id}/{ApiPath.indexes}/{self.index_id}/{ApiPath.records}",
            params={key: value for key, value in params.items() if value is not None},
        )
        if not records_data:
            return RecordPage()
        records = [
            IndexRecord(
                video_id=record.get("video_id"),
                understanding_id=record.get("understanding_id"),
                scene_id=record.get("scene_id"),
                start=record.get("start"),
                end=record.get("end"),
                data=record.get("data"),
                segment_id=record.get("segment_id"),
                start_sec=record.get("start_sec"),
                end_sec=record.get("end_sec"),
            )
            for record in records_data.get("records", [])
        ]
        return RecordPage(records=records, next_cursor=records_data.get("next_cursor"))

    def delete(self) -> None:
        """Delete the index.

        Removes the index's retrieval structures. It does not delete the original
        video or stored understanding artifacts.

        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        self._connection.delete(
            path=f"{ApiPath.video}/{self.video_id}/{ApiPath.indexes}/{self.index_id}",
            params={"collection_id": self.collection_id}
            if self.collection_id
            else None,
        )
