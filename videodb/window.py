"""Metadata for server-resolved semantic-search windows (no client fallback)."""

from dataclasses import asdict, dataclass, field, fields
from typing import Any, Dict, List, Optional


@dataclass
class WindowInfo:
    """How a returned interval was formed; coverage is hit coverage, not recall."""

    level: Optional[str] = None
    level_seconds: Optional[float] = None
    merged_from: int = 0
    coverage: float = 0.0
    seconds: float = 0.0
    hit_scene_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, value: Optional[Dict[str, Any]]) -> Optional["WindowInfo"]:
        if value is None:
            return None
        names = {item.name for item in fields(cls)}
        return cls(**{key: item for key, item in value.items() if key in names})

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
