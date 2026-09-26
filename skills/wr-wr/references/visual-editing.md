# Visual Editing

Use the shared editor when the user wants browser-based layout editing of an existing report.
Resolve the repository through the skill entry point, and read the README's "Visual Editing" section for commands, dependencies, and output behavior.
Report content still follows the shared report policy and the skill's evidence and comment-preservation guidance.

## Choose the Entry Point

On Linux/macOS and WSL, invoke `python3 <resolved-repository>/scripts/report-edit <source.tex>` with the intended `--date` when known.
Keep the process alive during the user's session and provide its printed local URL if the browser cannot open automatically.
The default output is a separate sibling `<source-stem>.edited.tex`; choose another new sibling with `--output` if needed.
Do not replace the original merely because the editor produced an output.
Review the source differences and final PDF within the user's authorized editing scope.

On native Windows, use the existing application's **시각 편집기** button for `.wr.json` reports, as described in `windows/README.md`.
That path retains the native form persistence and build workflow.
The native application remains available for normal report writing and administrator work.

## Preserve Content

The TeX entry point retains the original source, including the fully commented template, and edits only supported source spans.
Custom preambles, comments, and unsupported or ambiguous syntax are preserved as read-only regions; inspect the preserved-source panel or edit them in LaTeX.
Do not strip content or weaken preservation checks to force a structural operation.
`check_roundtrip.py` checks exact source preservation; similarity is diagnostic, not proof of rendering equivalence.
Compare exported changes with the original, including references, comments, scientific notation, and list hierarchy.
Keep source metadata when passing versioned state through JSON or HTML; legacy state cannot reconstruct source it never stored.
If concurrent browser, form, or external edits cause a save conflict, preserve unsaved work and reopen to reconcile it rather than retrying a stale overwrite.
Apply the relevant notation and reference checks in [latex-and-build.md](latex-and-build.md) to exported LaTeX; browser rendering alone does not establish compliance.
Do not reword user-edited text while transferring state.

Image previews are not substitutes for the originals needed by TeX.
The local editor stores uploaded originals in the report's `figures/` directory; verify every referenced image before building.
The browser uses the shared page dimensions but does not guarantee XeLaTeX pagination.
Use the existing `report-build` path and the same reporting date when PDF validation is needed, following [latex-and-build.md](latex-and-build.md), "Match Layout Work to the Stage".
Editing in the browser does not itself advance an initial draft into finalization; defer incidental cosmetic fixes unless the user requested them, and apply full page-count and content review during editorial revision or finalization.

## Existing Artifact Integrations

The root `scripts/` conversion and HTML-generation entry points delegate to the common implementation.
For an explicitly requested Artifact workflow, run `check_roundtrip.py` before import, use `tex_to_state.py` and `build_artifact.py`, and read the edited JSON from the `state-json` script element before running `state_to_tex.py` to a separate output for review.
Retain full-resolution image originals in the report directory.
Do not assume an Artifact tool or another report-authoring skill is available, and do not publish report contents merely to use the local editor.
