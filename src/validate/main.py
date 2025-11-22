"""
Main entry point for validate CLI.
"""

import sys
import logging
from argparse import Namespace
from typing import List, Dict, Type, Set
from pathlib import Path

from .core.plugin_discovery import (
    discover_validators,
    discover_remediators,
    discover_context_providers,
    validate_plugin_compatibility,
)
from .core.cli import build_parser
from .core.validator_selection import (
    determine_active_validators,
    validate_args_for_active_validators,
)
from .core.context_management import (
    instantiate_context_providers,
    validate_provider_args,
)
from .core.config_loader import load_env_file
from .core.contexts.base import ValidationContext
from .core.problem_types.base import ProblemType
from .remediators.base import RemediationResult, ProblemRemediationState, BaseRemediator
from .reporting.reporter import get_reporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 = success, 1 = validation errors, 2 = error)
    """
    try:
        # Load secrets from .validate.env
        load_env_file()

        # Phase 1: Plugin Discovery
        logger.debug("Discovering plugins...")
        validator_classes = discover_validators()
        remediator_classes = discover_remediators()
        context_provider_classes = discover_context_providers()

        logger.debug(
            f"Found {len(validator_classes)} validators, "
            f"{len(remediator_classes)} remediators, "
            f"{len(context_provider_classes)} context providers"
        )

        # Phase 2: Build Parser
        logger.debug("Building argument parser...")
        parser = build_parser(
            validator_classes,
            remediator_classes,
            context_provider_classes
        )

        # Phase 3: Parse Arguments
        args = parser.parse_args()

        # Re-configure logging based on args
        if args.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled via CLI flag")

        # Phase 4: Determine Active Validators
        logger.debug("Determining active validators...")
        active_validators = determine_active_validators(validator_classes, args)

        if not active_validators:
            logger.error("No validators selected. Use --tags or provide a valid target.")
            return 2

        logger.debug(f"Active validators: {[v.__name__ for v in active_validators]}")

        # Phase 5: Validate Arguments
        logger.debug("Validating arguments...")
        try:
            validate_args_for_active_validators(active_validators, args)
        except ValueError as e:
            parser.error(str(e))

        # Phase 6: Validate Plugin Compatibility
        validate_plugin_compatibility(validator_classes, remediator_classes)

        # Phase 7: Determine Required Contexts
        logger.debug("Determining required contexts...")
        context_types_needed: Set[Type[ValidationContext]] = set()
        for validator_cls in active_validators:
            context_types_needed.update(validator_cls.requires_context_types())

        logger.debug(f"Context types needed: {[ct.__name__ for ct in context_types_needed]}")

        # Phase 8: Instantiate Context Providers
        logger.debug("Instantiating context providers...")
        context_providers = instantiate_context_providers(
            context_provider_classes,
            context_types_needed,
            args
        )

        # Validate provider args
        validate_provider_args(context_providers, args)

        # Phase 9: Build All Contexts
        logger.debug("Building all required validation contexts...")
        built_contexts: Dict[Type[ValidationContext], List[ValidationContext]] = {}
        all_problems: List[ProblemType] = []
        problem_to_contexts_map: Dict[ProblemType, Dict[Type[ValidationContext], ValidationContext]] = {}

        for context_type, provider in context_providers.items():
            built_contexts[context_type] = provider.build_contexts(args)
            logger.debug(
                f"Built {len(built_contexts[context_type])} {context_type.__name__} instances"
            )
            # Collect setup errors (e.g. missing projects, auth failures)
            if provider.errors:
                all_problems.extend(provider.errors)
                for error in provider.errors:
                    # These problems have no context instance because context building failed.
                    # Remediators must handle this (e.g. by using a fresh provider/client).
                    problem_to_contexts_map[error] = {}

        # Phase 10: Run Validators
        logger.info("Running validators...")
        
        for validator_cls in active_validators:
            validator = validator_cls()
            required_types = validator.requires_context_types()

            if not required_types:
                continue

            primary_context_type = required_types[0]
            for primary_context_instance in built_contexts.get(primary_context_type, []):
                contexts_for_validator: Dict[Type[ValidationContext], ValidationContext] = {}
                for req_type in required_types:
                    if built_contexts.get(req_type):
                        contexts_for_validator[req_type] = built_contexts[req_type][0]
                
                contexts_for_validator[primary_context_type] = primary_context_instance
                
                problems = validator.validate(contexts_for_validator)
                all_problems.extend(problems)

                for problem in problems:
                    problem_to_contexts_map[problem] = contexts_for_validator

                if problems:
                    logger.debug(
                        f"{validator.name} found {len(problems)} problems"
                    )

        logger.info(f"Found {len(all_problems)} total problems")

        # Phase 11: Instantiate Remediators
        logger.debug(f"Instantiating {len(remediator_classes)} remediator classes...")
        remediator_instances: List[BaseRemediator] = sorted(
            [cls(args) for cls in remediator_classes],
            key=lambda r: r.priority
        )
        logger.debug(f"Instantiated {len(remediator_instances)} remediators: {[r.name for r in remediator_instances]}")

        # Phase 12: Run Remediators
        remediation_states: Dict[ProblemType, ProblemRemediationState] = {}
        remediation_results: List[RemediationResult] = []

        should_run_remediation = any(
            getattr(args, f"fix_{name}", False)
            for name in ["jira", "config", "custom"]
        ) or args.dry_run
        
        logger.debug(f"Should run remediation? {should_run_remediation} (Dry run: {args.dry_run})")

        if should_run_remediation:
            logger.info("Running remediators...")

            for remediator in remediator_instances:
                logger.debug(f"--- Processing remediator: {remediator.name} ---")
                problems_to_process: list[tuple[ProblemType, dict[Type[ValidationContext], ValidationContext]]] = []
                
                handled_types = remediator.handles_problem_types()
                logger.debug(f"  Remediator handles types: {[t.__name__ for t in handled_types]}")
                
                for p in all_problems:
                    p_type = type(p)
                    is_handled = p_type in handled_types
                    
                    # Only log detail if handled or if we suspect it should be
                    if is_handled: 
                        logger.debug(f"  Problem {p_type.__name__}: Handled by this remediator.")
                        state = remediation_states.get(p)
                        should_remediate = remediator.should_remediate(p, state)
                        logger.debug(f"    Should remediate? {should_remediate} (State: {state})")
                        
                        if should_remediate:
                            # Verify we have context (or empty dict for failures)
                            ctx = problem_to_contexts_map.get(p)
                            if ctx is None:
                                logger.error(f"    CRITICAL: No context found for problem {p}!")
                            else:
                                problems_to_process.append((p, ctx))
                    # else:
                        # logger.debug(f"  Problem {p_type.__name__}: NOT handled.")

                if not problems_to_process:
                    logger.debug(f"  No problems to process for {remediator.name}")
                    continue

                logger.debug(
                    f"{remediator.name} processing {len(problems_to_process)} problems "
                    f"(priority {remediator.priority})"
                )

                results = remediator.remediate_all(
                    problems_to_process,
                    args.dry_run
                )
                logger.debug(f"  Got {len(results)} results from remediator.")

                for result in results:
                    if result.problem not in remediation_states:
                        remediation_states[result.problem] = ProblemRemediationState(
                            problem=result.problem
                        )

                    state = remediation_states[result.problem]
                    state.results.append(result)
                    state.remediated_by.append(remediator.name)

                    if result.locked:
                        state.locked = True

                remediation_results.extend(results)
        
        # Phase 13: Report Results
        reporter = get_reporter(args.output)
        reporter.report(all_problems, remediation_results, args)

        has_errors = any(p.severity == "ERROR" for p in all_problems)
        return 1 if has_errors else 0

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())