"""
Diagnoses Jira connection and context building failures.
"""

from typing import Set, Type, Dict
from argparse import Namespace
from jira import JIRA
from jira.exceptions import JIRAError
from ..base import BaseRemediator, RemediationResult
from ...core.problem_types.base import ProblemType, ContextBuildFailure
from ...core.contexts.base import ValidationContext
from ...contextproviders.jira import JiraContextProvider


class JiraConnectionRemediator(BaseRemediator):
    """
    Diagnoses Jira connection issues (401, 403, 404) reported as ContextBuildFailures.
    """

    def __init__(self, args: Namespace):
        super().__init__(args)
        self.jira_client: JIRA = JiraContextProvider().get_jira_client(args)

    @property
    def name(self) -> str:
        return "Jira Connection Doctor"

    @property
    def priority(self) -> int:
        return 1  # Run first!

    @classmethod
    def handles_problem_types(cls) -> Set[Type[ProblemType]]:
        return {ContextBuildFailure}

    def remediate(
        self,
        problem: ProblemType,
        contexts: Dict[Type[ValidationContext], ValidationContext],
        dry_run: bool
    ) -> RemediationResult:
        if not isinstance(problem, ContextBuildFailure):
            return RemediationResult(problem=problem, success=False, message="Not a ContextBuildFailure")

        exception = problem.exception
        
        # Only handle Jira errors
        if not isinstance(exception, JIRAError):
             return RemediationResult(
                problem=problem, 
                success=False, 
                message=f"Skipping non-Jira error: {type(exception).__name__}",
                skipped=True
            )

        status_code = exception.status_code
        
        if status_code == 404:
            return self._diagnose_404(problem)
        elif status_code in (401, 403):
            return self._diagnose_auth(problem)
        
        return RemediationResult(
            problem=problem,
            success=False,
            message=f"Jira Error {status_code}: {exception.text}"
        )

    def _diagnose_404(self, problem: ContextBuildFailure) -> RemediationResult:
        """
        Diagnose 404 errors (Project not found).
        """
        # We can try to list all projects to see if we have access to ANY.
        try:
            projects = self.jira_client.projects()
            project_keys = [p.key for p in projects]
            
            if not project_keys:
                msg = "Connected to Jira, but no projects are visible. Check user permissions."
            else:
                msg = (
                    f"Project not found or not visible. "
                    f"Visible projects ({len(project_keys)}): {', '.join(project_keys[:5])}..."
                )
                
            return RemediationResult(
                problem=problem,
                success=False, # We didn't fix it, but we diagnosed it
                message=f"DIAGNOSIS: {msg}",
                error=str(problem.exception)
            )
        except Exception as e:
             return RemediationResult(
                problem=problem,
                success=False,
                message="DIAGNOSIS: 404 Error, and failed to list projects to verify access.",
                error=str(e)
            )

    def _diagnose_auth(self, problem: ContextBuildFailure) -> RemediationResult:
        """
        Diagnose 401/403 errors (Auth failed).
        """
        # Try to hit /myself endpoint
        try:
            myself = self.jira_client.myself()
            user_name = myself.get('displayName')
            email = myself.get('emailAddress')
            msg = (
                f"Authentication works! Logged in as {user_name} ({email}). "
                f"This 401/403 is likely a specific permission issue for the requested resource."
            )
        except Exception:
            msg = (
                "Authentication FAILED. The provided JIRA_TOKEN or JIRA_EMAIL appears invalid. "
                "Please check your environment variables."
            )

        return RemediationResult(
            problem=problem,
            success=False,
            message=f"DIAGNOSIS: {msg}",
            error=str(problem.exception)
        )
