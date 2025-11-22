"""
Jira-specific problem types.
"""

from typing import ClassVar, Literal
from .base import ProblemType
from ..models import FieldDefinition


class FieldMissingFromCreateScreen(ProblemType):
    """
    Field is in initial_values but not on CREATE screen.

    This prevents issue creation from succeeding.
    """

    TYPE_ID: ClassVar[str] = "jira.field_missing_from_create_screen"

    field: FieldDefinition
    project_key: str
    issue_type_name: str
    issue_type_id: str
    screen_id: str
    screen_name: str
    config_key_path: str

    @property
    def severity(self) -> Literal["ERROR", "WARNING", "INFO"]:
        return "ERROR"

    def get_description(self) -> str:
        return (
            f"Field '{self.field.name}' is in initial_values but not on "
            f"{self.project_key} {self.issue_type_name} CREATE screen"
        )

    def get_location_description(self) -> str:
        return (
            f"Config: {self.config_key_path}\n"
            f"Jira: {self.project_key}/{self.issue_type_name} "
            f"CREATE screen '{self.screen_name}' (ID: {self.screen_id})"
        )

    def _get_hash_key(self) -> tuple:
        return (
            self.field.id,
            self.project_key,
            self.issue_type_id,
            self.screen_id,
            "create"
        )


class FieldMissingFromEditScreen(ProblemType):
    """
    Field in mirrored_fields or mapped_fields but not on EDIT screen.

    This prevents issue updates from succeeding.
    """

    TYPE_ID: ClassVar[str] = "jira.field_missing_from_edit_screen"

    field: FieldDefinition
    project_key: str
    issue_type_name: str
    issue_type_id: str
    screen_id: str
    screen_name: str
    config_key_path: str
    source_config_section: Literal["mirrored_fields", "mapped_fields"]

    @property
    def severity(self) -> Literal["ERROR", "WARNING", "INFO"]:
        return "ERROR"

    def get_description(self) -> str:
        return (
            f"Field '{self.field.name}' is in {self.source_config_section} but not on "
            f"{self.project_key} {self.issue_type_name} EDIT screen"
        )

    def get_location_description(self) -> str:
        return (
            f"Config: {self.config_key_path}\n"
            f"Jira: {self.project_key}/{self.issue_type_name} "
            f"EDIT screen '{self.screen_name}' (ID: {self.screen_id})"
        )

    def _get_hash_key(self) -> tuple:
        return (
            self.field.id,
            self.project_key,
            self.issue_type_id,
            self.screen_id,
            "edit"
        )


class RequiredFieldMissingFromConfig(ProblemType):
    """
    Jira requires this field during creation, but it's not in initial_values.

    This prevents issue creation from succeeding.
    """

    TYPE_ID: ClassVar[str] = "jira.required_field_missing_from_config"

    field: FieldDefinition
    project_key: str
    issue_type_name: str
    issue_type_id: str
    config_key_path: str

    @property
    def severity(self) -> Literal["ERROR", "WARNING", "INFO"]:
        return "ERROR"

    def get_description(self) -> str:
        return (
            f"Field '{self.field.name}' is required by Jira but missing from "
            f"initial_values in config"
        )

    def get_location_description(self) -> str:
        return (
            f"Config: {self.config_key_path}\n"
            f"Jira: {self.project_key}/{self.issue_type_name} requires this field during creation"
        )

    def _get_hash_key(self) -> tuple:
        return (
            self.field.id,
            self.project_key,
            self.issue_type_id,
            "required_missing"
        )


class FieldMissingFromSourceProject(ProblemType):
    """
    Field in config but doesn't exist in source Jira project.

    This prevents field synchronization.
    """

    TYPE_ID: ClassVar[str] = "jira.field_missing_from_source_project"

    field_name_or_id: str
    project_key: str
    issue_type_name: str
    issue_type_id: str
    config_key_path: str
    source_config_section: str

    @property
    def severity(self) -> Literal["ERROR", "WARNING", "INFO"]:
        return "ERROR"

    def get_description(self) -> str:
        return (
            f"Field '{self.field_name_or_id}' referenced in {self.source_config_section} "
            f"but doesn't exist in {self.project_key} project"
        )

    def get_location_description(self) -> str:
        return f"Config: {self.config_key_path}"

    def _get_hash_key(self) -> tuple:
        return (
            self.field_name_or_id,
            self.project_key,
            self.issue_type_id,
            "missing_from_source"
        )


class FieldMissingFromTargetProject(ProblemType):
    """
    Field in config but doesn't exist in target Jira project.

    This prevents field synchronization.
    """

    TYPE_ID: ClassVar[str] = "jira.field_missing_from_target_project"

    field_name_or_id: str
    project_key: str
    issue_type_name: str
    issue_type_id: str
    config_key_path: str
    source_config_section: str

    @property
    def severity(self) -> Literal["ERROR", "WARNING", "INFO"]:
        return "ERROR"

    def get_description(self) -> str:
        return (
            f"Field '{self.field_name_or_id}' referenced in {self.source_config_section} "
            f"but doesn't exist in {self.project_key} project"
        )

    def get_location_description(self) -> str:
        return f"Config: {self.config_key_path}"

    def _get_hash_key(self) -> tuple:
        return (
            self.field_name_or_id,
            self.project_key,
            self.issue_type_id,
            "missing_from_target"
        )


class FieldSchemaMismatch(ProblemType):
    """
    Source and target fields have incompatible schemas.

    Warning only since string targets can accept anything.
    """

    TYPE_ID: ClassVar[str] = "jira.field_schema_mismatch"

    field_name: str
    source_field: FieldDefinition
    target_field: FieldDefinition
    source_project_key: str
    target_project_key: str
    source_issue_type: str
    target_issue_type: str
    config_key_path: str

    @property
    def severity(self) -> Literal["ERROR", "WARNING", "INFO"]:
        return "WARNING"

    def get_description(self) -> str:
        src_type = self.source_field.schema.get("type", "unknown")
        tgt_type = self.target_field.schema.get("type", "unknown")
        return (
            f"Field '{self.field_name}' schema mismatch: "
            f"source is {src_type}, target is {tgt_type}"
        )

    def get_location_description(self) -> str:
        return (
            f"Config: {self.config_key_path}\n"
            f"Source: {self.source_project_key}/{self.source_issue_type}\n"
            f"Target: {self.target_project_key}/{self.target_issue_type}"
        )

    def _get_hash_key(self) -> tuple:
        return (
            self.field_name,
            self.source_project_key,
            self.target_project_key,
            self.source_issue_type,
            self.target_issue_type
        )


class DuplicateIssueTypeMapping(ProblemType):
    """
    Same source->target issue type combination appears multiple times.

    This causes ambiguity in which config to use.
    """

    TYPE_ID: ClassVar[str] = "jira.duplicate_issue_type_mapping"

    source_project: str
    target_project: str
    source_issue_type: str
    target_issue_type: str
    count: int

    @property
    def severity(self) -> Literal["ERROR", "WARNING", "INFO"]:
        return "ERROR"

    def get_description(self) -> str:
        return (
            f"Duplicate mapping: {self.source_project} {self.source_issue_type} -> "
            f"{self.target_project} {self.target_issue_type} appears {self.count} times"
        )

    def get_location_description(self) -> str:
        return (
            f"Config: {self.source_project}.{self.target_project}.issue_types."
            f"{self.source_issue_type}.{self.target_issue_type}"
        )

    def _get_hash_key(self) -> tuple:
        return (
            self.source_project,
            self.target_project,
            self.source_issue_type,
            self.target_issue_type
        )
