from typing import Optional, List, Dict, Any
from videodb._constants import ApiPath


class Prompt:
    """Prompt class to interact with user prompt templates

    :ivar str prompt_id: Unique identifier for the prompt
    :ivar str name: Name of the prompt
    :ivar str content: Content/text of the prompt
    :ivar str description: Description of the prompt
    :ivar int active_version: Currently active version number
    :ivar int latest_version: Latest version number available
    :ivar str created_at: Timestamp when prompt was created
    :ivar str updated_at: Timestamp when prompt was last updated
    """

    def __init__(self, _connection, prompt_id: str, **kwargs) -> None:
        self._connection = _connection
        self.prompt_id = prompt_id
        self.name = kwargs.get("name", None)
        self.content = kwargs.get("content", None)
        self.description = kwargs.get("description", None)
        self.active_version = kwargs.get("active_version", None)
        self.latest_version = kwargs.get("latest_version", None)
        self.created_at = kwargs.get("created_at", None)
        self.updated_at = kwargs.get("updated_at", None)

    def __repr__(self) -> str:
        content_repr = None
        if self.content:
            content_repr = f"{self.content[:50]}{'...' if len(self.content) > 50 else ''}"
        
        return (
            f"Prompt("
            f"prompt_id={self.prompt_id}, "
            f"name={self.name}, "
            f"content={content_repr}, "
            f"description={self.description}, "
            f"active_version={self.active_version}, "
            f"latest_version={self.latest_version})"
        )

    def update(
        self,
        content: str,
        description: Optional[str] = None,
        changelog: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update the prompt content and create a new version.

        :param str content: New content for the prompt
        :param str description: Updated description (optional)
        :param str changelog: Changelog for this version (optional)
        :return: Updated prompt data
        :rtype: Dict[str, Any]
        """
        data = {"content": content}
        if description is not None:
            data["description"] = description
        if changelog:
            data["changelog"] = changelog

        prompt_data = self._connection.put(
            path=f"{ApiPath.prompts}/{self.prompt_id}", data=data
        )

        # Update local attributes with new data
        self.content = prompt_data.get("content", self.content)
        self.description = prompt_data.get("description", self.description)
        self.active_version = prompt_data.get("active_version", self.active_version)
        self.latest_version = prompt_data.get("latest_version", self.latest_version)
        self.updated_at = prompt_data.get("updated_at", self.updated_at)

        return {"success": True, "data": prompt_data}

    def delete(self) -> Dict[str, Any]:
        """Delete the prompt.

        :return: Delete operation result
        :rtype: Dict[str, Any]
        """
        response = self._connection.delete(path=f"{ApiPath.prompts}/{self.prompt_id}")
        return {"success": True, "data": response}

    def get_versions(self) -> Dict[str, Any]:
        """Get all versions of this prompt.

        :return: List of all prompt versions
        :rtype: Dict[str, Any]
        """
        versions_data = self._connection.get(
            path=f"{ApiPath.prompts}/{self.prompt_id}/{ApiPath.versions}"
        )
        return {"success": True, "data": versions_data}

    def set_active_version(self, version: int) -> Dict[str, Any]:
        """Set the active version of this prompt.

        :param int version: Version number to set as active
        :return: Operation result
        :rtype: Dict[str, Any]
        """
        response_data = self._connection.post(
            path=f"{ApiPath.prompts}/{self.prompt_id}/{ApiPath.versions}/{version}",
            data={},
        )

        # Update local active version
        self.active_version = version

        return {"success": True, "data": response_data}

    def get_version(self, version: int) -> Dict[str, Any]:
        """Get a specific version of this prompt.

        :param int version: Version number to retrieve
        :return: Prompt data for the specified version
        :rtype: Dict[str, Any]
        """
        prompt_data = self._connection.get(
            path=f"{ApiPath.prompts}/{self.prompt_id}", params={"version": version}
        )
        return {"success": True, "data": prompt_data}

    def refresh(self) -> None:
        """Refresh the prompt data from the server.

        :return: None
        :rtype: None
        """
        prompt_data = self._connection.get(path=f"{ApiPath.prompts}/{self.prompt_id}")
        if prompt_data:
            self.name = prompt_data.get("name", self.name)
            self.content = prompt_data.get("content", self.content)
            self.description = prompt_data.get("description", self.description)
            self.active_version = prompt_data.get("active_version", self.active_version)
            self.latest_version = prompt_data.get("latest_version", self.latest_version)
            self.created_at = prompt_data.get("created_at", self.created_at)
            self.updated_at = prompt_data.get("updated_at", self.updated_at)
