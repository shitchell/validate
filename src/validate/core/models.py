"""
Core data models used throughout the framework.

All models use Pydantic for validation and serialization.
"""

from pydantic import BaseModel, ConfigDict
from pathlib import Path
from argparse import Namespace
from typing import Any, Optional


class FieldDefinition(BaseModel):
    """
    Normalized field definition matching jira.fields() schema.

    Attributes:
        id: Field identifier (e.g., "customfield_12345" or "components")
        name: Display name (e.g., "Components")
        schema: Field schema dict with type information
        custom: Whether this is a custom field
        clause_names: Search clause names from Jira
        searchable: Whether field is searchable
        orderable: Whether field can be used in ORDER BY
        navigable: Whether field appears in navigator
    """

    model_config = ConfigDict(frozen=True)  # Immutable and hashable

    id: str
    name: str
    schema: dict[str, Any]
    custom: bool = False
    clause_names: list[str] = []
    searchable: bool = True
    orderable: bool = True
    navigable: bool = True

    def __hash__(self) -> int:
        """Hash on ID for use in sets"""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Equality based on ID"""
        if not isinstance(other, FieldDefinition):
            return False
        return self.id == other.id

    @classmethod
    def from_jira_field(cls, field_dict: dict[str, Any]) -> "FieldDefinition":
        """
        Create from jira.fields() response.

        Args:
            field_dict: Dictionary from jira.fields() response

        Returns:
            FieldDefinition instance
        """
        return cls(
            id=field_dict["id"],
            name=field_dict["name"],
            schema=field_dict.get("schema", {}),
            custom=field_dict.get("custom", False),
            clause_names=field_dict.get("clauseNames", []),
            searchable=field_dict.get("searchable", True),
            orderable=field_dict.get("orderable", True),
            navigable=field_dict.get("navigable", True),
        )


class ScreenType(str):
    """Screen types in Jira"""

    CREATE = "create"
    EDIT = "edit"
    VIEW = "view"
