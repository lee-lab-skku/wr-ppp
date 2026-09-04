<!-- markdownlint-disable MD010 -->

# Administrator Rollup Workflow

Use this workflow to select source PDFs, prepare a deterministic bundle plan, classify issues, and decide whether promotion requires approval.

## Resolve the Reporting Period

Use a date supplied by the user. Otherwise resolve the current date in the manifest timezone, not the host's implicit timezone. Run the repository's `scripts/report-metadata.sh` helper with that explicit target date to obtain the canonical label and Monday-to-Sunday period, and always pass the same date to `scripts/build-bundle`. This canonical period identifies the bundle; it does not require each source PDF to contain the same label.

## Discover Within Authorized Roots

For each member in manifest order, recursively enumerate regular files ending in `.pdf`, case-insensitively, below only that member's search roots. Use NUL-delimited filesystem operations so spaces and Unicode names are preserved. Exclude AppleDouble files named `._*.pdf`; do not follow directory symlinks.

Read prior `*.manifest.tsv` files from the administrator output when available. Prefer the most recent `complete` or `approved-with-issues` bundle whose report date precedes the target date. Verify that its recorded final PDF exists and its SHA-256 still matches before trusting it as history. A missing half of the PDF/manifest pair or a hash mismatch is an approval issue and makes that history untrusted.

Assess candidates from all available evidence:

- whether their path, modification time, or SHA-256 differs from the prior selection;
- proximity of filesystem or PDF metadata times to the reporting period;
- dates or revision hints in filenames, when present;
- extractable author, date, or reporting-period text;
- whether multiple candidates appear to be revisions of the same report.

No single signal is mandatory. Missing template fields or a missing internal week label is not an issue by itself.

## Classify and Propose

A required member with no plausible candidate is `missing`. An optional member with none is `optional-missing`. When several distinct readable candidates remain plausible, choose the best one as `exception` for the proposal and report the ambiguity. Use `included` only when the evidence is sufficiently clear and uncontradicted.

Probe a proposed PDF for readability before writing the plan. If it is damaged, encrypted, or cannot yield a page count, record it as a rejected candidate and an `unreadable-pdf` issue. Select a readable alternative as an `exception` when one exists; otherwise use `missing` or `optional-missing` so the draft can still be built with a status row and no invalid PDF. An unexpected builder probe failure must leave output untouched and be reported instead of bypassed.

Approval is required for:

- a missing required report;
- an ambiguous or weakly supported selection;
- an unreadable, damaged, or encrypted selected PDF;
- a prior manifest whose recorded PDF hash no longer matches;
- the first run, when no valid prior bundle exists.

Record rejected candidates and concise reason codes. Never silently choose a weak candidate merely to complete the roster.

## Write the Temporary Plan

Create a UTF-8, tab-separated file in temporary storage. Fields must not contain tabs or newlines. Use absolute source paths. The first record and every member entry are required:

```text
schema	admin-wr-plan/v1
entry	10	member-a	구성원 가	required	exception	/absolute/path/to/report-storage/member-a/report-current.pdf	ambiguous-best
entry	20	member-b	구성원 나	required	missing	-	missing-report
candidate	member-a	selected	/absolute/path/to/report-storage/member-a/report-current.pdf	ambiguous-best
candidate	member-a	rejected	/absolute/path/to/report-storage/member-a/report-previous.pdf	older-candidate
issue	error	ambiguous-report	member-a	Several plausible PDFs were found.
issue	error	missing-report	member-b	No plausible PDF was found.
```

Entry fields are `order`, `id`, `display_name`, `required|optional`, `included|exception|missing|optional-missing`, source path or `-`, and a machine-readable reason code.

Candidate fields are member ID, `selected|rejected`, absolute path, and reason code. Issue fields are `error|warning`, code, member ID or `-`, and a concise message.
Every `exception` or `missing` entry must have at least one issue naming that member; global issues such as `first-run` may be added separately.

## Build, Confirm, and Promote

For a clean run:

```bash
scripts/build-bundle \
    --storage-root /absolute/path/to/report-storage \
    --plan /tmp/admin-wr-plan.tsv \
    --date 2026-09-04
```

For a run with issues, first create a temporary draft:

```bash
scripts/build-bundle \
    --storage-root /absolute/path/to/report-storage \
    --plan /tmp/admin-wr-plan.tsv \
    --date 2026-09-04 \
    --draft \
    --output-dir /tmp/admin-wr-review
```

Report the proposed selections, rejected candidates, issues, and draft path. After explicit approval, recheck source hashes and run:

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

The final `<week>.manifest.tsv` uses schema `admin-wr-bundle/v1`. Its tab-separated records are:

```text
schema	admin-wr-bundle/v1
bundle	<date>	<week>	<start>	<end>	<state>	<approval>	<pdf-name>	<pdf-sha256>
created-at	<unix-epoch>
entry	<order>	<id>	<display-name>	<requirement>	<state>	<relative-source-or-dash>	<mtime-or-dash>	<sha256-or-dash>	<page-count>	<page-start-or-dash>	<page-end-or-dash>	<reason>
candidate	<id>	<selected-or-rejected>	<relative-source>	<mtime>	<sha256>	<reason>
issue	<severity>	<code>	<id-or-dash>	<message>
```

Valid final states are `complete` with `not-required` approval and `approved-with-issues` with `user-confirmed` approval. Draft manifests use `draft` and `required` and must never be treated as prior successful history. Recompute the PDF hash, and compare selected source path, mtime, and hash with current candidates before relying on any entry.
