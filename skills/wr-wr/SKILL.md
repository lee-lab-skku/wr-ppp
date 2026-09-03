---
name: wr-wr
description: Help users complete any task whose intended artifact is a wr-ppp weekly report, from orientation and source organization through evidence-grounded writing, revision, LaTeX or build troubleshooting, and final validation. Use even when the user does not name PPP or know the repository workflow; do not use for generic LaTeX work, unrelated report formats, or tasks about the wr-ppp repository development itself.
---

# Work with Weekly Reports

Help the user reach their intended report outcome at their current level of context and readiness. The supported situations are not a closed list: adapt whenever the task is directly about creating, understanding, changing, repairing, or evaluating a report built with this repository.

## Locate the Template Repository

Run `scripts/resolve-repo-root` from this skill directory to locate the repository that provides the template, style, documentation, and build scripts. Use the resolved path instead of assuming that the current working directory is the template repository.

## Determine What Help Is Needed

Establish only the context needed for the next useful action:

- the outcome the user wants, which may be an explanation, a file operation, content work, technical repair, review, or a combination;
- the artifacts that already exist, from no material through notes, figures, a partial source, a complete draft, a PDF, or a failed build;
- what evidence is available to the agent and what exists only in the user's knowledge;
- whether the user wants the agent to perform the work, guide them through it, or review their work.

Infer these from the request and accessible files when practical. Do not turn them into a mandatory questionnaire or force the user through a fixed end-to-end workflow. Ask a focused question only when the answer materially affects factual correctness, the destination or identity of a report, preservation of existing work, or the requested outcome.

## Choose and Combine Relevant Guidance

Read only the references needed for the current request. Combine them when a problem crosses boundaries.

- Read [references/report-conventions.md](references/report-conventions.md) when locating, naming, scaffolding, configuring, or building report sources and outputs.
- Read [references/content-quality.md](references/content-quality.md) when selecting evidence, drafting content, revising claims, preserving authorial intent, or working without supporting material.
- Read [references/latex-and-build.md](references/latex-and-build.md) when formatting content, using template helpers, diagnosing LaTeX, or validating a PDF.

Consult the resolved repository's `README.md`, `template.tex`, `weekly-report.sty`, or scripts when their current behavior matters. Those files are canonical; do not copy their full interface into the skill.

## Work Adaptively

- Start from the user's actual artifact instead of recreating work that already exists.
- Take the smallest set of actions that fully addresses the request. A conceptual question may need no file changes; a syntax problem may need no prose rewrite; a content revision may also reveal a build problem worth fixing.
- Explain unfamiliar conventions at the point they become relevant, using language appropriate to the user's apparent experience. Do not require the user to know LaTeX or repository terminology before helping them.
- Preserve the shared template and style during ordinary report work. Change them only when the user requests a reusable template or build-system change.
- Never invent evidence, measurements, completed work, citations, decisions, or figure contents. Separate verified facts, author-supplied claims, interpretations, and unresolved questions.
- When source material is unavailable, continue with work that does not require it. Improve clarity, organization, grammar, and LaTeX while preserving factual meaning; identify claims that cannot be strengthened or verified instead of silently changing them.
- Protect existing work. Inspect before overwriting, keep changes scoped to the requested report, and disclose placeholders or unresolved problems.

## Finish at the Right Level

Validate in proportion to the work performed. This may range from explaining a convention, through checking a focused source edit, to compiling and reviewing the final PDF. When files change, report their paths and summarize material decisions, factual limitations, and remaining build or content warnings. Do not publish or transmit a report without an explicit request.
