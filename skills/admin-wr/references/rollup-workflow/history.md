# Administrator Bundle History

Use this procedure to locate and verify prior bundles, prepare cumulative inclusion history, and preserve final records during publication and recovery.
The [format reference](formats.md) defines plan and execution fields; a record's presence alone does not establish a trusted submission.

## Resolve Configuration and History Paths

On native Windows, use the resolved launcher's `admin-paths` subcommand and Windows absolute paths, as described in the [skill entry point](../../SKILL.md#locate-configuration).
Do not invoke `scripts/admin-paths` or read `.local-config` directly on Windows.

On Linux/macOS, run `scripts/admin-paths` from this skill directory to resolve metadata locations from `.local-config`.
Its successful TSV output contains `manager-manifest<TAB>path`, `history-output<TAB>directory`, and zero or more `history<TAB>week<TAB>path` records.
Require the command to succeed before using its output, then read the returned manifest and history paths.
The helper resolves locations only, so [verify the record and PDF](#verify-the-record-and-pdf) before trusting history.

Resolve each file in this order, falling back only when it is absent:

| Priority | Manager manifest | Weekly execution history |
| --- | --- | --- |
| Configured `ADMIN_DATA_DIR` | `<directory>/manager-manifest.toml` | `<directory>/manifests/<week>.manifest.tsv` |
| Repository-local | `.manager-manifest.toml` | `.admin-wr/manifests/<week>.manifest.tsv` |
| Legacy administrator output | No additional fallback | TSV beside its PDF, only for weeks absent from both preferred locations |

Fallback is per file, so an existing external history directory may still use local records for missing weeks.
Do not bypass an existing invalid record by falling back to another copy.
The helper does not move or modify files.

## Verify the Record and PDF

Resolve the recorded PDF filename against the configured administrator output, regardless of where the manifest lives, and verify that the PDF exists and its SHA-256 still matches before trusting it as history.
A missing half of the PDF/manifest pair or a hash mismatch is an approval issue and makes that history untrusted.

Only `complete` with `not-required` approval or `approved-with-issues` with `user-confirmed` approval can establish prior successful history.
Draft manifests use `draft` and `required` and must never be treated as prior successful history.
Invalid history remains untrusted and requires review rather than falling back to a different copy.
Recompute the PDF hash, and compare selected source path, mtime, and hash with current candidates before relying on any entry.
For candidate comparison, prefer the most recent `complete` or `approved-with-issues` bundle whose report date precedes the target date.

## Prepare Cumulative History

Prepare the cover's history from verified weekly records in this order:

1. For the cover's cumulative table, collect every earlier week, not just the most recent bundle, using the same precedence and PDF-hash verification.
1. Use each week's own verified entry records as authoritative, rather than blindly copying a later bundle's cumulative snapshot.
1. Match members by stable ID, using the current manifest roster and display names.
1. Do not infer submission from a file's existence: this table records inclusion in the approved weekly bundle.
1. For any known week whose record cannot be verified, use `unknown`; never turn absent evidence into `missing`.
1. Include intervening weeks with no verified bundle as `unknown`, resolving their canonical labels with the metadata helper.
1. Do not invent a tracking start before the earliest available bundle; if no history exists, show only this week and retain the first-run approval issue.

## Preserve Final Records

Final PDFs are written to the configured administrator output.
Final execution TSVs are written to `<ADMIN_DATA_DIR>/manifests/<week>.manifest.tsv` when configured, otherwise `<repository>/.admin-wr/manifests/<week>.manifest.tsv`.
The builder uses the platform's `admin-paths` result for this destination; read fallback never redirects writes to local storage.
A write failure at the configured destination is an error, not permission to write elsewhere.

New builds do not move/delete prior manifests.
A caller may explicitly choose the PDF output as the history destination; otherwise the default layout keeps them separate.

Existing local and legacy history needs no migration to remain readable.
Administrators may move prior TSVs to the configured history directory without overwriting existing records for the same week.
The PDF filename in a final manifest remains relative to the configured administrator output, including after a configuration change; a missing PDF or hash mismatch still requires reassessment.

## Recover Interrupted Publication

Final and draft publication lock both canonical artifact destinations in a fixed order, wait at most 30 seconds in total, and revalidate selected source hashes after acquiring the locks.
A busy publication fails without replacing the existing artifacts; retry after the other run finishes.

Locks are adjacent hidden directories named `.<week>.pdf.publish.lock` and `.<week>.manifest.tsv.publish.lock`, each with an `owner` file containing the host and process ID.
Normal exits and handled signals release acquired locks.
After a forced kill, verify that the recorded host and process no longer own a running publication before manually removing a stale lock; do not remove another active run's lock.

Each artifact is staged in its own destination directory and replaced atomically, but the PDF/TSV pair is not a single atomic transaction.
PDF replacement has no deletion gap and updates mtime for viewers; a timestamp-update error is reported after the matching TSV has been written.
