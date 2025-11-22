# Validate — Project Identity

This document defines the foundational identity of the `validate` project: its mission, values, philosophy, and the experience it aims to deliver. Every design decision, architectural choice, and implementation detail should trace back to this document.

---

## Mission

**Validate systems and auto-remediate issues across any domain, so teams can confidently manage complex systems at scale.**

---

## Core Values

### Simple Flexibility
Extensibility that doesn't sacrifice readability. The system should be easy to extend with minimal code, but that code should be intuitive and self-explanatory.

### Explicit Over Magic
Clear, traceable behavior. No hidden conventions or implicit logic. A developer reading the code should be able to understand what happens and why.

### Strictest Correctness
Type safety at the highest level. No placeholders, no mock data (unless absolutely necessary). Real data, real tests, real confidence.

### Actionability
Problems must include everything needed to fix them. A validator should never report "something is wrong" — it should report exactly what, where, and provide all information required to fix it.

### Trust Through Transparency
Plugin authors define what constitutes a "change" in their domain. Users verify that plugins are trustworthy. The framework itself is domain-agnostic and makes no assumptions.

---

## Philosophy

### Invest Upfront
A few extra days for a robust, extensible system beats weeks of refactoring later. Design around reasonable future flex points.

### Reactive Evolution
Add validators and remediators as patterns emerge. Don't anticipate every possible use case — let real pain points drive development.

### Stateless and Deterministic
Same inputs produce same outputs. No state between runs. Predictable, reproducible behavior.

### Documentation as First-Class
Documentation helps both humans and LLMs understand context. Comprehensive docs are not optional — they're part of the deliverable.

### Organization
Before adding a new document or section of code, look for pre-existing locations where it would fit or existing patterns to follow. Don't create new structures when existing ones suffice.

---

## User Experience

### The Feeling

Users should feel:
- **In control** — Standard, familiar CLI patterns; never overwhelmed
- **Trustworthy** — Confident that validation is thorough and remediation is safe
- **Predictable** — No surprises; deterministic behavior
- **Empowered** — Clear explanations with actionable fixes

### Output Philosophy

**Easy to read without sacrificing information.**

- Standard options: `--verbose`, `--brief`, `--silent` for controlling output level
- Color is welcome — ANSI escapes improve readability and add life
- Emojis are welcome — a touch of whimsy makes structured output feel alive
- Consistent formatting across all validators and remediators

### CLI Option Conventions

Plugin options should be:
- **Consistent and intuitive** with domain prefixes
- **Concise** — 1-2 extra words that clearly explain purpose
- **Pattern:** `--<domain>-<descriptor>[-<optional-qualifier>]`

Examples:
- `--jira-project` ✓
- `--jira-dry-run` ✓
- `--this-does-the-thing-that-it-does` ✗

---

## Target Audience

### Primary Users
The DevOps team managing complex configurations (e.g., Jira mirroring with 70+ project mappings).

### Secondary Users
Anyone needing to validate system configurations and optionally auto-remediate issues. The framework is intentionally generic for future applicability.

### Plugin Authors
Developers extending the framework with new context providers, validators, and remediators. They should find the plugin API intuitive, type-safe, and well-documented.

---

## How to Use This Document

When making decisions about design, architecture, or implementation:

1. **Reference this document** — Does your decision align with the mission, values, and philosophy?
2. **Cite specific sections** — In design docs, architecture docs, and technical docs, reference which identity principles your decisions uphold
3. **Trace the line** — Any technical decision should trace coherently back to this identity

If a decision conflicts with this document, either:
- Reconsider the decision, or
- Propose an update to this identity (with clear rationale)

---

*This document is the source of truth for what `validate` is and aspires to be.*
