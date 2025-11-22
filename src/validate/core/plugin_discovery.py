"""
Plugin discovery and validation.
"""

import importlib
import pkgutil
import importlib.metadata
import logging
from typing import Type, List
from pathlib import Path

logger = logging.getLogger(__name__)


def discover_modules() -> List[str]:
    """
    Discover all plugin modules, both internal and from external packages.

    Returns:
        List of module names to import plugins from.
    """
    modules = []

    # 1. Discover internal plugin modules using pkgutil
    internal_packages = ['validate.validators', 'validate.remediators', 'validate.contextproviders']
    for package_name in internal_packages:
        try:
            package = importlib.import_module(package_name)
            package_path = Path(package.__file__).parent
            for _, modname, _ in pkgutil.walk_packages(
                [str(package_path)], prefix=f"{package_name}."
            ):
                logger.debug(f"Found module {modname}")
                modules.append(modname)
        except ImportError:
            continue

    # 2. Discover external plugin modules using entry points
    try:
        for entry_point in importlib.metadata.entry_points(group="validate.plugins"):
            modules.append(entry_point.value)
    except Exception:
        # Fails gracefully if entry points cannot be read
        pass

    return list(sorted(set(modules)))


def discover_plugins_from_modules(modules: List[str], base_class: Type) -> List[Type]:
    """Generic function to discover plugin classes from a list of modules."""
    plugins = []
    logger.debug(f"Discovering {base_class.__name__} from {len(modules)} modules")
    
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                if (
                    isinstance(attr, type)
                    and issubclass(attr, base_class)
                    and attr is not base_class
                    and not attr.__name__.startswith("_")
                    and attr.__module__ == module.__name__  # Only pick up classes defined in this module
                ):
                    logger.debug(f"Found plugin class {attr.__name__}")
                    plugins.append(attr)
        except ImportError as e:
            logger.debug(f"Error importing {module_name}: {e}")
            continue
    return plugins


def discover_validators() -> List[Type]:
    """Discover all validator classes."""
    from ..validators.base import BaseValidator
    modules = discover_modules()
    return discover_plugins_from_modules(modules, BaseValidator)


def discover_remediators() -> List[Type]:
    """Discover all remediator classes."""
    from ..remediators.base import BaseRemediator
    modules = discover_modules()
    return discover_plugins_from_modules(modules, BaseRemediator)


def discover_context_providers() -> List[Type]:
    """Discover all context provider classes."""
    from ..contextproviders.base import BaseContextProvider
    modules = discover_modules()
    return discover_plugins_from_modules(modules, BaseContextProvider)


def validate_plugin_compatibility(
    validator_classes: List[Type],
    remediator_classes: List[Type]
) -> None:
    """
    Validate that all produced problem types have handlers.

    Args:
        validator_classes: List of validator classes
        remediator_classes: List of remediator classes

    Logs warnings for unfixable problems.
    """
    # Get all produced problem types
    produced = set()
    for validator_cls in validator_classes:
        produced.update(validator_cls.register_problem_types())

    # Get all handled problem types
    handled = set()
    for remediator_cls in remediator_classes:
        handled.update(remediator_cls.handles_problem_types())

    # Warn about unfixable problems
    unfixable = produced - handled
    if unfixable:
        type_ids = [t.TYPE_ID for t in unfixable]
        logger.warning(
            f"The following problem types lack remediators: {type_ids}\n"
            f"These issues can be detected but not auto-fixed."
        )

    # Info about unused remediators
    unused = handled - produced
    if unused:
        type_ids = [t.TYPE_ID for t in unused]
        logger.info(f"Remediators registered for unused problem types: {type_ids}")