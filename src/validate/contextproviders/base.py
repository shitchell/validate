"""
Base context provider class.
"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace
from typing import Type, TypeVar, Generic, Set, List
from ..core.contexts.base import ValidationContext
from ..core.problem_types.base import ProblemType

T = TypeVar("T", bound=ValidationContext)


class BaseContextProvider(ABC, Generic[T]):
    """
    Base class for context providers.

    Context providers build typed contexts for validators/remediators.
    They handle the heavy lifting of:
    - API calls
    - Data fetching
    - Caching
    - Context construction

    Attributes:
        errors: List of problems encountered during context building.
    """

    def __init__(self):
        self.errors: List[ProblemType] = []

    @classmethod
    @abstractmethod
    def provides_context_type(cls) -> Type[T]:
        """
        Which ValidationContext subclass this provider builds.

        Returns:
            The context class this provider can build
        """
        pass

    @classmethod
    def register_args(cls, parser: ArgumentParser) -> None:
        """
        Optional: Register provider-specific CLI arguments.

        Args:
            parser: Argument parser to add args to
        """
        pass

    @classmethod
    def get_required_args(cls) -> Set[str]:
        """
        Declare required argument names.

        Returns:
            Set of required arg names (checked if provider is used)
        """
        return set()

    @abstractmethod
    def can_provide(self, args: Namespace) -> bool:
        """
        Can this provider build context given these args?

        Args:
            args: Parsed command-line arguments

        Returns:
            True if provider can build context
        """
        pass

    @abstractmethod
    def build_contexts(self, args: Namespace) -> List[T]:
        """
        Build validation contexts.

        May return multiple contexts (e.g., one per source->target pair).

        Args:
            args: Parsed command-line arguments

        Returns:
            List of validation contexts
        """
        pass