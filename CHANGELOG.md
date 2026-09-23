<!-- markdownlint-disable MD024 -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Baseline: merge [1a0a295](https://github.com/lee-lab-skku/wr-ppp/commit/1a0a295ab3df4d38b90ed778b15dd5777b7c5726) of [v1.5.0-beta](https://github.com/lee-lab-skku/wr-ppp/releases/tag/v1.5.0-beta) and [v1.4.1](https://github.com/lee-lab-skku/wr-ppp/releases/tag/v1.4.1), whose common parent release is [v1.4.0](https://github.com/lee-lab-skku/wr-ppp/releases/tag/v1.4.0).
The baseline includes the visual-editor drafting-stage and scientific-notation integration fixes; entries below describe changes after that merge.

### Added

- [docs] license original project materials under MIT in the laboratory's name, clarify research-content rights and attribution-free use in reports, credit contributors through Git history, and disclose AI use in project development.

### Fixed

- [build] include project license and report-use notices in Windows distributions, and preserve the full KaTeX notice with shared editor assets and standalone HTML exports.

## [1.4.1] &mdash; 2026-09-23

Parent tag: [v1.4.0](https://github.com/lee-lab-skku/wr-ppp/releases/tag/v1.4.0).
This maintenance release is later by date but lower in SemVer precedence than `v1.5.0-beta`; the two tags are separate descendants of `v1.4.0`.

### Fixed

- [skill] defer minor pagination, overflow, and alignment repairs until editorial revision while accurately reporting observed issues; retain early repairs for compilation blockers, substantive content loss, and explicit layout requests.
- [skill] keep drafts based on organized records in the author's research perspective without excessive first-person wording, carry meaningful structure into subsection bodies, and check applicable `siunitx` and `mhchem` notation in text, tables, and captions; silently skip irrelevant checks without adding content to satisfy them.

## [1.5.0-beta] &mdash; 2026-09-21

Parent tag: [v1.4.0](https://github.com/lee-lab-skku/wr-ppp/releases/tag/v1.4.0).

### Added

- [build] add a shared browser editor with figure sizing and side-by-side placement, a guarded TeX editing entry point for the Docker workflow that preserves the original source, and native Windows form integration with automatic saving and image uploads.
- [setup] add interactive Codex or Claude selection to register both report-writing and administrator skills from a Windows source checkout.

### Changed

- [skill] integrate optional visual-editing guidance into `wr-wr` and clarify native Windows commands, temporary paths, and configuration lookup across report and administrator workflows.
- [build] expose administrator bundle commands directly under root `scripts/` while preserving existing skill entry points through links.
- [ci] add shared-editor conversion, HTTP persistence, geometry, and browser checks with explicit entry points, and supply real image fixtures for portable Windows template builds.
- [docs] organize English Windows documentation around user guidance, contribution rules, and dated internal change/validation history, with repository versioning remaining at the root.

### Fixed

- [setup] allow Windows skill registration without symbolic-link privileges by falling back to directory junctions, including recognition during repeat installation and rollback.
- [build] save figure originals when they are added to a Windows report and include available images referenced by single-figure and paired-figure commands in the temporary build sources, preserving shared placeholder behavior for unavailable images.

## [1.4.0] &mdash; 2026-09-16

### Changed

- [build] reduce Windows report preparation overhead by staging the source and explicitly referenced local dependencies instead of copying the entire source directory, and avoid recursive repository-wide TeX searches.
- [ci] assemble stable GitHub Release notes from the matching stable, RC, and beta changelog sections while keeping changelog entries incremental; prerelease publications retain their own section only.

## [1.4.0-rc] &mdash; 2026-09-15

### Added

- [ci] manual CI runs validate and package a selected branch or tag, retaining Windows installers for download without publishing a release.

### Changed

- [ci] reuse prepared Windows build dependencies to reduce CI setup time while retaining PDF, packaging, and installation checks.
- [docs] root documents describe Windows capabilities and effects by default, with implementation and maintenance guidance in the Windows development guide; internal improvements may still be described at the root level.

### Fixed

- [ci] prevent false CI test failures caused by platform-specific temporary paths and leaked test exit codes.
- [ci] fix Windows dependency preparation failures on runners with multiple tool installations.
- [setup] complete setup and preserve configured update channels with macOS's Bash 3.2, including invocations without positional arguments or skill selections.
- [build] allow automatic release updates when `report-build` runs without arguments on Bash 3.2.

## [1.4.0-beta] &mdash; 2026-09-15

### Added

- [ci] tag-driven GitHub Actions tests on Linux/macOS and full Windows offline installer validation, with automatic EXE/checksum publication and changelog release notes after all platforms pass.
- [setup] native Windows GUI/CLI, source setup and automation, optional local report-building tools, and self-contained per-user offline installers.
- [build] native report compilation, explicit administrator bundles with reviewed promotion, and canonical Slack notifications without Bash, WSL, or Docker.
- [latex] form/Markdown headings and strike-through formatting, with consistent report headers and footers.
- [skill] native Windows command routing and canonical skill links for agents, Claude, and Antigravity, including shared destination aliases.

### Changed

- [docs] distinguish Bash automation on Linux/macOS from PowerShell automation on Windows, and document native build isolation and source setup migration.

## [1.3.1] &mdash; 2026-09-15

### Added

- [setup] `--skills=antigravity` links skills into `~/.gemini/config/skills`; `gemini` and `copilot` are aliases for the shared `agents` destination.

### Changed

- [setup] repeated skill service names and aliases for the same destination are accepted and installed once per destination.
- [docs] option, value, and alias additions that expose existing behavior without substantive functionality changes qualify for PATCH releases.

## [1.3.0] &mdash; 2026-09-14

### Added

- [setup] optional `--auto-update[=stable|prerelease|off]` release channels, checked at build time once per 24 hours, with shared installation locking, failure retry delays, and branch-preserving release checkout updates.

### Changed

- [docs] release tags allow only unnumbered beta and rc prereleases, with explicit numeric version and release-stage ordering.
- [skill] every figure requires a contextual body reference through `cleveref`; table and equation references remain optional but must use it when present.
  Review must correct manually written reference numbers and address missing figure references, while label prefixes and supported calling forms remain flexible.
- [skill] report authoring checks the shared style's loaded packages first and uses their relevant functionality; template comments illustrate cross-references, units, and chemical notation without restricting usage to the example calls.

### Fixed

- [latex] pin `mhchem` syntax to version 4.
- [skill] preserve literal quotes in missing-member notification names.
- [setup] reject invalid options and paths before installation, and preserve configuration and restore changed links when setup fails.
- [build] preserve existing PDFs until validated replacements are ready, update mtime after atomic replacement, and serialize administrator publication.
- [build] automatic report serial numbers exclude hidden, metadata, lock, temporary, and backup PDFs from the output-directory count, recognize uppercase PDF extensions, and count filenames containing newlines correctly.

## [1.3.0-beta] &mdash; 2026-09-12

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

[Unreleased]: https://github.com/lee-lab-skku/wr-ppp/compare/1a0a295ab3df4d38b90ed778b15dd5777b7c5726...HEAD
[1.4.1]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.4.0...v1.4.1
[1.5.0-beta]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.4.0...v1.5.0-beta
[1.4.0]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.4.0-rc...v1.4.0
[1.4.0-rc]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.4.0-beta...v1.4.0-rc
[1.4.0-beta]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.3.1...v1.4.0-beta
[1.3.1]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.3.0-beta...v1.3.0
[1.3.0-beta]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.2.1...v1.3.0-beta
[1.2.1]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/lee-lab-skku/wr-ppp/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/lee-lab-skku/wr-ppp/tree/v1.0.0
