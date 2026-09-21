---
name: wr-wr
description: Help users complete any task whose intended artifact is a wr-ppp weekly report, from orientation and source organization through evidence-grounded writing, revision, LaTeX or build troubleshooting, and final validation. Use even when the user does not name PPP or know the repository workflow; do not use for generic LaTeX work, unrelated report formats, or tasks about the wr-ppp repository development itself.
---

# Work with Weekly Reports

Help the user reach their intended report outcome at their current level of context and readiness. The supported situations are not a closed list: adapt whenever the task is directly about creating, understanding, changing, repairing, or evaluating a report built with this repository.

## Locate the Template Repository

On native Windows, resolve the real path of this `SKILL.md` (following its installation link); its grandparent directory is `skills`, and that directory's parent is the resource root. Read that root's `windows/README.md` and use `Start-Weekly-Report.ps1` subcommands instead of Bash scripts. Use `report-build` for compilation and `preflight` for dependency checks. Keep the writing and evidence policies below unchanged. In a packaged installation the resource root is `_internal`; use `WeeklyReportCLI.exe` beside that directory with the same subcommands.

On Linux/macOS, run `scripts/resolve-repo-root` from this skill directory to locate the repository that provides the template, style, documentation, and build scripts. Use the resolved path instead of assuming that the current working directory is the template repository.

## Determine What Help Is Needed

Establish only the context needed for the next useful action:

- the outcome the user wants, which may be an explanation, a file operation, content work, technical repair, review, or a combination;
- the artifacts that already exist, from no material through notes, figures, a partial source, a complete draft, a PDF, or a failed build;
- what evidence is available to the agent and what exists only in the user's knowledge;
- whether the user wants the agent to perform the work, guide them through it, or review their work.

Infer these from the request and accessible files when practical. Do not turn them into a mandatory questionnaire or force the user through a fixed end-to-end workflow. Ask a focused question only when the answer materially affects factual correctness, the destination or identity of a report, preservation of existing work, or the requested outcome.

## Choose and Combine Relevant Guidance

Before authoring or changing report LaTeX, first inspect the package declarations and relevant configuration in the resolved repository's `weekly-report.sty`.
Use the loaded packages where they suit the content, following [references/latex-and-build.md](references/latex-and-build.md); template command examples illustrate usage without limiting the supported commands or argument forms.

Before drafting, substantively revising, or reviewing report content, read the instructional comments in the resolved repository's canonical `template.tex` and the `README.md` sections "Write the Report" and "Length and Exceptions".
The README defines shared report policy; template comments explain how to apply it while writing.
Use the comments with judgment: distinguish report requirements, adaptable suggestions, and illustrative content.
Suggested elements and example layouts are optional; do not turn them into compulsory fields or treat example data as evidence for the user's report.
The README's figure, table, and equation reference rules are requirements, not optional example conventions.
When drafting, revising, or reviewing content, apply the reference checks in [references/latex-and-build.md](references/latex-and-build.md), including to existing user-written prose.

Read only the references needed for the current request. Combine them when a problem crosses boundaries.

- Read [references/report-conventions.md](references/report-conventions.md) when locating, naming, scaffolding, preserving template comments, configuring, or building report sources and outputs.
- Read [references/content-quality.md](references/content-quality.md) when assessing evidence, drafting from source material, making editorial decisions, revising claims, preserving authorial intent, or working without supporting material.
- Read [references/latex-and-build.md](references/latex-and-build.md) when formatting content, using template helpers, diagnosing LaTeX, or validating a PDF.
- Read [references/visual-editing.md](references/visual-editing.md) when the user wants to edit a report in the shared HTML editor or work with its state and exported source.

Consult the resolved repository's `weekly-report.sty` and scripts for exact LaTeX and build behavior, and the README for workflow details as needed.

## Work Adaptively

- Start from the user's actual artifact instead of recreating work that already exists.
- Take the smallest set of actions that fully addresses the request. A conceptual question may need no file changes; a syntax problem may need no prose rewrite; a content revision may also reveal a build problem worth fixing.
- Preserve a useful existing organization. Reorganize when requested or when it addresses a concrete communication problem within the authorized task; a difference from the example is not itself a defect.
- Explain unfamiliar conventions at the point they become relevant, using language appropriate to the user's apparent experience. Do not require the user to know LaTeX or repository terminology before helping them.
- Preserve the shared template and style during ordinary report work. Change them only when the user requests a reusable template or build-system change.
- Never invent evidence, measurements, completed work, citations, decisions, or figure contents. Separate verified facts, author-supplied claims, interpretations, and unresolved questions.
- When source material is unavailable, continue with work that does not require it. Improve clarity, organization, grammar, and LaTeX while preserving factual meaning; identify claims that cannot be strengthened or verified to the author or in author-only source comments instead of converting them into reader-facing uncertainty language.
- Protect existing work, including source comments and customizations. Inspect before overwriting, keep changes scoped to the requested report, and disclose placeholders or unresolved problems to the author without automatically rendering them in the report. Do not automatically synchronize existing reports' comments to the current template.

## Finish at the Right Level

Validate in proportion to the work performed.
This may range from explaining a convention, through checking a focused source edit, to compiling and reviewing the final PDF.
When files change, report their paths and summarize material decisions, factual limitations, and remaining build or content warnings.
For a final report, include the verified page count and any necessary length-exception justification; if rendering or page inspection is unavailable, disclose that the limit has not been verified.
Do not publish or transmit a report without an explicit request.
