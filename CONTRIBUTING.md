# Contributing

Thank you for contributing to the weekly research report template. Keep changes
focused, preserve the existing report workflow, and read `README.md` before
changing user-facing behavior.

## Compatibility and Ownership

Treat documented setup, build, output, LaTeX, and skill behavior as stable by
default. A deliberate breaking change should explain its rationale and impact,
update the relevant documentation in the same change, and provide migration
guidance when users must take action.

Use the repository sources according to their roles:

- `README.md` describes the user workflow.
- The files under `scripts/` implement setup and build behavior.
- `weekly-report.sty` defines the shared LaTeX interfaces and presentation.
- `template.tex` demonstrates the intended report structure and usage.

The `report-build` implementation lives in `scripts/report-build`;
`scripts/setup.sh` installs a link to that canonical script rather than
generating another copy. Routine report content should not require changes to
the template, style, or shared build scripts.

Keep system-command and agent-skill link installation on the shared setup
policy. Treat a link to the same source as an idempotent success, preserve
conflicting destinations by default, and require the explicit replacement
option before backing up and replacing a file or link. Never replace a
directory. Preflight every requested destination before changing the local
configuration or installing any link.

## Shell and Build Safety

Write shell scripts for both Linux and macOS whenever practical. Bash is the
project shell, and scripts should remain compatible with the Bash version
shipped with macOS. Avoid features that require newer Bash releases unless the
project requirements are updated explicitly.

Linux commonly provides GNU command-line utilities, while macOS provides BSD
variants. Avoid relying on implementation-specific flags or output formats. If
GNU and BSD tools require different invocations, detect the implementation and
provide both paths in the script. Do not require Homebrew packages merely to
replace standard macOS utilities when a reasonable portable implementation is
available.

macOS compatibility is a source-level design target, not a tested-platform
guarantee. Contributors should account for known macOS differences, but they
are not required to own macOS hardware, run the scripts on macOS, or guarantee
operation on every macOS and Docker Desktop version. State any known limitation
that remains after a change.

Quote path and variable expansions, preserve `set -euo pipefail` where it is
already used, and resolve script-relative paths without assuming the caller's
working directory.

Preserve the build's isolation and output-safety properties: the TeX container
runs without network access, reads the shared style through a read-only mount,
and compiles in temporary storage. A completed PDF should replace its target
only after a successful build, and the container must not modify source files.

## Editing the AI Skill

Use this order of reference when updating `skills/wr-wr`:

1. Read `skills/wr-wr/SKILL.md` and the reference file governing the behavior
   being changed.
1. Consult `README.md` and the scripts for workflow behavior, `template.tex`
   for intended report usage, and `weekly-report.sty` for exact LaTeX
   interfaces. These repository sources are authoritative.
1. Follow current Codex and Claude skill conventions for platform mechanics
   without overriding repository behavior.

Keep `SKILL.md` focused on activation scope, task routing, cross-cutting
safeguards, and completion behavior. Put detailed domain guidance in the
relevant file under `references/`, and keep deterministic repository-location
logic in the skill's script. Prefer extending an existing reference over adding
a new one unless the change introduces a distinct concern.

Do not duplicate the repository's full interfaces in the skill. Refer to the
canonical sources when exact behavior matters so that skill guidance does not
become a stale parallel manual. The same skill should remain usable through the
supported Codex and Claude links; avoid provider-specific instructions unless
they are necessary and clearly scoped.

Keep skill behavior adaptive, evidence-grounded, protective of existing user
work, and limited to authorized actions. When its capabilities or expectations
change, update the entry point, affected references, and the user-facing AI
workflow documentation together as applicable.

## Validation

Validate in proportion to the change and its risks. Exercise the affected
workflow and relevant error behavior, confirm documentation against the
canonical sources, and compile the example when build or LaTeX behavior
changes. Skill changes should cover representative activation, reference
routing, repository resolution, and affected report tasks.

Document checks that were not run when they would otherwise be relevant. Do
not claim macOS compatibility was verified unless the affected workflow was
actually exercised on macOS, and identify any supported agent service that was
not exercised when the distinction matters. An unavailable macOS or agent
environment does not by itself block a contribution.

## Documentation and Scope

Update `README.md` when setup arguments, generated command behavior, required
software, report-writing instructions, or user-visible skill capabilities
change.

Keep commits limited to meaningful changes and explain user-visible behavior in
the commit message. Do not include generated PDFs or local configuration unless
the contribution specifically requires updating a tracked artifact.

## Versioning and Releases

Use Semantic Versioning for the repository as a whole. The public interface is
the union of the documented LaTeX commands and environments, setup and build
commands, output semantics, template usage, and skill behavior. Determine a
release increment from every changed public surface and apply the highest
required increment:

- Increment MAJOR for any backward-incompatible public-interface change, such
  as removing or changing a documented LaTeX interface, command option,
  default, or output behavior in a way that requires user migration.
- Increment MINOR for backward-compatible functionality, including a new
  LaTeX interface, command option, setup capability, or skill capability, and
  when deprecating public functionality without removing it.
- Increment PATCH for backward-compatible bug fixes, portability and safety
  corrections, documentation corrections, and internal changes that do not
  alter the documented interface.

Compatibility means that documented usage continues to work with its stated
semantics; it does not require byte-identical PDFs or prevent presentation
refinements that preserve those semantics.

Do not increment the version or create a release tag without explicit developer
confirmation. Versions are recorded by Git tags named `vMAJOR.MINOR.PATCH`; do
not add a separate version metadata file. For every confirmed release, update
the repository version near the beginning of `README.md` and the version comment
at the beginning of `template.tex`, commit those changes, and create the matching
tag on that exact commit. Do not omit any of these three locations.

The setup and build scripts report the version derived from the current Git
checkout. A tagged release prints its tag, while later development commits may
include a commit suffix and a dirty checkout may include `-dirty`. The build
always uses the current checkout; do not add a facility for selecting another
repository version at build time.
