"""
Validates for duplicate issue type mappings in the config.
"""
from typing import List, Set, Type, Dict
from collections import Counter
from ..base import BaseValidator
from ...core.contexts.base import ValidationContext
from ...core.contexts.jira import JiraValidationContext
from ...core.problem_types.jira import DuplicateIssueTypeMapping
from ...core.problem_types.base import ProblemType

class DuplicateMappingValidator(BaseValidator):
    @property
    def name(self) -> str:
        return "Jira Duplicate Mapping Validator"

    @property
    def tags(self) -> Set[str]:
        return {"jira", "config"}

    @classmethod
    def requires_context_types(cls) -> list[Type[ValidationContext]]:
        return [JiraValidationContext]

    @classmethod
    def register_problem_types(cls) -> Set[Type[ProblemType]]:
        return {DuplicateIssueTypeMapping}

    def validate(self, contexts: Dict[Type[ValidationContext], ValidationContext]) -> List[ProblemType]:
        context = contexts[JiraValidationContext]
        problems: List[ProblemType] = []
        
        # This validator should only run once, not per context.
        # We can use a flag on the context args to ensure this.
        if getattr(context.args, "_duplicate_mapping_validated", False):
            return []
        
        setattr(context.args, "_duplicate_mapping_validated", True)

        mapping_counts = Counter()
        for source_proj, targets in context.config.items():
            for target_proj, direction_config in targets.items():
                for source_type, target_configs in direction_config.get("issue_types", {}).items():
                    for target_type in target_configs.keys():
                        mapping_counts[(source_proj, target_proj, source_type, target_type)] += 1
        
        for (source_proj, target_proj, source_type, target_type), count in mapping_counts.items():
            if count > 1:
                problems.append(DuplicateIssueTypeMapping(
                    source_project=source_proj,
                    target_project=target_proj,
                    source_issue_type=source_type,
                    target_issue_type=target_type,
                    count=count
                ))

        return problems
