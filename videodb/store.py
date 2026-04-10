from typing import Optional, List

from videodb._constants import ApiPath
from videodb.face import Identity, Face


class IdentityManager:
    """Manager for face identity operations within a FaceStore.

    Access via ``collection.face_store.identities``.
    """

    def __init__(self, _connection, _collection_id):
        self._connection = _connection
        self._collection_id = _collection_id

    def _path(self, *parts):
        segments = [
            ApiPath.collection, self._collection_id,
            ApiPath.store, ApiPath.faces, ApiPath.identities,
        ]
        segments.extend(parts)
        return "/".join(segments)

    def list(self, named: Optional[bool] = None) -> List[Identity]:
        """List all identities in the face store.

        :param bool named: Filter by named (True) or unnamed (False) identities
        :return: List of :class:`Identity <Identity>` objects
        :rtype: List[:class:`videodb.face.Identity`]
        """
        params = {}
        if named is not None:
            params["named"] = str(named).lower()

        response = self._connection.get(path=self._path(), params=params)
        if not response:
            return []
        return [
            Identity(
                _connection=self._connection,
                _collection_id=self._collection_id,
                **ident,
            )
            for ident in response.get("identities", [])
        ]

    def get(self, identity_id: str) -> Optional[Identity]:
        """Get an identity by ID.

        :param str identity_id: The identity ID
        :return: :class:`Identity <Identity>` object
        :rtype: :class:`videodb.face.Identity`
        """
        response = self._connection.get(path=self._path(identity_id))
        if not response:
            return None
        return Identity(
            _connection=self._connection,
            _collection_id=self._collection_id,
            **response,
        )

    def update(
        self,
        identity_id: str,
        name: Optional[str] = None,
        set_representative: Optional[dict] = None,
    ) -> Optional[dict]:
        """Update an identity.

        :param str identity_id: The identity ID
        :param str name: New name for the identity
        :param dict set_representative: {"face_id": "..."} to change representative
        :return: Response data
        :rtype: dict
        """
        data = {}
        if name is not None:
            data["name"] = name
        if set_representative is not None:
            data["set_representative"] = set_representative
        if not data:
            return None
        return self._connection.patch(path=self._path(identity_id), data=data)

    def delete(self, identity_id: str) -> None:
        """Delete an identity and unassign all its faces.

        :param str identity_id: The identity ID to delete
        """
        self._connection.delete(path=self._path(identity_id))

    def merge(
        self,
        source_ids: List[str],
        target_name: Optional[str] = None,
    ) -> Optional[Identity]:
        """Merge multiple identities into one.

        The identity with the highest face_count is kept as the target.

        :param list source_ids: List of identity IDs to merge (min 2)
        :param str target_name: Name for the merged identity
        :return: :class:`Identity <Identity>` of the merged result
        :rtype: :class:`videodb.face.Identity`
        """
        data = {"source_ids": source_ids}
        if target_name is not None:
            data["target_name"] = target_name

        response = self._connection.post(
            path=self._path(ApiPath.merge), data=data
        )
        if not response:
            return None
        return Identity(
            _connection=self._connection,
            _collection_id=self._collection_id,
            **response,
        )

    def split(
        self,
        identity_id: str,
        face_ids: List[str],
        new_identity_name: Optional[str] = None,
    ) -> Optional[dict]:
        """Split faces off an identity into a new one.

        :param str identity_id: Source identity ID
        :param list face_ids: Face IDs to split off
        :param str new_identity_name: Name for the new identity (optional)
        :return: New identity data if new_identity_name was provided
        :rtype: dict
        """
        data = {"face_ids": face_ids}
        if new_identity_name is not None:
            data["new_identity_name"] = new_identity_name
        return self._connection.post(
            path=self._path(identity_id, ApiPath.split), data=data
        )


class FaceManager:
    """Manager for face record operations within a FaceStore.

    Access via ``collection.face_store.faces``.
    """

    def __init__(self, _connection, _collection_id):
        self._connection = _connection
        self._collection_id = _collection_id

    def _path(self, *parts):
        segments = [
            ApiPath.collection, self._collection_id,
            ApiPath.store, ApiPath.faces, ApiPath.faces,
        ]
        segments.extend(parts)
        return "/".join(segments)

    def list(
        self,
        video_id: Optional[str] = None,
        identity_id: Optional[str] = None,
        source_index_id: Optional[str] = None,
    ) -> List[Face]:
        """List face records.

        :param str video_id: Filter by video ID
        :param str identity_id: Filter by identity ID
        :param str source_index_id: Filter by source index ID
        :return: List of :class:`Face <Face>` objects
        :rtype: List[:class:`videodb.face.Face`]
        """
        params = {}
        if video_id is not None:
            params["video_id"] = video_id
        if identity_id is not None:
            params["identity_id"] = identity_id
        if source_index_id is not None:
            params["source_index_id"] = source_index_id

        response = self._connection.get(path=self._path(), params=params)
        if not response:
            return []
        return [
            Face(
                _connection=self._connection,
                _collection_id=self._collection_id,
                **f,
            )
            for f in response.get("faces", [])
        ]

    def get(self, face_id: str) -> Optional[Face]:
        """Get a face record by ID.

        :param str face_id: The face ID
        :return: :class:`Face <Face>` object
        :rtype: :class:`videodb.face.Face`
        """
        response = self._connection.get(path=self._path(face_id))
        if not response:
            return None
        return Face(
            _connection=self._connection,
            _collection_id=self._collection_id,
            **response,
        )

    def delete(self, face_id: str) -> None:
        """Delete a face record.

        If the face's identity has no remaining faces, the identity is also deleted.

        :param str face_id: The face ID to delete
        """
        self._connection.delete(path=self._path(face_id))


class FaceStore:
    """Face store for a collection — manages identities and face records.

    Access via ``collection.face_store``.

    Usage::

        store = collection.face_store

        # Identity operations
        identities = store.identities.list()
        identity = store.identities.get("abc123")
        identity.update(name="Ashish")
        store.identities.merge(source_ids=["id1", "id2"], target_name="Final")
        store.identities.split("id1", face_ids=["f1", "f2"], new_identity_name="New")

        # Face operations
        faces = store.faces.list(video_id="m-xxx")
        face = store.faces.get("face_abc")
        store.faces.delete("face_abc")
    """

    def __init__(self, _connection, _collection_id, **kwargs):
        self._connection = _connection
        self._collection_id = _collection_id
        self.type = kwargs.get("type", "faces")
        self.collection_id = _collection_id
        self.status = kwargs.get("status")
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")

        self.identities = IdentityManager(_connection, _collection_id)
        self.faces = FaceManager(_connection, _collection_id)

    def __repr__(self):
        return f"FaceStore(collection_id={self._collection_id}, status={self.status})"
