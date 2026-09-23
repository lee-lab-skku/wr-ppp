# Contributing to the Windows Implementation

Follow the [repository contribution guidelines](../CONTRIBUTING.md) for shared contracts, report policy, versioning, and release authorization.
This document supplements the root guidelines with internal Windows architecture, implementation constraints, development setup, validation, and packaging procedures.
Keep shared policy and externally observable behavior in the root documents; record Windows-specific details here when they cannot be usefully described from that external perspective.
The local README serves users, this contribution guide serves maintainers, and the local CHANGELOG records internal changes and their validation evidence.
The repository has one version and release policy, owned by the root documents; these files do not define an independent Windows release.
See the [Windows user guide](README.md) for installation, source setup, and operation.

## Development Setup

Use Windows PowerShell 5.1 or newer and native Windows Python 3.11 or newer with Tcl/Tk, pip, and venv.
From the repository root, run `Windows-Setup.ps1` to prepare the project environment; preserve an incompatible existing environment instead of replacing it silently.
Use `windows/install-tex.ps1` for project-local TinyTeX when validating the distributed toolchain.
A separately installed Windows TeX Live may be selected for local development, but does not validate the bundled runtime.
See the [user guide](README.md#run-from-source) for source launch commands and configuration paths.
Commands in this document run from the repository root.
Use `-Python` on test and packaging scripts to select an explicit Windows interpreter when required.

## Implementation Boundaries

Windows automation uses PowerShell 5.1 or newer, with PowerShell 7 compatibility as a design target.
Use script-relative resource paths, literal filesystem operations, explicit native-process exit checks, and argument arrays without shell command construction.
Use `Get-Command -CommandType Application -TotalCount 1` when selecting an executable from PATH; multiple application matches otherwise become an invalid space-joined filename when passed to a scalar parameter.
Setup must be repeatable without prompts, preserve incompatible environments, and validate destinations before changing saved configuration or links.
Preserve caller environment variables and restore any temporary working-directory or environment changes.
Python owns the native GUI, LaTeX generation, PDF operations, and administrator rules; PowerShell must not duplicate those implementations.
The native backend uses temporary source copies and disables TeX shell escape, but does not provide container OS/network isolation.
Stage existing local images referenced by `\ReportFigure` and `\ReportFigurePair`, but leave unavailable images to the shared style's placeholder rendering instead of rejecting the build.
Preserve the staging exclusion for symbolic links and junctions; do not follow links to supply missing assets.
Keep the source commands intact, including pairs with one available image, and retain normal TeX errors for raw `\includegraphics` references.
Keep the shared report policy, plan/manifest formats, publication safety, and skill destination aliases consistent across platforms.
Directory publication locks cover both PDF and history destinations and revalidate source fingerprints after acquisition; never automatically steal a NAS lock.
The Git release updater remains specific to Bash; native Windows updates are manual.

The native GUI remains responsible for its report form, builds, and administrator screens.
Its visual-editor adapter in `wr/visual_editor.py` converts `.wr.json` values and persists native form output; it delegates HTTP serving and browser assets to the root `report_editor` package.
Keep that package independent of Windows modules and preserve the existing native save callbacks when changing the adapter.
PyInstaller must analyze both the Windows and repository import roots and bundle `report_editor/assets/editor.html` at its package-relative location.
Source launchers and native test entry points prepare these import roots explicitly; `wr/__init__.py` must remain free of import-path mutations.

Bundle the canonical root `LICENSE.txt` and `NOTICE.txt` as resources, together with `report_editor/assets/KaTeX-LICENSE.txt`.
Keep the full KaTeX notice inside the editor's document element so both state injection and browser DOM serialization preserve it in standalone HTML.
The sidecar holds the upstream license verbatim; update its embedded copy together and verify both editor adapters and HTML export.
Portable and installed smoke checks compare these resources and the attributed HTML byte-for-byte with the selected source checkout through `tests/check_license_files.ps1`.
These checks establish notice preservation for these files, not completeness of all third-party notices or corresponding sources.

Collect runtime notices using the same interpreter as PyInstaller.
Require that interpreter's base installation `LICENSE.txt`, preserve the installed pypdf/tzdata/PyInstaller license files, and retain the source attribution of runtime hooks actually selected by analysis.
Record collected native-file hashes and resolved build-distribution versions without leaking host installation paths into the distribution.
The generated runtime notice index lives under `_internal/licenses`; it supplements the existing package metadata rather than replacing upstream license files.

Keep TeX legal documents independent of the optional full documentation/source installation settings.
Use `install-tex.ps1 -PrepareDistribution` to prepare notices during TeX setup, as CI does before saving the dependency cache; this uses the configured Windows Python environment or `-Python`.
Distribution preparation resolves the HTTPS repository redirect once, then uses that concrete mirror for package updates, installation, and notice collection.
It runs `tlmgr update --self --all` before installing the selected collections so packages already present in the daily bootstrap or a previous local setup are aligned too; `tlmgr install` alone leaves existing packages untouched.
Ordinary source-only TeX setup does not perform this additional download, while `package.ps1 -IncludeTeX` always requires preparation or a matching prepared cache.
Preparation records the installed package database and retrieves named legal/readme files from documentation archives whose SHA512 matches that database.
Archive checksums require downloading complete documentation containers even though only selected notices are retained in the distribution; allow extra preparation time and disk space on a cache miss.
The remote package index must identify the same documentation container; never substitute newer notices for an older cached package by name alone.
Check all installed documentation checksums before downloading archives, and report the selected repository, package revisions, and differing hashes on failure.
Even a concrete mirror can change during a build; if this check fails, prepare again against a synchronized mirror or an intentional matching snapshot rather than bypassing it.
Keep the resulting notices and inventory in `tlpkg/wr-licenses` inside prepared TinyTeX so a matching cache can be reused offline.
If a prepared tree changes, regenerate its notice inventory against matching repository content; `install-tex.ps1 -Repository <snapshot-url>` selects a matching HTTPS repository.
The archive download cache under `.runtime/tex-notice-cache` is preparation-only and must not be copied into the application.
The filename-based collection covers explicit legal/readme files; review in-source notices, embedded dependencies and corresponding-source requirements separately.
It does not acquire complete corresponding sources; maintain explicit source-access directions for reviewed components as described below.

PowerShell scripts containing non-ASCII literals require UTF-8 with BOM for Windows PowerShell 5.1; otherwise keep their source ASCII.

## Validation

Run `windows/test.ps1` from the repository root for native tests and common checks; run POSIX-only checks separately in WSL/Linux.
Use `-RealBuild`, `-Gui`, and `-Package` for opt-in native TeX, hidden GUI, and offline EXE checks:

```powershell
.\windows\test.ps1
.\windows\test.ps1 -RealBuild -Gui
.\windows\package.ps1 -IncludeTeX
.\windows\test.ps1 -Package
```

Normal automated checks inspect and merge real PDF fixtures but substitute LaTeX execution.
`windows/tests/real_build.py` exercises native PDF generation; `windows/tests/render_qa.py` supports visual inspection of the generated test material.
These reports are explicit test fixtures, not research results.
`self-test --output <absolute-path.json>` checks hidden GUI creation, packaged resources, and PDF library loading.
`-Package` excludes development Python/TeX from PATH, builds the bundled template, and restores the environment on exit.
Common checks run on Windows; POSIX-only checks must run separately in WSL/Linux.
These checks do not replace the release pipeline's installed application and uninstallation checks.
Record validation with the relevant internal change in [CHANGELOG.md](CHANGELOG.md), including environment, checked source or artifact when known, outcomes, and limitations.
Identify unrecorded provenance rather than assigning a commit or release by inference.
Record checks that were not run and do not treat earlier validation records as certification of a newly built installer.

## CI and Packaging

See the [release procedure](../CONTRIBUTING.md#tag-driven-ci-and-windows-releases) for manual runs, tag preparation, publication, and retry behavior.

Windows uses PowerShell 5.1 for orchestration, runs the native/common tests (including PowerShell 7 checks when available), prepares project-local TinyTeX and the checksum-pinned Inno Setup compiler, tests native PDF generation, then builds the offline installer.
The sanitized portable bundle and the installed application must pass checks with development Python/TeX excluded from PATH; the installer check also verifies uninstallation preserves user configuration and PDFs.
Run the installer check only on a clean machine; it refuses an existing Weekly Report installation.

Verify the official Inno Setup checksum when updating the compiler version.
The workflow prepares TinyTeX, validates real PDF generation, saves a newly prepared dependency cache, then prepares Inno Setup and packages the installer.
On failure, available installer and uninstaller logs from `.runtime/qa` are retained in the `windows-installer-diagnostics` Actions artifact for seven days.

### Local Packaging

PyInstaller creates `windows/dist/WeeklyReport/WeeklyReport.exe` and `WeeklyReportCLI.exe`; distribute the complete folder, not an individual executable.
`windows/package.ps1 -IncludeTeX` adds the prepared `.runtime/TinyTeX` installation under `tex` for offline operation.
Without that option, the application still needs a separately prepared TeX runtime.

For the installer, prepare Inno Setup 6, the Python build environment, and `.runtime/TinyTeX`, then run:

```powershell
.\windows\build-installer.ps1
```

Use `-Compiler` to select `ISCC.exe`.
Use `-SkipPackage` only with an already validated portable bundle; it packages that bundle's version rather than the current source checkout.
`-Python` remains available when sanitizing an existing bundle with `-SkipPackage`.
Outputs are `windows/dist/installer/WeeklyReport-<version>-Setup.exe` and its SHA256 file.
Keep binaries, checksums, credentials, and generated local state out of tracked source; publish distribution artifacts through the root release workflow.

Before installer creation, `sanitize-bundle.py` removes development-machine TeX logs and font caches and normalizes generated paths.
Offline portable packaging applies the same sanitization and includes the canonical `TeX-NOTICE.txt` as `tex/README.WeeklyReport.txt` to identify these distribution changes.
Preserve collected legal files during sanitization.
Keep the sanitizer and its distribution checks aligned when changing the bundled runtime.
The earlier distribution review was targeted validation, not a guarantee about every bundled dependency or secret.

Packaging, pre-installer validation, and both portable/installed smoke checks verify generated notice manifests, native-file hashes, and the TeX database/notice fingerprints.
Smoke checks run the source validator with development Python before restricting the application test's PATH.
They fail for missing/modified legal files or a mismatched TeX inventory; passing them establishes transport integrity rather than complete license compliance.
Exercise the collector's offline fixtures with `python -B -m unittest discover -s tests -p 'test_distribution_licenses.py' -v`.

The bundle stores the Git-derived repository version in `_internal/VERSION`, including development or dirty suffixes when applicable.
Do not add a separate application `-Version` option or maintain a Windows-specific version sequence.
Follow the root contribution guide for release authorization, tag preparation, CI dispatch, publication, and retries.

### Third-Party Source References

Keep the installed Ghostscript source directions in `TeX-NOTICE.txt`, which packaging copies to `tex/README.WeeklyReport.txt`.
This file is fixed to LF in Git because distribution checks compare it byte-for-byte, including when inspecting a Windows installation from WSL.
The Windows README links to this canonical notice; the release's selected root changelog section carries version-specific source links and access instructions next to the installer download.
Use upstream versioned archives and revision-specific history rather than a generic latest-source link.
No additional release asset is needed for this external source-access route.

Bind the directions to the installed `tlgs.windows` revision and container SHA512 recorded in `GHOSTSCRIPT_PACKAGE` in `distribution_licenses.py`.
Preparation and artifact checks reject another package identity, including reuse of a prepared cache, until its matching source and Windows patch have been reviewed and the notice and identity updated together.
This check prevents stale source directions; it does not establish complete source correspondence or test remote availability.
When updating, check the source/archive hashes, upstream binary/source/patch history, patch applicability and relevant build/dependency material, and preserve applicable third-party terms.
Keep patch bytes intact, including non-UTF-8 text.
The checked Ghostscript source is the upstream archive plus the TeX Live Windows patch; the TeX Live package README separately describes replaced fonts and distribution layout changes.

Before publishing, verify access to both referenced source files and keep a retained copy outside the source checkout for recovery if upstream moves or removes them.
The current rsync directory follows TeX Live development; its historical Subversion revisions provide the versioned fallback documented in the notice.
If source access becomes unavailable, restore an accessible location and update the published directions; an integrity manifest or a local temporary copy alone does not provide download access to recipients.

## TinyTeX Cache

CI caches the complete prepared `.runtime/TinyTeX` tree, including installed packages and generated TeX formats.
An exact cache hit skips `install-tex.ps1`; a miss uses the daily bootstrap, updates its packages, and installs the required collections from the same resolved repository used for notices.
The cache key includes the Windows runner image label, architecture, installation script, shared PowerShell helper and notice collector hashes, and `TINYTEX_CACHE_REVISION` in the workflow.
Do not add release tags or source commit IDs to this dependency key, or use partial restore keys that could mix incompatible TeX installations.
Increment `TINYTEX_CACHE_REVISION` to refresh upstream TeX packages or replace an unusable cache; dependency changes must update `install-tex.ps1` so its hash invalidates the cache automatically.
Every run validates actual native TeX and administrator builds, including cache hits; a new cache is saved only after those checks pass, before Inno Setup preparation and packaging.
Installer packaging, portable tests, installation tests, and release artifact verification still run each time; no finished installer or previous test result is reused.
GitHub scopes caches by ref and permits fallback to the default branch's cache; a `dev` cache is not directly shared with tag runs.
To seed a shared cache, run this workflow manually on the default branch with the matching cache key inputs before subsequent branch or tag runs; the workflow and its build dependencies must already be present there.
Cache eviction or an unavailable cache causes fresh preparation, and caching does not make release builds byte-reproducible.

## Documenting Internal Changes

Use the three local documents according to their audience: README for Windows users, CONTRIBUTING for durable implementation and development rules, and CHANGELOG for meaningful internal changes with validation evidence.
Root documents describe observable behavior and shared contracts; these local documents add the Windows implementation details behind those contracts without copying root policy.

Record pending changes in `Unreleased` and consolidate their net effect before moving them to a dated change group.
Use `YYYY-MM-DD` plus a descriptive change-group title and a link to the implementing commit or PR once available.
A date identifies the recorded change group, not a separate release or an implied date for every associated test.
Use `Added`, `Changed`, `Fixed`, and `Removed` in that order when applicable, and place related checks under `Validation` with their actual execution context.
Record the tested source or artifact, environment, meaningful results, and untested areas; link a CI run when available instead of reproducing full logs.
A later substantial validation pass may have its own dated group referencing the same change.
Do not add an entry for every routine test invocation or duplicate the root release notes.

For migrated records, distinguish the commit containing the record from the commit actually tested.
Keep missing dates or tested revisions explicitly unknown; retain historical artifact names as evidence without treating them as an independent version scheme.
All release versions and publication authority remain at the repository root.
