# Weekly Research Report Template

A compact LaTeX template for weekly laboratory research reports following the **PPP structure: Progress, Problems, and Plans**. Reports are generally intended to stay within two A4 pages, but the layout and page counter support the length the week's content actually requires.

The entry point contains the report content and editable values, while layout, date calculation, and reusable helpers are kept in a separate local style file.

## Features

- Compact A4 weekly research report with a two-page target rather than a hard limit
- Editable report title with a numbered `Weekly Report #N` subtitle
- PPP structure:
  - **Progress**
  - **Problems**
  - **Plans**
- Automatic monthly week identifier in `yyyy-mm-Wn` format
- Four-day majority rule for assigning boundary weeks to months
- Automatically numbered subsection headings inside each PPP box
- Optional table helpers for experimental results and future plans
- Helpers for one figure or two independent side-by-side figures
- Automatic placeholders for missing figure files
- Footer page count based on the actual compiled document length
- Compact layout suitable for laboratory meetings
- Complete illustrative `template.tex` showing several writing and evidence formats
- Local `weekly-report.sty` package for reusable formatting

## Docker Build Scripts

After cloning the repository, configure the PDF output directory and Docker image:

```bash
./setup.sh /path/to/pdf-output texlive-docker-image-name
```

The settings are stored locally and used by both scripts.

### Test style changes

Run from the repository:

```bash
./test.sh
```

This compiles `template.tex` and writes the result to `template.pdf`.

### Compile a report

Run `report-build` from the report source directory:

```bash
cd /path/to/report
report-build
```

By default it compiles `main.tex`.

Before compiling, `report-build` counts the PDF files already present directly in the configured output directory. It adds one to that count and passes the result to the template as the report serial number. This serial number is independent of the automatic reporting week.

The resulting PDF is written to the output directory configured by `setup.sh`, using the current directory name as the PDF filename. The subtitle and lower-left footer show `Weekly Report #N`; the footer also includes the report title.

For example:

```text
/path/to/reports/W1
→
/configured/pdf-output/W1.pdf
```

## File Structure

- `template.tex`: the entry point; edit report information, prose, table rows, and figure helper calls here
- `weekly-report.sty`: packages, page styling, automatic week calculation, and reusable layout helpers

Keep both files in the same directory when compiling. Routine report writing should not require editing `weekly-report.sty`.

## Automatic Reporting Week

The report uses the date on which LaTeX is compiled to calculate the reporting week. Date calculations use the TeX primitives:

```latex
\year
\month
\day
```

Therefore, the report requires no manual week entry.

For example, if the document is compiled on August 22, 2026:

```text
2026-08-W3
```

### Reporting Week Convention

A reporting week runs from:

```text
Monday -- Sunday
```

The reporting month is determined using a four-day majority rule.

A week belongs to the month containing at least four of its seven days.

This is equivalent to using the month containing the **Thursday** of that week.

For example:

```text
Monday     2026-08-31
Tuesday    2026-09-01
Wednesday  2026-09-02
Thursday   2026-09-03
Friday     2026-09-04
Saturday   2026-09-05
Sunday     2026-09-06
```

## Editing the Report

Weekly editing should be limited to `template.tex`. The file begins with only the document class, the local style package, and the report body:

```latex
\documentclass[10pt,a4paper]{article}
\usepackage{weekly-report}

\begin{document}
```

### Basic Information

Replace the three values passed to `\ReportHeader`:

```latex
\ReportHeader
    {Write Your Report Title Here}
    {Your Name}
    {Project / Team}
```

The arguments are the report title, name, and project/team. The reporting week is generated automatically in `yyyy-mm-Wn` format.

### PPP Box Subsections

Use `\ReportSubsection` when headings help organize a `pppbox`:

```latex
\begin{pppbox}{Progress}

\ReportSubsection{Main Development}

Describe the principal change in the work or understanding.

\ReportSubsection{Supporting Evidence}

Present only the evidence that helps explain that change.

\end{pppbox}
```

The numbering restarts at 1 for each `pppbox`. The command applies the heading font and vertical spacing automatically. Subsection names and counts are not fixed: rename, duplicate, or omit them to fit the work being reported. Prose, lists, equations, tables, and figures may be mixed as needed.

For `Problems`, describe a working hypothesis, attempted solutions, and their outcomes when those concepts apply. Some problems instead concern missing evidence, external constraints, resource allocation, or a decision requiring feedback; in those cases, state the uncertainty or constraint and what would move the work forward.

## Table Template

When a quantitative comparison helps explain the week, experimental results can be inserted through `\ReportResultsTable`. Its three arguments are the table rows, caption, and unique label. A table is optional and should not be added merely to fill the report.

Example:

```latex
\ReportResultsTable
    {
        \toprule
        Method & Accuracy & F1 & AUROC \\
        \midrule
        Baseline   & 81.2 & 79.8 & 85.1 \\
        Proposed   & 83.5 & 82.0 & 87.4 \\
        \bottomrule
    }
    {Main experimental results.}
    {tab:main-results}
```

Replace the metric names and values as needed.

The optional planning table uses `\ReportPlanTable` with the same three-argument structure:

```latex
\ReportPlanTable
    {
        \toprule
        Priority & Task & Expected Output \\
        \midrule
        High & Verify the revised model. & Validation notes \\
        Medium & Review candidate journals. & Shortlist \\
        \bottomrule
    }
    {Planned tasks for the next reporting period.}
    {tab:next-week}
```

Use this when priorities and deliverables genuinely clarify the plan. A prose or list-based plan is equally valid.

## Figure Template

Figures can be added by copying a helper command and changing only its arguments. Each single figure needs:

- An image file path
- A caption
- A unique label used for cross-references
- A display height, written as a TeX dimension such as `45mm`

When an image comes from an external source, identify that source in the caption or surrounding text.

### One Figure

```latex
\ReportFigure
    {figures/main-result.pdf}
    {Main experimental result.}
    {fig:main-result}
    {45mm}
```

Copy the whole command again wherever another figure is needed. Change all four arguments, especially the label, which must be unique. The height may be adjusted for a wide screenshot, a compact plot, or another aspect ratio; the image is scaled without distortion.

### Two Figures in One Row

Use `\ReportFigurePair` to place two independent figures side by side:

```latex
\ReportFigurePair
    {figures/result-a.pdf}
    {Result A.}
    {fig:result-a}
    {figures/result-b.pdf}
    {Result B.}
    {fig:result-b}
```

The first three arguments belong to the left figure, and the next three belong to the right figure. Each receives its own figure number, caption, and label. This does not use subfigures.

Paired figures use a fixed height of `35mm`, so they do not take separate height arguments.

PDF is recommended for plots and other vector graphics. PNG and JPEG files also work; use the actual extension in the path:

```latex
\ReportFigure
    {figures/main-result.png}
    {Main experimental result.}
    {fig:main-result}
    {45mm}
```

## Figure Placeholder

Both helpers check whether each requested image exists. If a file is missing, a fixed-size placeholder displays the exact path where the image should be added. The report therefore remains compilable while plots are being prepared, and replacing a placeholder requires no LaTeX layout changes.

## Recommended Writing Style

Weekly reports should emphasize changes in research understanding rather than simply documenting activity.

Prefer:

```text
Validation performance improved by 2.3 percentage points after
removing component B, suggesting that the previous regularization
term may have been too strong.
```

over:

```text
Ran Experiment A.
Ran Experiment B.
Changed component B.
```

For each important result, try to communicate:

```text
What was tested?
What happened?
What does it imply?
What should be tested next?
```
