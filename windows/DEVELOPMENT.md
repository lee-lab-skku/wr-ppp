# Windows Development

Follow the [repository contribution guidelines](../CONTRIBUTING.md) for shared contracts, report policy, versioning, and release authorization.
This guide is the authoritative reference for Windows-specific implementation constraints and build maintenance.
See the [Windows user guide](README.md) for installation, source setup, and operation.

## Implementation Boundaries

Windows automation uses PowerShell 5.1 or newer, with PowerShell 7 compatibility as a design target.
Use script-relative resource paths, literal filesystem operations, explicit native-process exit checks, and argument arrays without shell command construction.
Use `Get-Command -CommandType Application -TotalCount 1` when selecting an executable from PATH; multiple application matches otherwise become an invalid space-joined filename when passed to a scalar parameter.
Setup must be repeatable without prompts, preserve incompatible environments, and validate destinations before changing saved configuration or links.
Preserve caller environment variables and restore any temporary working-directory or environment changes.
Python owns the native GUI, LaTeX generation, PDF operations, and administrator rules; PowerShell must not duplicate those implementations.
The native backend uses temporary source copies and disables TeX shell escape, but does not provide container OS/network isolation.
Keep the shared report policy, plan/manifest formats, publication safety, and skill destination aliases consistent across platforms.
Directory publication locks cover both PDF and history destinations and revalidate source fingerprints after acquisition; never automatically steal a NAS lock.
The Git release updater remains specific to Bash; native Windows updates are manual.

PowerShell scripts containing non-ASCII literals require UTF-8 with BOM for Windows PowerShell 5.1; otherwise keep their source ASCII.

## Validation

Run `windows/test.ps1` from the repository root for native tests and common checks; run POSIX-only checks separately in WSL/Linux.
Use `-RealBuild`, `-Gui`, and `-Package` for the opt-in native TeX, hidden GUI, and offline EXE checks described in [README.md](README.md).
These checks do not replace the release pipeline's installed application and uninstallation checks.
Record checks that were not run and do not treat earlier validation records as certification of a newly built installer.

## CI and Packaging

See the [release procedure](../CONTRIBUTING.md#tag-driven-ci-and-windows-releases) for manual runs, tag preparation, publication, and retry behavior.

Windows uses PowerShell 5.1 for orchestration, runs the native/common tests (including PowerShell 7 checks when available), prepares project-local TinyTeX and the checksum-pinned Inno Setup compiler, tests native PDF generation, then builds the offline installer.
The sanitized portable bundle and the installed application must pass checks with development Python/TeX excluded from PATH; the installer check also verifies uninstallation preserves user configuration and PDFs.
Run the installer check only on a clean machine; it refuses an existing Weekly Report installation.

Verify the official Inno Setup checksum when updating the compiler version.
The workflow prepares TinyTeX, validates real PDF generation, saves a newly prepared dependency cache, then prepares Inno Setup and packages the installer.
On failure, available installer and uninstaller logs from `.runtime/qa` are retained in the `windows-installer-diagnostics` Actions artifact for seven days.

## TinyTeX Cache

CI caches the complete prepared `.runtime/TinyTeX` tree, including installed packages and generated TeX formats.
An exact cache hit skips `install-tex.ps1`; a miss uses the existing daily bootstrap and current TeX package repository.
The cache key includes the Windows runner image label, architecture, installation script and shared PowerShell helper hashes, and `TINYTEX_CACHE_REVISION` in the workflow.
Do not add release tags or source commit IDs to this dependency key, or use partial restore keys that could mix incompatible TeX installations.
Increment `TINYTEX_CACHE_REVISION` to refresh upstream TeX packages or replace an unusable cache; dependency changes must update `install-tex.ps1` so its hash invalidates the cache automatically.
Every run validates actual native TeX and administrator builds, including cache hits; a new cache is saved only after those checks pass, before Inno Setup preparation and packaging.
Installer packaging, portable tests, installation tests, and release artifact verification still run each time; no finished installer or previous test result is reused.
GitHub scopes caches by ref and permits fallback to the default branch's cache; a `dev` cache is not directly shared with tag runs.
To seed a shared cache, run this workflow manually on the default branch with the matching cache key inputs before subsequent branch or tag runs; the workflow and its build dependencies must already be present there.
Cache eviction or an unavailable cache causes fresh preparation, and caching does not make release builds byte-reproducible.
