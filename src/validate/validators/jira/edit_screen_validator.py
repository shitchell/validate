"""
Validates EDIT screen configuration.
"""
from typing import List, Set, Type, Dict
from ..base import BaseValidator
from ...core.contexts.base import ValidationContext
from ...core.contexts.jira import JiraValidationContext
from ...core.problem_types.jira import FieldMissingFromEditScreen
from ...core.problem_types.base import ProblemType

class EditScreenValidator(BaseValidator):
    @property
    def name(self) -> str:
        return "Jira EDIT Screen Validator"

    @property
    def tags(self) -> Set[str]:
        return {"jira", "screen", "edit"}

    @classmethod
    def requires_context_types(cls) -> list[Type[ValidationContext]]:
        return [JiraValidationContext]

    @classmethod
    def register_problem_types(cls) -> Set[Type[ProblemType]]:
        return {FieldMissingFromEditScreen}

    def validate(self, contexts: Dict[Type[ValidationContext], ValidationContext]) -> List[ProblemType]:
        context = contexts[JiraValidationContext]
        problems: List[ProblemType] = []
        
        mirrored_fields = context.mapping_config.get("mirrored_fields", [])
        mapped_fields = context.mapping_config.get("mapped_fields", {})

        for field_name in mirrored_fields:
            field = context.all_fields.get(field_name)
            if field and field not in context.target_edit_screen_fields:
                problems.append(self._create_problem(context, field, "mirrored_fields"))

        for target_field_name in mapped_fields.values():
            field = context.all_fields.get(target_field_name)
            if field and field not in context.target_edit_screen_fields:
                problems.append(self._create_problem(context, field, "mapped_fields"))
                
        return problems

    def _create_problem(self, context: JiraValidationContext, field: Dict, source_section: str) -> FieldMissingFromEditScreen:
        return FieldMissingFromEditScreen(
            field=field,
            project_key=context.target_project_key,
            issue_type_name=context.target_issue_type,
            issue_type_id=context.target_issue_type_id,
            screen_id=context.target_edit_screen_id,
            screen_name=context.target_edit_screen_name,
            config_key_path=f"{context.source_project_key}.{context.target_project_key}.issue_types.{context.source_issue_type}.{context.target_issue_type}.{source_section}",
            source_config_section=source_section
        )
