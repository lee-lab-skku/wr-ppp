---
name: wr-wr
description: Create, revise, and validate concise PPP weekly research reports using the wr-ppp LaTeX template and build workflow. Use for weekly Progress, Problems, and Plans reports; do not use for unrelated report formats.
---

# Write Weekly Report

Create an evidence-grounded weekly report without changing the shared template or style during routine report writing.

## Locate the Template Repository

Run `scripts/resolve-repo-root` from this skill directory to locate the repository that provides `template.tex`, `weekly-report.sty`, and the report build configuration. Use that resolved path instead of assuming that the current working directory contains the template repository.

## Workflow

1. Identify the reporting date, author, project, requested language, source directory, and available weekly evidence. Ask only for material information that cannot be inferred safely.
1. Inspect the supplied notes, results, figures, previous reports, and authorized project artifacts before drafting. Do not invent measurements, completed work, citations, decisions, or figure paths.
1. Organize verified content as Abstract, Progress, Problems, and Plans. Distinguish observations from interpretations, and give plans an expected output or success criterion when the evidence supports one.
1. Copy the repository's `template.tex` to a new report source as `main.tex`. Replace the illustrative content and remove structures that do not help communicate the report. Do not edit the canonical template or style unless the user explicitly requests a template change.
1. Build the report with `report-build`, using explicit date or serial overrides when the reporting context requires them. Treat the two-page target as guidance rather than a hard limit.
1. Check that the PDF builds, the header metadata is correct, illustrative example content is gone, quantitative claims match their evidence, references are valid, and final figures are present. Missing-figure placeholders may remain in a draft but must be disclosed.
1. Report the source and PDF paths together with any unresolved factual or build warnings. Do not publish or transmit the report without an explicit request.

## Repository Guidance

Read the resolved repository's `README.md` for current build behavior and `template.tex` for the supported report structures. Prefer those canonical files over duplicating their detailed instructions here.
