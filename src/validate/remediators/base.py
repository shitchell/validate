"""
Base remediator class and related models.
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from pydantic import BaseModel
from typing import Type, Set, Optional, Any, Dict, List, Tuple
from ..core.problem_types.base import ProblemType
from ..core.contexts.base import ValidationContext


class RemediationResult(BaseModel):
    """
    Result of a remediation attempt.

    Attributes:
        problem: The problem that was remediated
        success: Whether remediation succeeded
        message: Human-readable message about what happened
        skipped: True if skipped (e.g., flag not set)
        locked: True if this problem should not be touched by future remediators
        error: Error message if failed
    """

    problem: ProblemType
    success: bool
    message: str
    skipped: bool = False
    locked: bool = False
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class ProblemRemediationState(BaseModel):
    """
    Tracks remediation state for a problem.

    Attributes:
        problem: The problem being tracked
        remediated_by: List of remediator names that touched this problem
        locked: Whether this problem is locked from future remediation
        results: All remediation results for this problem
    """

    problem: ProblemType
    remediated_by: list[str] = []
    locked: bool = False
    results: list[RemediationResult] = []

    class Config:
        arbitrary_types_allowed = True


class BaseRemediator(ABC):
    """
    Base class for all remediators.

    Remediators receive ProblemType instances (with all needed data)
    and fix them.

    Attributes:
        args: Parsed command-line arguments

    Methods:
        name: Human-readable remediator name
        priority: Priority (lower = runs first)
        handles_problem_types: Which problem types this remediator can fix
        register_args: Register CLI arguments
        should_remediate: Should remediate this problem
        remediate: Fix a single problem
        remediate_all: Fix multiple problems
    """

    def __init__(self, args: Namespace):
        """
        Initialize remediator.

        Args:
            args: Parsed command-line arguments
        """
        self.args = args

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable remediator name.

        Returns:
            Remediator name
        """
        pass

    @property
    def priority(self) -> int:
        """
        Priority for this remediator (lower = runs first).

        If multiple remediators handle the same problem type,
        the one with lower priority runs first and can lock the problem.

        Priority ranges:
            10-19: Direct system fixes (Jira, K8s, etc.)
            20-29: Config file updates
            30-39: Documentation/reporting
            40+: Logging/auditing

        Returns:
            Priority value (default: 100)
        """
        return 100

    @classmethod
    @abstractmethod
    def handles_problem_types(cls) -> Set[Type[ProblemType]]:
        """
        Declare which ProblemType subclasses this remediator can fix.

        Returns:
            Set of ProblemType subclass types
        """
        pass

    @classmethod
    def register_args(cls, parser: ArgumentParser) -> None:
        """
        Optional: Register remediator-specific CLI arguments.

        Args:
            parser: Main argument parser to add arguments to
        """
        pass

    def should_remediate(
        self, problem: ProblemType, state: Optional[ProblemRemediationState]
    ) -> bool:
        """
        Decide whether to remediate this problem.

        Override to implement custom logic based on:
        - Whether problem was already touched (state.remediated_by)
        - Which remediators touched it
        - Whether it was locked

        Args:
            problem: The problem to potentially remediate
            state: Current remediation state (None if not yet remediated)

        Returns:
            True if should remediate
        """
        return not (state and state.locked)

    @abstractmethod
    def remediate(
        self,
        problem: ProblemType,
        contexts: dict[Type[ValidationContext], ValidationContext],
        dry_run: bool
    ) -> RemediationResult:
        """
        Fix a single problem.

        Args:
            problem: The problem instance with all data needed to fix it.
            contexts: A dictionary of all contexts that were used to generate the problem.
            dry_run: If True, only report what would be done.

        Returns:
            Result of the remediation attempt.
        """
        pass

    def remediate_all(
        self,
        problems_with_contexts: list[tuple[ProblemType, dict[Type[ValidationContext], ValidationContext]]],
        dry_run: bool
    ) -> list[RemediationResult]:
        """
        Fix multiple problems.

        Default implementation calls remediate() for each.
        Subclasses can override for batch operations.

        Args:
            problems_with_contexts: A list of tuples, each containing a problem
                                    and its associated context dictionary.
            dry_run: If True, only report what would be done.

        Returns:
            List of remediation results.
        """
        return [self.remediate(p, c, dry_run) for p, c in problems_with_contexts]
