# Versioning and Releases

Use Semantic Versioning for the repository as a whole.
The public interface is the union of the documented LaTeX commands and environments, setup and build commands, output semantics, template usage, and skill behavior.
Determine a release increment from every changed public surface and apply the highest required increment:

- Increment MAJOR for any backward-incompatible public-interface change, such as removing or changing a documented LaTeX interface, command option, default, or output behavior in a way that requires user migration.
- Increment MINOR for backward-compatible additions or changes to substantive functionality, including a new LaTeX interface, setup capability, or skill capability, and when deprecating public functionality without removing it.
  A new command option requires MINOR only when it introduces substantive functionality.
- Increment PATCH for backward-compatible bug fixes, portability and safety corrections, documentation corrections, and internal changes that do not alter the documented interface.
  Also use PATCH for new options, accepted values, or aliases that expose existing behavior without adding or changing substantive functionality, such as supporting another agent through the existing skill-link installation mechanism.

Compatibility means that documented usage continues to work with its stated semantics; it does not require byte-identical PDFs or prevent presentation refinements that preserve those semantics.

Maintain `CHANGELOG.md` using the Keep a Changelog structure.

Begin every changelog item with the most relevant component marker: `[latex]`, `[template]`, `[build]`, `[setup]`, `[skill]`, `[ci]`, or `[docs]`.
Use `[ci]` for CI/CD workflows, automated validation, dependency caches, and release packaging or publication automation; use `[build]` for report compilation and artifact generation behavior.
As the repository's responsibilities expand, extend this list when a distinct component needs its own marker, and document the new marker and its scope here in the same change.
Describe notable user-facing differences rather than copying the commit log, and combine closely related commits into one entry when they deliver one change.
Keep each version section incremental; do not copy beta or release-candidate entries into the stable section.
Order dated changelog sections newest first, preserving the actual release sequence for same-date entries when known.
Chronological order does not determine SemVer precedence or Git ancestry.
When chronological order reverses SemVer precedence or the releases do not form a linear ancestry chain, identify their parent release tags explicitly.
For a merged development baseline, identify the merge commit and its parent tags in `Unreleased`, and base its comparison link on that commit; distinguish integration changes in the baseline from subsequent unreleased changes.

If you are an AI agent, do not increment the version or create a release tag without explicit developer confirmation.
Versions are recorded by Git tags named `vMAJOR.MINOR.PATCH`, optionally followed by exactly `-beta` or `-rc` for prereleases.
Each numeric component is `0` or a positive decimal integer without leading zeroes.
Do not use other prerelease identifiers, numbered prereleases such as `-beta.1` or `-rc.2`, or build metadata in release tags.
Compare major, minor, and patch numerically, then order equal base versions as beta, release candidate, and official release.
Published tags are immutable; use the next allowed release stage or a new base version for subsequent publications rather than rewriting a tag.
For every confirmed release, move the relevant changelog entries from `Unreleased` into a dated version section, update the version comment at the beginning of `template.tex`, commit those changes, and create the matching tag on that exact commit.
For releases that distribute bundled third-party binaries, maintain version-specific source-access directions in `windows/RELEASE-NOTICE.md`; the release generator appends this notice once after the selected change sections so it appears beside the installer.
Keep distribution directions out of individual changelog sections and retain only change history there.
The notice belongs to the release checkout: preserve it during promotion and update it when bundled sources change, using the [Windows source-reference procedure](../windows/CONTRIBUTING.md#third-party-source-references).
Confirm that the latest-version badge near the beginning of `README.md` remains configured to derive its value from the repository's SemVer tags.
Do not omit the changelog update, template update, badge check, or tag.

The setup and build scripts report the version derived from the current Git checkout.
A tagged release prints its tag, while later development commits may include a commit suffix and a dirty checkout may include `-dirty`.
By default the build uses the current checkout; the optional automatic updater may advance it to an eligible published release before compilation.
This channel-based update is the supported exception; do not add arbitrary per-build version selection.

## Tag-driven CI and Windows Releases

`.github/workflows/release.yml` runs on pushed `v*` tags.
It also supports `workflow_dispatch` for manually testing and packaging a selected branch or tag, without running on branch pushes.
In GitHub Actions, open **Test and release**, choose **Run workflow**, and select the branch to check.
The workflow must be present on the default branch for manual dispatch to be available.
Manual runs pin every job to the selected commit, skip release-note preparation checks, and never publish a GitHub Release, even when a tag is selected.
They run the same platform tests, Windows packaging, installer smoke tests, and checksum verification as tag pushes, retaining the installer and SHA256 in the `windows-installer` Actions artifact for seven days.
Manual installer versions use the existing Git-derived bundle version, including a development commit suffix when applicable; the checkout must have a reachable supported version tag and must produce a clean version.
Use the Actions run and its commit SHA to identify the build; manual runs do not create or increment release tags.

For tag pushes, the validation job accepts only the release-tag grammar above, requires the tag and triggering commit to match the checkout, checks the version comment in `template.tex`, and requires exactly one matching dated changelog section.
Release notes must contain at least one change across the selected sections; a stable section may be empty when promotion adds no changes beyond its prereleases.
Complete the normal release preparation before pushing the tag; CI does not create tags, increment versions, or edit source files.

Linux and macOS run the common/POSIX regression suite on their own hosted runners, using the operating system's `/bin/bash`.
These jobs substitute Docker and desktop viewers and do not build release artifacts or install TeX.
Windows must pass native/common regression checks, actual PDF generation, and portable and installed application checks before publication.
Validate the offline distribution without relying on development tools, and verify that uninstallation preserves user configuration and PDFs.
See the [Windows development guide](../windows/CONTRIBUTING.md#ci-and-packaging) for build dependencies and packaging procedures.

Only the publication job has `contents: write`, and it runs after every platform succeeds.
Use the repository's automatic `GITHUB_TOKEN`; no personal access token is required.
Organization/repository Actions policies must allow the pinned official actions and release-writing job permission.
Keep third-party action revisions pinned to full commit IDs; follow the Windows development guide when updating installer build dependencies.

CI packages the exact triggering tag even if multiple tags refer to the same commit.
The release contains only `WeeklyReport-<tag>-Setup.exe` and its `.exe.sha256` file; the publication job revalidates both after artifact transfer.
`.github/scripts/release.py` uses only the matching changelog section for a prerelease publication.
For a stable publication, it collects the matching stable section and any same-version `-rc` and `-beta` sections, in that order with version headings, without changing `CHANGELOG.md`.
After collecting changes, the generator appends `windows/RELEASE-NOTICE.md` from the same checkout exactly once for stable and prerelease publications.
A missing or blank notice fails release preparation and publication.
Missing prerelease stages are allowed; duplicate sections or invalid dates in any selected stage fail validation before publication.
Unreleased changes and other base versions are never included.
Tags ending in `-beta` or `-rc` produce prereleases and cannot become Latest; stable releases use GitHub's default Latest selection.
Publication uploads to a draft before making it public.
Retry a failed run using GitHub Actions' rerun controls: unpublished drafts for the same commit can resume, but published assets are never overwritten.
An existing complete published release is left unchanged; a published release missing expected assets or a draft targeting a different commit fails for maintainer review.
Preserve published tags and use a new allowed version when source fixes are needed.

CI reuses prepared Windows build dependencies to reduce setup time while retaining all build and distribution checks.
Cache misses trigger fresh preparation; finished installers and previous test results are not reused.
See [dependency cache maintenance](../windows/CONTRIBUTING.md#tinytex-cache) for refresh and sharing procedures.
Release builds are tested artifacts rather than byte-reproducible rebuilds.
Failures in dependency preparation, any test, checksum verification, or asset upload prevent publication.
Windows installers and available failure diagnostics are retained as separate Actions artifacts for seven days.
