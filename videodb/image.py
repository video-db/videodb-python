from videodb._constants import (
    ApiPath,
)


class Image:
    def __init__(self, _connection, id: str, collection_id: str, **kwargs) -> None:
        self._connection = _connection
        self.id = id
        self.collection_id = collection_id
        self.name = kwargs.get("name", None)

    def __repr__(self) -> str:
        return (
            f"Image("
            f"id={self.id}, "
            f"collection_id={self.collection_id}, "
            f"name={self.name})"
        )

    def delete(self) -> None:
        self._connection.delete(f"{ApiPath.image}/{self.id}")
