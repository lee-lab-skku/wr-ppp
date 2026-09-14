# Report Conventions

Use these conventions when helping a user locate, organize, create, or build a report. Read the repository `README.md` and build scripts when exact current behavior is needed.

## Find the Relevant Files

- Resolve the template repository with the skill's `scripts/resolve-repo-root` helper.
- Treat the user's report source directory as separate from the template repository unless the existing layout shows otherwise.
- Look for an existing `main.tex`, another explicitly named `.tex` source, supporting figures, neighboring weekly directories, and previous report sources before proposing new files.
- If several plausible reports exist and the request does not identify one, ask which report is in scope rather than guessing.

## Choose a Source Directory

There is no mandatory weekly-directory naming scheme. The `W1` directory in the repository documentation is illustrative.

- Respect a path or naming scheme supplied by the user.
- Otherwise, inspect sibling report directories and continue an evident convention.
- If no convention exists, suggest a stable, readable name such as the reporting-week label, but explain the choice when it affects the output name.
- The source directory's basename becomes the PDF filename. It does not determine the reporting week printed in the document; the build date does.
- Do not overwrite an existing `main.tex` merely because the directory looks like the desired week. Treat it as an existing draft and inspect it first.

When the user wants a new source, create the chosen directory and copy the canonical `template.tex` to `main.tex`.
Read its instructional comments before adapting the illustrative report content to the user's material.
Do not copy `weekly-report.sty`; the build command supplies it.

## Preserve Instructional Comments

When adapting a new report from the template, preserve retained instructional comments verbatim, including shared guidance and section prompts.
Comments exclusively associated with an omitted optional example may be removed with that example; retain comments that also apply to remaining content.
Keep retained comments with the material they guide if it moves, and keep any new author-only notes separate.
Preserving a comment does not require including every content element it suggests.
Before handing off a newly scaffolded source, compare its retained instructional comments with the canonical template and check that any removed comments belonged exclusively to omitted examples.

For an existing report, preserve its comments and customizations without automatically replacing or inserting comments from the current template.
An explicit user request to edit or remove comments governs that work; ordinary content adaptation does not imply such a request.

## Set Report Identity

The source must provide the report title, author, and project through `\ReportHeader`. The build resolves the date, reporting-week label, and serial number.

- Use the current date only when the user intends the current reporting period.
- Use `--date YYYY-MM-DD` for a backdated report or when the intended week differs from today.
- Use `--serial` only when the user has a known numbering requirement; otherwise preserve automatic numbering.
- If a directory name, requested date, and surrounding reports disagree, surface the discrepancy before finalizing.

## Build and Output

Run `report-build` from the report source directory. It uses `main.tex` unless another source is supplied. Use `--here` only when a local PDF is desired; it replaces the same-named local PDF after successful compilation and validation.
Existing PDFs remain available while compiling, and local PDFs outside the selected output target are preserved. Without `--here`, the configured output directory receives the result.

If `report-build` or its configuration is unavailable, explain or perform the repository setup appropriate to the user's request. Installing the command or user-level skill links may require permissions outside the report directory, so do not assume authorization beyond the current task.
