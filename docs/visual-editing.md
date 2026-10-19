# Visual Editing

The Docker workflow and the native Windows application share the same HTML editor.
On Linux/macOS or WSL, start it from the repository with an existing report source:

```bash
python3 /path/to/wr-ppp/scripts/report-edit /path/to/report/main.tex --date 2026-09-21
```

The command opens a local browser session and prints its URL; use `--no-open` to open that URL yourself.
Keep the terminal process running while editing, then stop it with Ctrl+C after saving.
Edits are saved to `main.edited.tex` beside the source, leaving `main.tex` unchanged.
Use `--output /path/to/report/another-name.tex` to choose a different new sibling file; existing output files are refused.
Uploaded image originals go into the report's `figures/` directory.
To resume later, pass the edited file as the source and choose another new output filename.
The command is available directly from the checkout; `setup.sh` continues to install `report-build` and the selected skills.

The editor retains the original TeX, including the commented example template, preamble, labels, figure order, table columns, whitespace, and line endings.
Saving without edits preserves the source byte-for-byte; editing a supported field replaces its source span while retaining untouched text.
Unknown commands, complex tables, comments, and ambiguous regions remain read-only; expand the preserved-source panel to inspect them and use your LaTeX editor to change them.
Moving or deleting content across protected regions is refused rather than silently changing its scope or losing comments.
Figure labels survive supported moves and pair splits; referenced figures cannot be deleted while their references remain.
The round-trip command reports exact source preservation; its similarity percentage is diagnostic and `--min` cannot permit source loss.
Legacy JSON without source metadata remains readable, but cannot reconstruct previously discarded comments or settings.

Automatic saves are serialized and only acknowledged snapshots are marked saved.
The save button waits for pending edits, including the active text field.
If another tab or application changes the source or output, saving stops with a conflict; retain your unsaved text and reopen the report to reconcile it.
Interrupted publication can leave a sibling `.editor-lock` directory; verify that the editing process has stopped before removing that directory.
Do not remove content or comments to bypass a preservation check.
The browser preview is a layout aid, and matching page dimensions does not guarantee the same line or page breaks as XeLaTeX.
Review the generated source and build the edited file through the usual Docker command:

```bash
cd /path/to/report
report-build --here --date 2026-09-21 main.edited.tex
```

Use the same date for the editor preview and the PDF build.
Check the actual PDF, references, and page count before replacing the original source with a reviewed revision.
The [LaTeX and build reference](../skills/wr-wr/references/latex-and-build.md) defines stage-aware layout and scientific-notation checks, which also apply to visual-editor exports.
The native Windows application retains its form editor, PDF generation, and administrator screens; its **시각 편집기** button opens this shared browser editor with the existing `.wr.json` save workflow described in the [Windows guide](../windows/README.md).

For existing script-based integrations, `scripts/tex_to_state.py`, `state_to_tex.py`, `build_artifact.py`, `check_roundtrip.py`, and `verify_geometry.py` remain entry points to the common implementation.
The duplicated `ppp-editor/` tree and root `SKILL.md` have been consolidated: use these root scripts and the installed `wr-wr` skill's visual-editing guidance instead of a separate `ppp-editor` skill link.
Artifact HTML export remains available through `build_artifact.py`; the local workflow does not require an Artifact service or upload the report to one.
