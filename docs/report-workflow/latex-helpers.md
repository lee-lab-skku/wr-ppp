# LaTeX Helpers

This reference describes the shared table helper's arguments and column layouts, and the figure helpers' behavior when images are missing.
Tables and figures are optional.
The template includes a flexible table helper, one figure, and two independent figures in one row.

## Flexible Tables

`\ReportTable` takes a column layout followed by the rows, caption, and label:

```latex
\ReportTable
    {L C R}
    {
        \toprule
        Item & Score & Change \\
        \midrule
        Baseline & 71.4 & +0.0 \\
        Updated model & 73.7 & +2.3 \\
        \bottomrule
    }
    {Illustrative comparison.}
    {tab:comparison}
```

The number of column specifiers determines the number of columns.
`L`, `C`, and `R` create wrapping, flexible-width columns aligned left, center, and right.
Standard `tabularx` specifiers such as `l`, `c`, `r`, and `p{20mm}` can also be mixed into the layout.

## Missing Figure Images

For `\ReportFigure` and `\ReportFigurePair`, both Docker and native Windows builds show a placeholder containing the expected path when an image is unavailable.
A pair may contain one real image and one placeholder.
Raw `\includegraphics` commands retain normal LaTeX missing-file errors.
