class VoiceClone:
    """Reusable cloned voice reference backed by a VideoDB audio asset."""

    def __init__(
        self,
        _connection,
        id=None,
        voice_clone_id=None,
        ref_audio_id=None,
        ref_text=None,
        name=None,
        description=None,
        language=None,
        collection_id=None,
        status=None,
        created_at=None,
        updated_at=None,
        **kwargs,
    ):
        self._connection = _connection
        self.id = voice_clone_id or id
        self.ref_audio_id = ref_audio_id
        self.ref_text = ref_text
        self.name = name
        self.description = description
        self.language = language
        self.collection_id = collection_id
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return (
            f"VoiceClone(id={self.id}, name={self.name}, "
            f"ref_audio_id={self.ref_audio_id}, status={self.status})"
        )

    def _update(self, data):
        if not data:
            return
        self.id = data.get("voice_clone_id", data.get("id", self.id))
        self.ref_audio_id = data.get("ref_audio_id", self.ref_audio_id)
        self.ref_text = data.get("ref_text", self.ref_text)
        self.name = data.get("name", self.name)
        self.description = data.get("description", self.description)
        self.language = data.get("language", self.language)
        self.collection_id = data.get("collection_id", self.collection_id)
        self.status = data.get("status", self.status)
        self.created_at = data.get("created_at", self.created_at)
        self.updated_at = data.get("updated_at", self.updated_at)

    def refresh(self):
        """Fetch latest voice clone state from the server."""
        from videodb._constants import ApiPath

        data = self._connection.get(path=f"{ApiPath.voice_clone}/{self.id}")
        self._update(data or {})
        return self

    def delete(self):
        """Delete this voice clone."""
        from videodb._constants import ApiPath

        self._connection.delete(path=f"{ApiPath.voice_clone}/{self.id}")
        return None
