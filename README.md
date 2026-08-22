# Weekly Research Report Template

A compact two-page LaTeX template for weekly laboratory research reports following the **PPP structure: Progress, Problems, and Plans**.

The template is designed as a self-contained `.tex` file. No custom document class or external style file is required. Report content can be edited directly in the provided sections.

## Features

- Two-page A4 weekly research report
- PPP structure:
  - **Progress**
  - **Problems**
  - **Plans**
- Automatic reporting date using the LaTeX compilation date
- Automatic Monday--Sunday reporting period
- Automatic monthly week number
- Four-day majority rule for assigning boundary weeks to months
- Table templates for experimental results and future plans
- Figure template with an automatic placeholder
- Compact layout suitable for laboratory meetings
- No custom `.cls` or `.sty` files

## Automatic Date

The report uses the date on which LaTeX is compiled.

The displayed date is produced by:

```latex
\today
```

Date calculations use the corresponding TeX primitives:

```latex
\year
\month
\day
```

Therefore, the report normally requires no manual date entry.

For example, if the document is compiled on August 22, 2026:

```text
Date:
August 22, 2026
```

## Reporting Week Convention

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

Edit:

```latex
Name
    & Your Name
```

```latex
Project
    & Project / Research Topic
```

```latex
Advisor
    & Advisor Name
```

and the `Main Goal` field.

The date, reporting week, and reporting period are generated automatically.

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

The default figure path is:

```text
figures/main-result.pdf
```

If this file exists, it is automatically inserted into the report.

```latex
\includegraphics[
    width=0.72\linewidth
]{figures/main-result.pdf}
```

PDF is recommended for plots and other vector graphics.

PNG or JPEG can also be used by changing the file path.

For example:

```latex
\includegraphics[
    width=0.72\linewidth
]{figures/main-result.png}
```

## Figure Placeholder

The template uses:

```latex
\IfFileExists
```

to determine whether the requested figure exists.

If the figure has not yet been generated, a placeholder box is displayed instead.

This allows the report to remain compilable while experiments or plots are still being prepared.

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
