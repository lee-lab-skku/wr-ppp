# LaTeX and Build Support

Use this guidance when a report needs formatting, template-specific source work, build diagnosis, or PDF validation. Solve the user's actual problem without turning every request into a general LaTeX lesson.

## Work from the Exact Artifact

- Inspect the relevant source and the complete error context before changing syntax.
- Separate content problems, LaTeX syntax problems, missing assets, and environment or configuration failures.
- Prefer the repository's existing helpers and style conventions over local formatting inventions.
- Make focused repairs when the user asks about one construct; do not rewrite unrelated prose or layout.

When inserting ordinary text, handle LaTeX-sensitive characters such as `%`, `&`, `_`, `#`, braces, backslashes, tildes, and carets according to context. Do not escape characters blindly inside commands, paths, URLs, or mathematics.

## Template Interfaces

Confirm the current definitions in `weekly-report.sty` when exact arguments matter. The principal interfaces are:

- `\ReportHeader{title}{author}{project}` for report identity;
- `reportabstract` and `pppbox` environments for the abstract and PPP areas;
- `\ReportSubsection{title}` for numbered subsections within PPP boxes;
- `\ReportTable{column layout}{rows}{caption}{label}` for flexible tables;
- `\ReportFigure` and `\ReportFigurePair` for figures.

For `\ReportTable`, the number of column specifiers must match the row data. `L`, `C`, and `R` are flexible-width wrapping columns; standard `tabularx` specifiers may be mixed in. Keep labels unique and use cross-references consistently.

Missing figure files intentionally render as placeholders. That can support drafting, but disclose it and do not treat a placeholder as a completed final figure.

## Diagnose and Validate

Use the canonical `report-build` command so the report sees the shared style and resolved metadata. On failure, identify the first actionable error rather than reacting only to the final generic failure message. Apply a repair, rebuild, and stop when the requested issue is resolved or when progress requires missing user information or authorization.

For work intended as a final report, check as relevant:

- successful compilation and a nonempty PDF;
- correct title, author, project, reporting week, and serial context;
- absence of illustrative template content and unintended placeholders;
- valid table layouts, labels, cross-references, and figure paths;
- readable page flow and any meaningful warnings;
- consistency between rendered content and the available evidence.

Do not make a two-page result a hard pass condition. Report excess length as a design consideration and improve it only when that serves the user's intended audience.
