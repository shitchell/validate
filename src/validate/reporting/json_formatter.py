"""
JSON output formatter.
"""
import json
from typing import List, Any, Dict

from pydantic import BaseModel

from ..core.problem_types.base import ProblemType
from ..remediators.base import RemediationResult
from .reporter import BaseReporter
from argparse import Namespace


class JsonFormatter(BaseReporter):
    """Formats output as a JSON object."""

    def report(
        self,
        problems: List[ProblemType],
        remediation_results: List[RemediationResult],
        args: Namespace
    ) -> None:
        
        class PydanticEncoder(json.JSONEncoder):
            def default(self, o: Any) -> Any:
                if isinstance(o, BaseModel):
                    return o.model_dump(mode='json')
                return super().default(o)

        output = {
            "summary": {
                "total_problems": len(problems),
                "errors": sum(1 for p in problems if p.severity == "ERROR"),
                "warnings": sum(1 for p in problems if p.severity == "WARNING"),
                "info": sum(1 for p in problems if p.severity == "INFO"),
            },
            "problems": problems,
            "remediation_results": remediation_results,
        }
        print(json.dumps(output, cls=PydanticEncoder, indent=2))
