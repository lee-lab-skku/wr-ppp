---
model: sonnet
name: ppp-editor
description: >
  Opens a confirmed weekly PPP report in a browser-based visual editor
  (published as a Claude Artifact) so the user can lay it out before the PDF
  is built: attach real images to the figure slots, adjust figure height,
  reorder subsections and content blocks, and see a true-scale A4 preview
  with the same page breaks LaTeX will produce. Reads the edited artifact
  back and writes main.tex deterministically. Use between research-weekly's
  Step 7 confirmation and the wr-wr build, or whenever an existing
  PPP main.tex should be revised visually. Not for generic LaTeX editing.
---

# PPP Visual Editor

Sits between "the content is agreed" and "the PDF is built". Everything it
shows is derived from `weekly-report.sty`, so the preview is a scale model of
the real page rather than a loose approximation.

## What it is not

It does not decide content. `research-weekly` gathers and confirms that
(including which figures to use, in Step 6.7). It does not replace `wr-wr`
either: build diagnosis, page-layout pitfalls and content-quality review stay
there. This skill owns exactly two mechanical jobs — **show the layout** and
**transcribe state ↔ LaTeX without drift**.

## Directory naming

`<report-week>` is wr-ppp's own label — `YYYY-MM-Wn`, month and ordinal both
taken from that week's Thursday — not the ISO week the vault's weekly note uses.
Read it from `report-metadata.sh --date <monday>` rather than deriving it, so
the folder, the PDF filename and the header printed by `\ReportWeekLabel` all
agree (ISO `2026-W36` -> `2026-09-W1`).

## Prerequisites

| Dependency | If missing |
|---|---|
| `report-build` on PATH (lee-lab-skku/wr-ppp) | Build steps are skipped; the editor and `.tex` generation still work |
| Chrome/Chromium | Only needed to run `tests/`; not needed for normal use |

## Workflow

### Step 1 — Build the state

From the confirmed content, or from an existing report:

```bash
# ALWAYS check first - the importer silently drops what it cannot model,
# and that loss would land in main.tex when the artifact is written back
scripts/check_roundtrip.py <PPP>/<report-week>/main.tex   || stop here

scripts/tex_to_state.py <PPP>/<report-week>/main.tex state.json --week-start <monday>
```

The check refuses hand-written `figure`/`minipage` environments, appendices
after `\clearpage`, raw `tabular`, and preamble `\newcommand`/`\renewcommand`
or extra packages - all of which real reports do contain. When it refuses, say
so and leave the report in plain LaTeX rather than editing part of it.

Writing state from scratch: the shape is
`{title, author, project, weekStart, abstract, flow[]}` where `flow` entries are

- `{type:"subsection", boxId:"progress|problems|plans", id, heading}` — heading only
- `{type:"block", subId|boxId, id, text}` — prose / `- ` bullets / `1. ` list / `| … |` table
  (a block belongs to a subsection via `subId`, or straight to a box via `boxId`)
- `{type:"figure", id, heightMm, items:[{path, caption}]}` — one item = `\ReportFigure`,
  two items = `\ReportFigurePair` (height then fixed at 35mm)
- `{type:"pagebreak"}` — `\clearpage`

Seed the figure slots from research-weekly Step 6.7: the path under `figures/`,
the English caption, and one item vs two. The user attaches the actual image in
the editor; do not invent images.

### Step 2 — Publish the editor

```bash
scripts/build_artifact.py state.json out.html
```

Publish `out.html` with the `Artifact` tool (`capabilities: {"artifact": {}}`)
and hand the user the link. Report in one line what was seeded.

### Step 3 — The user edits and saves

Saving publishes a new artifact version; **nothing else persists**. The toolbar
shows "● 저장 안 된 변경 있음" while there are unsaved changes.

### Step 4 — Read it back and write main.tex

Read the artifact (`action: "read"`), take the JSON out of the
`<script id="state-json">` block, then:

```bash
scripts/state_to_tex.py state.json <PPP>/<report-week>/main.tex
```

Do not re-word anything on the way through. The user already settled the
wording in the editor; a model rewriting it only introduces drift.

### Step 5 — Place the real images

The artifact only carries a downscaled preview. For every figure whose
`items[].path` is set, the full-resolution original must exist at that path
under the report directory (`<PPP>/<report-week>/figures/…`), because `report-build`
tars only that directory into the container and runs with `--network none`.
Copy the originals there before building. XeLaTeX takes PDF/PNG/JPG, not SVG.

### Step 6 — Build

Hand over to `wr-wr` (build, layout check, quality review):

```bash
cd <PPP>/<report-week> && report-build --here --date <monday>
```

## Text format

Inline text is stored as **LaTeX verbatim**, so anything the template supports
survives the round trip untouched: `\texttt{}`, `\qty{50}{ms}`, `$math$`,
`\%`, `` `` '' ``, `---`. The editor renders that subset directly. The one
shortcut on top is `**bold**` (it maps to `\textbf{}` and back).

Consequence worth knowing: a literal `&` or `%` typed as plain text will break
the build. Write `\&`, `\%`.

## Checks

```bash
scripts/check_roundtrip.py <main.tex>   # would editing this report lose anything?
scripts/verify_geometry.py              # editor page model still matches weekly-report.sty
tests/run_tests.py                      # headless-Chrome behaviour checks
```

`verify_geometry.py` is the guard against silent drift: the editor hardcodes
the A4 margins, 10pt body, 0.8pt box rule, 1.5mm arc, 3mm padding and the
35mm figure-pair height that live in another repo. Run it after any wr-ppp
update.

## Related skills

| Skill | Relationship |
|---|---|
| `research-weekly` | Produces the confirmed content and the figure slots this skill seeds from |
| `wr-wr` | Owns the LaTeX build, layout pitfalls and content-quality review |
