"""
Validates schema compatibility between mirrored fields.
"""
from typing import List, Set, Type, Dict
from ..base import BaseValidator
from ...core.contexts.base import ValidationContext
from ...core.contexts.jira import JiraValidationContext
from ...core.problem_types.jira import FieldSchemaMismatch
from ...core.problem_types.base import ProblemType

class SchemaCompatibilityValidator(BaseValidator):
    @property
    def name(self) -> str:
        return "Jira Schema Compatibility Validator"

    @property
    def tags(self) -> Set[str]:
        return {"jira", "schema"}

    @classmethod
    def requires_context_types(cls) -> list[Type[ValidationContext]]:
        return [JiraValidationContext]

    @classmethod
    def register_problem_types(cls) -> Set[Type[ProblemType]]:
        return {FieldSchemaMismatch}

    def validate(self, contexts: Dict[Type[ValidationContext], ValidationContext]) -> List[ProblemType]:
        context = contexts[JiraValidationContext]
        problems: List[ProblemType] = []

        mirrored_fields = context.mapping_config.get("mirrored_fields", [])
        for field_name in mirrored_fields:
            source_field = context.source_available_fields.get(field_name)
            target_field = context.target_available_fields.get(field_name)

            if source_field and target_field:
                source_type = source_field.schema.get("type")
                target_type = target_field.schema.get("type")
                if source_type != target_type and target_type != "string":
                    problems.append(FieldSchemaMismatch(
                        field_name=field_name,
                        source_field=source_field,
                        target_field=target_field,
                        source_project_key=context.source_project_key,
                        target_project_key=context.target_project_key,
                        source_issue_type=context.source_issue_type,
                        target_issue_type=context.target_issue_type,
                        config_key_path=f"{context.source_project_key}.{context.target_project_key}.issue_types.{context.source_issue_type}.{context.target_issue_type}.mirrored_fields"
                    ))
        return problems
