# 🔍 Validate

A flexible validation and auto-remediation framework for any system.

Validate configurations, detect issues, and automatically fix them — all through a plugin-based architecture that grows with your needs.

---

## ✨ Features

- **Plugin-based** — Domain logic lives in plugins, not the core
- **Auto-remediation** — Fix issues automatically, not just report them
- **Type-safe** — Strict typing throughout; problems carry all data needed to fix them
- **Extensible** — Add validators for Jira today, Kubernetes tomorrow
- **CI/CD friendly** — Standard exit codes, JSON output, configurable verbosity

---

## 📦 Installation

```bash
# From source
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### Jira Mirroring Validation

```bash
# Set up credentials
export JIRA_URL=https://your-instance.atlassian.net
export JIRA_EMAIL=your-email@example.com
export JIRA_TOKEN=your-api-token

# Validate a mirroring configuration
validate config.json

# Filter by tags
validate config.json --tags jira,screen

# Preview fixes without applying
validate config.json --fix-jira --dry-run

# Apply fixes
validate config.json --fix-jira
```

---

## 🎛️ CLI Options

### Output Control

| Option | Description |
|--------|-------------|
| `--verbose` | Detailed output with context |
| `--brief` | Summary counts only |
| `--silent` | No output (exit code only) |
| `--json` | Machine-readable JSON |

### Validation Control

| Option | Description |
|--------|-------------|
| `--tags TAG,TAG` | Run only validators with these tags |

### Remediation

| Option | Description |
|--------|-------------|
| `--fix-jira` | Apply Jira remediations |
| `--dry-run` | Show what would be fixed without applying |

### Plugin Options

Plugins add their own options with domain prefixes:

```bash
--jira-config FILE       # Jira mirroring config file
--jira-source-project    # Source project key
--jira-target-project    # Target project key
```

---

## 📊 Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success — no errors found |
| `1` | Validation errors found |
| `2` | Fatal tool error |
| `130` | Interrupted (Ctrl+C) |

---

## 🔌 Current Plugins

### Jira

**Validators:**
- Field existence in source/target projects
- CREATE screen field requirements
- EDIT screen field requirements
- Field schema compatibility
- Duplicate mapping detection

**Remediators:**
- Add missing fields to Jira screens

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [Project Identity](./docs/IDENTITY.md) | Mission, values, philosophy, UX |
| [Design Principles](./docs/DESIGN_PRINCIPLES.md) | Major decisions with rationale |
| [Architecture](./docs/ARCHITECTURE.md) | Components, data flow, structure |
| [Contributing](./CONTRIBUTING.md) | How to write plugins |

---

## 🤝 Contributing

Want to add a validator or remediator? See [CONTRIBUTING.md](./CONTRIBUTING.md) for the plugin development guide.

---

## 📄 License

[Add license here]
