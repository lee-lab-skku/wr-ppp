# Release Publication

Use this procedure to prepare a confirmed release, test a selected checkout, or recover a failed publication.
Follow the [versioning and release rules](../releases.md), including developer confirmation for version increments and new tags.
Paths refer to the repository root.

## Prepare a Confirmed Release

For a confirmed release, complete these preparation steps:

1. Move the relevant changelog entries from `Unreleased` into a dated version section.
1. Update the version comment at the beginning of `template.tex`.
1. For releases that distribute bundled third-party binaries, maintain version-specific source-access directions in `windows/RELEASE-NOTICE.md`.
   The release generator appends this notice once after the selected change sections so it appears beside the installer.
   Keep distribution directions out of individual changelog sections and retain only change history there.
   The notice belongs to the release checkout: preserve it during promotion and update it when bundled sources change, using the [Windows source-reference procedure](../../windows/CONTRIBUTING.md#third-party-source-references).
1. Confirm that the latest-version badge near the beginning of `README.md` remains configured to derive its value from the repository's SemVer tags.
1. Commit those changes and create the matching tag on that exact commit.

Do not omit the changelog update, template update, badge check, or tag.

## Test a Selected Checkout

The release workflow supports `workflow_dispatch` for manually testing and packaging a selected branch or tag, without running on branch pushes.
The workflow must be present on the default branch for manual dispatch to be available.

- **Start a run**: In GitHub Actions, open **Test and release**, choose **Run workflow**, and select the branch to check.
- **Checkout and artifacts**: Manual runs pin every job to the selected commit, skip release-note preparation checks, and never publish a GitHub Release, even when a tag is selected.
  They run the same platform tests, Windows packaging, installer smoke tests, and checksum verification as tag pushes, retaining the installer and SHA256 in the `windows-installer` Actions artifact for seven days.
- **Version and identity**: Manual installer versions use the existing Git-derived bundle version, including a development commit suffix when applicable; the checkout must have a reachable supported version tag and must produce a clean version.
  Use the Actions run and its commit SHA to identify the build; manual runs do not create or increment release tags.

## Validate a Release Tag

`.github/workflows/release.yml` runs on pushed `v*` tags.
For tag pushes, the validation job accepts only the [release-tag grammar](../releases.md#tags-and-authorization), requires the tag and triggering commit to match the checkout, checks the version comment in `template.tex`, and requires exactly one matching dated changelog section.

Release notes must contain at least one change across the selected sections; a stable section may be empty when promotion adds no changes beyond its prereleases.
Complete the normal release preparation before pushing the tag; CI does not create tags, increment versions, or edit source files.

## Required Checks and Permissions

Linux and macOS run the common/POSIX regression suite on their own hosted runners, using the operating system's `/bin/bash`.
These jobs substitute Docker and desktop viewers and do not build release artifacts or install TeX.
Windows must pass native/common regression checks, actual PDF generation, and portable and installed application checks before publication.
Validate the offline distribution without relying on development tools, and verify that uninstallation preserves user configuration and PDFs.
See the [Windows development guide](../../windows/CONTRIBUTING.md#ci-and-packaging) for build dependencies and packaging procedures.

Only the publication job has `contents: write`, and it runs after every platform and the shared [Markdown check](../development.md#markdown-structure) succeed.
Use the repository's automatic `GITHUB_TOKEN`; no personal access token is required.

Organization/repository Actions policies must allow the pinned official actions and release-writing job permission.
Keep third-party action revisions pinned to full commit IDs; follow the Windows development guide when updating installer build dependencies.

## Published Assets and Notes

CI packages the exact triggering tag even if multiple tags refer to the same commit.
The release contains only `WeeklyReport-<tag>-Setup.exe` and its `.exe.sha256` file; the publication job revalidates both after artifact transfer.

`.github/scripts/release.py` uses only the matching changelog section for a prerelease publication.
For a stable publication, it collects the matching stable section and any same-version `-rc` and `-beta` sections, in that order with version headings, without changing `CHANGELOG.md`.
After collecting changes, the generator appends `windows/RELEASE-NOTICE.md` from the same checkout exactly once for stable and prerelease publications.

A missing or blank notice fails release preparation and publication.
Missing prerelease stages are allowed; duplicate sections or invalid dates in any selected stage fail validation before publication.
Unreleased changes and other base versions are never included.

Tags ending in `-beta` or `-rc` produce prereleases and cannot become Latest; stable releases use GitHub's default Latest selection.

## Recover a Failed Run

Publication uploads to a draft before making it public.
Retry a failed run using GitHub Actions' rerun controls: unpublished drafts for the same commit can resume, but published assets are never overwritten.
An existing complete published release is left unchanged; a published release missing expected assets or a draft targeting a different commit fails for maintainer review.
Preserve published tags and use a new allowed version when source fixes are needed.

## Dependency Preparation and Diagnostics

CI reuses prepared Windows build dependencies to reduce setup time while retaining all build and distribution checks.
Cache misses trigger fresh preparation; finished installers and previous test results are not reused.
See [dependency cache maintenance](../../windows/CONTRIBUTING.md#tinytex-cache) for refresh and sharing procedures.

Release builds are tested artifacts rather than byte-reproducible rebuilds.
Failures in dependency preparation, any test, checksum verification, or asset upload prevent publication.
Windows installers and available failure diagnostics are retained as separate Actions artifacts for seven days.
