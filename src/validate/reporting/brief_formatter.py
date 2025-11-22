"""
Brief console output formatter.
"""
from collections import defaultdict
from typing import List, Dict

from ..core.problem_types.base import ProblemType
from ..remediators.base import RemediationResult
from .reporter import BaseReporter
from argparse import Namespace


class BriefFormatter(BaseReporter):
    """Brief console output, summarizing problems."""

    def report(
        self,
        problems: List[ProblemType],
        remediation_results: List[RemediationResult],
        args: Namespace
    ) -> None:
        if not problems:
            print("✓ No issues found.")
            return

        print("\n--- Validation Summary ---")
        by_severity: Dict[str, List[ProblemType]] = defaultdict(list)
        for problem in problems:
            by_severity[problem.severity].append(problem)

        for severity in ["ERROR", "WARNING", "INFO"]:
            if by_severity[severity]:
                symbol = "✗" if severity == "ERROR" else "⚠" if severity == "WARNING" else "ℹ"
                print(f"{symbol} {len(by_severity[severity])} {severity}(s) found.")

        if remediation_results:
            print("\n--- Remediation Summary ---")
            success_count = sum(1 for r in remediation_results if r.success and not r.skipped)
            if args.dry_run:
                print(f"DRY RUN: Would fix {success_count} problems.")
            else:
                print(f"✓ Fixed {success_count} problems.")

