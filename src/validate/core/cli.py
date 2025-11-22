"""
CLI argument parsing.
"""

import argparse
from typing import List, Type
from pathlib import Path


def build_parser(
    validator_classes: List[Type],
    remediator_classes: List[Type],
    context_provider_classes: List[Type]
) -> argparse.ArgumentParser:
    """
    Build argument parser with all validator/remediator args.

    Args:
        validator_classes: List of validator classes
        remediator_classes: List of remediator classes
        context_provider_classes: List of context provider classes

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="validate",
        description="Flexible validation framework with auto-remediation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  validate config.json                          # Auto-detect validators
  validate config.json --tags jira              # Only Jira validators
  validate config.json --fix-jira --dry-run     # Preview Jira fixes
  validate k8s.yaml --tags kubernetes,security  # Multiple tags
        """,
    )

    # Core arguments
    core_group = parser.add_argument_group("Core Options")
    core_group.add_argument(
        "target",
        nargs="?",
        help="File, directory, or URL to validate"
    )
    core_group.add_argument(
        "--tags",
        action="append",
        help="Only run validators with these tags (can be repeated)"
    )
    core_group.add_argument(
        "--exclude-tags",
        action="append",
        help="Skip validators with these tags (can be repeated)"
    )
    core_group.add_argument(
        "--output",
        choices=["verbose", "brief", "json"],
        default="verbose",
        help="Output format"
    )
    core_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be fixed without making changes"
    )
    core_group.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    # Context provider args
    for provider_cls in context_provider_classes:
        if hasattr(provider_cls, "register_args"):
            group_name = f"{provider_cls.__name__} Options"
            group = parser.add_argument_group(group_name)
            provider_cls.register_args(group)

    # Validator args
    for validator_cls in validator_classes:
        if hasattr(validator_cls, "register_args"):
            validator_name = (
                validator_cls.name
                if hasattr(validator_cls, "name")
                else validator_cls.__name__
            )
            group = parser.add_argument_group(f"{validator_name} Options")
            validator_cls.register_args(group)

    # Remediator args
    for remediator_cls in remediator_classes:
        if hasattr(remediator_cls, "register_args"):
            remediator_name = (
                remediator_cls.name
                if hasattr(remediator_cls, "name")
                else remediator_cls.__name__
            )
            group = parser.add_argument_group(f"{remediator_name} Options")
            remediator_cls.register_args(group)

    return parser
