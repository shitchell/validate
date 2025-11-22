"""
Jira-specific validation context.
"""

from pydantic import BaseModel, ConfigDict
from pathlib import Path
from argparse import Namespace
from typing import Dict, Set
from .base import ValidationContext
from ..models import FieldDefinition


class JiraValidationContext(ValidationContext):
    """
    Context for Jira mirroring validation.

    Contains all Jira-specific data needed for validation.
    Built by JiraContextProvider.

    Attributes:
        config_path: Path to mirroring config file
        config: Full config dict
        source_project_key: Source project key (e.g., "BP")
        target_project_key: Target project key (e.g., "HLXDEV")
        source_issue_type: Source issue type name (e.g., "Sustainment")
        target_issue_type: Target issue type name (e.g., "Bug")
        all_fields: Global field cache (all fields in Jira instance)
        source_available_fields: Fields available in source project/issue type
        target_available_fields: Fields available in target project/issue type
        target_required_fields: Fields required during target issue creation
        target_create_screen_fields: Fields on target CREATE screen
        target_edit_screen_fields: Fields on target EDIT screen
        target_view_screen_fields: Fields on target VIEW screen
        target_create_screen_id: CREATE screen ID
        target_create_screen_name: CREATE screen name
        target_edit_screen_id: EDIT screen ID
        target_edit_screen_name: EDIT screen name
        source_issue_type_id: Source issue type ID
        target_issue_type_id: Target issue type ID
        mapping_config: Config for this specific source->target mapping
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Config
    config_path: Path
    config: dict

    # Project pair
    source_project_key: str
    target_project_key: str
    source_issue_type: str
    target_issue_type: str

    # Cached Jira data (reused across validators)
    all_fields: Dict[str, FieldDefinition]

    # Source project data
    source_available_fields: Dict[str, FieldDefinition]

    # Target project data
    target_available_fields: Dict[str, FieldDefinition]
    target_required_fields: Set[FieldDefinition]
    target_create_screen_fields: Set[FieldDefinition]
    target_edit_screen_fields: Set[FieldDefinition]
    target_view_screen_fields: Set[FieldDefinition]

    # Screen metadata
    target_create_screen_id: str
    target_create_screen_name: str
    target_edit_screen_id: str
    target_edit_screen_name: str

    # Issue type IDs
    source_issue_type_id: str
    target_issue_type_id: str

    # Config section for this mapping
    mapping_config: dict
