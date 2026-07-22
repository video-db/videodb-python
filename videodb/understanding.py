class FaceDetection:
    """A single detected face occurrence in a frame."""

    def __init__(self, bbox, confidence, face_detection_id=None, timestamp_ms=None, **kwargs):
        self.face_detection_id = face_detection_id
        self.bbox = bbox
        self.confidence = float(confidence) if confidence is not None else None
        self.timestamp_ms = int(timestamp_ms) if timestamp_ms is not None else None

    def __repr__(self):
        return f"FaceDetection(bbox={self.bbox}, confidence={self.confidence})"


class SegmentResult:
    """Detection results for a single time segment / frame."""

    def __init__(self, timestamp_ms=None, frame_url=None, detections=None, **kwargs):
        self.timestamp_ms = int(timestamp_ms) if timestamp_ms is not None else None
        self.frame_url = frame_url
        self.detections = [
            FaceDetection(**d) if isinstance(d, dict) else d
            for d in (detections or [])
        ]

    def __repr__(self):
        return f"SegmentResult(timestamp_ms={self.timestamp_ms}, faces={len(self.detections)})"


class UnderstandingResult:
    """Result of a video.understand() call."""

    def __init__(
        self,
        _connection=None,
        understanding_id=None,
        video_id=None,
        collection_id=None,
        extract=None,
        status=None,
        store=None,
        config=None,
        results=None,
        **kwargs,
    ):
        self._connection = _connection
        self.id = understanding_id
        self.video_id = video_id
        self.collection_id = collection_id
        self.extract = extract or []
        self.status = status
        self.store = store
        self.config = config or {}
        self.results_raw = results or {}
        self.results = self._parse_results(results)

    @staticmethod
    def _parse_results(results):
        """Parse results from either dict format (get) or list format (create).

        Server get_understanding returns:
            {"faces": {"status": "done", "data": [segment dicts]}}
        Server create/understand returns:
            [segment dicts]
        """
        if results is None:
            return []

        # Dict format from get_understanding: {extract_type: {status, data}}
        if isinstance(results, dict):
            segments = []
            for extract_type, extract_data in results.items():
                if isinstance(extract_data, dict):
                    data = extract_data.get("data")
                    if isinstance(data, list):
                        segments.extend(data)
                elif isinstance(extract_data, list):
                    segments.extend(extract_data)
            return [
                SegmentResult(**s) if isinstance(s, dict) else s
                for s in segments
            ]

        # List format from create understanding
        if isinstance(results, list):
            return [
                SegmentResult(**r) if isinstance(r, dict) else r
                for r in results
            ]

        return []

    def to_source_dict(self) -> dict:
        """Serialize detection data for passing to video.index(source=...)."""
        return {
            "type": "faces",
            "detections": [
                {
                    "timestamp_ms": seg.timestamp_ms,
                    "frame_url": seg.frame_url,
                    "detections": [
                        {
                            "face_detection_id": d.face_detection_id,
                            "bbox": d.bbox,
                            "confidence": d.confidence,
                        }
                        for d in seg.detections
                    ],
                }
                for seg in self.results
            ],
        }

    def __repr__(self):
        return (
            f"UnderstandingResult(id={self.id}, status={self.status}, "
            f"segments={len(self.results)})"
        )
