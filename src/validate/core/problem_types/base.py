"""
Base ProblemType and related models.
"""

from pydantic import BaseModel, ConfigDict
from abc import ABC, abstractmethod
from typing import ClassVar, Literal, Any


class ProblemType(BaseModel, ABC):
    """
    Base class for all validation problems.

    Subclasses represent specific problems and carry all data needed
    to understand AND remediate the issue.

    Class Variables:
        TYPE_ID: Unique identifier for this problem type

    Methods:
        severity: How severe is this problem (ERROR/WARNING/INFO)
        get_description: Human-readable description
        get_location_description: Where the problem is
        _get_hash_key: Fields that uniquely identify this problem
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    TYPE_ID: ClassVar[str]

    @property
    @abstractmethod
    def severity(self) -> Literal["ERROR", "WARNING", "INFO"]:
        """
        How severe is this problem.

        Returns:
            "ERROR", "WARNING", or "INFO"
        """
        pass

    @abstractmethod
    def get_description(self) -> str:
        """
        Human-readable description of the problem.

        Returns:
            Description string
        """
        pass

    @abstractmethod
    def get_location_description(self) -> str:
        """
        Where the problem is (config path, Jira location, etc.).

        Returns:
            Location description string
        """
        pass

    @abstractmethod
    def _get_hash_key(self) -> tuple[Any, ...]:
        """
        Return tuple of fields that uniquely identify this problem.

        Should include enough fields to uniquely identify the problem,
        but not so many that equivalent problems have different hashes.

        Returns:
            Tuple of hashable values
        """
        pass

    def __hash__(self) -> int:
        """Hash based on problem type and identifying fields"""
        return hash((type(self).__name__, self._get_hash_key()))

    def __eq__(self, other: object) -> bool:
        """Equality based on type and identifying fields"""
        if not isinstance(other, type(self)):
            return False
        return self._get_hash_key() == other._get_hash_key()

    @classmethod
    def get_type_id(cls) -> str:
        """Get the unique type ID for this problem type"""
        return cls.TYPE_ID


class ContextBuildFailure(ProblemType):
    """
    Represents a failure to build a validation context.
    """
    TYPE_ID: ClassVar[str] = "core.context_build_failure"
    
    context_name: str
    exception: Exception

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    @property
    def severity(self) -> Literal["ERROR", "WARNING", "INFO"]:
        return "ERROR"

    def get_description(self) -> str:
        return f"Failed to build context '{self.context_name}': {str(self.exception)}"

    def get_location_description(self) -> str:
        return "Context Provider"

    def _get_hash_key(self) -> tuple[Any, ...]:
        return (self.context_name, str(self.exception))
