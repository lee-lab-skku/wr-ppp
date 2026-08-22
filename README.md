# Weekly Research Report Template

A compact two-page LaTeX template for weekly laboratory research reports following the **PPP structure: Progress, Problems, and Plans**.

The template is designed as a self-contained `.tex` file. No custom document class or external style file is required. Report content can be edited directly in the provided sections.

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
- No custom `.cls` or `.sty` files

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

Most weekly editing should be limited to the content sections.

### Basic Information

Replace the title placeholder:

```latex
Write Your Report Title Here
```

Then edit the name and project/team placeholders in the single-line information row:

```latex
Name
    & Your Name
    & Project
    & Project / Team
    & Reporting Week
    & \ReportWeekLabel
```

The reporting week is generated automatically in `yyyy-mm-Wn` format. The form does not display a separate creation date or reporting period.

## Table Template

Experimental results can be inserted directly into the provided table.

Example:

```latex
\begin{table}[H]
    \centering
    \small

    \begin{tabularx}{0.95\linewidth}{
        l
        >{\centering\arraybackslash}X
        >{\centering\arraybackslash}X
        >{\centering\arraybackslash}X
    }
        \toprule
        Method & Accuracy & F1 & AUROC \\
        \midrule
        Baseline   & 81.2 & 79.8 & 85.1 \\
        Proposed   & 83.5 & 82.0 & 87.4 \\
        \bottomrule
    \end{tabularx}

    \caption{Main experimental results.}
    \label{tab:main-results}
\end{table}
```

Replace the metric names and values as needed.

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
