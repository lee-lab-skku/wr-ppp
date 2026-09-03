<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] &mdash; 2026-09-03

### Added

- [latex] Added the reusable weekly-report package with report headers, PPP content boxes, numbered subsections, flexible tables, figure helpers, automatic metadata, and page footers.
- [template] Added a complete illustrative PPP report that can be copied and adapted without changing the shared package.
- [build] Added Docker-isolated XeLaTeX builds with a default or explicit TeX source and configured or current-directory output.
- [build] Added host-resolved report dates, Thursday-based reporting weeks, automatic serial numbers, and explicit date and serial overrides.
- [build] Added Git-derived repository version output to identify the checkout used for each build.
- [setup] Added reusable output-directory and Docker-image configuration with an installed `report-build` command.
- [setup] Added preflighted, backup-preserving command and agent-skill link installation with explicit replacement controls.
- [setup] Added Git-derived repository version output during setup.
- [skill] Added a portable report-writing skill for orientation, drafting, revision, build diagnosis, and final validation.
- [docs] Added user and contributor guidance for the report workflow, compatibility, safety, validation, and repository-wide Semantic Versioning.
- [docs] Added a Keep a Changelog release history with component-prefixed entries.
- [docs] Added a GitHub badge that reports the latest SemVer tag as the latest repository version.

[Unreleased]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/lee-lab-skku/wr-ppp/tree/v1.0.0
