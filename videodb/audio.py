from videodb._constants import (
    ApiPath,
)


class Audio:
    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
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

    def delete(self) -> None:
        self._connection.delete(f"{ApiPath.audio}/{self.id}")
