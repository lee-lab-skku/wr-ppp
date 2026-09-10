<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [skill] optional Slack Incoming Webhook notices for administrator-decided holds caused by missing required reports, with message preview, hidden credential setup, and duplicate-send protection.

### Changed

- [docs] contributor guidance focuses on durable contracts and design constraints, links to canonical operating procedures instead of duplicating them, and uses sentence-based line breaks.

### Fixed

- [setup] administrator manifest creation no longer fails on NAS filesystems that reject `chmod`; restrictive permissions are requested at file creation with `umask 077`.

## [1.2.1] &mdash; 2026-09-10

### Added

- [setup] `--admin-data` stores the manager manifest and execution history beneath one directory, with repository-local defaults and per-file read fallback for missing configured metadata.

### Changed

- [setup] `--skills=agents` is the canonical name for installing to `~/.agents/skills`; `codex` remains a backward-compatible alias.
- [skill] administrator bundle covers omit page ranges and add cumulative inclusion tables with newest weeks first and members as columns, using verified historical records and distinct markers for exceptions, optional omissions, and unknown history.
  All members share one table with angled name headings, and the target week's row has a pale blue background.

## [1.2.0] &mdash; 2026-09-08

### Added

- [skill] administrator draft builds print a review command that opens the temporary PDF on Linux, macOS, or WSL, and the agent presents a clickable draft path before approval.

### Changed

- [skill] report guidance now requires research-focused content, claims followed by evidence and implications, and a two-page maximum per person per week, with only a justified minimum exception when essential research content cannot be shortened further; administrator review flags overlength submissions.
- [skill] writing assistance reads canonical template comments with judgment, preserves retained instructional comments in new reports, and keeps evidence, editorial, and build procedures in selectively loaded references while shared report policy remains in the README.
- [template] the illustrative report now leads with its research result and omits standalone software and tooling progress.
  Comments provide adaptable writing prompts that preserve author choice in organization and form.
- [build] final administrator execution TSVs are stored in the repository's Git-ignored `.admin-wr/manifests/`, while draft TSVs stay in a temporary `.manifests/` subdirectory; legacy manifests beside final PDFs remain usable as history.

### Fixed

- [build] draft bundles are rejected inside descendants of the configured final output directory, including paths resolved through directory links.

## [1.1.1] &mdash; 2026-09-05

### Fixed

- [skill] missing factual support is now handled as an author-facing gap instead of automatically becoming reader-facing uncertainty language or placeholder values.

## [1.1.0] &mdash; 2026-09-05

### Added

- [setup] optional administrator mode installs `admin-wr` with requested agent services, preserves a private manager manifest, and stores an independently optional bundle output directory.
- [skill] an `admin-wr` workflow for manifest-scoped AI candidate selection, evidence and issue reporting, draft review, explicit approval, and traceable final promotion.
- [build] deterministic XeLaTeX administrator bundles with a one-page index, normalized source staging, page-range and source-hash validation, and atomic same-week replacement.
- [docs] administrator installation, manifest configuration, selection and approval behavior, and contributor boundaries.

### Changed

- [build] the report metadata helper now provides a direct TSV interface, and administrator workflows require container-provided PDF inspection tools.
- [skill] an otherwise clear report with a conflicting internal week remains included with an approval-requiring warning.

### Fixed

- [build] administrator preflight and PDF probing preserve Docker errors and distinguish CLI, access, daemon, image, dependency, and runtime failures.
- [docs] administrator period resolution and PDF inspection instructions now match their executable interfaces.

## [1.0.0] &mdash; 2026-09-03

### Added

- [latex] the reusable weekly-report package with report headers, PPP content boxes, numbered subsections, flexible tables, figure helpers, automatic metadata, and page footers.
- [template] a complete illustrative PPP report that can be copied and adapted without changing the shared package.
- [build] Docker-isolated XeLaTeX builds with a default or explicit TeX source and configured or current-directory output.
- [build] host-resolved report dates, Thursday-based reporting weeks, automatic serial numbers, and explicit date and serial overrides.
- [build] Git-derived repository version output to identify the checkout used for each build.
- [setup] reusable output-directory and Docker-image configuration with an installed `report-build` command.
- [setup] preflighted, backup-preserving command and agent-skill link installation with explicit replacement controls.
- [setup] Git-derived repository version output during setup.
- [skill] a portable report-writing skill for orientation, drafting, revision, build diagnosis, and final validation.
- [docs] user and contributor guidance for the report workflow, compatibility, safety, validation, and repository-wide Semantic Versioning.
- [docs] a Keep a Changelog release history with component-prefixed entries.
- [docs] a GitHub badge that reports the latest SemVer tag as the latest repository version.

[Unreleased]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.2.1...HEAD
[1.2.1]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/lee-lab-skku/wr-ppp/tree/v1.0.0
