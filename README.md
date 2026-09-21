# Weekly Research Report Template

**Native Windows:** use the GUI/CLI and self-contained offline installer described in the [Windows guide](windows/README.md).
Source users run `Windows-Setup.ps1`, then `Start-Weekly-Report.ps1` from PowerShell.
The Bash/Docker instructions below apply to Linux/macOS and WSL.
Validated releases provide a Windows offline installer and its SHA256 checksum through GitHub Releases.

Latest version: [![Latest repository version](https://img.shields.io/github/v/tag/lee-lab-skku/wr-ppp?sort=semver&label=release)](https://github.com/lee-lab-skku/wr-ppp/tags)

A LaTeX template for concise weekly research reports using **Progress, Problems, and Plans (PPP)** as a communication framework.
It provides consistent formatting while leaving the organization, form, and level of detail to the author within a strict limit of **two A4 pages per person per week**.
Exceed that limit only when essential research content cannot fit after all reasonable cuts without compromising its meaning or evidence.

## What It Provides

- A reusable PPP structure with an abstract and optional numbered subsections
- Consistent formatting for prose, lists, equations, tables, and figures
- Automatic reporting week, serial number, and page count
- Docker-based PDF builds without a local TeX installation
- An optional shared browser editor for supported report sources
- A shared style file, so routine report writing is limited to the report source

## Requirements

Linux/macOS use Bash and Docker; macOS compatibility is a source-level design target rather than a tested-platform guarantee.
The optional local browser editor also needs Python 3.9 or newer on the host, using only its standard library.
The native Windows offline installer includes the tools needed to generate reports without separate dependency installation.
See the [Windows guide](windows/README.md) for source prerequisites and installation.
For the Bash/Docker workflow, make sure that:

- Bash and Docker are installed.
- The Docker daemon is running and your account can run Docker containers.
- You can use `sudo` during setup to install `report-build` under
  `/usr/local/bin`.

The recommended image is `danteev/texlive:latest`. Another compatible TeX Live
Docker image may be supplied to `scripts/setup.sh` if preferred.
The image must provide XeLaTeX, `latexmk`, and `pdfinfo` (Poppler); these PDF tools are not required on the host.

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
./scripts/setup.sh ~/report-output danteev/texlive:latest --skills=agents,claude
```

Each value links the repository's canonical skill into the following user-level directory:

| Value | Skill directory | Aliases |
| --- | --- | --- |
| `agents` | `~/.agents/skills` | `codex`, `gemini`, `copilot` |
| `claude` | `~/.claude/skills` | |
| `antigravity` | `~/.gemini/config/skills` | |

[Gemini CLI](https://geminicli.com/docs/cli/skills/) supports `~/.agents/skills` and gives it precedence over `~/.gemini/skills`, so `gemini` uses the shared `agents` destination.
[GitHub Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) also supports `~/.agents/skills` for personal skills, so `copilot` is another alias for `agents`.
The previous `codex` alias remains supported.
The `antigravity` destination follows the current [Antigravity global skill directory](https://antigravity.google/docs/skills).
For example, `--skills=gemini,antigravity` installs links in both the shared and Antigravity directories.
Repeated service names and aliases for the same destination are automatically deduplicated, preserving the first occurrence.
For example, `--skills=agents,codex,gemini,copilot,claude,claude` installs each skill once into `~/.agents/skills` and once into `~/.claude/skills`.
When setup runs in WSL, these paths are under the WSL home directory; this does not install skills into a Windows-native agent's separate home directory.
Omitting `--skills` leaves user-level skill directories unchanged.

Setup applies the same destination policy to `/usr/local/bin/report-build` and
each requested skill link. A missing destination is linked, and a link that
already resolves to the same repository source is accepted without change. By
default, any other file, link, or directory is preserved and reported as an
error. All requested destinations are checked before the configuration or any
links are changed.
Checks include destination parent paths, and unsupported options are rejected before setup changes anything.
Setup saves configuration atomically after installing the requested links; if installation fails, it preserves the previous configuration and attempts to restore links changed by that run.
Any incomplete rollback reports the preserved backup locations.

Use `--replace-existing` to replace conflicting files or links explicitly:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest \
    --skills=agents,claude --replace-existing
```

Each replaced entry is moved to an adjacent backup such as `report-build.backup`
or `wr-wr.backup.1`, and setup prints a warning containing the backup path.
Existing backup names are not overwritten. Directories are never replaced,
even with `--replace-existing`. This option also provides the migration path
for a regular `report-build` file installed by an older setup version.

Output directories must be absolute paths beginning with `/` or home-relative
paths beginning with `~/`. Other relative paths are not accepted.

### Install Administrator Mode

Administrator mode is a maintainer workflow documented in [CONTRIBUTING.md](CONTRIBUTING.md#administrator-weekly-bundles).
Install it with `--admin`; use optional `--admin-output` for final PDFs and `--admin-data` for the manager manifest and execution history:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest \
    --skills=agents,claude \
    --admin \
    --admin-output=/absolute/path/to/admin-bundles \
    --admin-data=/absolute/path/to/admin-data
```

`--admin` requires `--skills`; `--admin-output` may be omitted until final bundle output is needed.
Administrator paths must not contain tabs, newlines, carriage returns, or `.` / `..` path components; setup and administrator commands apply the same rules.
The bundle cover shows cumulative weekly inclusion with weeks as rows (newest first) and members as columns, without report page counts or ranges.
`--admin-data` stores `manager-manifest.toml` and `manifests/<week>.manifest.tsv` beneath the chosen directory.
The manifest can be stored on a NAS that manages permissions on the server; setup does not require changing its permissions after creation.
Omitting it with `--admin` selects the existing repository-local `.manager-manifest.toml` and `.admin-wr/manifests/` locations.
When reading a missing configured file, the workflow falls back to its local counterpart; writes still use the configured destination.
The admin workflow opens temporary drafts for review and keeps their execution TSVs in the temporary review directory.
Concurrent publications sharing a PDF or history target are serialized; a busy target times out after 30 seconds with retry and lock-recovery guidance.
Optional [Slack webhook notifications](skills/admin-wr/references/slack-notifications.md) can notify a channel when the administrator holds a bundle because required reports are missing; this feature requires Python 3.

Verify the setup by compiling the included template:

```bash
./scripts/test.sh
```

A successful test writes `template.pdf` in the repository.
The same command is also used after editing `weekly-report.sty` to check that the example report still builds.

### Automatic Release Updates

This Git updater applies to the Linux/macOS Bash workflow, including WSL.
Native Windows source checkouts and EXE installations are updated manually.

Automatic updates are optional and require Git and access to the installation's existing `origin` remote.
Enable them during setup or when changing an existing setup:

```bash
./scripts/setup.sh --auto-update
./scripts/setup.sh --auto-update=prerelease
./scripts/setup.sh --auto-update=off
```

`--auto-update` defaults to `stable`; `--auto-update=stable` is equivalent.
`stable` follows official releases, while `prerelease` includes beta and release-candidate tags as well as official releases.
`off` disables an existing setting.
Omitting the option preserves the saved channel, or leaves updates off on first installation.
Explicit values must follow `=`; no extra Python or Node.js packages are needed.
Setup saves the setting without contacting the remote or switching versions.

On a valid `report-build` invocation, an enabled installation checks for releases if its last successful check was at least 24 hours ago.
This is an elapsed-time check at build time, not a scheduled background job; independent terminals and agent commands share the same installation-local check record.
Changing channels or disabling and re-enabling updates makes the next build check again.
Remote lookup and fetch attempts each have a 30-second timeout with a short termination grace period.
Failures are reported, the existing checkout is used, and remote failures are retried no sooner than one hour later.
Help and invalid build requests do not check for updates.

Only origin tags named `vX.Y.Z`, `vX.Y.Z-beta`, or `vX.Y.Z-rc` are eligible, with no leading zeroes in numeric components except `0` itself.
Version components sort numerically, then `beta < rc < official release`; numbered prereleases such as `-beta.1`, other suffixes, and build metadata are excluded.
The selected release is checked out as detached HEAD, preserving existing branches, and the build restarts using the updated scripts and shared style.
Channel changes do not automatically downgrade the installation.

Use `--auto-update=off` for a development clone: automatic updates change the current checkout to a release.
Tracked edits or staged changes cause an update to be skipped, and a target must include the current commit in its history.
Thus a clone already ahead of the latest eligible release waits until a release includes its commits.
Updates never automatically stash work, force-reset a checkout, or overwrite an existing conflicting tag.
After resolving a skipped update, the normal check interval still applies; disabling and re-enabling updates requests a fresh check on the next build.

Enabled builds hold an installation lock through compilation so another automatic update cannot change the style mid-build.
A concurrent build waits up to 30 seconds, then asks you to retry if the installation is still busy.
Normal exits and handled interrupts release the lock; after a forced kill, inspect `.report-update/lock/owner` and verify that the recorded host and process no longer own a running build before removing the stale lock directory.
Local update records are stored under the Git-ignored `.report-update/` directory.
Installed skill links follow the updated files; an agent that already read the skill may need to read it again to use changed guidance.

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

Existing PDFs remain available throughout compilation, including with `--here` or when the configured output is the source directory.
After validating the completed PDF, the build stages it beside its destination, replaces it atomically, and updates its modification time so PDF viewers can notice the change.
A failed compilation or staging operation preserves the previous PDF.
A local PDF that is not the output target is left unchanged.
This avoids the deletion gap that can interrupt LaTeX Workshop and vscode-pdf file watching; viewer or filesystem limitations may still affect automatic refresh.
If the final timestamp update fails, the command reports that the PDF has already been replaced.

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

Then replace the illustrative abstract and PPP content with the week's research.
Adapt sections, subsections, grouping, and presentation to what best communicates that work, including weeks with several research threads.
The comments in `template.tex` provide section-level prompts alongside a worked example.
This README defines shared report policy; the comments help apply it while writing, and the skills describe how an agent assists and validates.

Use the prompts with judgment: suggested content and example layouts are optional, and a useful report need not contain every element mentioned in a comment.
Choose prose, lists, equations, tables, or figures to suit the material.

Keep the report focused on research progress, problems, and plans.
Share software, tooling, administrative, and workflow updates briefly in project meetings instead.
Include a technical detail only when it is necessary to explain a research result, its validity, or a research blocker; describe that research consequence rather than the implementation activity.

Lead with important takeaways and make the relationships among claims, supporting evidence or reasoning, and research implications clear.
These relationships do not require three labeled parts, a fixed sentence sequence in every item, or a single finding encompassing the week.
Give significant developments prominence and keep supporting details subordinate to them.
Use concise headings where helpful and remove repeated background and activity-log detail that does not help the reader assess the research.

Every figure must be referenced at least once in the report's body using a label-based `cleveref` command, in a context that explains its connection to the discussion.
References to tables and equations are optional, but any such references must also use `cleveref` rather than manually written numbers.
Use `\cref` or an appropriate supported variant, such as `\Cref` for capitalization or commands for multiple labels and ranges; this rule does not restrict valid calling forms.
Labels must be unique; prefixes such as `fig:`, `tab:`, and `eq:` are optional.

PPP and the abstract provide useful perspectives on the week:

- **Abstract:** an overview of the scope and significant developments
- **Progress:** changes in research results or understanding and their support and significance
- **Problems:** relevant unresolved research issues and their consequences
- **Plans:** next research directions and intended learning or outcomes

### Length and Exceptions

The complete weekly report must fit within two A4 pages per person, including the abstract, figures, tables, and references.
Shorter reports are welcome; two pages are a maximum, not a quota.
Check the compiled PDF, cut non-research material and repetition, consolidate supporting evidence, and keep only what the reader needs to assess the research claims, problems, and next steps.
Preserve readable typography and hierarchy; do not shrink fonts or margins, crowd the layout, or add an appendix to evade the limit.

An exception is justified only when every reasonable cut or reorganization has been exhausted and further reduction would remove essential evidence or qualifications, or make a research result, problem, or plan misleading or impossible to assess.
Keep any excess to the minimum necessary and explain the specific indispensable content and why it cannot be shortened in the submission note or author handoff.
A busy week, many projects, or a preference for more detail does not justify extra pages.
An overlength report without that justification still needs revision.

## Visual Editing

The Docker workflow and the native Windows application share the same HTML editor.
On Linux/macOS or WSL, start it from the repository with an existing report source:

```bash
python3 /path/to/wr-ppp/scripts/report-edit /path/to/report/main.tex --date 2026-09-21
```

The command opens a local browser session and prints its URL; use `--no-open` to open that URL yourself.
Keep the terminal process running while editing, then stop it with Ctrl+C after saving.
Edits are saved to `main.edited.tex` beside the source, leaving `main.tex` unchanged.
Use `--output /path/to/report/another-name.tex` to choose a different new sibling file; existing output files are refused.
Uploaded image originals go into the report's `figures/` directory.
To resume later, pass the edited file as the source and choose another new output filename.
The command is available directly from the checkout; `setup.sh` continues to install `report-build` and the selected skills.

The existing LaTeX importer supports a subset of the template interfaces.
A round-trip check refuses sources whose content or structure would be lost, including many customized reports and the fully commented example template.
Keep refused reports in LaTeX; do not remove their content or comments merely to make the editor accept them.
The browser preview is a layout aid, and matching page dimensions does not guarantee the same line or page breaks as XeLaTeX.
Review the generated source and build the edited file through the usual Docker command:

```bash
cd /path/to/report
report-build --here --date 2026-09-21 main.edited.tex
```

Use the same date for the editor preview and the PDF build.
Check the actual PDF, references, and page count before replacing the original source with a reviewed revision.
The native Windows application retains its form editor, PDF generation, and administrator screens; its **시각 편집기** button opens this shared browser editor with the existing `.wr.json` save workflow described in the [Windows guide](windows/README.md).

For existing script-based integrations, `scripts/tex_to_state.py`, `state_to_tex.py`, `build_artifact.py`, `check_roundtrip.py`, and `verify_geometry.py` remain entry points to the common implementation.
The duplicated `ppp-editor/` tree and root `SKILL.md` have been consolidated: use these root scripts and the installed `wr-wr` skill's visual-editing guidance instead of a separate `ppp-editor` skill link.
Artifact HTML export remains available through `build_artifact.py`; the local workflow does not require an Artifact service or upload the report to one.

## AI-Assisted Workflow

The optional `wr-wr` skill helps an agent work with any part of this report
workflow. It can orient a new user to report sources and build conventions,
turn available material into a draft, improve an existing report, address
template-specific LaTeX or build problems, and review the resulting artifact.
These are examples rather than a fixed sequence: the agent should start from
the user's current files and intended outcome.

For drafting, substantive revision, and content review, the skill reads the canonical template's instructional comments and the shared report policy above.
Before authoring or changing report LaTeX, it first checks the packages and configuration in `weekly-report.sty` and uses the available functionality where appropriate.
The template includes commented examples for cross-references (`\cref`), units (`\si`, `\SI`), and chemical notation (`\ce`); these illustrate usage without restricting other supported commands, argument forms, or options.
It applies relevant prompts with judgment and preserves useful author choices; matching the example's organization is not a review requirement.
Its references provide task-specific procedures for source conventions, editorial judgment and evidence, optional visual editing, and LaTeX and build validation.
During review, the agent must identify manually written figure, table, and equation numbers and correct them to label-based `cleveref` references when editing is in scope; review-only feedback must specify the correction.
For an unreferenced figure, it must guide the author to a suitable place and context for a body reference, or add one when editing is authorized and the available material supports the connection.
It checks the rendered page count and revises overlength drafts within the authorized scope; any unavoidable exception must be explained in the handoff.

When creating a report from the template, the agent preserves retained instructional comments verbatim.
Comments exclusively associated with an omitted optional example may be removed with that example; shared guidance remains.
Existing reports retain their comments and customizations without automatic synchronization to the current template.
New author-only notes stay separate, and explicit requests to edit comments are respected.

AI assistance does not replace the author's responsibility for the report's
accuracy. When supporting material is unavailable, the skill permits editorial
and technical improvements but directs the agent not to invent or strengthen
factual claims. It treats missing support as an authoring gap to raise with the
author or record in an author-only source comment, rather than automatically
rendering uncertainty language or placeholder values for the report's reader.

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
also be mixed into the layout.
For `\ReportFigure` and `\ReportFigurePair`, both Docker and native Windows builds show a placeholder containing the expected path when an image is unavailable.
A pair may contain one real image and one placeholder.
Raw `\includegraphics` commands retain normal LaTeX missing-file errors.

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
The count accepts `.pdf` extensions case-insensitively and excludes symbolic links, hidden files (including AppleDouble `._*` files), `_.*` metadata files, `~$*` lock files, and temporary or backup files ending in `.tmp.pdf`, `.temp.pdf`, or `.bak.pdf` (case-insensitively).
Files inside subdirectories are not counted.

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
./scripts/setup.sh --replace-existing
```

The new values replace the previous local configuration and are used by both `scripts/test.sh` and `report-build`.
The `--skills` and `--replace-existing` options may be combined with any of these forms.
The [automatic update option](#automatic-release-updates) may also be combined with them; omitting it preserves the saved channel.

## Repository Files

- `template.tex`: the illustrative source copied to `main.tex` for a new report
- `weekly-report.sty`: shared layout, automatic values, and reusable helpers
- `scripts/report-build`: canonical implementation of the installed build command
- `scripts/report-edit`: local browser editing entry point for the Docker workflow
- `report_editor/`: common HTML, editor transport, and LaTeX conversion tools
- `scripts/report-metadata.sh`: source-compatible report date and reporting-week CLI
- `scripts/setup.sh`: saves the build configuration and links `report-build`
- `scripts/test.sh`: verifies the setup through the canonical build command
- `skills/wr-wr`: service-neutral report-writing skill

Routine report writing should require changes only to the copied `main.tex` and
its supporting figure files.
