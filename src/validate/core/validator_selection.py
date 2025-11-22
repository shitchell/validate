"""
Determine which validators should run.
"""

from argparse import Namespace
from typing import List, Type, Any
from pathlib import Path


def determine_active_validators(
    validator_classes: List[Type],
    args: Namespace
) -> List[Type]:
    """
    Determine which validators should run based on:
    - Target type (auto-detection)
    - Explicit tags (--tags jira)
    - Exclude tags (--exclude-tags security)
    - Validator-specific flags

    Args:
        validator_classes: All discovered validator classes
        args: Parsed command-line arguments

    Returns:
        List of validator classes that should run
    """
    active = []

    # Get target
    target: Any = None
    if hasattr(args, "target") and args.target:
        target_str = args.target
        target = Path(target_str) if not target_str.startswith("http") else target_str

    for validator_cls in validator_classes:
        # Check auto-detection
        can_validate = False
        if target:
            can_validate = validator_cls.can_validate(target)

        # Check tags filter
        if hasattr(args, "tags") and args.tags:
            requested_tags = set(args.tags)
            # Instantiate temporarily to get tags
            temp_instance = validator_cls()
            validator_tags = temp_instance.tags
            if not (requested_tags & validator_tags):
                continue  # No tag overlap, skip

        # Check exclude tags
        if hasattr(args, "exclude_tags") and args.exclude_tags:
            excluded_tags = set(args.exclude_tags)
            temp_instance = validator_cls()
            validator_tags = temp_instance.tags
            if excluded_tags & validator_tags:
                continue  # Has excluded tag, skip

        # Check validator-specific enable logic
        temp_instance = validator_cls()
        if temp_instance.is_enabled(args):
            active.append(validator_cls)
        elif can_validate:
            # Auto-detected, include it
            active.append(validator_cls)

    return active


def validate_args_for_active_validators(
    validator_classes: List[Type],
    args: Namespace
) -> None:
    """
    Validate that all required args are present for active validators.

    Args:
        validator_classes: Validators that will run
        args: Parsed arguments

    Raises:
        ValueError: If any validator has missing required args
    """
    missing_args = []

    for validator_cls in validator_classes:
        required = validator_cls.get_required_args()
        for arg_name in required:
            value = getattr(args, arg_name, None)

            # Check if missing or empty
            if value is None:
                validator_name = (
                    validator_cls.name
                    if hasattr(validator_cls, "name")
                    else validator_cls.__name__
                )
                missing_args.append(
                    f"{validator_name} requires --{arg_name.replace('_', '-')}"
                )
            elif isinstance(value, list) and not value:
                validator_name = (
                    validator_cls.name
                    if hasattr(validator_cls, "name")
                    else validator_cls.__name__
                )
                missing_args.append(
                    f"{validator_name} requires --{arg_name.replace('_', '-')}"
                )

    if missing_args:
        raise ValueError("Missing required arguments:\n  " + "\n  ".join(missing_args))
