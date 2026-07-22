class IndexResult:
    """Result of a ``video.index()`` call."""

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
