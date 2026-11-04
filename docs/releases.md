# Versioning and Releases

This reference defines repository-wide versioning, changelog conventions, tag grammar, and reported checkout versions.
Use the [release publication procedure](releases/publishing.md) to prepare a confirmed release or run the validation workflow.

## Version Increments

Use Semantic Versioning for the repository as a whole.
The public interface is the union of the documented LaTeX commands and environments, setup and build commands, output semantics, template usage, and skill behavior.
Determine a release increment from every changed public surface and apply the highest required increment:

- **MAJOR**: Increment MAJOR for any backward-incompatible public-interface change, such as removing or changing a documented LaTeX interface, command option, default, or output behavior in a way that requires user migration.
- **MINOR**: Increment MINOR for backward-compatible additions or changes to substantive functionality, including a new LaTeX interface, setup capability, or skill capability, and when deprecating public functionality without removing it.
  A new command option requires MINOR only when it introduces substantive functionality.
- **PATCH**: Increment PATCH for backward-compatible bug fixes, portability and safety corrections, documentation corrections, and internal changes that do not alter the documented interface.
  Also use PATCH for new options, accepted values, or aliases that expose existing behavior without adding or changing substantive functionality, such as supporting another agent through the existing skill-link installation mechanism.

Compatibility means that documented usage continues to work with its stated semantics; it does not require byte-identical PDFs or prevent presentation refinements that preserve those semantics.

## Changelog

Maintain `CHANGELOG.md` using the Keep a Changelog structure.

- **Component markers**: Begin every changelog item with the most relevant component marker: `[latex]`, `[template]`, `[build]`, `[setup]`, `[skill]`, `[ci]`, or `[docs]`.
  Use `[ci]` for CI/CD workflows, automated validation, dependency caches, and release packaging or publication automation; use `[build]` for report compilation and artifact generation behavior.
  As the repository's responsibilities expand, extend this list when a distinct component needs its own marker, and document the new marker and its scope here in the same change.
- **Incremental history**: Describe notable user-facing differences rather than copying the commit log, and combine closely related commits into one entry when they deliver one change.
  Keep each version section incremental; do not copy beta or release-candidate entries into the stable section.
- **Dates and ancestry**: Order dated changelog sections newest first, preserving the actual release sequence for same-date entries when known.
  Chronological order does not determine SemVer precedence or Git ancestry.
  When chronological order reverses SemVer precedence or the releases do not form a linear ancestry chain, identify their parent release tags explicitly.
  For a merged development baseline, identify the merge commit and its parent tags in `Unreleased`, and base its comparison link on that commit; distinguish integration changes in the baseline from subsequent unreleased changes.

## Tags and Authorization

If you are an AI agent, do not increment the version or create a release tag without explicit developer confirmation.

Versions are recorded by Git tags named `vMAJOR.MINOR.PATCH`, optionally followed by exactly `-beta` or `-rc` for prereleases.
Each numeric component is `0` or a positive decimal integer without leading zeroes.
Do not use other prerelease identifiers, numbered prereleases such as `-beta.1` or `-rc.2`, or build metadata in release tags.
Compare major, minor, and patch numerically, then order equal base versions as beta, release candidate, and official release.

Published tags are immutable; use the next allowed release stage or a new base version for subsequent publications rather than rewriting a tag.

## Checkout Versions

The setup and build scripts report the version derived from the current Git checkout.
A tagged release prints its tag, while later development commits may include a commit suffix and a dirty checkout may include `-dirty`.

By default the build uses the current checkout; the optional automatic updater may advance it to an eligible published release before compilation.
This channel-based update is the supported exception; do not add arbitrary per-build version selection.

## Tag-driven CI and Windows Releases

[Release Publication](releases/publishing.md) covers confirmed release preparation, manual validation, tag-triggered checks, assets, and failed-run recovery.
The repository-wide version remains the authority for native Windows; its implementation and packaging procedures stay in the Windows development guide.
