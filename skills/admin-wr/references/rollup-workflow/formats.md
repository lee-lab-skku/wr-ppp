<!-- markdownlint-disable MD010 -->

# Bundle Plan and Execution Formats

This reference defines the temporary plan TSV, execution-manifest TSV, and cumulative cover table used by administrator bundles.
Use it when writing a plan or interpreting records; [history management](history.md) defines which records and evidence may be trusted.

## Temporary Plan TSV

Create a UTF-8, tab-separated file in temporary storage.
Fields must not contain tabs or newlines.
Use absolute source paths.
The first record and every member entry are required:

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

Fields after each record name have the following order:

| Record | Fields |
| --- | --- |
| `entry` | `order`, `id`, `display_name`, `required` or `optional`, `included` or `exception` or `missing` or `optional-missing`, source path or `-`, machine-readable reason code |
| `candidate` | Member ID, `selected` or `rejected`, absolute path, reason code |
| `issue` | `error` or `warning`, code, member ID or `-`, concise message |
| `history` | Canonical week, member ID, state, evidence: verified manifest path or concise explanation of unavailable evidence |

Every `exception` or `missing` entry must have at least one issue naming that member; global issues such as `first-run` may be added separately.

History records are an optional additive extension of `admin-wr-plan/v1`.
For normal skill runs, use [verified cumulative history](history.md#prepare-cumulative-history) to include every earlier week from the start of available history through the week before the target week, with one cell per current member.
Accepted historical states are `included`, `exception`, `missing`, `optional-missing`, and `unknown`.

The builder rejects duplicate member/week pairs, unknown member IDs, and current or future weeks; this week's row values come from the proposed entries.
The builder consumes explicit history without searching storage or making evidence judgments.
Unknown states or absent member cells in a supplied week add a `history-unavailable` warning requiring draft review.
Older plans without history remain buildable, but show only the current week; they do not establish that no earlier submissions exist.

## Execution Manifest TSV

The final `<week>.manifest.tsv` retains schema `admin-wr-bundle/v1`.
Its tab-separated records are:

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

The supported bundle state and approval pairs are:

| Artifact | State | Approval | Use as prior successful history |
| --- | --- | --- | --- |
| Clean final bundle | `complete` | `not-required` | Yes, after verification |
| Approved final bundle with issues | `approved-with-issues` | `user-confirmed` | Yes, after verification |
| Review draft | `draft` | `required` | Never |

The TSV format preserves literal quotes, missing-entry `0`/`-` values, and optional history records.
Before relying on an entry, follow [history verification](history.md#verify-the-record-and-pdf), including the PDF hash and current candidate comparisons.

## Cumulative Cover Table

The first page replaces the current-only status list with the cumulative table, omitting report page counts and page ranges.
Its cumulative table uses weeks as rows in descending order (this week first), and members as columns in manifest order.
Highlight the target bundle week's entire row with a pale blue background, including when rebuilding an earlier week.

The legend distinguishes `O` (included), `O*` (exception), `X` (missing required report), `--` (optional not included), and `?` (unknown).
Draft current-week cells describe proposed inclusion, while historical cells describe verified final records.
Keep all members in one table with a single row per week.
Use compact column spacing and angled member names so larger rosters remain readable without repeating the history.

Never discard older weeks to fit the cover; the one-page overflow check fails safely if the full table does not fit, requiring a layout adjustment before rebuilding.
Page counts and ranges remain in the execution manifest for source validation and traceability.
