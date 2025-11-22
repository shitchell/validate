# Validate — Architecture

This document describes the technical architecture of the `validate` framework: its components, data flow, and how they interact. Each section references the [Design Principles](./DESIGN_PRINCIPLES.md) and [Project Identity](./IDENTITY.md) it implements.

---

## Overview

The `validate` framework is a plugin-based orchestration system with three primary actor types:

| Component | Role |
|-----------|------|
| **Context Provider** | Fetches data from external systems, builds typed contexts |
| **Validator** | Analyzes contexts, produces problem objects |
| **Remediator** | Fixes problems using information from contexts and problem objects |

The **Orchestrator** (`main.py`) coordinates these actors without knowing anything about specific domains.

**Implements:** [Plugin-First Architecture](./DESIGN_PRINCIPLES.md#1-plugin-first-architecture)

---

## Data Flow

```
┌─────────────┐     ┌──────────────────┐     ┌────────────┐     ┌─────────────┐
│  Discovery  │ ──▶ │ Context Building │ ──▶ │ Validation │ ──▶ │ Remediation │
└─────────────┘     └──────────────────┘     └────────────┘     └─────────────┘
```

### 1. Discovery
The orchestrator finds all available plugins (internal and external) via entry points.

### 2. Selection
Validators are selected based on:
- User input (`--tags jira,screen`)
- Auto-detection from provided arguments

### 3. Context Building
- Validators declare required context types (`requires_context_types`)
- Orchestrator instantiates context providers for those types
- Context providers fetch data and build typed context objects

**Implements:** [Typed Contexts](./DESIGN_PRINCIPLES.md#2-typed-contexts), [Context Providers as Singleton Factories](./DESIGN_PRINCIPLES.md#5-context-providers-as-singleton-factories)

### 4. Validation
- Each validator receives its required contexts
- Validators analyze data and produce `ProblemType` objects
- Problems contain all information needed for remediation

**Implements:** [Rich, Self-Contained Problem Objects](./DESIGN_PRINCIPLES.md#3-rich-self-contained-problem-objects), [Data Gathering Responsibility Chain](./DESIGN_PRINCIPLES.md#12-data-gathering-responsibility-chain)

### 5. Remediation
- Remediators are sorted by priority
- Each remediator receives problems it can handle, plus source contexts
- Remediators can lock problems to prevent subsequent handlers

**Implements:** [Prioritized Remediation with Locking](./DESIGN_PRINCIPLES.md#7-prioritized-remediation-with-locking)

### 6. Reporting
Results are formatted based on output mode (`--verbose`, `--brief`, `--json`).

**Implements:** [User Experience](./IDENTITY.md#user-experience)

---

## Directory Structure

```
src/validate/
├── __init__.py
├── main.py                      # Orchestrator entry point
├── core/
│   ├── cli.py                   # Argument parsing
│   ├── models.py                # Core data models
│   ├── plugin_discovery.py      # Plugin discovery system
│   ├── validator_selection.py   # Determines active validators
│   ├── context_management.py    # Context provider management
│   ├── contexts/
│   │   ├── base.py              # ValidationContext base class
│   │   └── jira.py              # JiraValidationContext
│   └── problem_types/
│       ├── base.py              # ProblemType base class
│       └── jira.py              # Jira-specific problem types
├── validators/
│   ├── base.py                  # BaseValidator ABC
│   └── jira/                    # Jira validators
├── remediators/
│   ├── base.py                  # BaseRemediator ABC
│   └── jira/                    # Jira remediators
├── contextproviders/
│   ├── base.py                  # BaseContextProvider ABC
│   └── jira.py                  # JiraContextProvider
└── reporting/
    ├── reporter.py              # Reporter base and factory
    ├── verbose_formatter.py
    ├── brief_formatter.py
    └── json_formatter.py
```

**Implements:** [Philosophy: Organization](./IDENTITY.md#organization)

---

## Component Details

### Context Providers

**Location:** `src/validate/contextproviders/`

**Responsibilities:**
- Register CLI arguments for their domain
- Connect to external systems (APIs, databases)
- Fetch and cache data
- Build typed context objects

**Base class:** `BaseContextProvider`

**Example:** `JiraContextProvider`
- Reads `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN` from environment
- Fetches field definitions, screen configurations, required fields
- Builds `JiraValidationContext` for each source→target mapping
- Caches the Jira client for reuse

**Implements:** [Dependency Injection for Plugins](./DESIGN_PRINCIPLES.md#6-dependency-injection-for-plugins), [Mandatory Pagination Handling](./DESIGN_PRINCIPLES.md#10-mandatory-pagination-handling)

---

### Validators

**Location:** `src/validate/validators/`

**Responsibilities:**
- Declare required context types
- Register problem types they can produce
- Declare tags for filtering
- Analyze contexts and emit problem objects

**Base class:** `BaseValidator`

**Key attributes:**
- `requires_context_types: list[Type[ValidationContext]]`
- `produces_problem_types: list[Type[ProblemType]]`
- `tags: list[str]`

**Current Jira validators:**
- `FieldExistenceValidator` — Fields exist in source/target projects
- `CreateScreenValidator` — CREATE screen has required fields
- `EditScreenValidator` — EDIT screen has mapped fields
- `SchemaCompatibilityValidator` — Field types are compatible
- `DuplicateMappingValidator` — No duplicate issue type mappings

**Implements:** [Granular Validators and Remediators](./DESIGN_PRINCIPLES.md#11-granular-validators-and-remediators)

---

### Problem Types

**Location:** `src/validate/core/problem_types/`

**Responsibilities:**
- Carry all data needed to understand and fix an issue
- Provide human-readable descriptions
- Support deduplication via hash keys

**Base class:** `ProblemType` (Pydantic model, frozen)

**Key attributes:**
- `severity: Severity` (ERROR, WARNING, INFO)
- `get_description() -> str`
- `get_location_description() -> str`

**Current Jira problem types:**
- `FieldMissingFromCreateScreen`
- `FieldMissingFromEditScreen`
- `RequiredFieldMissingFromConfig`
- `FieldMissingFromSourceProject`
- `FieldMissingFromTargetProject`
- `FieldSchemaMismatch`
- `DuplicateIssueTypeMapping`

**Implements:** [Rich, Self-Contained Problem Objects](./DESIGN_PRINCIPLES.md#3-rich-self-contained-problem-objects)

---

### Remediators

**Location:** `src/validate/remediators/`

**Responsibilities:**
- Declare which problem types they handle
- Declare priority (lower runs first)
- Fix problems using provided data
- Support dry-run mode
- Optionally lock problems

**Base class:** `BaseRemediator`

**Key attributes:**
- `handles_problem_types: list[Type[ProblemType]]`
- `priority: int`

**Current Jira remediators:**
- `JiraScreenRemediator` — Adds missing fields to Jira screens

**Implements:** [Prioritized Remediation with Locking](./DESIGN_PRINCIPLES.md#7-prioritized-remediation-with-locking), [Data Gathering Responsibility Chain](./DESIGN_PRINCIPLES.md#12-data-gathering-responsibility-chain)

---

### Reporting

**Location:** `src/validate/reporting/`

**Formatters:**
- `VerboseFormatter` — Detailed console output with symbols and colors
- `BriefFormatter` — Summary counts only
- `JsonFormatter` — Machine-readable JSON output

**Implements:** [User Experience: Output Philosophy](./IDENTITY.md#output-philosophy)

---

## Execution Flow

The orchestrator (`main.py`) follows this sequence:

1. **Discover plugins** — Find all validators, remediators, context providers
2. **Build argument parser** — Dynamically add arguments from all plugins
3. **Parse arguments** — Process CLI input
4. **Select validators** — Filter by tags or auto-detect from arguments
5. **Validate arguments** — Ensure required args for active validators
6. **Check compatibility** — Warn about unfixable problem types
7. **Determine required contexts** — Collect context types needed by validators
8. **Instantiate context providers** — Create providers for required contexts
9. **Build contexts** — Fetch data and construct typed contexts
10. **Run validators** — Execute each validator against its contexts
11. **Instantiate remediators** — Create and sort by priority
12. **Run remediators** — Fix problems (if `--fix-*` or `--dry-run`)
13. **Report results** — Format and output problems and remediation results
14. **Exit** — Return appropriate exit code

**Implements:** [Standardized Exit Codes](./DESIGN_PRINCIPLES.md#9-standardized-exit-codes)

---

## Configuration

### Environment Variables (Secrets)
```bash
JIRA_URL=https://your-instance.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_TOKEN=your-api-token
```

### Configuration File (`.validate.yaml`)
Shared settings that can be committed to version control.

### Plugin Defaults
Fallback values defined in plugin code.

**Implements:** [Configuration Hierarchy](./DESIGN_PRINCIPLES.md#8-configuration-hierarchy)

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success — no errors found |
| `1` | Validation errors found |
| `2` | Fatal tool error |
| `130` | Interrupted by user (Ctrl+C) |

**Implements:** [Standardized Exit Codes](./DESIGN_PRINCIPLES.md#9-standardized-exit-codes)

---

*This architecture implements the [Design Principles](./DESIGN_PRINCIPLES.md), which in turn uphold the [Project Identity](./IDENTITY.md). Any architectural change should trace back through this chain.*
