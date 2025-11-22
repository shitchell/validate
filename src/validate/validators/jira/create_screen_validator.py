"""
Validates CREATE screen configuration.
"""

from typing import List, Set, Type, Dict
from ..base import BaseValidator
from ...core.contexts.base import ValidationContext
from ...core.contexts.jira import JiraValidationContext
from ...core.problem_types.jira import (
    FieldMissingFromCreateScreen,
    RequiredFieldMissingFromConfig
)
from ...core.problem_types.base import ProblemType


class CreateScreenValidator(BaseValidator):
    """
    Validates CREATE screen configuration.

    Checks:
    1. All fields in initial_values are on CREATE screen
    2. All Jira-required fields are in initial_values (or mirrored_fields)
    """

    @property
    def name(self) -> str:
        return "Jira CREATE Screen Validator"

    @property
    def tags(self) -> Set[str]:
        return {"jira", "screen", "create"}

    @classmethod
    def requires_context_types(cls) -> list[Type[ValidationContext]]:
        return [JiraValidationContext]

    @classmethod
    def register_problem_types(cls) -> Set[Type[ProblemType]]:
        return {
            FieldMissingFromCreateScreen,
            RequiredFieldMissingFromConfig
        }

    def validate(self, contexts: Dict[Type[ValidationContext], ValidationContext]) -> List[ProblemType]:
        """Validate CREATE screen configuration"""
        context = contexts[JiraValidationContext]
        problems: List[ProblemType] = []

        # Check 1: Fields in initial_values must be on CREATE screen
        initial_values = context.mapping_config.get("initial_values", {})

        for field_name_or_id in initial_values.keys():
            field = context.all_fields.get(field_name_or_id)
            if not field:
                continue

            if field not in context.target_create_screen_fields:
                problems.append(FieldMissingFromCreateScreen(
                    field=field,
                    project_key=context.target_project_key,
                    issue_type_name=context.target_issue_type,
                    issue_type_id=context.target_issue_type_id,
                    screen_id=context.target_create_screen_id,
                    screen_name=context.target_create_screen_name,
                    config_key_path=(
                        f"{context.source_project_key}.{context.target_project_key}."
                        f"issue_types.{context.source_issue_type}.{context.target_issue_type}."
                        f"initial_values.{field_name_or_id}"
                    )
                ))

        # Check 2: Required fields must be in initial_values
        system_fields = {"Project", "Issue Type", "Summary", "Reporter"}
        mirrored_fields_set = set(context.mapping_config.get("mirrored_fields", []))

        for required_field in context.target_required_fields:
            if required_field.name in system_fields:
                continue

            if required_field.name in mirrored_fields_set:
                continue

            if (
                required_field.name not in initial_values
                and required_field.id not in initial_values
            ):
                problems.append(RequiredFieldMissingFromConfig(
                    field=required_field,
                    project_key=context.target_project_key,
                    issue_type_name=context.target_issue_type,
                    issue_type_id=context.target_issue_type_id,
                    config_key_path=(
                        f"{context.source_project_key}.{context.target_project_key}."
                        f"issue_types.{context.source_issue_type}.{context.target_issue_type}."
                        f"initial_values"
                    )
                ))

        return problems
