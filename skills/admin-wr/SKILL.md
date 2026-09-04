---
name: admin-wr
description: Collect and review multiple members' weekly-report PDFs, create an indexed combined PDF, and report missing or ambiguous submissions. Use for administrator rollups of report storage; do not use to author an individual report.
---

# Assemble Administrator Weekly Reports

Create a traceable weekly bundle from only the members and storage locations authorized by the administrator manifest. Candidate discovery and selection require judgment; PDF assembly must remain deterministic.

## Locate Configuration

Run `scripts/resolve-repo-root` from this skill directory. Read `.manager-manifest.toml` and `.local-config` from the resolved repository.

- If the manager manifest is incomplete, help configure it only when the user asks, and do not search beyond paths they authorize.
- An administrator output directory is required only when promoting a final bundle. A draft may be built in temporary storage without it.
- Read [references/manager-manifest.md](references/manager-manifest.md) when configuring or validating the manifest.

## Select Reports

Read [references/rollup-workflow.md](references/rollup-workflow.md) before discovering candidates, comparing prior runs, preparing a bundle plan, or classifying issues.

Treat filenames, directory depth, document layout, and embedded dates as evidence rather than contracts. A report need not use the repository template or contain a reporting-week label. Never invent a date, author, submission, selection reason, or approval.

Stay within every member's declared search roots, do not follow directory symlinks, and do not broaden the search because an expected report is absent. Preserve source files.

## Build and Promote

Use `scripts/build-bundle` from this skill directory after selecting the best candidate for each member and writing the required temporary plan TSV.

- With no issues, build and promote a complete bundle.
- With any issue, build a draft outside the configured administrator output, report the draft path and evidence, and obtain explicit approval before promotion.
- On approval, confirm selected source hashes have not changed and rebuild with `--approved-with-issues`. If they changed, reassess instead of publishing stale choices.
- Never use `--draft` with the configured administrator output directory.

Report the final PDF and execution-manifest paths, member statuses, unresolved limitations, and whether approval was required. Do not distribute the bundle beyond its configured output directory without a separate explicit request.
