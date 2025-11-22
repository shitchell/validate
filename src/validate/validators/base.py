"""
Base validator class and plugin interface.
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Type, Set, Any, List, Dict
from ..core.contexts.base import ValidationContext
from ..core.problem_types.base import ProblemType


class BaseValidator(ABC):
    """
    Base class for all validators.

    Validators examine a ValidationContext and produce ProblemType instances
    containing all data needed for understanding and remediating issues.

    Methods:
        name: Human-readable validator name
        tags: Tags for filtering (e.g., {'jira', 'schema'})
        requires_context_types: Which context types this validator needs
        register_problem_types: Which problem types this validator produces
        register_args: Register CLI arguments
        get_required_args: Declare required arguments
        validate_args: Validate arguments
        can_validate: Can this validator handle the target
        is_enabled: Should this validator run
        validate: Perform validation
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable validator name.

        Returns:
            Validator name (e.g., "Jira Field Existence Validator")
        """
        pass

    @property
    def tags(self) -> Set[str]:
        """
        Tags for filtering.

        Returns:
            Set of tags (e.g., {'jira', 'schema', 'security'})
        """
        return set()

    @classmethod
    @abstractmethod
    def requires_context_types(cls) -> list[Type[ValidationContext]]:
        """
        Which ValidationContext subclasses this validator needs.

        The framework ensures these context types are built before
        calling validate().

        Returns:
            A list of ValidationContext subclass types.
            e.g., [JiraValidationContext, K8sValidationContext]
        """
        pass

    @classmethod
    @abstractmethod
    def register_problem_types(cls) -> Set[Type[ProblemType]]:
        """
        Declare which ProblemType subclasses this validator can produce.

        Used for compile-time type checking and runtime compatibility validation.

        Returns:
            Set of ProblemType subclass types
        """
        pass

    @classmethod
    def register_args(cls, parser: ArgumentParser) -> None:
        """
        Optional: Register validator-specific CLI arguments.

        Args:
            parser: Argument parser to add arguments to
        """
        pass

    @classmethod
    def get_required_args(cls) -> Set[str]:
        """
        Declare required argument names for this validator.

        These are checked ONLY if the validator will actually run.

        Returns:
            Set of argument names (without -- prefix)
            Example: {'config_file', 'source_project'}
        """
        return set()

    @classmethod
    def validate_args(cls, args: Namespace) -> None:
        """
        Validate that required args are present.

        Args:
            args: Parsed arguments

        Raises:
            ValueError: If required args are missing or invalid
        """
        for arg_name in cls.get_required_args():
            value = getattr(args, arg_name, None)
            if value is None or (isinstance(value, list) and not value):
                raise ValueError(
                    f"{cls.name if hasattr(cls, 'name') else cls.__name__} "
                    f"requires --{arg_name.replace('_', '-')}"
                )

    @classmethod
    def can_validate(cls, target: Any) -> bool:
        """
        Can this validator handle this target?

        Used for auto-detection.

        Args:
            target: Target to validate (file path, URL, etc.)

        Returns:
            True if this validator can handle the target
        """
        return False

    def is_enabled(self, args: Namespace) -> bool:
        """
        Determine if this validator should run.

        Override to implement conditional logic based on:
        - Target type (file extension, content structure)
        - Explicit flags (--validate-jira)
        - Tags (--tags jira)

        Args:
            args: Parsed arguments

        Returns:
            True if validator should run
        """
        return True

    @abstractmethod
    def validate(self, contexts: dict[Type[ValidationContext], ValidationContext]) -> list[ProblemType]:
        """
        Perform validation.

        Args:
            contexts: A dictionary mapping context types to their instances,
                      containing all contexts requested by requires_context_types().

        Returns:
            List of problem instances (empty if all validations pass)
        """
        pass
