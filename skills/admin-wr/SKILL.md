---
name: admin-wr
description: Collect and review multiple members' weekly-report PDFs, create an indexed combined PDF, and report missing or ambiguous submissions. Use for administrator rollups of report storage; do not use to author an individual report.
---

# Assemble Administrator Weekly Reports

Create a traceable weekly bundle from only the members and storage locations authorized by the administrator manifest. Candidate discovery and selection require judgment; PDF assembly must remain deterministic.

## Locate Configuration

On native Windows, resolve the real path of this `SKILL.md` through its installation link to find the resource root above `skills`. Read `windows/README.md` first. Use `Start-Weekly-Report.ps1` subcommands (`preflight`, `admin-paths`, `discover`, `probe-report`, `report-metadata`, `build-bundle`, `open-bundle`, and `notify-held`) instead of the Bash commands below. In a packaged installation the resource root is `_internal`; use `WeeklyReportCLI.exe` beside that directory with the same subcommands. Native configuration is `.windows-config.json`, not `.local-config`; packaged installations use the per-user location documented there. These substitutions change execution only: preserve the evidence, history, selection, and approval policies below and in the references. When approving a native draft, also supply its generated `--review` JSON so changed source files or plans invalidate approval. Do not diagnose a native tool failure as a Docker failure.

On Windows, treat every `scripts/<name>` command and every Bash command block in this skill and its references as a Linux/macOS example only. Invoke the matching subcommand through the absolute `Start-Weekly-Report.ps1` or `WeeklyReportCLI.exe` path resolved above. Use a Windows temporary directory and Windows absolute paths instead of `/tmp` and `/absolute/path`. The Windows mapping is:

| Linux/macOS helper or procedure | Windows subcommand |
|---|---|
| `scripts/admin-preflight` | `preflight` |
| `scripts/admin-paths` | `admin-paths` |
| `scripts/report-metadata.sh` | `report-metadata` |
| Direct filesystem enumeration within each member's declared search roots ([procedure](references/rollup-workflow.md#discover-within-authorized-roots)) | `discover` |
| `scripts/probe-report` | `probe-report` |
| `scripts/build-bundle` | `build-bundle` |
| `scripts/open-bundle` | `open-bundle` |
| `scripts/notify-held` | `notify-held` |

On Linux/macOS, run `scripts/resolve-repo-root` from this skill directory and read `.local-config` from the resolved repository.
Run the platform's `admin-paths` command and require success before using its output; read the resolved `manager-manifest` path and use its `history` records for prior-run lookup.
It prefers configured administrator data files and falls back to repository-local files when they are absent, as described in the workflow reference.
Run the platform's preflight command as a standalone command before discovery. On Windows this is `preflight`, which checks native Python and XeLaTeX; on Linux/macOS this is `scripts/admin-preflight`, which checks Docker and the configured image.
If Docker works for the user but the direct helper reports socket permission denial in the agent environment, request execution authorization for that exact helper instead of asking the user to reconfigure Docker.

- If the manager manifest is incomplete, help configure it only when the user asks, and do not search beyond paths they authorize.
- An administrator output directory is required only when promoting a final bundle. A draft may be built in temporary storage without it.
- Read [references/manager-manifest.md](references/manager-manifest.md) when configuring or validating the manifest.

## Select Reports

Read [references/rollup-workflow.md](references/rollup-workflow.md) before discovering candidates, comparing prior runs, preparing a bundle plan, or classifying issues.

Treat filenames, directory depth, document layout, and embedded dates as evidence rather than contracts. A report need not use the repository template or contain a reporting-week label. Never invent a date, author, submission, selection reason, or approval.

Stay within every member's declared search roots, do not follow directory symlinks, and do not broaden the search because an expected report is absent. Preserve source files.
Run the platform's `probe-report` command as a standalone command for every proposed source before writing the plan.
Check each person's weekly report against the two-page maximum using the probe's page count; follow the workflow reference for overlength warnings and the narrow necessity exception.
Preserve complete source PDFs during review and assembly; do not truncate or reformat them to satisfy the limit.

## Build and Promote

Use the platform's `build-bundle` command after selecting the best candidate for each member and writing the required temporary plan TSV, including cumulative weekly inclusion history as described in the workflow reference.
Invoke it directly rather than wrapping it in another shell command or pipeline so execution and platform-specific errors remain visible.

- With no issues, build and promote a complete bundle, then open the final PDF at the builder's printed output path with the platform's `open-bundle` command.
- With any issue, build a draft outside the configured administrator output and use the printed review path to open it for the user with the platform's `open-bundle` command. Include a clickable PDF path and the evidence in the review request, then obtain explicit approval before promotion.
- On approval, confirm selected source hashes have not changed and rebuild with `--approved-with-issues`. If they changed, reassess instead of publishing stale choices.
- Never use `--draft` with the configured administrator output directory or its descendants.
- If the administrator decides to hold because required reports are missing, follow [references/slack-notifications.md](references/slack-notifications.md) for an optional Slack notice. A draft alone is not a hold decision; send only when Slack notifications have been authorized for that channel and this condition.

Final execution TSVs go to the `history-output` directory reported by the platform's `admin-paths` command (repository-local by default); draft TSVs live under `.manifests/` in the temporary review directory.
Report the final PDF and execution-manifest paths, member statuses, unresolved limitations, and whether approval was required. Do not distribute the bundle beyond its configured output directory without a separate explicit request.
