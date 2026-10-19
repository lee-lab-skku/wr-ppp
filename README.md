# Weekly Report Template

[![latest badge](https://img.shields.io/github/v/tag/lee-lab-skku/wr-ppp?sort=semver&label=latest)](https://github.com/lee-lab-skku/wr-ppp/tags)

A LaTeX template for concise weekly research reports using **Progress, Problems, and Plans (PPP)** as a communication framework.
It provides consistent formatting while leaving the organization, form, and level of detail to the author within a strict limit of **two A4 pages per person per week**.
Exceed that limit only when essential research content cannot fit after all reasonable cuts without compromising its meaning or evidence.

**Native Windows:** use the GUI/CLI and self-contained offline installer described in the [Windows guide](windows/README.md).
Source users run `Windows-Setup.ps1`, then `Start-Weekly-Report.ps1` from PowerShell.
The Bash/Docker instructions below apply to Linux/macOS and WSL.
Validated releases provide a Windows offline installer and its SHA256 checksum through GitHub Releases.

## Quick Start

Install Bash and Docker, start the Docker daemon, and ensure your account can run containers.
Setup uses `sudo` to link `report-build` under `/usr/local/bin`.
From the cloned repository, configure an output directory and verify the template:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest
./scripts/test.sh
```

Create a report source and build it:

```bash
mkdir -p ~/report-source/W1
cp template.tex ~/report-source/W1/main.tex
cd ~/report-source/W1
# Replace the illustrative content in main.tex with your research.
report-build
```

This writes `~/report-output/W1.pdf`; routine report writing changes only the copied source and supporting figures.
The shared style supplies formatting, scientific notation, reusable table and figure helpers, reporting week, serial number, and page count.
Use `report-build --here` for a PDF beside the source, or `report-build --date 2026-08-31 --serial 17 draft.tex` for explicit metadata and a different source.
See [report sources and builds](docs/report-workflow.md) for options, output safety, automatic values, and LaTeX helper examples.

To install optional agent skills, add `--skills=agents,claude` to setup.
See [Setup and Updates](docs/setup.md) for requirements, all supported skill destinations, replacement and backup rules, and configuration changes.
macOS compatibility is a source-level design target rather than a tested-platform guarantee.

## Write the Report

Set the title, author, and project in `\ReportHeader`, then adapt the abstract and PPP content to the week's research.
Use a title that conveys the actual research topic or development, and focus on supported findings, unresolved research problems, and next steps.
The [shared report policy](docs/report-policy.md) is authoritative for content, organization, scientific notation, and body references.
The comments in [template.tex](template.tex) help apply it; example layouts and suggested elements are adaptable.

### Length and Exceptions

The complete weekly report must fit within two A4 pages per person, including figures, tables, and references.
An exception requires indispensable research content after every reasonable cut or reorganization, with a specific explanation in the submission note or handoff.
Follow the full [length and exception criteria](docs/report-policy.md#length-and-exceptions).

## Visual Editing

The optional shared browser editor opens existing report sources on Linux/macOS or WSL:

```bash
python3 /path/to/wr-ppp/scripts/report-edit /path/to/report/main.tex
```

It requires host Python 3.9 or newer and saves a separate `main.edited.tex`, preserving the original source.
Read the [visual editing guide](docs/visual-editing.md) for supported edits, source preservation, save conflicts, and PDF validation.
Native Windows opens the same interface through the application's **시각 편집기** button; see the [Windows guide](windows/README.md).

## AI-Assisted Workflow

The optional `wr-wr` skill helps with orientation, evidence-grounded drafting, revision, LaTeX or build repair, visual editing, and final review, starting from the user's current files and intended outcome.
AI assistance does not replace the author's responsibility for accuracy.
The skill preserves author choices and source comments, avoids invented claims, and checks the report policy in proportion to the task.
Its references are the canonical task procedures:

- [Report conventions](skills/wr-wr/references/report-conventions.md): sources, identity, scaffolding, and comment preservation.
- [Content quality](skills/wr-wr/references/content-quality.md): evidence, editorial judgment, abstract timing, revision, and shortening.
- [LaTeX and build support](skills/wr-wr/references/latex-and-build.md): package use, body references, stage-aware layout checks, and PDF validation.
- [Visual editing assistance](skills/wr-wr/references/visual-editing.md): editor routing, preservation, and export review.

## Administrator Mode

Install the optional `admin-wr` skill with `--skills=agents --admin`; add `--admin-output=/absolute/path/to/bundles` and `--admin-data=/absolute/path/to/metadata` as needed.
See [administrator setup](docs/setup.md#administrator-mode), the [manager manifest](skills/admin-wr/references/manager-manifest.md), and the [rollup workflow](skills/admin-wr/references/rollup-workflow.md) for configuration, discovery, review, and publication.
Optional [Slack notices](skills/admin-wr/references/slack-notifications.md) require approval of each complete message before sending.

## Automatic Release Updates

Bash installations can opt in with `./scripts/setup.sh --auto-update`; development clones should use `--auto-update=off`.
See [update channels, safeguards, and recovery](docs/setup.md#automatic-release-updates).
Native Windows updates remain manual.

## Documentation and Contributions

Use the [documentation index](docs/README.md) to find detailed user and developer guides and their canonical references.
For development setup, verification, and contribution rules, start with [CONTRIBUTING.md](CONTRIBUTING.md).
Release history is in [CHANGELOG.md](CHANGELOG.md).

## AI Disclosure

AI tools are used in the development and maintenance of this project's code, documentation, templates, and agent skills.
The maintainers remain responsible for the project's design decisions and released changes.
The optional AI-assisted report-writing workflow is described [above](#ai-assisted-workflow).

## License and Contributors

The project's original code, templates, style files, documentation, and agent skills are licensed under the [MIT License](LICENSE.txt).
Copyright is held by Advanced Additive Manufacturing Systems Laboratory, Sungkyunkwan University.
See [NOTICE](NOTICE.txt) for research-content rights and permission to use project-owned template and style material in report sources and generated reports without project attribution or license notices in those reports.
Third-party components retain their own licenses.
The shared browser editor includes KaTeX CSS and fonts under the [KaTeX MIT license](report_editor/assets/KaTeX-LICENSE.txt); editor HTML exports retain its full notice.
Individual contributions are credited in the [Git history](https://github.com/lee-lab-skku/wr-ppp/commits).
