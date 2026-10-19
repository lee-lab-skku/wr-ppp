# Administrator Development

See the [administrator setup](setup.md#administrator-mode), [manager manifest](../skills/admin-wr/references/manager-manifest.md), and [rollup workflow](../skills/admin-wr/references/rollup-workflow.md) for installation, configuration schema, discovery, review, and artifact formats.
Preserve the following contracts when changing this workflow.

## Setup and Storage

`--admin` requires `--skills`; `--admin-data` requires `--admin`.
Administrator output and metadata paths must be absolute or begin with `~/`.
Omitting `--admin-output` preserves the saved output location and allows an unconfigured first installation; final promotion requires an output location, but discovery and drafts do not.
Setup must not create the final output directory.

An administrator setup without `--admin-data` selects repository-local metadata, even if a previous setup saved an external directory.
Setup without `--admin` preserves the saved metadata directory, and empty or absent `ADMIN_DATA_DIR` means local storage.
Changing configuration must not copy or move existing metadata.
Create manifest parent directories as needed, but defer execution-history directory creation until a final build.

Create a missing manager manifest under `umask 077`, requesting mode `0600`.
Do not require a subsequent `chmod`: NAS filesystems may allow creation while rejecting POSIX permission changes, with effective access governed by server permissions or ACLs.
Preserve an existing regular manifest or valid symbolic link regardless of `--replace-existing`, reject a conflicting directory, and never infer member or storage values.

Use the shared metadata resolver for reads and final history destinations.
Fallback applies only to missing files, per week for history; existing invalid content or PDF hashes must be diagnosed rather than bypassed.
Reads must not move or delete metadata, and final writes must use the configured destination or its unconfigured local default even when reads used fallback.
Preserve lookup compatibility with repository-local and legacy history so migration remains optional.

## Responsibility and Artifact Safety

Keep candidate selection, evidence assessment, issue classification, and approval decisions in the agent workflow.
The deterministic builder consumes an explicit plan and selected PDFs; it must not discover reports, parse the manager configuration, or judge evidence.
Keep shared helpers canonical across command and skill entry points.
Python execution-manifest consumers share the field definitions and structural validation in `admin_records.py`; keep this module independent of Windows and notification dependencies.
Validate records before accessing referenced files, then apply consumer-specific trust and approval checks.
Do not introduce a host Python requirement into the Bash/Docker builder merely to share this parser.

Restrict discovery to declared member roots without following directory symlinks or escaping storage.
Report filenames, internal labels, and templates must remain unrestricted; source PDFs must never be modified or deleted.
Preflight must distinguish host, Docker access, image dependency, and runtime failures while preserving the underlying error.
Keep PDF inspection dependencies in the configured container rather than requiring host Poppler tools.

Preserve all selected source pages and their aspect ratios, manifest ordering, and a single-page A4 index with cumulative inclusion history.
Reject cover overflow instead of dropping history, and keep missing, exceptional, optional, and unknown states distinguishable.
The [rollup workflow](../skills/admin-wr/references/rollup-workflow.md#write-the-temporary-plan) defines plan fields and cover presentation.

Keep review drafts and their records outside the final output directory and its descendants, available after the builder exits.
A viewer opening is not approval; source or candidate changes invalidate the previous review.
Apply the workflow's approval conditions before promotion and revalidate source hashes before rebuilding the final bundle.

Validate the completed PDF before replacing final artifacts, using temporary files in each destination directory and atomic moves.
Serialize publication against both canonical PDF and execution-record destinations, using a fixed lock order and a bounded total wait.
Revalidate sources after acquiring the locks, hold them through both replacements, and release only locks acquired by the current run.
Preserve the builder's stdout contract: absolute PDF and execution-record paths, one per line in that order.
Drafts must never replace final history.
PDF and execution-record replacement is not a single transaction: an interruption between replacements must be detected through PDF-hash validation on the next run and require approval.

## Slack Review Notifications

See the [Slack setup and operation guide](../skills/admin-wr/references/slack-notifications.md) for configuration, commands, and recovery procedures.
The command requires Python 3 with the standard library only.

Keep issue judgment and notification authorization in the agent workflow, separate from deterministic PDF building.
Preview by default; `notify-issues` sends only supported issues from a draft after the administrator approves the complete message for the destination channel.
Sending requires `--approved <preview-fingerprint> --send`; a prior standing authorization or draft creation alone is not message approval, and the fingerprint does not establish human consent.
Supported issues are missing required reports, ambiguous candidates, unreadable PDFs, overlength reports, and internal week mismatches.
Derive member identities and issue scope from the execution record; allow evidence-grounded agent prose for explanations and requested actions without disclosing source paths, raw issue messages, or secrets.
Do not notify for optional omissions alone, history-only issues, clean bundles, or already promoted bundles.
Retain `notify-held --held --send` as the legacy missing-report hold path with its existing authorization conditions and receipt keys.

Accept webhook secrets through hidden terminal input and keep them out of command arguments, tracked files, logs, PDFs, and execution records.
Configuration must not send a message.
Protect secret files through filesystem access controls without requiring post-creation `chmod` on NAS storage.
Read secrets only from the configured location; fallback could send to a different channel.

Deduplicate review notices by target week, member/issue set, rendered message, and webhook destination; ignore private evidence and issue record ordering.
Serialize identical sends and recheck the receipt after acquiring the lock.
A failed or interrupted send must retain the lock and never retry automatically because delivery might already have occurred.
Slack failure must not publish a bundle, modify execution history, or claim successful notification.
Use plain-text message blocks to prevent injected mentions or formatting, HTTPS Slack endpoints without redirects, bounded response reads, and a network timeout.
Tests must substitute transport and never send to Slack.
