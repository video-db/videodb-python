"""Model-specific ``config`` objects for generation methods.

Pass one as ``config=`` or use a plain dict with the same keys. A plain dict also
works for options the service adds before the SDK lists them.
"""
from dataclasses import dataclass, fields
from typing import ClassVar, Dict, Optional, Tuple

DOCS_URL = "https://docs.videodb.io/api-reference/generation/generate_video"


@dataclass
class HeyGenConfig:
    """Options for ``generate_video(model="heygen", ...)``.

    :param str voice: Voice name, exact spelling (default ``"Warm Pro Narrator"``).
        :attr:`voices` has a starter set; every voice is listed on the docs page.
    :param str audio_id: Your audio ID to lip-sync instead of speaking ``prompt``.
        Cannot be combined with ``voice``.
    :param str talking_style: One of :attr:`talking_styles` (default ``"stable"``).
    :param str expression: One of :attr:`expressions`.
    :param bool caption: Burn in subtitles.
    :param dict background: ``{"type": "color", "value": "#FFFFFF"}``, or ``"type"``
        ``"image"`` / ``"video"`` with a public URL as ``"value"``.
    """

    voice: Optional[str] = None
    audio_id: Optional[str] = None
    talking_style: Optional[str] = None
    expression: Optional[str] = None
    caption: Optional[bool] = None
    background: Optional[Dict[str, str]] = None

    #: A starter set of voices. Any voice from the full list works; see :data:`docs`.
    voices: ClassVar[Tuple[str, ...]] = (
        "Warm Pro Narrator",
        "Chill Brian",
        "Ivy",
        "Professor Dean",
        "Calm Chloe",
        "Crisp Chloe",
        "Baritone Ben",
        "Mellow Marcus",
        "Grace Elder",
        "Expressive Evan",
        "Bold Blake",
        "Serenity",
    )
    talking_styles: ClassVar[Tuple[str, ...]] = ("stable", "expressive")
    expressions: ClassVar[Tuple[str, ...]] = ("happy",)
    background_types: ClassVar[Tuple[str, ...]] = ("color", "image", "video")
    aspect_ratios: ClassVar[Tuple[str, ...]] = ("16:9", "9:16", "4:5", "5:4", "1:1", "auto")
    resolutions: ClassVar[Tuple[str, ...]] = ("360p", "480p", "540p", "720p", "1080p")
    #: Longest script (estimated speech) or audio, in seconds.
    max_seconds: ClassVar[int] = 120
    docs: ClassVar[str] = DOCS_URL

    def to_dict(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}
