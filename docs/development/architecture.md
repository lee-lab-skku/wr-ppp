# Shared Architecture

This reference defines source ownership, shared editor boundaries, and command entry-point contracts.
Use it when deciding where implementation belongs or which existing contract a change must preserve.

## Source Responsibilities

Use the repository sources according to their roles:

- `README.md` introduces the user workflow; [the report policy](../report-policy.md) defines shared authoring requirements, and [the documentation index](../README.md) identifies the canonical guide for each topic.
- The files under `scripts/` implement Linux/macOS setup and build behavior; the [Windows guide](../../windows/README.md) defines the native Windows entry points and workflow.
- The files under `skills/` define agent workflows and safeguards, with task-specific procedures in selectively loaded references.
- `weekly-report.sty` defines the shared LaTeX interfaces and presentation.
- `template.tex` provides contextual writing prompts and an adaptable worked example.

## Repository Files

These sources provide the report workflow and its shared implementation:

| Source | Responsibility |
| --- | --- |
| `template.tex` | the illustrative source copied to `main.tex` for a new report |
| `weekly-report.sty` | shared layout, automatic values, and reusable helpers |
| `scripts/report-build` | canonical implementation of the installed build command |
| `scripts/report-edit` | local browser editing entry point for the Docker workflow |
| `report_editor/` | common HTML, editor transport, and LaTeX conversion tools |
| `scripts/report-metadata.sh` | source-compatible report date and reporting-week CLI |
| `scripts/setup.sh` | saves the build configuration and links `report-build` |
| `scripts/test.sh` | verifies the setup through the canonical build command |
| `skills/wr-wr` | service-neutral report-writing skill |

## Shared Editor

The Docker workflow is the primary report path; native Windows adapts shared capabilities to its GUI and build environment.

- **Common implementation**: Keep HTML editing resources, local browser transport, and portable LaTeX conversion in `report_editor/`, without imports from `windows/` or a dependency on an Artifact provider.
  Keep one HTML source and one implementation of each conversion tool; root script entry points delegate to the shared package.
- **TeX adapter**: The TeX adapter exposes editing through `scripts/report-edit` and leaves PDF compilation to `report-build`.
- **Native adapter**: Windows retains its native application and owns form-model conversion and persistence through an adapter to the common editor.

## Source Preservation

Preserve these conversion boundaries and their diagnostics:

- **Source spans**: Preserve the source-backed editor contract: no-op exports must retain every source byte, and supported edits must leave unrelated spans intact.
  Keep lexical scanning, protected source regions, stable figure identities, and lossless export in the shared package; the native form adapter retains ownership of its own model.
- **Protected content**: Do not execute TeX or expand external inputs to discover editable regions.
  Ambiguous boundaries and unsupported syntax are read-only; reject operations that cross protected boundaries or discard their content.
- **State metadata**: State format version 2 optionally carries immutable preservation metadata; retain legacy JSON loading without claiming recovery of absent source.
- **Round-trip diagnostics**: Similarity scores are diagnostic, never permission to discard source.
  The round-trip command reports exact source preservation; its similarity percentage is diagnostic and `--min` cannot permit source loss.

## Persistence

Browser saves carry a revision and state snapshot; serialize writes, reject stale revisions, and mark only acknowledged snapshots clean.
Adapters must check destination fingerprints under a publication lock before writing; conflicts must preserve the newer file.

## Command and Skill Entry Points

Keep implementations canonical across entry points:

- **Canonical links**: Install command and skill links to canonical repository sources rather than generating duplicate implementations.
  Keep Linux/macOS operational command implementations in root `scripts/`; expose them from `skills/*/scripts/` through relative links rather than placing the canonical implementation inside a skill.
  Skill-specific templates and procedural references may remain with the skill; resolve their paths from the repository root so commands work through either entry point.
- **Development checks**: Keep development-only checks in `tests/`, with names that identify their scope; preserve a documented older command with a thin wrapper when needed.
- **Import paths**: Source launchers and test entry points prepare Python import paths; importing a library package must not modify `sys.path`.
- **Report isolation**: Routine report content should not require changes to the template, style, or shared build scripts.

## Existing Editor Integrations

For existing script-based integrations, `scripts/tex_to_state.py`, `state_to_tex.py`, `build_artifact.py`, `check_roundtrip.py`, and `verify_geometry.py` remain entry points to the common implementation.
The duplicated `ppp-editor/` tree and root `SKILL.md` have been consolidated: use these root scripts and the installed `wr-wr` skill's visual-editing guidance instead of a separate `ppp-editor` skill link.
Artifact HTML export remains available through `build_artifact.py`; the local workflow does not require an Artifact service or upload the report to one.
