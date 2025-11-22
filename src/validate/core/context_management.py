"""
Context provider management.
"""

from typing import Dict, List, Type, Any
from argparse import Namespace
from .contexts.base import ValidationContext


def instantiate_context_providers(
    provider_classes: List[Type],
    context_types_needed: set[Type[ValidationContext]],
    args: Namespace
) -> Dict[Type[ValidationContext], Any]:
    """
    Find and instantiate providers for needed context types.

    Args:
        provider_classes: All discovered provider classes
        context_types_needed: Context types required by validators
        args: Parsed arguments

    Returns:
        Map of context type -> provider instance

    Raises:
        ValueError: If no provider found for a needed context type
    """
    providers = {}

    for context_type in context_types_needed:
        # Find provider for this context type
        provider_cls = None
        for cls in provider_classes:
            if cls.provides_context_type() == context_type:
                provider_cls = cls
                break

        if not provider_cls:
            raise ValueError(f"No context provider found for {context_type.__name__}")

        # Instantiate
        provider = provider_cls()

        # Check if it can provide
        if not provider.can_provide(args):
            raise ValueError(
                f"{provider_cls.__name__} cannot provide context with given args"
            )

        providers[context_type] = provider

    return providers


def validate_provider_args(providers: Dict[Type, Any], args: Namespace) -> None:
    """
    Validate required args for providers.

    Args:
        providers: Map of context type -> provider instance
        args: Parsed arguments

    Raises:
        ValueError: If required args missing
    """
    missing_args = []

    for provider in providers.values():
        required = provider.__class__.get_required_args()
        for arg_name in required:
            value = getattr(args, arg_name, None)
            if value is None or (isinstance(value, list) and not value):
                missing_args.append(
                    f"{provider.__class__.__name__} requires --{arg_name.replace('_', '-')}"
                )

    if missing_args:
        raise ValueError("Missing required arguments:\n  " + "\n  ".join(missing_args))
