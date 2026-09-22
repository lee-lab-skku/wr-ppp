# Content Quality

Use this guidance for any task that changes or evaluates report meaning, whether the starting point is raw material, a partial draft, a completed source, or only rendered output.

## Ground the Work

Build a lightweight mental inventory of available support: user notes, existing prose, experiment outputs, figures, code or commit history, prior reports, and statements supplied in conversation. Use only sources that are in scope and accessible.

- Treat an existing draft as evidence of what the author currently claims, not independent proof that each claim is true.
- Treat repository activity as evidence that work changed, not by itself as proof of scientific meaning, performance, or completion.
- Do not turn missing data into plausible-looking numbers, citations, outcomes, or figure descriptions.
- Preserve useful uncertainty. Distinguish direct observations, interpretations, hypotheses, decisions, and plans.

When required factual support is missing, treat it as an authoring gap rather than automatically making it report content. Ask the author when the gap blocks correctness. Otherwise omit the unsupported statement and notify the author in the handoff or an author-only source comment. Do not render `unknown`, `not verified`, TODOs, or placeholder values unless the user explicitly requests a visibly incomplete draft. Describe missing evidence in the report only when its absence is itself a relevant, author-approved finding or problem. Do not block unrelated improvements merely because every fact cannot be independently verified.

## Write from the Author's Research Perspective

Source verification is the agent's working process, not the report's narrative viewpoint.
When the user supplies experiment logs, summaries, tables, or other organized material, report the supported research actions, results, interpretations, and plans as the author's work rather than as facts an outside observer discovered in those files.
Prefer the experiment, method, sample, or result as the grammatical subject, or omit the subject where natural in the report's language; do not repeatedly add "I", "we", "the author", or "the researcher" to establish ownership.
For example, if the records support it, write "At the tested temperature, yield increased relative to the baseline" rather than "Reviewing the supplied experiment log revealed that the researcher obtained a higher yield."
Keep source traceability in appropriate references or author-only notes instead of making every finding a statement about what the supplied material says.

Preserve attribution when the material describes collaborators' work, external literature, or a secondary analysis that is itself the reported research activity.
Do not convert a documented plan into completed work, assume ownership of external results, or strengthen certainty while changing viewpoint.
Resolve ambiguous ownership or status before making a consequential claim.

## Exercise Editorial Judgment

Apply the README's research focus when selecting source material.
If suggesting that out-of-scope updates be shared in a project meeting, do not send them or create a separate deliverable unless requested.
Do not fill a quiet research week with maintenance activity or invented findings.

Use the canonical template comments, as directed by `SKILL.md`, to assess how well the actual research and its support are communicated.
Missing a suggested element or using a different grouping is not itself a defect.
Before reorganizing an existing draft, identify the concrete communication problem the change would address and keep the revision within the requested scope.
Do not demand metrics, positive findings, or invented blockers to fill the example's structure.

Check the body beneath each subsection as well as its title.
When several findings, comparisons, conditions, or next steps are buried in continuous prose, expose their relationships with the template's structural guidance: distinct items for parallel points and subordinate support for a parent finding, or a table for comparable dimensions.
Adding subsection headings alone does not resolve an unstructured body.
Retain short prose for a single connected argument and for transitions; do not fragment every sentence into a bullet or require the same labels and nesting depth everywhere.
Apply author viewpoint, meaningful body structure, and scientific notation while drafting, rather than deferring these content requirements as cosmetic layout work.

## Shorten and Recheck

Use the resolved repository's `README.md`, "Length and Exceptions", for the page limit and complete necessity criteria.
Before editorial revision, keep content concise but report any observed excess and defer page-fitting iterations under [latex-and-build.md](latex-and-build.md), "Match Layout Work to the Stage".
During editorial revision and finalization, check the rendered page count and revise overlength content within the authorized scope before declaring it ready.
For review-only tasks, identify the necessary cuts and any exception without changing the source.

Look for content reductions suited to the material, then rebuild and reassess:

1. Remove non-research updates, repeated background, and activity-log detail that does not help assess the research.
1. Consolidate related claims and supporting evidence; use the clearest compact prose, table, or figure and remove redundant displays.
1. Keep only the context, evidence, limitations, and next steps needed to assess the research; leave nonessential supporting detail in its source records, with a reference when useful.

Preserve readable typography and essential caveats during revision.
Do not declare an overlength report ready unless the README's narrow exception is established.
In that case, state the verified page count and specific necessity justification in the author handoff, keeping any excess to the minimum necessary.
If necessity cannot be established, treat the excess as unresolved revision work.

## Revise Without Overclaiming

When supporting material is available, check important claims against it and correct inconsistencies. When only a draft is available:

- improve clarity, flow, concision, organization, grammar, and presentation without changing factual meaning;
- preserve the author's language, voice, degree of certainty, research priorities, and effective presentation choices while applying shared report policy within the requested scope;
- flag internal contradictions, unexplained metrics, unsupported causal wording, or missing context;
- do not add stronger conclusions or apparent verification merely to make the report sound more persuasive.

If only a PDF is available, determine whether the user wants feedback on the rendered artifact or an editable reconstruction. Do not imply that reconstructed LaTeX is the original source.

## Review Proportionately

Assess the report against shared policy and the relevant template prompts, with attention to factual traceability, decision usefulness, and readability.
For a focused review, address the requested issue and flag material report-policy problems without silently expanding into a full rewrite.
