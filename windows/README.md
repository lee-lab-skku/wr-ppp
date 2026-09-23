# Windows Native Edition

The native Windows application runs without Docker, WSL, or Bash.
It supplements the existing Linux/macOS scripts and shared report template.

## Install the Application

Download and run `WeeklyReport-<version>-Setup.exe` from a GitHub Release that includes a Windows installer.
Keep the desktop shortcut option selected and launch **Weekly Report** after installation.
Python and TinyTeX are included, so no separate installation is required.
The installer supports Windows 10/11 x64 and installs for the current user.
Uninstall through Windows Settings; user configuration and authored reports are preserved.
The installer is not currently code-signed.
The installation's `_internal` directory contains the project's `LICENSE.txt` and `NOTICE.txt`.
The editor's KaTeX notice is in `_internal/report_editor/assets/KaTeX-LICENSE.txt` and is also preserved inside exported editor HTML.

## Run from Source

Use Windows PowerShell 5.1 or newer, or PowerShell 7, and native Windows Python 3.11 or newer with Tcl/Tk, pip, and venv.
Run these commands from the repository root:

```powershell
.\Windows-Setup.ps1
.\windows\install-tex.ps1
.\Start-Weekly-Report.ps1
```

If the Python launcher is unavailable, specify an interpreter with `Windows-Setup.ps1 -Python 'C:\Python313\python.exe'`.
Setup creates or reuses the repository's `.venv` and finishes without interactive prompts.
An existing non-Windows virtual environment is preserved and reported as an error; rename it before retrying.
TinyTeX is a separate TeX distribution, not a package included with Python.
`install-tex.ps1` installs it under the project's `.runtime/TinyTeX`.
If Windows TeX Live is already installed, skip this step and select its `bin/windows` directory in the application settings.
Setup does not change the system PATH or other TeX installations.

The former `Windows-Setup.cmd` and `Start-Weekly-Report.cmd` launchers have been removed.
Source users should use the corresponding `.ps1` files.
The installed executable and desktop shortcut run directly without these PowerShell launchers.
If execution policy blocks a script, use `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Windows-Setup.ps1` for that invocation only.

`Start-Weekly-Report.ps1` uses the repository's virtual environment and opens the GUI when called without arguments.
Arguments are passed to the Python CLI, preserving its exit code and stdout/stderr.
The launcher also works through an absolute path from another working directory; relative input paths remain relative to the caller's directory.
An existing `WR_CONFIG` environment variable is preserved.

## Write a Report

Enter the title, author, project, abstract, and PPP content in the report form.
You can add figures and CSV tables.
Choose whether each figure appears after the abstract, Progress, Problems, or Plans.
Figures saved by earlier versions without position information appear after Plans.
Saving creates `.wr.json` data and generated `.wr.tex` source.
Figures are copied into the report's relative `figures` directory.
If an image referenced by `\ReportFigure` or `\ReportFigurePair` is unavailable, the shared template renders a placeholder with its expected path, as in the Docker workflow.
This does not make missing files in raw `\includegraphics` commands optional.
Use a separate directory for each report; its name determines the PDF filename.

The **Visual editor** button saves the current form and opens an A4 preview in the default browser.
Text edits immediately affect the displayed height and are saved to `.wr.json` and `.wr.tex` after approximately 300 ms.
Add images by dropping or selecting them, adjust a single figure's height from 15 to 120 mm, or place two figures side by side.
Original images are stored in the report's `figures` directory.
Keep the application running while using the browser editor.
The interface currently uses Korean labels; the English control names in this guide describe their functions.

The HTML editing interface is shared with the [Docker workflow's visual editor](../README.md#visual-editing).
The native form, file saving, PDF generation, and administrator screens remain available, and browser edits use the existing Windows report files.
Line and page breaks may differ between the browser preview and the generated PDF; inspect the final PDF.

Use `$a+b$` for inline mathematics and `$$E=mc^2$$` for display mathematics.
Characters such as `%`, `&`, and `_` outside math are handled automatically.
Unclosed math expressions and file or document manipulation commands are rejected when saving.

The abstract and PPP input fields support Markdown.
`## Heading` creates an unnumbered heading, `- Item` a bulleted list, and `1. Item` a numbered list.
`**bold**`, `*italic*`, `` `code` ``, and `[label](https://example.com)` are converted to their LaTeX equivalents.
Use **Markdown &rightarrow; LaTeX** to inspect the result in the LaTeX tab.
The same conversion runs when saving or building a PDF.
Raw LaTeX entered into Markdown fields is treated as text.

Markdown heading numbers are not generated automatically; only numbers explicitly entered, such as `# 1.1 Heading`, are shown.
By default, `<style>...</style>` blocks are removed and the shared LaTeX template styling is used.
Enable **Allow user Markdown styles (unlock)** in settings to convert a supported subset of CSS into LaTeX settings.
Supported properties cover A4 margins in `@page`, body font size and line spacing, heading size/spacing/margins for `h1` through `h3`, paragraph spacing, and size/spacing/cell padding for `table`, `th`, and `td`.
Pipe tables are converted regardless of the style-lock setting.
Markdown image paths do not import files automatically; the generated output marks them as requiring attachment.
Use **Add figure** to select the actual files.

The formatting toolbar supports font families (default, serif, sans serif, and monospace), sizes from 8 to 16 pt, bold, italic, underline, strike-through, code, links, bullets, numbered lists, and three heading levels.
Select text within one paragraph before applying character formatting.
Formatting is stored in the report data and rendered within the shared LaTeX template.

Open an existing `.tex` file in source-editing mode to preserve its comments and custom code.
Arbitrary LaTeX is not converted back into form fields, and form values are not applied in source-editing mode.
The form allows figure-position selection and places tables after the PPP sections.
Use source-editing mode for more flexible placement.

The application supports report dates, serial numbers, and saving the PDF in the current directory.
Reports longer than two pages produce a warning; content and pages are not truncated.
Form-generated Windows sources include `kotex`; existing sources do not receive packages automatically.

## Administrator Workflow

Configure the final bundle output and optional administrator data directory in settings.
Enter storage roots, time zones, and each member's ID, name, order, required status, and relative search directory.
The current Windows user must have access to any NAS or UNC paths.

After discovery, double-click a member to select a candidate explicitly.
Inspect PDFs for content and page count; modification time alone does not select a report.
Follow **Create draft &rightarrow; inspect PDFs and issues &rightarrow; confirm after review**.
Changes to the plan or source files after draft creation invalidate promotion.

The application supports the existing TOML member configuration and `admin-wr-plan/v1` and `admin-wr-bundle/v1` TSV formats.
Replace Linux absolute paths with Windows paths explicitly; files are not moved automatically.
History lookup falls back from configured external storage to repository-local storage and then legacy final-output storage only when files are missing.
Invalid records or mismatched hashes require review rather than being bypassed.

The cover uses the existing LaTeX asset and retains the full history.
Generation fails if the cover cannot fit on one page.
Source PDFs are combined with pypdf while preserving every page and its dimensions.
Historical states distinguish included, exceptional, required-missing, optional-not-included, and unknown submissions.

Slack notifications reuse the existing Python implementation.
Configuration does not send a message.
Sending requires confirmation of both holding the bundle and notifying about missing required reports in a draft.
Successful sends are deduplicated, and uncertain failures are never retried automatically.
The webhook is stored in `slack-webhook.url` under the administrator data directory.
Use Windows or NAS access controls to restrict that directory to you and authorized administrators.

## CLI and AI Workflows

```powershell
.\Start-Weekly-Report.ps1 setup --pdf-output C:\Reports --tex-bin C:\texlive\2026\bin\windows
.\Start-Weekly-Report.ps1 preflight
.\Start-Weekly-Report.ps1 report-build C:\Sources\W1\main.tex --date 2026-09-04 --serial 17 --here
.\Start-Weekly-Report.ps1 test
.\Start-Weekly-Report.ps1 report-metadata --date 2026-09-04
.\Start-Weekly-Report.ps1 admin-paths
.\Start-Weekly-Report.ps1 discover
.\Start-Weekly-Report.ps1 probe-report --storage-root C:\Reports --file C:\Reports\member-a\report.pdf
.\Start-Weekly-Report.ps1 build-bundle --storage-root C:\Reports --plan C:\Review\plan.tsv --date 2026-09-04 --draft --output-dir C:\Review\draft
.\Start-Weekly-Report.ps1 build-bundle --storage-root C:\Reports --plan C:\Review\plan.tsv --date 2026-09-04 --approved-with-issues --review C:\Review\draft\2026-09-W1.review.json
.\Start-Weekly-Report.ps1 notify-held --manifest C:\Review\draft\.manifests\2026-09-W1.manifest.tsv
```

On Windows, replace the skills' shell commands with the corresponding subcommands above.
External AI agents handle writing, evidence review, and candidate selection under the existing skill policies; the application does not embed an AI API.
Register skill links through **Register AI skills** in settings or `install-skills --services agents,claude,antigravity --admin`.
Registration tries symbolic links first and falls back to Windows junctions when permissions prevent them, so Developer Mode is not required.
Conflicting entries are preserved by default.
`--replace-existing` backs up and replaces only files or links; ordinary directories are never replaced.
If installation fails, link changes are rolled back.

### Use AI Skills in VS Code

For a source checkout opened in VS Code, first run `Windows-Setup.ps1` to prepare `.venv` and confirm that `Start-Weekly-Report.ps1 preflight` succeeds.
Then register the skills in the user directories for your chosen agents.

Run the interactive registration program from the cloned repository and select `1. Codex` or `2. Claude`.
It links both `wr-wr` and `admin-wr` into the selected agent's user skill directory and leaves other agent directories unchanged.
No additional dependencies are required.

```powershell
python .\windows\register_skills.py
```

If several Python commands are available, you can also use `py .\windows\register_skills.py`.
The links point to the repository's canonical skill sources, so updating that checkout with `git pull` also updates the linked skills.

To register multiple agents at once, use the existing CLI:

```powershell
.\Windows-Setup.ps1
.\Start-Weekly-Report.ps1 preflight
.\Start-Weekly-Report.ps1 install-skills --services agents,claude --admin
```

For an installed application, pass the same subcommands to `WeeklyReportCLI.exe` in the installation directory.
Restart the VS Code AI extension after registration so it reloads the skills.
Both skills resolve the installed `SKILL.md` link to locate their resource root.
They use `Start-Weekly-Report.ps1` for source checkouts and `WeeklyReportCLI.exe` beside `_internal` for packaged installations.
Do not run the references' Bash, Docker, `/tmp`, or `.local-config` examples on native Windows.

`codex`, `gemini`, and `copilot` are aliases for `agents`; identical destinations are installed only once.
Rollback preserves entries changed by the user during registration and reports any backup it could not restore.

## Runtime and Storage Differences

- Source checkouts use `.windows-config.json` and do not execute or overwrite Bash `.local-config`.
  Packaged applications store configuration in `%LOCALAPPDATA%/WeeklyReport/config.json`.
  Set `WR_CONFIG` to select a test configuration path.
- XeLaTeX runs up to five times until references stabilize, without `latexmk` or Perl.
  Custom build stages such as BibTeX or Biber are not run automatically.
- Builds use temporary copies with shell escape disabled.
  This does not provide Docker's OS or network isolation.
  Use the Docker workflow for untrusted sources that require those isolation guarantees.
- A failed build preserves the existing PDF.
  Local PDF cleanup occurs only after the new output has been validated and saved.
- Publication locks both the PDF and history destinations, revalidates sources, and replaces each file atomically, but the pair is not a single transaction.
  A later history lookup detects an interruption between replacements through hash validation.
- The GUI always reviews a draft first.
  The CLI can directly publish an explicit plan without issues, as in the existing workflow.

Git release auto-updates are available only in the Linux/macOS Bash workflow.
Update Windows source checkouts through Git and installed applications through a new installer.
If a publication lock remains, inspect the host and PID in the reported `.publish.lock/owner` file and remove the lock directory only after confirming that the process has exited.
Do not remove another NAS user's active lock.

## Development and Change History

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, internal architecture, validation, and packaging procedures.
[CHANGELOG.md](CHANGELOG.md) records internal Windows changes and their validation evidence.
The [root README](../README.md) owns shared report policy and Docker usage; the [root changelog](../CHANGELOG.md) owns repository versions and user-visible release changes.
