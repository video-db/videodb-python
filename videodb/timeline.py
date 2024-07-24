from typing import Union

from videodb._constants import ApiPath
from videodb.asset import VideoAsset, AudioAsset, ImageAsset, TextAsset


class Timeline(object):
    def __init__(self, connection) -> None:
        self._connection = connection
        self._timeline = []
        self.stream_url = None
        self.player_url = None

    def to_json(self) -> dict:
        timeline_json = []
        for asset in self._timeline:
            if isinstance(asset, tuple):
                overlay_start, audio_asset = asset
                asset_json = audio_asset.to_json()
                asset_json["overlay_start"] = overlay_start
                timeline_json.append(asset_json)
            else:
                timeline_json.append(asset.to_json())
        return {"timeline": timeline_json}

    def add_inline(self, asset: VideoAsset) -> None:
        """Add a video asset to the timeline

        :param VideoAsset asset: The video asset to add, :class:`VideoAsset` <VideoAsset> object
        :raises ValueError: If asset is not of type :class:`VideoAsset` <VideoAsset>
        :return: None
        :rtype: None
        """
        if not isinstance(asset, VideoAsset):
            raise ValueError("asset must be of type VideoAsset")
        self._timeline.append(asset)

    def add_overlay(
        self, start: int, asset: Union[AudioAsset, ImageAsset, TextAsset]
    ) -> None:
        """Add an overlay asset to the timeline

        :param int start: The start time of the overlay asset
        :param Union[AudioAsset, ImageAsset, TextAsset] asset: The overlay asset to add, :class:`AudioAsset <AudioAsset>`, :class:`ImageAsset <ImageAsset>`, :class:`TextAsset <TextAsset>` object
        :return: None
        :rtype: None
        """
        if (
            not isinstance(asset, AudioAsset)
            and not isinstance(asset, ImageAsset)
            and not isinstance(asset, TextAsset)
        ):
            raise ValueError(
                "asset must be of type AudioAsset, ImageAsset or TextAsset"
            )
        self._timeline.append((start, asset))

    def generate_stream(self) -> str:
        """Generate a stream url for the timeline

        :return: The stream url
        :rtype: str
        """
        stream_data = self._connection.post(
            path=f"{ApiPath.timeline}",
            data={
                "request_type": "compile",
                "timeline": self.to_json().get("timeline"),
            },
        )
        self.stream_url = stream_data.get("stream_url")
        self.player_url = stream_data.get("player_url")
        return stream_data.get("stream_url", None)
