---
name: admin-wr
description: Collect and review multiple members' weekly-report PDFs, create an indexed combined PDF, and report missing or ambiguous submissions. Use for administrator rollups of report storage; do not use to author an individual report.
---

# Assemble Administrator Weekly Reports

Create a traceable weekly bundle from only the members and storage locations authorized by the administrator manifest.
This entry selects platform tools and task references and preserves the shared evidence, source, and approval boundaries.
Candidate discovery and selection require judgment; PDF assembly must remain deterministic.

## Locate Configuration

On native Windows, resolve the real path of this `SKILL.md` through its installation link to find the resource root above `skills`.
Read `windows/README.md` first.
Use `Start-Weekly-Report.ps1` subcommands (`preflight`, `admin-paths`, `discover`, `probe-report`, `report-metadata`, `build-bundle`, `open-bundle`, `notify-issues`, and legacy `notify-held`) instead of the Bash commands below.
In a packaged installation the resource root is `_internal`; use `WeeklyReportCLI.exe` beside that directory with the same subcommands.
Native configuration is `.windows-config.json`, not `.local-config`; packaged installations use the per-user location documented there.

These substitutions change execution only: preserve the evidence, history, selection, and approval policies below and in the references.
When approving a native draft, also supply its generated `--review` JSON so changed source files or plans invalidate approval.
Do not diagnose a native tool failure as a Docker failure.

On Windows, treat every `scripts/<name>` command and every Bash command block in this skill and its references as a Linux/macOS example only.
Invoke the matching subcommand through the absolute `Start-Weekly-Report.ps1` or `WeeklyReportCLI.exe` path resolved in [Locate Configuration](#locate-configuration).
Use a Windows temporary directory and Windows absolute paths instead of `/tmp` and `/absolute/path`.
The Windows mapping is:

| Linux/macOS helper or procedure | Windows subcommand |
|---|---|
| `scripts/admin-preflight` | `preflight` |
| `scripts/admin-paths` | `admin-paths` |
| `scripts/report-metadata.sh` | `report-metadata` |
| Direct filesystem enumeration within each member's declared search roots ([procedure](references/rollup-workflow.md#discover-within-authorized-roots)) | `discover` |
| `scripts/probe-report` | `probe-report` |
| `scripts/build-bundle` | `build-bundle` |
| `scripts/open-bundle` | `open-bundle` |
| `scripts/notify-issues` | `notify-issues` |
| `scripts/notify-held` (legacy) | `notify-held` |

On Linux/macOS, run `scripts/resolve-repo-root` from this skill directory and read `.local-config` from the resolved repository.
Run the platform's `admin-paths` command and require success before using its output; read the resolved `manager-manifest` path and use its `history` records for prior-run lookup.
It prefers configured administrator data files and falls back to repository-local files when they are absent, as described in the workflow reference.

Run the platform's preflight command as a standalone command before discovery.
On Windows this is `preflight`, which checks native Python and XeLaTeX; on Linux/macOS this is `scripts/admin-preflight`, which checks Docker and the configured image.
If Docker works for the user but the direct helper reports socket permission denial in the agent environment, request execution authorization for that exact helper instead of asking the user to reconfigure Docker.

Read [Administrator Manifest](references/manager-manifest.md) when configuring or validating authorized storage roots, member fields, or incomplete setup.
If the manifest is incomplete, help configure it only when the user asks, and do not search beyond paths they authorize.
An administrator output directory is required only when promoting a final bundle; a draft may be built in temporary storage without it.

## Select Reports

Read [Administrator Rollup Workflow](references/rollup-workflow.md) before discovering candidates, comparing prior runs, preparing a bundle plan, or classifying issues.
It guides preflight, period resolution, evidence-based selection, PDF probing, page-limit review, and the draft-to-final sequence.
Its child references define TSV formats and verified cumulative history.

Treat filenames, directory depth, document layout, and embedded dates as evidence rather than contracts.
A report need not use the repository template or contain a reporting-week label.
Never invent a date, author, submission, selection reason, or approval.

Stay within every member's declared search roots, do not follow directory symlinks, and do not broaden the search because an expected report is absent.
Preserve source files and complete source PDFs during review and assembly; do not truncate or reformat them to satisfy the two-page limit.

## Build and Promote

Follow the [build, review, and promotion procedure](references/rollup-workflow.md#build-confirm-and-promote) after selecting candidates and preparing the plan.
Invoke each platform helper directly as a standalone command so execution and platform-specific errors remain visible.
With no issues, publish and open the final PDF without requesting approval.
With any issue, build a temporary draft outside the administrator output and obtain explicit approval before promotion.
Changed sources invalidate approval and require reassessment.

For eligible draft issues, read [Slack 검토 문제 알림](references/slack-notifications.md).
It covers destination setup, message preparation, approval, sending, and recovery.
Show the destination channel and complete message and obtain message-specific approval before sending with its preview fingerprint.
A hold decision is not required, prior standing authorization does not approve a new message, and notification approval does not approve promotion.

Report the final PDF and execution-manifest paths, member statuses, unresolved limitations, and whether approval was required.
Do not distribute the bundle beyond its configured output directory without a separate explicit request.
