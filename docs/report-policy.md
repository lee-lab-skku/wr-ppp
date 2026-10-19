# Report Policy

Begin by replacing the three values in `\ReportHeader`:

```latex
\ReportHeader
    {Write Your Report Title Here}
    {Your Name}
    {Project / Team}
```

Choose a title that conveys the week's actual research topic, question, or significant development, including multiple threads when appropriate.
Do not use only a project name, reporting week, a generic label such as "Weekly Report", or a combination of these as the report title.

Then replace the illustrative abstract and PPP content with the week's research.
Adapt sections, subsections, grouping, and presentation to what best communicates that work, including weeks with several research threads.
The comments in [`template.tex`](../template.tex) provide section-level prompts alongside a worked example.
This document defines shared report policy; the comments help apply it while writing, and the skills describe how an agent assists and validates.

Use the prompts with judgment: suggested content and example layouts are optional, and a useful report need not contain every element mentioned in a comment.
Choose prose, lists, equations, tables, or figures to suit the material.

Keep the report focused on research progress, problems, and plans.
Share software, tooling, administrative, and workflow updates briefly in project meetings instead.
Include a technical detail only when it is necessary to explain a research result, its validity, or a research blocker; describe that research consequence rather than the implementation activity.

Lead with important takeaways and make the relationships among claims, supporting evidence or reasoning, and research implications clear.
These relationships do not require three labeled parts, a fixed sentence sequence in every item, or a single finding encompassing the week.
Give significant developments prominence and keep supporting details subordinate to them.
Carry this hierarchy into the body beneath each subsection: use lists for parallel findings or actions, subordinate items for their supporting conditions or evidence, and tables when comparison is clearer across shared dimensions.
Subsection headings alone do not provide enough structure when several distinct points remain buried in continuous prose.
Use short prose for a connected explanation or transition; neither every sentence nor every subsection needs a list or a fixed set of labels.
Use concise headings where helpful and remove repeated background and activity-log detail that does not help the reader assess the research.

Selected body text may be emphasized at the user's request, under applicable guidance, or at the agent's discretion.
Use italics unless another emphasis style is specified.

Write from the report author's research perspective, including when drafting from organized notes or experiment records.
Describe supported actions, findings, and plans objectively without repeatedly using first-person pronouns or narrating what an outside reviewer learned from the supplied files.
Preserve the distinction between the author's work, collaborators' contributions, and external findings, as well as between completed work and plans.

Use the scientific notation facilities provided by `weekly-report.sty` where applicable: `siunitx` for scientific numerical values and units, and `mhchem` for chemical formulas and reactions, including in tables and captions.
Preserve values and meaning; ordinary counts, dates, identifiers, and algebraic expressions do not require mechanical conversion.

Every figure must be referenced at least once in the report's body using a label-based `cleveref` command, in a context that explains its connection to the discussion.
References to tables and equations are optional, but any such references must also use `cleveref` rather than manually written numbers.
Use `\cref` or an appropriate supported variant, such as `\Cref` for capitalization or commands for multiple labels and ranges; this rule does not restrict valid calling forms.
Labels must be unique; prefixes such as `fig:`, `tab:`, and `eq:` are optional.

PPP and the abstract provide useful perspectives on the week:

- **Abstract:** an overview of the scope and significant developments
- **Progress:** changes in research results or understanding and their support and significance
- **Problems:** relevant unresolved research issues and their consequences
- **Plans:** next research directions and intended learning or outcomes

## Length and Exceptions

The complete weekly report must fit within two A4 pages per person, including the abstract, figures, tables, and references.
Shorter reports are welcome; two pages are a maximum, not a quota.
Check the compiled PDF, cut non-research material and repetition, consolidate supporting evidence, and keep only what the reader needs to assess the research claims, problems, and next steps.
Preserve readable typography and hierarchy; do not shrink fonts or margins, crowd the layout, or add an appendix to evade the limit.

An exception is justified only when every reasonable cut or reorganization has been exhausted and further reduction would remove essential evidence or qualifications, or make a research result, problem, or plan misleading or impossible to assess.
Keep any excess to the minimum necessary and explain the specific indispensable content and why it cannot be shortened in the submission note or author handoff.
A busy week, many projects, or a preference for more detail does not justify extra pages.
An overlength report without that justification still needs revision.
