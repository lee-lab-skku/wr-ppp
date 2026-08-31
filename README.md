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
Docker image may be supplied to `scripts/setup.sh` if preferred.

## Quick Start

Run the setup script from the cloned repository. The following example stores
finished PDFs in `~/report-output`:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest
```

This saves the selected image and output directory in the repository's local
configuration and links the `report-build` command into `/usr/local/bin`.

To also make the bundled report-writing skill available from any working
directory, pass the supported services as a comma-separated `--skills` option:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest --skills=codex,claude
```

This links the repository's canonical skill into `~/.agents/skills` for Codex
and `~/.claude/skills` for Claude. Omitting `--skills` leaves user-level skill
directories unchanged. An existing link to the same skill is accepted, while
another file, directory, or link at the destination is preserved and reported
as an error.

Output directories must be absolute paths beginning with `/` or home-relative
paths beginning with `~/`. Other relative paths are not accepted.

Verify the setup by compiling the included template:

```bash
./scripts/test.sh
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

By default, the report date is the host's current local date and the serial
number is selected automatically. Use `--date` and `--serial` to override
either value for backdated or manually numbered reports:

```bash
report-build --date 2026-08-31
report-build --serial 17
report-build --date 2026-08-31 --serial 17 draft.tex
```

Dates must use the `YYYY-MM-DD` format, and serial numbers must be positive
integers. All options may be combined with `--here`.

The directory name is still used as the PDF filename. For example, running
`report-build --here` inside `~/report-source/W1` writes
`~/report-source/W1/W1.pdf`.

Before every build, `report-build` removes an existing PDF with that name from
the current directory. With `--here`, the new PDF replaces it; without
`--here`, the new PDF is written only to the configured output directory. Other
PDFs in the current directory do not affect the report serial number.

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

Tables and figures are optional. The template includes a flexible table helper,
one figure, and two independent figures in one row. `\ReportTable` takes a
column layout followed by the rows, caption, and label:

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

The number of column specifiers determines the number of columns. `L`, `C`,
and `R` create wrapping, flexible-width columns aligned left, center, and
right. Standard `tabularx` specifiers such as `l`, `c`, `r`, and `p{20mm}` can
also be mixed into the layout. If a referenced image is not yet available, the
PDF shows a placeholder containing the expected file path.

## Automatic Values

`report-build` resolves the report date on the host before starting the Docker
container. It uses the host's current local date unless `--date` supplies one.
The reporting week is calculated from that date and displayed as `yyyy-mm-Wn`.
Weeks run from Monday through Sunday; a week spanning two months belongs to the
month containing its Thursday. Both the resolved date and the week label are
passed into LaTeX, so the container's time zone does not affect either value.

The report serial number is independent of the reporting week and of the
`--here` option. Before each build, `report-build` counts the PDFs directly
inside the configured output directory and uses the next number. When that
directory already contains a PDF for the current report, the existing target is
excluded from the serial-number calculation without being deleted before the
build. This preserves the configured PDF if compilation fails. The subtitle
and footer display the resulting number, and the footer also shows the actual
page count. `--serial` bypasses the automatic count for that build.

If the reporting week or serial number does not match the expected reporting
context, contact the repository maintainer.

## Change the Setup

Run `scripts/setup.sh` again whenever the output directory or Docker image
needs to change:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest
```

After the initial setup, either value can be updated independently. With no
arguments, both saved values are reused. A single argument beginning with `/`
or `~/` updates the output directory; any other single argument updates the
Docker image. The omitted value is read from `.local-config`:

```bash
./scripts/setup.sh
./scripts/setup.sh /mnt/reports
./scripts/setup.sh danteev/texlive:latest
```

The new values replace the previous local configuration and are used by both
`scripts/test.sh` and `report-build`.

## Repository Files

- `template.tex`: the illustrative source copied to `main.tex` for a new report
- `weekly-report.sty`: shared layout, automatic values, and reusable helpers
- `scripts/report-build`: canonical implementation of the installed build command
- `scripts/report-metadata.sh`: host-side report date and reporting-week calculation
- `scripts/setup.sh`: saves the build configuration and links `report-build`
- `scripts/test.sh`: verifies the setup through the canonical build command
- `skills/write-weekly-report`: service-neutral report-writing skill

Routine report writing should require changes only to the copied `main.tex` and
its supporting figure files.
