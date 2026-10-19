# Documentation

Start with the root [README](../README.md) for a first report and [CONTRIBUTING](../CONTRIBUTING.md) for development setup and checks.
Each topic below has one canonical guide; a skill reference may serve as that guide for both readers and agents.
Paths and commands assume the repository root unless stated otherwise.

## User Guides

| Topic | Canonical guide |
| --- | --- |
| Bash/Docker installation, skill links, administrator setup, configuration, and automatic updates | [Setup and Updates](setup.md) |
| Source creation, build options, output semantics, automatic values, and LaTeX helper examples | [Report Sources and Builds](report-workflow.md) |
| Shared writing requirements, references, page limit, and exceptions | [Report Policy](report-policy.md) |
| Browser editing, source preservation, conflicts, and export validation | [Visual Editing](visual-editing.md) |
| Native Windows installation and operation | [Windows guide](../windows/README.md) |

## Canonical Skill References

The skill entry points route agent work; these references own the detailed task procedures rather than duplicating them in a separate manual.
Shared authoring requirements remain in [Report Policy](report-policy.md), and [template comments](../template.tex) provide adaptable prompts and examples.

| Topic | Canonical reference |
| --- | --- |
| Report location, identity, scaffolding, and comment preservation | [Report Conventions](../skills/wr-wr/references/report-conventions.md) |
| Evidence, author perspective, editorial stages, and content revision | [Content Quality](../skills/wr-wr/references/content-quality.md) |
| Package use, LaTeX repair, body-reference checks, and PDF validation | [LaTeX and Build Support](../skills/wr-wr/references/latex-and-build.md) |
| Agent assistance with the visual editor and Artifact integrations | [Visual Editing Assistance](../skills/wr-wr/references/visual-editing.md) |
| Administrator configuration schema and authorized search roots | [Manager Manifest](../skills/admin-wr/references/manager-manifest.md) |
| Discovery, selection, approval, plan and execution formats, publication, and history | [Rollup Workflow](../skills/admin-wr/references/rollup-workflow.md) |
| Slack webhook setup, message approval, sending, and recovery | [Slack Notifications](../skills/admin-wr/references/slack-notifications.md) |

## Contributor Guides

| Topic | Canonical guide |
| --- | --- |
| Architecture, portability, safety, skill maintenance, validation, and document ownership | [Development Guide](development.md) |
| Administrator storage, builder boundaries, artifact safety, and notification contracts | [Administrator Development](admin-development.md) |
| Versioning, changelog conventions, CI, and release publication | [Versioning and Releases](releases.md) |
| Native Windows implementation and packaging | [Windows Development Guide](../windows/CONTRIBUTING.md) |

[CHANGELOG.md](../CHANGELOG.md) records repository release history; the [Windows changelog](../windows/CHANGELOG.md) records native internal changes under that version authority.
