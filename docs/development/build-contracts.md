# Shell and Build Contracts

This reference defines portability, setup transactions, compilation isolation, PDF publication, and automatic-update safeguards.
Preserve these contracts when changing the Bash/Docker workflow or shared artifact publication.

## Shell Portability

Apply the portability rules for each execution boundary:

- **Bash version**: Write shell scripts for both Linux and macOS whenever practical.
  Bash is the Linux/macOS automation shell, and those scripts should remain compatible with the Bash version shipped with macOS.
  Avoid features that require newer Bash releases unless the project requirements are updated explicitly.
  Guard expansions of possibly empty arrays with `${items[@]+"${items[@]}"}`: Bash 3.2 treats a direct empty-array expansion as unset under `set -u`, and substituting one empty argument changes command behavior.
- **System utilities**: Linux commonly provides GNU command-line utilities, while macOS provides BSD variants.
  Avoid relying on implementation-specific flags or output formats.
  If GNU and BSD tools require different invocations, detect the implementation and provide both paths in the script.
  Do not require Homebrew packages merely to replace standard macOS utilities when a reasonable portable implementation is available.
- **Platform claims**: macOS compatibility is a source-level design target, not a tested-platform guarantee.
  Contributors should account for known macOS differences, but they are not required to own macOS hardware, run the scripts on macOS, or guarantee operation on every macOS and Docker Desktop version.
  State any known limitation that remains after a change.
- **Shell invocation**: Quote path and variable expansions, preserve `set -euo pipefail` where it is already used, and resolve script-relative paths without assuming the caller's working directory.
- **Checkout text and links**: Keep POSIX scripts as LF text through `.gitattributes` so Windows checkouts remain usable from WSL.
  When Windows Git materializes repository symlinks as plain files (`core.symlinks=false`), run POSIX checks in a Linux checkout that preserves the Git symlink modes; line-ending normalization alone cannot restore links.

## Setup Transactions

Apply the [shared setup destination policy](../setup.md#install) to command and skill links, preserving idempotency, explicit replacement, directory protection, and preflight before mutation.

- **Preflight**: Normalize supported destination aliases and deduplicate requested destinations, preserving their first occurrence.
  Preflight every requested link's parent path and validate final administrator path settings with the shared path helper before changing installation state.
- **Commit and recovery**: Prepare private configuration separately and commit it atomically only after link installation succeeds.
  Journal link changes for reverse-order rollback on failure; preserve existing configuration and never overwrite an unrelated entry during rollback.
  If restoration fails, report the backup path and remaining partial changes.

## Build Isolation

Preserve the builds' isolation and output-safety properties.
Linux/macOS TeX containers run without network access and compile in temporary storage.
A completed PDF should replace its target only after a successful build and validation, and containers must not modify source files.

Windows must preserve the shared report policy, plan/manifest formats, publication safety, and skill destination aliases.
Native Windows builds do not provide container OS/network isolation, and Windows updates remain manual.
Follow the [Windows development guide](../../windows/CONTRIBUTING.md) for implementation constraints and platform-specific validation.

## PDF Publication

Validate report readability and a positive page count with container-provided `pdfinfo`; keep PDF tooling off the host.
Use the shared PDF publisher for user-facing PDFs: stage and verify bytes in the destination directory, atomically replace without a deletion gap, and update mtime for file watchers.
A timestamp-update error occurs after replacement and must be reported as such; bundle publication must still complete its matching execution record.
Do not use in-place truncation or pre-build deletion to refresh a viewer.

## Automatic Updates

See the [automatic release update workflow](../setup.md#automatic-release-updates) for setup options, update intervals, and recovery.
Keep development clones opted out; enabling updates authorizes release checkout changes during builds.
Implement version selection with Bash and standard utilities without new language runtimes or package dependencies, retaining the existing Linux/macOS source-level compatibility target.

### Version Selection

Validate build arguments and inputs before invoking automatic updates or touching output PDFs.
Use only eligible tags advertised by the existing origin remote and verify the fetched commit against that advertisement.
Never force-update conflicting tags, discard tracked changes, or move to a commit that does not contain the current HEAD.
Preserve branches when switching to a release, retain report arguments and configuration, and restart with the updated build implementation.
Keep update status on stderr and leave the PDF output contract intact.

### State and Locking

Persist check state as data rather than shell code, write it atomically, and invalidate it when the channel changes.
Hold an installation-wide directory lock through the refreshed build, recheck state after acquiring it, and release it on ordinary exit or handled signals.
Bound lock and network waits, preserve active locks, and continue with the existing checkout on update failures when no concurrent update lock prevents a consistent build.
Tests must use local Git remotes and substituted network/build dependencies without updating a real installation or contacting publication remotes.
