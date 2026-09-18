# ppp-editor

Visual layout pass for wr-ppp weekly reports, between "content confirmed" and
"PDF built". See `SKILL.md`.

```
assets/editor.html      the artifact source (self-contained; KaTeX fonts inlined)
scripts/tex_to_state.py main.tex  -> state.json
scripts/state_to_tex.py state.json -> main.tex   (deterministic, no re-wording)
scripts/build_artifact.py state.json -> publishable html
scripts/verify_geometry.py  guards against drift from weekly-report.sty
tests/run_tests.py      headless-Chrome behaviour checks
```
