# Weekly Research Report Template

A compact two-page LaTeX template for weekly laboratory research reports following the **PPP structure: Progress, Problems, and Plans**.

The entry point contains the report content and editable values, while layout, date calculation, and reusable helpers are kept in a separate local style file.

## Features

- Two-page A4 weekly research report
- Editable report title with `Weekly Report` as the subtitle
- PPP structure:
  - **Progress**
  - **Problems**
  - **Plans**
- Automatic monthly week identifier in `yyyy-mm-Wn` format
- Four-day majority rule for assigning boundary weeks to months
- Table templates for experimental results and future plans
- Helpers for one figure or two independent side-by-side figures
- Automatic placeholders for missing figure files
- Compact layout suitable for laboratory meetings
- Minimal `template.tex` entry point
- Local `weekly-report.sty` package for reusable formatting

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

## Table Template

Experimental results can be inserted through `\ReportResultsTable`. Its three arguments are the table rows, caption, and unique label.

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

The planning table uses `\ReportPlanTable` with the same three-argument structure. Its row block contains `Priority`, `Task`, and `Expected Output` columns, as shown in `template.tex`.

## Figure Template

Figures can be added by copying a helper command and changing only its arguments. Each figure needs:

- An image file path
- A caption
- A unique label used for cross-references

### One Figure

```latex
\ReportFigure
    {figures/main-result.pdf}
    {Main experimental result.}
    {fig:main-result}
```

Copy the whole command again wherever another figure is needed. Change all three arguments, especially the label, which must be unique.

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

PDF is recommended for plots and other vector graphics. PNG and JPEG files also work; use the actual extension in the path:

```latex
\ReportFigure
    {figures/main-result.png}
    {Main experimental result.}
    {fig:main-result}
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
