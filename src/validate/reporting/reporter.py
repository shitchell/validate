"""
Reporting infrastructure.
"""

from abc import ABC, abstractmethod
from typing import List
from argparse import Namespace
from ..core.problem_types.base import ProblemType
from ..remediators.base import RemediationResult


class BaseReporter(ABC):
    """Base class for reporters"""

    @abstractmethod
    def report(
        self,
        problems: List[ProblemType],
        remediation_results: List[RemediationResult],
        args: Namespace
    ) -> None:
        """
        Generate report.

        Args:
            problems: All problems found
            remediation_results: All remediation results
            args: CLI arguments
        """
        pass


def get_reporter(output_format: str) -> BaseReporter:
    """
    Get reporter for output format.

    Args:
        output_format: "verbose", "brief", or "json"

    Returns:
        Reporter instance
    """
    from .verbose_formatter import VerboseFormatter
    from .brief_formatter import BriefFormatter
    from .json_formatter import JsonFormatter

    if output_format == "json":
        return JsonFormatter()
    elif output_format == "brief":
        return BriefFormatter()
    else:
        return VerboseFormatter()
