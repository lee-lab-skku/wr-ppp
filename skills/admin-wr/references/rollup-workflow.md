<!-- markdownlint-disable MD010 -->

# Administrator Rollup Workflow

Use this workflow to select source PDFs, prepare a deterministic bundle plan, classify issues, and decide whether promotion requires approval.

## Preflight the Administrator Tools

Run the following from this skill directory as its own command before reading report storage:

```bash
scripts/admin-preflight
```

Do not combine it with filters, pipelines, or unrelated shell commands. It checks the configured Docker image and the host and container tools required by the administrator workflow. Preserve its original Docker error output. If Docker succeeds for the user but this direct command reports socket access denial only in the agent environment, request execution authorization for this exact helper rather than diagnosing the user's Docker installation as broken.

## Resolve the Reporting Period

Use a date supplied by the user. Otherwise resolve the current date in the manifest timezone, not the host's implicit timezone. Resolve the repository root and run the executable metadata helper with that explicit date:

```bash
/absolute/path/to/repository/scripts/report-metadata.sh --date 2026-09-04
```

The helper prints `report-metadata/v1` TSV containing the report date, canonical label, and Monday-to-Sunday period. Always pass the same date to `scripts/build-bundle`. The canonical period identifies the bundle; it does not require each source PDF to contain the same label.

## Discover Within Authorized Roots

For each member in manifest order, recursively enumerate regular files ending in `.pdf`, case-insensitively, below only that member's search roots. Use NUL-delimited filesystem operations so spaces and Unicode names are preserved. Exclude AppleDouble files named `._*.pdf`; do not follow directory symlinks.

Read prior `*.manifest.tsv` files from the resolved repository's `.admin-wr/manifests/` when available.
For older bundles, also read manifests beside the PDFs in the configured administrator output, but only for weeks without a manifest in the new location.
Do not fall back to a legacy manifest to bypass an invalid newer record.
For candidate comparison, prefer the most recent `complete` or `approved-with-issues` bundle whose report date precedes the target date.
For the cover's cumulative table, collect every earlier week, not just the most recent bundle, using the same precedence and PDF-hash verification.
Use each week's own verified entry records as authoritative, rather than blindly copying a later bundle's cumulative snapshot.
Match members by stable ID, using the current manifest roster and display names.
Do not infer submission from a file's existence: this table records inclusion in the approved weekly bundle.
For any known week whose record cannot be verified, use `unknown`; never turn absent evidence into `missing`.
Include intervening weeks with no verified bundle as `unknown`, resolving their canonical labels with the metadata helper.
Do not invent a tracking start before the earliest available bundle; if no history exists, show only this week and retain the first-run approval issue.
Resolve the recorded PDF filename against the configured administrator output, regardless of where the manifest lives, and verify that the PDF exists and its SHA-256 still matches before trusting it as history.
A missing half of the PDF/manifest pair or a hash mismatch is an approval issue and makes that history untrusted.

Assess candidates from all available evidence:

- whether their path, modification time, or SHA-256 differs from the prior selection;
- proximity of filesystem or PDF metadata times to the reporting period;
- dates or revision hints in filenames, when present;
- extractable author, date, or reporting-period text;
- whether multiple candidates appear to be revisions of the same report.

No single signal is mandatory. Missing template fields or a missing internal week label is not an issue by itself. A filesystem modification time alone is not sufficient evidence that a report belongs to the target period.

## Classify and Propose

A required member with no plausible candidate is `missing`. An optional member with none is `optional-missing`. When several distinct readable candidates remain plausible, choose the best one as `exception` for the proposal and report the ambiguity. Use `included` when the report identity, target-period relevance, and final-candidate status are clear.

An explicit internal week that differs from the canonical week is `included` with an `internal-week-mismatch` warning when the author, target-period relevance, and lack of a competing final candidate are otherwise clear. The warning still requires draft review and approval. If another signal also conflicts or several candidates remain plausible, classify the selection as `exception` with an error instead.

Probe every proposed PDF before writing the plan, running each invocation as a standalone command:

```bash
scripts/probe-report \
    --storage-root /absolute/path/to/report-storage \
    --file /absolute/path/to/report-storage/member-a/report-current.pdf
```

The probe prints `admin-wr-probe/v1` records for the canonical file path, mtime, SHA-256, readability, page count, encryption, creation date, and text status, followed by `text-begin` and `text-end` delimiters around extracted text. If it reports a damaged, encrypted, unreadable, or uninspectable PDF, record that candidate as rejected with an `unreadable-pdf` issue. Select a readable alternative as an `exception` when one exists; otherwise use `missing` or `optional-missing` so the draft can still be built with a status row and no invalid PDF. Do not bypass a probe failure.

The complete weekly report has a two-page maximum per person, as described in the repository README's writing guidance.
For a selected report longer than two pages, add an `overlength-report` warning with its page count and any available explanation of necessity; do not invent a justification from length alone.
Keep an otherwise clear selection `included`, preserve every source page in the draft, and use the existing issue-review process before promotion.
An exception is justified only when all reasonable cuts and reorganization have been exhausted and further reduction would compromise essential research meaning or evidence; record that specific rationale in the issue message if established.
Without it, report that the submission needs shortening rather than describing it as compliant.
The bundle's index page and total combined length do not count against an individual's limit.

Approval is required for:

- a missing required report;
- an ambiguous or weakly supported selection;
- an unreadable, damaged, or encrypted selected PDF;
- an overlength report, with the necessity justification or unresolved need for revision shown in the review;
- a prior manifest whose recorded PDF hash no longer matches;
- the first run, when no valid prior bundle exists.

Record rejected candidates and concise reason codes. Never silently choose a weak candidate merely to complete the roster.

## Write the Temporary Plan

Create a UTF-8, tab-separated file in temporary storage. Fields must not contain tabs or newlines. Use absolute source paths. The first record and every member entry are required:

```text
schema	admin-wr-plan/v1
entry	10	member-a	구성원 가	required	exception	/absolute/path/to/report-storage/member-a/report-current.pdf	ambiguous-best
entry	20	member-b	구성원 나	required	missing	-	missing-report
history	2026-08-W4	member-a	included	/absolute/path/to/2026-08-W4.manifest.tsv
history	2026-08-W4	member-b	missing	/absolute/path/to/2026-08-W4.manifest.tsv
candidate	member-a	selected	/absolute/path/to/report-storage/member-a/report-current.pdf	ambiguous-best
candidate	member-a	rejected	/absolute/path/to/report-storage/member-a/report-previous.pdf	older-candidate
issue	error	ambiguous-report	member-a	Several plausible PDFs were found.
issue	error	missing-report	member-b	No plausible PDF was found.
```

Entry fields are `order`, `id`, `display_name`, `required|optional`, `included|exception|missing|optional-missing`, source path or `-`, and a machine-readable reason code.

Candidate fields are member ID, `selected|rejected`, absolute path, and reason code. Issue fields are `error|warning`, code, member ID or `-`, and a concise message.
Every `exception` or `missing` entry must have at least one issue naming that member; global issues such as `first-run` may be added separately.

History records are an optional additive extension of `admin-wr-plan/v1`: `history`, canonical week, member ID, state, and evidence (a verified manifest path or a concise explanation of unavailable evidence).
For normal skill runs, include every earlier week from the start of available history through the week before the target week, with one cell per current member.
Accepted historical states are `included`, `exception`, `missing`, `optional-missing`, and `unknown`.
The builder rejects duplicate member/week pairs, unknown member IDs, and current or future weeks; this week's row values come from the proposed entries.
The builder consumes explicit history without searching storage or making evidence judgments.
Unknown states or absent member cells in a supplied week add a `history-unavailable` warning requiring draft review.
Older plans without history remain buildable, but show only the current week; they do not establish that no earlier submissions exist.

The first page replaces the current-only status list with the cumulative table, omitting report page counts and page ranges.
Its cumulative table uses weeks as rows in descending order (this week first), and members as columns in manifest order.
Highlight the target bundle week's entire row with a pale blue background, including when rebuilding an earlier week.
The legend distinguishes `O` (included), `O*` (exception), `X` (missing required report), `--` (optional not included), and `?` (unknown).
Draft current-week cells describe proposed inclusion, while historical cells describe verified final records.
Keep all members in one table with a single row per week.
Use compact column spacing and angled member names so larger rosters remain readable without repeating the history.
Never discard older weeks to fit the cover; the one-page overflow check fails safely if the full table does not fit, requiring a layout adjustment before rebuilding.
Page counts and ranges remain in the execution manifest for source validation and traceability.

## Build, Confirm, and Promote

For a clean run:

```bash
scripts/build-bundle \
    --storage-root /absolute/path/to/report-storage \
    --plan /tmp/admin-wr-plan.tsv \
    --date 2026-09-04
```

Run each builder invocation as its own command rather than wrapping it with `bash`, a pipeline, or unrelated verification commands.

For a run with issues, first create a temporary draft:

```bash
scripts/build-bundle \
    --storage-root /absolute/path/to/report-storage \
    --plan /tmp/admin-wr-plan.tsv \
    --date 2026-09-04 \
    --draft \
    --output-dir /tmp/admin-wr-review
```

The builder prints the absolute PDF and execution-manifest paths on stdout, one per line, and a shell-quoted `review command` on stderr for draft builds.
The draft PDF remains in the requested temporary directory after the builder exits; its TSV is stored in that directory's `.manifests/` subdirectory and never replaces final history.
Use the emitted command as a standalone invocation to show the PDF in the user's desktop viewer:

```bash
scripts/open-bundle /tmp/admin-wr-review/2026-09-W1.pdf
```

The helper uses `open` on macOS, `xdg-open` on Linux, or `wslview` / Windows PowerShell with `wslpath` on WSL.
It reports a failure if no opener is available or the viewer cannot be launched; in that case, provide the printed PDF path (and Windows path when available) so the user can open it manually.
Include a clickable absolute PDF path, proposed selections, rejected candidates, and issues in the review request.
Keep the draft and plan available until the review is resolved.
Opening the viewer does not establish approval.
After explicit approval, recheck source hashes and run:

```bash
scripts/build-bundle \
    --storage-root /absolute/path/to/report-storage \
    --plan /tmp/admin-wr-plan.tsv \
    --date 2026-09-04 \
    --approved-with-issues
```

If the user changes a candidate, update the plan, rebuild the draft, and request approval again for every remaining issue before promotion.
If the temporary directory or plan is no longer available, reconstruct it from current evidence and revalidate rather than assuming it is unchanged. A changed source invalidates the approval and requires reassessment.

## Read Execution History

Final PDFs are written to the configured administrator output; final execution TSVs are written to `<repository>/.admin-wr/manifests/<week>.manifest.tsv`.
New builds do not write TSVs beside final PDFs or move/delete legacy manifests.
Existing history needs no migration to remain readable; administrators may move legacy TSVs into the new directory, preserving an existing new-location record for the same week.
The PDF filename in a final manifest remains relative to the configured administrator output, including after a configuration change; a missing PDF or hash mismatch still requires reassessment.
Each artifact is staged in its own destination directory and replaced atomically, but the PDF/TSV pair is not a single atomic transaction.

The final `<week>.manifest.tsv` retains schema `admin-wr-bundle/v1`. Its tab-separated records are:

```text
schema	admin-wr-bundle/v1
bundle	<date>	<week>	<start>	<end>	<state>	<approval>	<pdf-name>	<pdf-sha256>
created-at	<unix-epoch>
history	<week>	<id>	<state>	<evidence>
entry	<order>	<id>	<display-name>	<requirement>	<state>	<relative-source-or-dash>	<mtime-or-dash>	<sha256-or-dash>	<page-count>	<page-start-or-dash>	<page-end-or-dash>	<reason>
candidate	<id>	<selected-or-rejected>	<relative-source>	<mtime>	<sha256>	<reason>
issue	<severity>	<code>	<id-or-dash>	<message>
```

Optional `history` records preserve the supplied cumulative snapshot, with the same fields as the plan extension.
Legacy execution manifests without these records remain valid; their own `entry` records still establish that week's inclusion.

Valid final states are `complete` with `not-required` approval and `approved-with-issues` with `user-confirmed` approval. Draft manifests use `draft` and `required` and must never be treated as prior successful history. Recompute the PDF hash, and compare selected source path, mtime, and hash with current candidates before relying on any entry.
