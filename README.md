# Weekly Research Report Template

A LaTeX template for concise weekly research reports organized around
**Progress, Problems, and Plans (PPP)**. It keeps the report structure and
layout consistent while leaving the weekly content, evidence, and level of
detail to the author. Two A4 pages are a target, not a hard limit.

## What It Provides

- A reusable PPP structure with an abstract and optional numbered subsections
- Consistent formatting for prose, lists, equations, tables, and figures
- Automatic reporting week, serial number, and page count
- Docker-based PDF builds without a local TeX installation
- A shared style file, so routine report writing is limited to the report source

## Requirements

The provided scripts are intended for Linux systems &mdash; macOS compatibility
is best-effort, not always ensured; Windows users are expected to take advantage
from the WSL magic, as that's a Docker's dependency anyway. Before starting, make
sure that:

- Bash and Docker are installed.
- The Docker daemon is running and your account can run Docker containers.
- You can use `sudo` during setup to install `report-build` under
  `/usr/local/bin`.

The recommended image is `danteev/texlive:latest`. Another compatible TeX Live
Docker image may be supplied to `setup.sh` if preferred.

## Quick Start

Run the setup script from the cloned repository. The following example stores
finished PDFs in `~/report-output`:

```bash
./setup.sh ~/report-output danteev/texlive:latest
```

This saves the selected image and output directory in the repository's local
configuration and installs the `report-build` command.

Output directories must be absolute paths beginning with `/` or home-relative
paths beginning with `~/`. Other relative paths are not accepted.

Verify the setup by compiling the included template:

```bash
./test.sh
```

A successful test writes `template.pdf` in the repository. The same command is
also used after editing `weekly-report.sty` to check that the example report
still builds.

## Create a Weekly Report

From the repository, create a source directory and copy the template as
`main.tex`:

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

`report-build` uses `main.tex` by default. To compile a differently named source
file, pass it explicitly:

```bash
report-build draft.tex
```

To write the PDF directly into the directory where `report-build` is run,
instead of the configured output directory, pass `--here`. The option may be
combined with an explicit source filename:

```bash
report-build --here
report-build --here draft.tex
```

The directory name is still used as the PDF filename. For example, running
`report-build --here` inside `~/report-source/W1` writes
`~/report-source/W1/W1.pdf`. If that local output file already exists, it is
removed before the new build. PDFs in the current directory do not affect the
report serial number.

The shared `weekly-report.sty` file does not need to be copied into each report
directory; `report-build` makes it available during compilation.

## Write the Report

Begin by replacing the three values in `\ReportHeader`:

```latex
\ReportHeader
    {Write Your Report Title Here}
    {Your Name}
    {Project / Team}
```

Then replace the illustrative abstract and PPP content with the week's work.
Keep, rename, duplicate, or remove subsections and optional elements according
to what best communicates the report. The comments and examples in
`template.tex` provide the detailed writing guidance.

The main content areas are:

- **Abstract:** the week's main change, evidence, unresolved issue, and next
  direction in brief
- **Progress:** changes in results, implementation, or understanding and the
  evidence supporting them
- **Problems:** uncertainties, attempted responses, constraints, or decisions
  that require feedback
- **Plans:** prioritized next actions and their expected outputs or success
  criteria

Tables and figures are optional. The template includes helpers for results and
planning tables, one figure, and two independent figures in one row. If a
referenced image is not yet available, the PDF shows a placeholder containing
the expected file path.

## Automatic Values

The reporting week is calculated from the build date and displayed as
`yyyy-mm-Wn`. Weeks run from Monday through Sunday; a week spanning two months
belongs to the month containing its Thursday.

The report serial number is independent of the reporting week and of the
`--here` option. Before each build, `report-build` counts the PDFs directly
inside the configured output directory and uses the next number. When that
directory already contains a PDF for the current report, the existing target is
excluded from the serial-number calculation without being deleted before the
build. This preserves the configured PDF if compilation fails. The subtitle
and footer display the resulting number, and the footer also shows the actual
page count.

If the reporting week or serial number does not match the expected reporting
context, contact the repository maintainer.

## Change the Setup

Run `setup.sh` again whenever the output directory or Docker image needs to
change:

```bash
./setup.sh ~/report-output danteev/texlive:latest
```

After the initial setup, either value can be updated independently. With no
arguments, both saved values are reused. A single argument beginning with `/`
or `~/` updates the output directory; any other single argument updates the
Docker image. The omitted value is read from `.local-config`:

```bash
./setup.sh
./setup.sh /mnt/reports
./setup.sh danteev/texlive:latest
```

The new values replace the previous local configuration and are used by both
`test.sh` and `report-build`.

## Repository Files

- `template.tex`: the illustrative source copied to `main.tex` for a new report
- `weekly-report.sty`: shared layout, automatic values, and reusable helpers
- `setup.sh`: saves the build configuration and installs `report-build`
- `test.sh`: verifies the setup and tests changes to the shared style

Routine report writing should require changes only to the copied `main.tex` and
its supporting figure files.
