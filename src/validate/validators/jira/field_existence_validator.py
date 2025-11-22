"""
Validates field existence in Jira projects.
"""
from typing import List, Set, Type, Dict
from ..base import BaseValidator
from ...core.contexts.base import ValidationContext
from ...core.contexts.jira import JiraValidationContext
from ...core.problem_types.jira import FieldMissingFromSourceProject, FieldMissingFromTargetProject
from ...core.problem_types.base import ProblemType

class FieldExistenceValidator(BaseValidator):
    @property
    def name(self) -> str:
        return "Jira Field Existence Validator"

    @property
    def tags(self) -> Set[str]:
        return {"jira", "fields"}

    @classmethod
    def requires_context_types(cls) -> list[Type[ValidationContext]]:
        return [JiraValidationContext]

    @classmethod
    def register_problem_types(cls) -> Set[Type[ProblemType]]:
        return {FieldMissingFromSourceProject, FieldMissingFromTargetProject}

    def validate(self, contexts: Dict[Type[ValidationContext], ValidationContext]) -> List[ProblemType]:
        context = contexts[JiraValidationContext]
        problems: List[ProblemType] = []
        
        mirrored_fields = context.mapping_config.get("mirrored_fields", [])
        mapped_fields = context.mapping_config.get("mapped_fields", {})
        initial_values = context.mapping_config.get("initial_values", {})

        for field_name in mirrored_fields:
            if field_name not in context.source_available_fields:
                problems.append(self._create_missing_source_problem(context, field_name, "mirrored_fields"))
            if field_name not in context.target_available_fields:
                problems.append(self._create_missing_target_problem(context, field_name, "mirrored_fields"))

        for source_field, target_field in mapped_fields.items():
            if source_field not in context.source_available_fields:
                problems.append(self._create_missing_source_problem(context, source_field, "mapped_fields"))
            if target_field not in context.target_available_fields:
                problems.append(self._create_missing_target_problem(context, target_field, "mapped_fields"))

        for field_name in initial_values.keys():
            if field_name not in context.target_available_fields:
                problems.append(self._create_missing_target_problem(context, field_name, "initial_values"))
                
        return problems

    def _create_missing_source_problem(self, context: JiraValidationContext, field_name: str, section: str) -> FieldMissingFromSourceProject:
        return FieldMissingFromSourceProject(
            field_name_or_id=field_name,
            project_key=context.source_project_key,
            issue_type_name=context.source_issue_type,
            issue_type_id=context.source_issue_type_id,
            config_key_path=f"{context.source_project_key}.{context.target_project_key}.issue_types.{context.source_issue_type}.{context.target_issue_type}.{section}",
            source_config_section=section
        )

    def _create_missing_target_problem(self, context: JiraValidationContext, field_name: str, section: str) -> FieldMissingFromTargetProject:
        return FieldMissingFromTargetProject(
            field_name_or_id=field_name,
            project_key=context.target_project_key,
            issue_type_name=context.target_issue_type,
            issue_type_id=context.target_issue_type_id,
            config_key_path=f"{context.source_project_key}.{context.target_project_key}.issue_types.{context.source_issue_type}.{context.target_issue_type}.{section}",
            source_config_section=section
        )
