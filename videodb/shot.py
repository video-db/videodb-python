"""This module contains the shot class"""


from typing import Optional
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
        self.stream = None

    def __repr__(self) -> str:
        return (
            f"Shot("
            f"video_id={self.video_id}, "
            f"video_title={self.video_title}, "
            f"start={self.start}, "
            f"end={self.end}, "
            f"text={self.text}, "
            f"search_score={self.search_score}, "
            f"stream={self.stream})"
        )

    def __getitem__(self, key):
        """Get an item from the shot object"""
        return self.__dict__[key]

    def get_stream(self) -> str:
        """Get the shot into a stream link

        :return: The stream link
        :rtype: str
        """

        if self.stream:
            return self.stream
        else:
            stream_data = self._connection.post(
                path=f"{ApiPath.video}/{self.video_id}/{ApiPath.stream}",
                data={
                    "timeline": [(self.start, self.end)],
                    "length": self.video_length,
                },
            )
            self.stream = stream_data.get("stream_link")
            return self.stream
