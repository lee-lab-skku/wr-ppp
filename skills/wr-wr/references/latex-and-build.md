# LaTeX and Build Support

Use this guidance when a report needs formatting, template-specific source work, build diagnosis, or PDF validation. Solve the user's actual problem without turning every request into a general LaTeX lesson.

## Work from the Exact Artifact

- Inspect the relevant source and the complete error context before changing syntax.
- Separate content problems, LaTeX syntax problems, missing assets, and environment or configuration failures.
- Prefer the repository's existing helpers and style conventions over local formatting inventions.
- Make focused repairs when the user asks about one construct; do not rewrite unrelated prose or layout.

When inserting ordinary text, handle LaTeX-sensitive characters such as `%`, `&`, `_`, `#`, braces, backslashes, tildes, and carets according to context. Do not escape characters blindly inside commands, paths, URLs, or mathematics.

## Use the Style's Packages

Inspect `weekly-report.sty` for its current `\RequirePackage` declarations, options, and configuration before choosing LaTeX constructs or adding packages.
Use suitable functionality already provided by the style instead of manually reproducing it or loading the same package again.
For example, use `cleveref` for labeled cross-references, `siunitx` for numbers and units, and `mhchem` for chemical notation when the report calls for them.
These are examples, not an exhaustive package list; the style remains the source of truth.

Read the package-usage comments in canonical `template.tex` as starting points.
Choose other commands, argument forms, and options supported by the loaded package version when they better express the material; do not constrain usage to the exact example calls or insert unrelated scientific content merely to demonstrate them.
When syntax or version support is uncertain, consult the package documentation available in the build environment and validate the chosen construct by compiling.

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

Note the repository version printed by `report-build` when diagnosing version-sensitive behavior or comparing results from different checkouts. The command builds the current checkout; the displayed version identifies that checkout rather than selecting a version to build.

For work intended as a final report, check as relevant:

- successful compilation and a nonempty PDF;
- correct title, author, project, reporting week, and serial context;
- absence of illustrative template content and unintended placeholders;
- valid table layouts, labels, cross-references, and figure paths;
- readable page flow and any meaningful warnings;
- the actual rendered page count against the README's length policy for the complete weekly report;
- consistency between rendered content and the available evidence.

Use the resolved repository's `README.md`, "Length and Exceptions", for the page limit and necessity criteria.
Read [content-quality.md](content-quality.md) when overflow requires content revision or final review raises questions about evidence or meaning.
A successful build alone does not establish that a report meets the length requirement.
If the PDF exceeds the limit, revise content within the authorized scope, rebuild, and inspect again while preserving readable typography and layout.
Do not declare an overlength report ready unless the narrow necessity exception is established and explained with the verified page count in the handoff.
If PDF generation or page inspection is unavailable, report that length compliance remains unverified.
