from videodb._constants import ApiPath


class IndexResult:
    """Result of a video.index() call.

    For async index types (e.g. face), the SDK auto-polls until completion.
    """

    def __init__(
        self,
        _connection=None,
        index_id=None,
        video_id=None,
        collection_id=None,
        name=None,
        type=None,
        status=None,
        source=None,
        config=None,
        use_for=None,
        output_url=None,
        created_at=None,
        **kwargs,
    ):
        self._connection = _connection
        self.id = index_id
        self.video_id = video_id
        self.collection_id = collection_id
        self.name = name
        self.type = type
        self.status = status
        self.source = source or {}
        self.config = config or {}
        self.use_for = use_for or []
        self.output_url = output_url
        self.created_at = created_at

    def __repr__(self):
        return (
            f"IndexResult(id={self.id}, type={self.type}, "
            f"status={self.status}, name={self.name})"
        )


class Identity:
    """A face identity within a collection's face store.

    Typically accessed via ``collection.face_store.identities.get(id)``.
    """

    def __init__(
        self,
        _connection=None,
        _collection_id=None,
        identity_id=None,
        collection_id=None,
        name=None,
        face_count=None,
        example_count=None,
        preview_faces=None,
        source_index_ids=None,
        created_at=None,
        updated_at=None,
        **kwargs,
    ):
        self._connection = _connection
        self._collection_id = _collection_id or collection_id
        self.id = identity_id
        self.collection_id = collection_id
        self.name = name
        self.face_count = face_count or 0
        self.example_count = example_count or 0
        self.representative_faces = kwargs.get("representative_faces", [])
        self.preview_faces = preview_faces or []
        self.source_index_ids = source_index_ids or []
        self.created_at = created_at
        self.updated_at = updated_at

    def _identity_path(self):
        return (
            f"{ApiPath.collection}/{self._collection_id}"
            f"/{ApiPath.store}/{ApiPath.faces}"
            f"/{ApiPath.identities}/{self.id}"
        )

    def update(self, name=None, set_representative=None):
        """Update this identity.

        :param str name: New name for the identity
        :param dict set_representative: {"face_id": "..."} to change the representative face
        :return: Updated response data
        :rtype: dict
        """
        data = {}
        if name is not None:
            data["name"] = name
        if set_representative is not None:
            data["set_representative"] = set_representative
        if not data:
            return
        response = self._connection.patch(
            path=self._identity_path(),
            data=data,
        )
        if name is not None:
            self.name = name
        return response

    def delete(self):
        """Delete this identity and unassign all its faces."""
        self._connection.delete(path=self._identity_path())

    def __repr__(self):
        return (
            f"Identity(id={self.id}, name={self.name}, "
            f"face_count={self.face_count})"
        )


class Face:
    """A single detected and indexed face record.

    Typically accessed via ``collection.face_store.faces.get(id)``.
    """

    def __init__(
        self,
        _connection=None,
        _collection_id=None,
        face_id=None,
        video_id=None,
        collection_id=None,
        identity_id=None,
        source_index_id=None,
        source=None,
        timestamp_ms=None,
        frame_url=None,
        image_url=None,
        bbox=None,
        confidence=None,
        created_at=None,
        **kwargs,
    ):
        self._connection = _connection
        self._collection_id = _collection_id or collection_id
        self.id = face_id
        self.video_id = video_id
        self.collection_id = collection_id
        self.identity_id = identity_id
        self.source_index_id = source_index_id
        self.source = source
        self.timestamp_ms = int(timestamp_ms) if timestamp_ms is not None else None
        self.frame_url = frame_url
        self.image_url = image_url
        self.bbox = bbox
        self.confidence = float(confidence) if confidence is not None else None
        self.created_at = created_at

    def delete(self):
        """Delete this face record."""
        self._connection.delete(
            path=(
                f"{ApiPath.collection}/{self._collection_id}"
                f"/{ApiPath.store}/{ApiPath.faces}"
                f"/{ApiPath.faces}/{self.id}"
            ),
        )

    def __repr__(self):
        return (
            f"Face(id={self.id}, identity_id={self.identity_id}, "
            f"confidence={self.confidence})"
        )
