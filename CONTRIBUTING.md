# Contributing to Validate

This guide covers how to extend the `validate` framework with new plugins. Before contributing, please read:

- [Project Identity](./docs/IDENTITY.md) — Our mission, values, and philosophy
- [Design Principles](./docs/DESIGN_PRINCIPLES.md) — Why we made specific decisions
- [Architecture](./docs/ARCHITECTURE.md) — How components fit together

Every contribution should trace back to these documents.

---

## Plugin Types

The framework has three plugin types:

| Type | Purpose | Location |
|------|---------|----------|
| **Context Provider** | Fetch data, build typed contexts | `src/validate/contextproviders/` |
| **Validator** | Analyze contexts, produce problems | `src/validate/validators/` |
| **Remediator** | Fix problems | `src/validate/remediators/` |

---

## Writing a Validator

### 1. Create the File

```python
# src/validate/validators/mydomain/my_validator.py

from validate.validators.base import BaseValidator
from validate.core.contexts.mydomain import MyDomainContext
from validate.core.problem_types.mydomain import MyProblemType

class MyValidator(BaseValidator):
    """One-sentence description of what this validates."""

    requires_context_types = [MyDomainContext]
    produces_problem_types = [MyProblemType]
    tags = ["mydomain", "specific-check"]

    def validate(self, contexts: dict) -> list:
        context = contexts[MyDomainContext]
        problems = []

        # Your validation logic here
        if something_is_wrong:
            problems.append(MyProblemType(
                # Include ALL data needed to fix this
                item_id=context.item_id,
                item_name=context.item_name,
                expected_value=expected,
                actual_value=actual,
                url=context.item_url,
            ))

        return problems
```

### 2. Key Principles

**Granularity:** Each validator should perform one specific check.

> **Rule of thumb:** "Would half of this validator also apply elsewhere?" If yes, split it.

**Data gathering:** Validators can fetch additional data beyond what the context provides, but must encapsulate everything in the problem object so remediators don't need to re-fetch.

**No fixing:** Validators never fix anything. They report problems with all required information. That's it.

---

## Writing a Problem Type

### 1. Create the Type

```python
# src/validate/core/problem_types/mydomain.py

from validate.core.problem_types.base import ProblemType, Severity

class MyProblemType(ProblemType, frozen=True):
    """Problem: Something is misconfigured."""

    # All data needed to understand AND fix this issue
    item_id: str
    item_name: str
    expected_value: str
    actual_value: str
    url: str

    severity: Severity = Severity.ERROR

    def get_description(self) -> str:
        return (
            f"'{self.item_name}' has value '{self.actual_value}' "
            f"but expected '{self.expected_value}'"
        )

    def get_location_description(self) -> str:
        return f"{self.item_name} ({self.item_id})"
```

### 2. Key Principles

**Self-contained:** Include IDs, names, URLs — everything a remediator or human needs to act without looking anything up.

**Immutable:** Problem types are frozen Pydantic models. Don't mutate them.

**No prescriptions:** Describe what's wrong and provide context. Don't tell anyone how to fix it.

---

## Writing a Remediator

### 1. Create the File

```python
# src/validate/remediators/mydomain/my_remediator.py

from validate.remediators.base import BaseRemediator, RemediationResult
from validate.core.problem_types.mydomain import MyProblemType

class MyRemediator(BaseRemediator):
    """Fixes MyProblemType by doing X."""

    handles_problem_types = [MyProblemType]
    priority = 100  # Lower runs first

    def remediate(self, problem: MyProblemType, contexts: dict, dry_run: bool) -> RemediationResult:
        if dry_run:
            return RemediationResult(
                success=True,
                message=f"Would fix {problem.item_name}",
                dry_run=True,
            )

        # Your fix logic here using data from the problem object
        # DO NOT fetch additional data — use what's in the problem

        return RemediationResult(
            success=True,
            message=f"Fixed {problem.item_name}",
            locked=True,  # Prevent other remediators from handling this
        )
```

### 2. Key Principles

**No data gathering:** Remediators act on information already in the problem object and contexts. If you need to fetch data, something is wrong upstream.

**Dry-run support:** Always support `dry_run=True` to preview changes.

**Locking:** Return `locked=True` if other remediators shouldn't also handle this problem.

---

## Writing a Context Provider

### 1. Create the File

```python
# src/validate/contextproviders/mydomain.py

from validate.contextproviders.base import BaseContextProvider
from validate.core.contexts.mydomain import MyDomainContext

class MyDomainContextProvider(BaseContextProvider):
    """Provides context for MyDomain validation."""

    provides_context_type = MyDomainContext

    @classmethod
    def register_arguments(cls, parser):
        parser.add_argument(
            "--mydomain-config",
            help="Path to MyDomain configuration",
        )

    def build_contexts(self, args) -> list:
        # Connect to external system
        # Fetch MINIMAL required data
        # Handle pagination for ALL results

        return [
            MyDomainContext(
                item_id=item["id"],
                item_name=item["name"],
                # ... minimal data
            )
            for item in items
        ]
```

### 2. Key Principles

**Minimal data:** Fetch only what validators and remediators need to run. Let validators fetch extras.

**Pagination:** Always handle pagination. A tool that only checks the first page is worse than useless.

**Caching:** Cache expensive resources (API clients, large fetches) so multiple plugins can share them.

---

## CLI Option Conventions

Plugin options must follow this pattern:

```
--<domain>-<descriptor>[-<optional-qualifier>]
```

**Good:**
- `--jira-project`
- `--jira-dry-run`
- `--k8s-namespace`

**Bad:**
- `--this-does-the-thing-that-it-does`
- `--project` (no domain prefix)

Keep it to 1-2 descriptive words after the domain prefix.

---

## Code Style

### General

- Functions should be ≤50 lines
- Explicit names over clever one-liners
- Readability over micro-optimization
- No placeholders or mock data in implementation code

### Typing

Strictest mypy settings. The goal: "damn, dude."

```python
# Good
def get_fields(project_id: str) -> list[FieldDefinition]:
    ...

# Bad
def get_fields(project_id):
    ...
```

---

## Testing

**Goal:** 95-100% coverage.

**Strategy:**
- Unit tests for all validators and remediators with mock contexts
- Integration tests for context providers
- Minimal e2e tests covering major workflows

Prefer real data over mocks where feasible.

---

## Checklist Before Submitting

- [ ] Validator/remediator is granular (single responsibility)
- [ ] Problem types include all data needed to fix
- [ ] Remediators don't fetch additional data
- [ ] CLI options follow `--<domain>-<descriptor>` pattern
- [ ] Pagination is handled in context providers
- [ ] Types are strict (mypy passes)
- [ ] Tests are included
- [ ] Code traces back to [IDENTITY.md](./docs/IDENTITY.md)

---

*When in doubt, reference the [Project Identity](./docs/IDENTITY.md). If your contribution can't be justified by those values, reconsider the approach.*
