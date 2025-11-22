"""
Verbose console output formatter.
"""

from typing import List, Dict
from argparse import Namespace
from collections import defaultdict
from ..core.problem_types.base import ProblemType
from ..remediators.base import RemediationResult
from .reporter import BaseReporter


class VerboseFormatter(BaseReporter):
    """Detailed console output"""

    def report(
        self,
        problems: List[ProblemType],
        remediation_results: List[RemediationResult],
        args: Namespace
    ) -> None:
        """Print verbose report"""

        # Group problems by severity
        by_severity: Dict[str, List[ProblemType]] = defaultdict(list)
        for problem in problems:
            by_severity[problem.severity].append(problem)

        # Print problems
        if problems:
            print("\n" + "=" * 80)
            print("VALIDATION RESULTS")
            print("=" * 80 + "\n")

            for severity in ["ERROR", "WARNING", "INFO"]:
                severity_problems = by_severity[severity]
                if not severity_problems:
                    continue

                symbol = "✗" if severity == "ERROR" else "⚠" if severity == "WARNING" else "ℹ"
                print(f"\n{symbol} {severity}S ({len(severity_problems)}):")
                print("-" * 80)

                for problem in severity_problems:
                    print(f"\n  {problem.get_description()}")
                    print(f"  Location: {problem.get_location_description()}")

        # Print remediation results
        if remediation_results:
            print("\n" + "=" * 80)
            print("REMEDIATION RESULTS")
            print("=" * 80 + "\n")

            success_count = sum(1 for r in remediation_results if r.success and not r.skipped)
            skipped_count = sum(1 for r in remediation_results if r.skipped)
            failed_count = sum(1 for r in remediation_results if not r.success and not r.skipped)

            if args.dry_run:
                print(f"DRY RUN: Would fix {success_count} problems")
            else:
                print(f"✓ Fixed: {success_count}")
                print(f"⊘ Skipped: {skipped_count}")
                if failed_count:
                    print(f"✗ Failed: {failed_count}")

            # Show details
            for result in remediation_results:
                if result.success or result.error:
                    symbol = "✓" if result.success else "✗"
                    print(f"\n  {symbol} {result.message}")
                    if result.error:
                        print(f"     Error: {result.error}")

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total problems: {len(problems)}")
        print(f"  Errors: {len(by_severity['ERROR'])}")
        print(f"  Warnings: {len(by_severity['WARNING'])}")
        print(f"  Info: {len(by_severity['INFO'])}")

        if remediation_results:
            auto_fixable = sum(
                1 for p in problems
                if any(r.problem == p and (r.success or r.skipped) for r in remediation_results)
            )
            print(f"\nAuto-fixable: {auto_fixable}")

        print()
