# Report Sources and Builds

Create a report source, choose build options, and check the resulting PDF and automatic metadata with the Bash/Docker workflow.
These commands use the Bash/Docker setup described in [Setup and Updates](setup.md).
Follow the [shared report policy](report-policy.md) when adapting the template.

## Create a Weekly Report

From the repository, create a source directory and copy the template as `main.tex`:

```bash
mkdir -p ~/report-source/W1
cp template.tex ~/report-source/W1/main.tex
cd ~/report-source/W1
```

Edit `main.tex`, then build it from its source directory:

```bash
report-build
```

The directory name becomes the output filename:

```text
~/report-source/W1
→
~/report-output/W1.pdf
```

The shared `weekly-report.sty` file does not need to be copied into each report directory; `report-build` makes it available during compilation.
Routine report writing should require changes only to the copied `main.tex` and its supporting figure files.

## Build Options

`report-build` uses `main.tex` by default.
To compile a differently named source file, pass it explicitly:

```bash
report-build draft.tex
```

To write the PDF directly into the directory where `report-build` is run, instead of the configured output directory, pass `--here`.
The option may be combined with an explicit source filename:

```bash
report-build --here
report-build --here draft.tex
```

By default, the report date is the host's current local date and the serial number is selected automatically.
Use `--date` and `--serial` to override either value for backdated or manually numbered reports:

```bash
report-build --date 2026-08-31
report-build --serial 17
report-build --date 2026-08-31 --serial 17 draft.tex
```

Dates must use the `YYYY-MM-DD` format, and serial numbers must be positive integers.
All options may be combined with `--here`.

## Output Safety

The directory name is still used as the PDF filename.
For example, running `report-build --here` inside `~/report-source/W1` writes `~/report-source/W1/W1.pdf`.

Existing PDFs remain available throughout compilation, including with `--here` or when the configured output is the source directory.
After validating the completed PDF, the build stages it beside its destination, replaces it atomically, and updates its modification time so PDF viewers can notice the change.
A failed compilation or staging operation preserves the previous PDF.
A local PDF that is not the output target is left unchanged.

This avoids the deletion gap that can interrupt LaTeX Workshop and vscode-pdf file watching; viewer or filesystem limitations may still affect automatic refresh.
If the final timestamp update fails, the command reports that the PDF has already been replaced.
If staging or replacement fails after a successful compilation, the command names the failing step and its error, states that the build itself succeeded, and leaves any previous PDF unchanged.

## Automatic Values

`report-build` resolves the report date on the host before starting the Docker container.
It uses the host's current local date unless `--date` supplies one.
The reporting week is calculated from that date and displayed as `yyyy-mm-Wn`.
Weeks run from Monday through Sunday; a week spanning two months belongs to the month containing its Thursday.
Both the resolved date and the week label are passed into LaTeX, so the container's time zone does not affect either value.

The report serial number is independent of the reporting week and of the `--here` option.
Before each build, `report-build` counts the PDFs directly inside the configured output directory and uses the next number.
When that directory already contains a PDF for the current report, the existing target is excluded from the serial-number calculation without being deleted before the build.
This preserves the configured PDF if compilation fails.
The subtitle and footer display the resulting number, and the footer also shows the actual page count.
`--serial` bypasses the automatic count for that build.

The count accepts `.pdf` extensions case-insensitively and excludes symbolic links, hidden files (including AppleDouble `._*` files), `_.*` metadata files, `~$*` lock files, and temporary or backup files ending in `.tmp.pdf`, `.temp.pdf`, or `.bak.pdf` (case-insensitively).
Files inside subdirectories are not counted.

If the reporting week or serial number does not match the expected reporting context, contact the repository maintainer.

## LaTeX Helpers

Tables and figures are optional.
[LaTeX Helpers](report-workflow/latex-helpers.md) describes the table helper's arguments and column layouts, and the figure helpers' behavior when images are missing.

## Repository Files

The [repository file inventory](development/architecture.md#repository-files) identifies the shared template, style, commands, editor, and skills for contributors.
