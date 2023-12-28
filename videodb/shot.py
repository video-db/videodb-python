"""This module contains the shot class"""


from typing import Optional
from videodb._utils._video import play_stream
from videodb._constants import (
    ApiPath,
)


class Shot:
    """A shot is a part of a video that contains a specific scene"""

    def __init__(
        self,
        _connection,
        video_id: str,
        video_length: float,
        video_title: str,
        start: float,
        end: float,
        text: Optional[str] = None,
        search_score: Optional[int] = None,
    ) -> None:
        self._connection = _connection
        self.video_id = video_id
        self.video_length = video_length
        self.video_title = video_title
        self.start = start
        self.end = end
        self.text = text
        self.search_score = search_score
        self.stream_url = None
        self.player_url = None

    def __repr__(self) -> str:
        return (
            f"Shot("
            f"video_id={self.video_id}, "
            f"video_title={self.video_title}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"text={self.text}, "
            f"search_score={self.search_score}, "
            f"stream_url={self.stream_url}, "
            f"player_url={self.player_url})"
        )

    def __getitem__(self, key):
        """Get an item from the shot object"""
        return self.__dict__[key]

    def generate_stream(self) -> str:
        """Generate a stream url for the shot

        :return: The stream url
        :rtype: str
        """

        if self.stream_url:
            return self.stream_url
        else:
            stream_data = self._connection.post(
                path=f"{ApiPath.video}/{self.video_id}/{ApiPath.stream}",
                data={
                    "timeline": [(self.start, self.end)],
                    "length": self.video_length,
                },
            )
            self.stream_url = stream_data.get("stream_url")
            self.player_url = stream_data.get("player_url")
            return self.stream_url

    def play(self) -> str:
        """Generate a stream url for the shot and open it in the default browser/ notebook

        :return: The stream url
        :rtype: str
        """
        self.generate_stream()
        return play_stream(self.stream_url)
