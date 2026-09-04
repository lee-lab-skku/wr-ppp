<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- [setup] optional administrator mode installs `admin-wr` with requested agent services, preserves a private manager manifest, and stores an independently optional bundle output directory.
- [skill] an `admin-wr` workflow for manifest-scoped AI candidate selection, evidence and issue reporting, draft review, explicit approval, and traceable final promotion.
- [build] deterministic XeLaTeX administrator bundles with a one-page index, normalized source staging, page-range and source-hash validation, and atomic same-week replacement.
- [docs] administrator installation, manifest configuration, selection and approval behavior, and contributor boundaries.

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

[Unreleased]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/lee-lab-skku/wr-ppp/tree/v1.0.0
