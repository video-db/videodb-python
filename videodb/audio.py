from videodb._constants import (
    ApiPath,
)


class Audio:
    """Audio class to interact with the Audio

    :ivar str id: Unique identifier for the audio
    :ivar str collection_id: ID of the collection this audio belongs to
    :ivar str name: Name of the audio file
    :ivar float length: Duration of the audio in seconds
    """

    def __init__(
        self, _connection, id: str, collection_id: str, **kwargs
    ) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self.name = kwargs.get("name", None)
        self.length = kwargs.get("length", None)

    def __repr__(self) -> str:
        return (
            f"Audio("
            f"id={self.id}, "
            f"collection_id={self.collection_id}, "
            f"name={self.name}, "
            f"length={self.length})"
        )

    def generate_url(self) -> str:
        """Generate the signed url of the audio.

        :raises InvalidRequestError: If the get_url fails
        :return: The signed url of the audio
        :rtype: str
        """
        url_data = self._connection.post(
            path=f"{ApiPath.audio}/{self.id}/{ApiPath.generate_url}",
            params={"collection_id": self.collection_id},
        )
        return url_data.get("signed_url", None)

    def delete(self) -> None:
        """Delete the audio.

        :raises InvalidRequestError: If the delete fails
        :return: None if the delete is successful
        :rtype: None
        """
        self._connection.delete(f"{ApiPath.audio}/{self.id}")
