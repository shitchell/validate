"""
Adds fields to Jira screens.
"""

from typing import Set, Type, Dict
from argparse import ArgumentParser, Namespace
from jira import JIRA
from ..base import BaseRemediator, RemediationResult
from ...core.problem_types.jira import (
    FieldMissingFromCreateScreen,
    FieldMissingFromEditScreen
)
from ...core.problem_types.base import ProblemType
from ...core.contexts.base import ValidationContext
from ...contextproviders.jira import JiraContextProvider


class JiraScreenRemediator(BaseRemediator):
    """
    Adds fields to Jira screens.

    Handles:
    - FieldMissingFromCreateScreen
    - FieldMissingFromEditScreen

    Uses Jira REST API to add fields to screen tabs.
    """

    def __init__(self, args: Namespace):
        super().__init__(args)
        self.jira_client: JIRA = JiraContextProvider().get_jira_client(args)

    @property
    def name(self) -> str:
        return "Jira Screen Remediator"

    @property
    def priority(self) -> int:
        return 10

    @classmethod
    def handles_problem_types(cls) -> Set[Type[ProblemType]]:
        return {
            FieldMissingFromCreateScreen,
            FieldMissingFromEditScreen
        }

    @classmethod
    def register_args(cls, parser: ArgumentParser) -> None:
        fix_group = parser.add_argument_group("Jira Fix Options")
        fix_group.add_argument(
            "--fix-jira",
            action="store_true",
            help="Automatically fix issues in Jira (add fields to screens)"
        )

    def remediate(
        self,
        problem: ProblemType,
        contexts: Dict[Type[ValidationContext], ValidationContext],
        dry_run: bool
    ) -> RemediationResult:
        """Fix Jira screen issues"""
        if not self.args.fix_jira:
            return RemediationResult(
                problem=problem,
                success=False,
                message="Skipped (--fix-jira not set)",
                skipped=True
            )

        if isinstance(problem, (FieldMissingFromCreateScreen, FieldMissingFromEditScreen)):
            return self._add_field_to_screen(problem, dry_run)
        else:
            return RemediationResult(
                problem=problem,
                success=False,
                message=f"Unknown problem type: {type(problem)}",
                error="Remediator doesn't handle this type"
            )

    def _add_field_to_screen(
        self,
        problem: FieldMissingFromCreateScreen | FieldMissingFromEditScreen,
        dry_run: bool
    ) -> RemediationResult:
        screen_name = "CREATE" if isinstance(problem, FieldMissingFromCreateScreen) else "EDIT"
        if dry_run:
            return RemediationResult(
                problem=problem, success=True,
                message=f"Would add field '{problem.field.name}' to {problem.project_key} {screen_name} screen"
            )
        try:
            tab_id = self._get_target_tab_id(problem.screen_id)
            
            # Use raw API to ensure we add to the specific tab we selected
            url = f"{self.jira_client._options['server']}/rest/api/2/screens/{problem.screen_id}/tabs/{tab_id}/fields"
            resp = self.jira_client._session.post(url, json={"fieldId": problem.field.id})
            resp.raise_for_status()
            
            return RemediationResult(
                problem=problem, success=True,
                message=f"Added '{problem.field.name}' to {screen_name} screen", locked=True
            )
        except Exception as e:
            return RemediationResult(
                problem=problem, success=False,
                message=f"Failed to add '{problem.field.name}'", error=str(e)
            )

    def _get_target_tab_id(self, screen_id: str) -> str:
        """
        Finds the most appropriate tab on a screen to add a field to.
        """
        tabs = self.jira_client.screen_tabs(screen_id)
        if not tabs:
            raise ValueError(f"Screen '{screen_id}' has no tabs.")

        if len(tabs) > 1:
            for tab in tabs:
                if tab.name.lower() in {"default", "general"}:
                    return tab.id
        return tabs[0].id
