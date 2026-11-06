# Documentation

Start with the root [README](../README.md) for a first report and [CONTRIBUTING](../CONTRIBUTING.md) for development setup and checks.
Each topic below has one canonical guide; a skill reference may serve as that guide for both readers and agents.
Paths and commands assume the repository root unless stated otherwise.

## User Guides

Choose a guide for the report task; its overview introduces any detailed child references.

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
| Discovery, evidence-based selection, issue review, approval, and publication | [Rollup Workflow](../skills/admin-wr/references/rollup-workflow.md) |
| Plan and execution TSV records, state/approval pairs, and cover presentation | [Bundle Plan and Execution Formats](../skills/admin-wr/references/rollup-workflow/formats.md) |
| Prior-run lookup, PDF/hash verification, cumulative history, and recovery | [Administrator Bundle History](../skills/admin-wr/references/rollup-workflow/history.md) |
| Slack webhook setup, message approval, sending, and recovery | [Slack Notifications](../skills/admin-wr/references/slack-notifications.md) |

## Contributor Guides

The [Development Guide](development.md) introduces the shared architecture, contracts, documentation workflow, and validation references.
Use the following documents for the specific contribution concern.

| Topic | Canonical guide |
| --- | --- |
| Source ownership, repository files, editor boundaries, and command entry points | [Shared Architecture](development/architecture.md) |
| Shell portability, setup transactions, build isolation, PDF publication, and update safeguards | [Shell and Build Contracts](development/build-contracts.md) |
| Document ownership, the mddt writing procedure, skill maintenance, and CI minimum checks | [Documentation Maintenance](development/documentation.md) |
| Proportionate checks for report guidance, skills, the shared editor, and common workflows | [Development Validation](development/validation.md) |
| Administrator storage, judgment and builder boundaries, record parsing, publication, and notifications | [Administrator Development](admin-development.md) |
| Versioning, changelog conventions, tag grammar, and checkout versions | [Versioning and Releases](releases.md) |
| Confirmed release preparation, manual validation, tag CI, publication, and retry | [Release Publication](releases/publishing.md) |
| Native Windows implementation and packaging | [Windows Development Guide](../windows/CONTRIBUTING.md) |

[CHANGELOG.md](../CHANGELOG.md) records repository release history; the [Windows changelog](../windows/CHANGELOG.md) records native internal changes under that version authority.
