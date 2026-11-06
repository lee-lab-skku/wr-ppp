# Documentation Maintenance

This guide covers document ownership, writing and review with mddt, skill maintenance, and the automated minimum check.
Use it when changing repository Markdown, report guidance, or the bundled agent skills.

## Document Responsibilities

Keep each document responsible for its own reader and task:

- **Entry points**: Keep `README.md` and `CONTRIBUTING.md` concise entry points with essential setup, usage, and verification commands.
  Update the relevant canonical guide when setup arguments, generated command behavior, required software, report-writing instructions, or user-visible skill capabilities change, and update the root entry point when its summary or links change.
- **Canonical guides**: Use the [documentation index](../README.md) to locate topic ownership; move detailed material instead of maintaining duplicate manuals.
  Keep administrator development contracts in [Administrator Development](../admin-development.md) and operating procedures in the administrator references.
  Limit the README's administrator section to a short pointer and basic setup options.
- **Contribution scope**: Keep commits limited to meaningful changes and explain user-visible behavior in the commit message.
  Do not include generated PDFs or local configuration unless the contribution specifically requires updating a tracked artifact.

## Documentation and Scope

Shared documentation describes Windows from the repository-wide perspective:

- **External view**: When editing root documents or shared guides under `docs/`, treat the Windows implementation as a black box by default.
  Describe its supported capabilities, inputs and outputs, observable behavior, compatibility, and repository-wide contracts without requiring readers to understand its internal components.
  Keep Windows-specific architecture, implementation rules, and dependency or packaging procedures in the [Windows development guide](../../windows/CONTRIBUTING.md), and link there when detail is needed.
- **Windows entry points**: Use `windows/README.md`, `windows/CONTRIBUTING.md`, and `windows/CHANGELOG.md` as the three Windows documentation entry points.
  Their roles mirror the root documents: user guidance, durable contributor guidance, and internal change history with relevant validation evidence.
  Keep Windows internals that cannot be adequately described through the root documents' external perspective in these subordinate documents, and link to root policy instead of duplicating it.
- **History and evidence**: The Windows changelog supplements the root history using dated change groups linked to commits or PRs, with relevant validation recorded alongside them; it must not introduce independent version numbers or release authority.
  Keep its detailed entry conventions in [the Windows contribution guide](../../windows/CONTRIBUTING.md#documenting-internal-changes).
  Preserve the environment, scope, and limitations of historical validation when consolidating records; do not present past checks as verification of current source.
- **Internal improvements**: This perspective does not prohibit describing changes that are entirely internal: explain relevant improvements, their purpose, evidence, and limitations at the level appropriate to the root document, even when the public interface is unchanged.
  For example, root documentation may describe faster CI dependency preparation or more reliable installation; the implementation and cache maintenance steps belong in the Windows guide.

## Markdown Structure

For repository Markdown, follow the [mddt](https://github.com/mirinae3145/mddt) skill's [writing procedure](https://github.com/mirinae3145/mddt/blob/main/skills/mddt/references/writing.md).
Place content in the document tree before writing it, and reread each changed topic whole once the content settles.
The checker then covers only the requirements a parser can decide.
This adoption covers root documents, shared guides, and skill documentation; Windows documentation remains outside its current scope.

Use an installed copy of the mddt skill or a checkout of its repository, which provide the procedure's reference documents and the checker.
Apply the procedure with these repository-specific decisions:

- **Placement**: Before writing, identify the reader, the question the content answers, and its [document kind](https://github.com/mirinae3145/mddt/blob/main/skills/mddt/references/kinds.md).
  Locate its canonical home with the [documentation index](../README.md) and the [document responsibilities](#document-responsibilities), as [placing a document](https://github.com/mirinae3145/mddt/blob/main/skills/mddt/references/writing.md#placing-a-document) describes.
- **Settled content**: Once the content settles, update its overview, parent summaries, and affected links.
  Then reread the changed topics whole against the [document model](https://github.com/mirinae3145/mddt/blob/main/skills/mddt/references/model.md), including judgments the checker cannot make.
  Explain structural choices in review when their rationale is not evident from the document.
- **Findings**: After this review, run the [automated minimum check](#automated-minimum-check) and judge its warnings in context, as [checking](https://github.com/mirinae3145/mddt/blob/main/skills/mddt/references/writing.md#checking) describes.
  Passing establishes only the automated requirements, not that the document's meaning, organization, or placement follows the model.
- **Reports**: Report the mddt commit the check printed, the files it covered, and the warnings kept after judgment with their reasons.

## Editing AI Skills

Use this order of reference when updating `skills/wr-wr` or `skills/admin-wr`:

1. Read the selected skill's `SKILL.md` and the reference file governing the behavior being changed.
1. Consult [the shared report policy](../report-policy.md), `template.tex` for contextual writing guidance, and the scripts and `weekly-report.sty` for exact build and LaTeX behavior.
   Preserve these ownership boundaries when updating skills.
1. Follow current Codex and Claude skill conventions for platform mechanics without overriding repository behavior.

Preserve these ownership and maintenance boundaries:

- **Entry and references**: Keep `SKILL.md` focused on activation scope, task routing, cross-cutting safeguards, and completion behavior.
  Put task-specific procedures and safeguards in the relevant file under `references/`, and keep deterministic repository-location logic in the shared `scripts/resolve-repo-root`.
  Prefer extending an existing reference over adding a new one unless the change introduces a distinct concern.
- **Report authoring**: For report content work, the writing skill must explicitly direct agents to read the canonical template comments and shared report policy.
  Keep the comments focused on writing decisions at each location, and distinguish requirements, adaptable suggestions, and illustrative content.
  Avoid duplicating section-writing prescriptions in skill references or treating the example's organization as a requirement.
  Treat [report conventions](../../skills/wr-wr/references/report-conventions.md), [content quality](../../skills/wr-wr/references/content-quality.md), and [LaTeX and build support](../../skills/wr-wr/references/latex-and-build.md) as the canonical procedures for comment preservation, evidence, editorial stages, and report validation.
  Keep the README's AI-assisted workflow section focused on capabilities and links to those references.
- **Administrator formats**: When editing `admin-wr`, preserve the responsibility boundary defined in [Administrator Development](../admin-development.md) rather than moving judgment into deterministic scripts.
  Changes to the plan or execution-manifest formats must update the workflow reference, tests, and user documentation together.
- **Shared interfaces**: Do not duplicate the repository's full interfaces in a skill.
  Refer to the canonical sources when exact behavior matters so that skill guidance does not become a stale parallel manual.
  Both skills should remain usable through all supported installation destinations; avoid provider-specific instructions unless they are necessary and clearly scoped.
- **Behavior and scope**: Keep skill behavior adaptive, evidence-grounded, protective of existing user work, and limited to authorized actions.
  When its capabilities or expectations change, update the entry point, affected references, and the user-facing AI workflow documentation together as applicable.

## Automated Minimum Check

With Git and [uv](https://docs.astral.sh/uv/getting-started/installation/) installed, run the check from the repository root:

```bash
bash tests/check_docs.sh
```

The command fetches mddt's current default branch into temporary storage on every run, prints its commit, and removes the checkout afterward.
uv prepares Python and the dependencies declared by the upstream checker, including its local English model.
The check requires network access, but document text is analyzed locally.

The check deliberately follows mddt without pinning a tag, version, or commit:

- **Current rules**: Upstream rules and fixes apply without a repository change.
- **Run identity**: The printed commit identifies the checker a run used, for reports and for reproducing a result.
- **New rules**: A new upstream rule can report errors in unchanged documents and fail CI; fix them in a change of their own.

Pass `--review` for additional structural review findings or `--format json` for machine-readable output.
The `.mddtignore` file excludes `windows/` from checking, while links into Windows documentation still resolve against those files.

Errors and execution failures fail the check; warnings remain visible for editorial judgment and do not fail CI.
The check lists warnings across the whole tree, so judge those in the files a change touched and leave the rest to their own changes.
The checker does not replace a formatting linter.

The **Check documentation** workflow runs this minimum check on branch pushes, pull requests, and manual dispatches.
The release workflow also calls it before publication, using the same triggering commit as the platform checks.
