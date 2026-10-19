# Contributing

Thank you for contributing to the weekly research report template.
Keep changes focused, preserve the existing report workflow, and read [README.md](README.md) before changing user-facing behavior.

## Compatibility and Ownership

Submit contributions under the project's [MIT License](LICENSE.txt), with the report-use permission described in [NOTICE](NOTICE.txt).
Contributors must have the right to provide their contributions under these terms and preserve applicable third-party notices.
Submission alone does not assign copyright; any required assignment to the laboratory is handled separately.
Individual contributions are credited through Git history.

Treat documented setup, build, output, LaTeX, and skill behavior as stable by default.
A deliberate breaking change should explain its rationale and impact, update the relevant documentation in the same change, and provide migration guidance when users must take action.

The [development guide](docs/development.md) defines architectural responsibilities, shell portability, build and publication safety, skill maintenance, and documentation scope.
Follow the [administrator development contracts](docs/admin-development.md) when changing bundles or notifications.
Native Windows implementation and packaging procedures remain in [windows/CONTRIBUTING.md](windows/CONTRIBUTING.md).
The [documentation index](docs/README.md) identifies the canonical policy or reference for each topic.

## Development Setup and Validation

Keep automatic updates disabled in development checkouts so builds do not switch them to a release:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest --auto-update=off
```

Bash/Docker setup requires Docker access and `sudo` for the installed command link; see [setup details](docs/setup.md).
Python checks require host Python 3 with the standard library; editor rendering checks also use Node.js and browser checks need a supported browser.
Run checks in proportion to the affected behavior:

- Build or LaTeX changes: `./scripts/test.sh` to compile the example through the canonical build command.
- Administrator workflow changes: `python3 -B -m unittest discover -s tests -v` for isolated regression checks with substituted Docker and viewers.
- Shared editor changes: `python3 -B -m unittest discover -s tests -p 'test_editor.py' -v`, plus the rendering, persistence, and browser checks in the [validation guide](docs/development.md#validation).
- Guidance or skill changes: check the [report policy](docs/report-policy.md), template comments, affected reference routing, and representative report tasks.

Exercise the affected workflow and failure behavior; substituted dependencies do not verify actual TeX rendering or desktop viewers.
Report relevant checks not run and platform limitations; do not claim macOS or agent-service verification without exercising that environment.
Use the [full validation guidance](docs/development.md#validation) and [Windows validation guidance](windows/CONTRIBUTING.md#validation) for their respective scopes.

## Contribution Workflow

Keep routine report content separate from shared template, style, and script changes.
Preserve documented setup, output, LaTeX, and skill contracts; explain deliberate breaking changes and provide migration guidance when users must act.
Update the relevant canonical documentation with behavior changes, keeping the root entry points concise.
Keep commits limited to meaningful changes and explain user-visible behavior in the commit message.
Do not include generated PDFs or local configuration unless the contribution specifically requires updating a tracked artifact.

## Versioning and Releases

Follow the existing [versioning and release policy](docs/releases.md) for SemVer decisions, changelog conventions, tag grammar, and release preparation.
AI agents must not increment the version or create a release tag without explicit developer confirmation.
Published tags are immutable.

### Tag-driven CI and Windows Releases

See the [release procedure](docs/releases.md#tag-driven-ci-and-windows-releases) for manual workflow runs, tag validation, publication, and retry behavior.
The repository-wide release remains the version authority for native Windows.
