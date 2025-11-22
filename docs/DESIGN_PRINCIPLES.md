# Validate — Design Principles

This document captures the major design decisions for the `validate` framework and the rationale behind each. Every principle references the [Project Identity](./IDENTITY.md) it upholds.

---

## 1. Plugin-First Architecture

**Principle:** The core framework is domain-agnostic. All domain logic (Jira, Kubernetes, APIs) resides in plugins discovered via Python namespace packages and entry points.

**Rationale:** New domains can be added by installing a Python package (`pip install validate-kubernetes`) without modifying the core. The ecosystem can grow indefinitely without bloating the orchestrator.

**Upholds:**
- [Simple Flexibility](./IDENTITY.md#simple-flexibility) — Easy to extend with minimal code
- [Trust Through Transparency](./IDENTITY.md#trust-through-transparency) — Framework makes no domain assumptions

---

## 2. Typed Contexts

**Principle:** Data passed to validators is encapsulated in strictly typed Pydantic models (e.g., `JiraValidationContext`), not generic dictionaries.

**Rationale:** Typed contexts enable static analysis (mypy) and IDE autocompletion. This prevents runtime `KeyError` bugs and makes available data self-documenting for plugin developers.

**Upholds:**
- [Strictest Correctness](./IDENTITY.md#strictest-correctness) — Type safety at the highest level
- [Explicit Over Magic](./IDENTITY.md#explicit-over-magic) — Clear, traceable data structures

---

## 3. Rich, Self-Contained Problem Objects

**Principle:** Validators return rich objects (e.g., `FieldMissingFromCreateScreen`) containing all specific IDs and data needed to understand the issue. They are not just error strings or codes.

**Rationale:** Remediators should not have to re-discover data. By packaging the field ID, screen ID, project key, and relevant URLs into the problem object, the remediator has everything needed to act immediately. This avoids duplicate API calls and logic.

**Upholds:**
- [Actionability](./IDENTITY.md#actionability) — Problems include everything needed to fix them
- [Philosophy: Stateless and Deterministic](./IDENTITY.md#stateless-and-deterministic) — No re-fetching required

---

## 4. Explicit Multi-Context Injection

**Principle:** Validators and remediators declare required contexts by type (`requires_context_types`). They receive a dictionary keyed by those types.

**Rationale:** This allows for complex, cross-domain validation (e.g., "Verify this Jira ticket matches this GitHub PR"). Keying by `Type` (the class itself) provides a type-safe, unambiguous lookup mechanism, eliminating error-prone list indexing or `isinstance` checks.

**Upholds:**
- [Simple Flexibility](./IDENTITY.md#simple-flexibility) — Easy to request multiple contexts
- [Strictest Correctness](./IDENTITY.md#strictest-correctness) — Type-safe lookup mechanism
- [Explicit Over Magic](./IDENTITY.md#explicit-over-magic) — Explicit declaration of dependencies

---

## 5. Context Providers as Singleton Factories

**Principle:** Context providers implement caching logic to ensure expensive resources (API connections, large data fetches) are created/fetched only once per execution.

**Rationale:** Multiple plugins can request the same provider and receive the same cached, authenticated instance. This effectively implements a "shared object" mechanism without global state.

**Upholds:**
- [Philosophy: Stateless and Deterministic](./IDENTITY.md#stateless-and-deterministic) — Shared state within a single run, but stateless between runs
- [Simple Flexibility](./IDENTITY.md#simple-flexibility) — Plugins don't manage their own connections

---

## 6. Dependency Injection for Plugins

**Principle:** Plugins acquire external dependencies (like `jira_client`) via their corresponding context provider, not from the main orchestrator.

**Rationale:** The core orchestrator should not know how to construct a Jira client, Kubernetes client, or database connection. This inversion of control keeps the main loop generic and allows plugins to manage their own lifecycle and configuration.

**Upholds:**
- [Simple Flexibility](./IDENTITY.md#simple-flexibility) — Plugins are self-contained
- [Trust Through Transparency](./IDENTITY.md#trust-through-transparency) — Framework doesn't impose dependency patterns

---

## 7. Prioritized Remediation with Locking

**Principle:** Remediators have a `priority` attribute and run in order. A remediator can return `locked=True` to prevent subsequent remediators from processing the same problem.

**Rationale:** Multiple remediators might handle the same problem type differently. Priority ensures deterministic execution order. Locking prevents race conditions or conflicting modifications to external systems.

**Upholds:**
- [Philosophy: Stateless and Deterministic](./IDENTITY.md#stateless-and-deterministic) — Predictable execution order
- [Trust Through Transparency](./IDENTITY.md#trust-through-transparency) — Clear rules for conflict resolution

---

## 8. Configuration Hierarchy

**Principle:** Configuration loads from: Environment Variables (secrets) → `.validate.yaml` (shared settings) → Plugin Defaults.

**Rationale:** Secrets (e.g., Jira tokens) must never be committed. Shared settings (e.g., Jira URL) should be committed for team consistency. This hierarchy satisfies both security and usability.

**Upholds:**
- [Trust Through Transparency](./IDENTITY.md#trust-through-transparency) — Clear precedence rules
- [Explicit Over Magic](./IDENTITY.md#explicit-over-magic) — No hidden configuration sources

---

## 9. Standardized Exit Codes

**Principle:** The CLI returns specific exit codes: `0` (success), `1` (validation errors found), `>1` (fatal tool error).

**Rationale:** CI/CD pipelines need to distinguish between "the tool crashed" (retry might help) and "validation failed" (code change required). Standard exit codes make this machine-readable.

**Upholds:**
- [Actionability](./IDENTITY.md#actionability) — Clear signals for automation
- [User Experience: Predictable](./IDENTITY.md#the-feeling) — No surprises in behavior

---

## 10. Mandatory Pagination Handling

**Principle:** All API interactions in context providers must handle pagination (loop through all pages of results).

**Rationale:** A validation tool that only checks the first 50 items is worse than useless — it provides false confidence. Pagination ensures the tool works reliably on production-scale datasets.

**Upholds:**
- [Strictest Correctness](./IDENTITY.md#strictest-correctness) — Real data, real confidence
- [Actionability](./IDENTITY.md#actionability) — Complete information for decision-making

---

## 11. Granular Validators and Remediators

**Principle:** Each validator and remediator should perform a single, specific check or action. Never a broad "jira" validator — always targeted checks.

**Rationale:** Granularity enables composition and reuse. If half a validator would apply in another use case, it should be split.

**Rule of thumb:** "Would half of this also be applicable elsewhere?" If yes, split it.

**Upholds:**
- [Simple Flexibility](./IDENTITY.md#simple-flexibility) — Easy to compose and reuse
- [Philosophy: Organization](./IDENTITY.md#organization) — Follow existing patterns

---

## 12. Data Gathering Responsibility Chain

**Principle:**
- Context providers gather the bare minimum for validators and remediators to run
- Validators gather additional data as needed and encapsulate everything in problem objects
- Remediators gather nothing — they act solely on provided information

**Rationale:** This clear separation prevents duplicate data fetching and ensures remediators can be tested in isolation with mock problem objects.

**Upholds:**
- [Explicit Over Magic](./IDENTITY.md#explicit-over-magic) — Clear responsibility boundaries
- [Actionability](./IDENTITY.md#actionability) — Problems are self-contained

---

*Each principle in this document should trace back to [IDENTITY.md](./IDENTITY.md). If a design decision cannot be justified by the project identity, reconsider the decision or propose an identity update.*
