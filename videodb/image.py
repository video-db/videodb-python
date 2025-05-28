from videodb._constants import (
    ApiPath,
)


class Image:
    """Image class to interact with the Image

    :ivar str id: Unique identifier for the image
    :ivar str collection_id: ID of the collection this image belongs to 
    :ivar str name: Name of the image file
    :ivar str url: URL of the image
    """

    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self.name = kwargs.get("name", None)
        self.url = kwargs.get("url", None)

    def __repr__(self) -> str:
        return (
            f"Image("
            f"id={self.id}, "
            f"collection_id={self.collection_id}, "
            f"name={self.name}, "
            f"url={self.url})"
        )

    def generate_url(self) -> str:
        """Generate the signed url of the image.

        :raises InvalidRequestError: If the get_url fails
        :return: The signed url of the image
        :rtype: str
        """
        url_data = self._connection.post(
            path=f"{ApiPath.image}/{self.id}/{ApiPath.generate_url}",
            params={"collection_id": self.collection_id},
        )
        return url_data.get("signed_url", None)

    def delete(self) -> None:
        """Delete the image.

        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        self._connection.delete(f"{ApiPath.image}/{self.id}")


class Frame(Image):
    """Frame class to interact with video frames

    :ivar str id: Unique identifier for the frame
    :ivar str video_id: ID of the video this frame belongs to
    :ivar str scene_id: ID of the scene this frame belongs to
    :ivar str url: URL of the frame
    :ivar float frame_time: Timestamp of the frame in the video
    :ivar str description: Description of the frame contents
    """

    def __init__(
        self,
        _connection,
        id: str,
        video_id: str,
        scene_id: str,
        url: str,
        frame_time: float,
        description: str,
    ):
        super().__init__(_connection=_connection, id=id, collection_id=None, url=url)
        self.scene_id = scene_id
        self.video_id = video_id
        self.frame_time = frame_time
        self.description = description

    def __repr__(self) -> str:
        return (
            f"Frame("
            f"id={self.id}, "
            f"video_id={self.video_id}, "
            f"scene_id={self.scene_id}, "
            f"url={self.url}, "
            f"frame_time={self.frame_time}, "
            f"description={self.description})"
        )

    def to_json(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "scene_id": self.scene_id,
            "url": self.url,
            "frame_time": self.frame_time,
            "description": self.description,
        }

    def describe(self, prompt: str = None, model_name=None):
        """Describe the frame.

        :param str prompt: (optional) The prompt to use for the description
        :param str model_name: (optional) The model to use for the description
        :return: The description of the frame
        :rtype: str
        """
        description_data = self._connection.post(
            path=f"{ApiPath.video}/{self.video_id}/{ApiPath.frame}/{self.id}/{ApiPath.describe}",
            data={"prompt": prompt, "model_name": model_name},
        )
        self.description = description_data.get("description", None)
        return self.description
