# Content Quality

Use this guidance for any task that changes or evaluates report meaning, whether the starting point is raw material, a partial draft, a completed source, or only rendered output.

## Ground the Work

Build a lightweight mental inventory of available support: user notes, existing prose, experiment outputs, figures, code or commit history, prior reports, and statements supplied in conversation. Use only sources that are in scope and accessible.

- Treat an existing draft as evidence of what the author currently claims, not independent proof that each claim is true.
- Treat repository activity as evidence that work changed, not by itself as proof of scientific meaning, performance, or completion.
- Do not turn missing data into plausible-looking numbers, citations, outcomes, or figure descriptions.
- Preserve useful uncertainty. Distinguish direct observations, interpretations, hypotheses, decisions, and plans.

When required factual support is missing, treat it as an authoring gap rather than automatically making it report content. Ask the author when the gap blocks correctness. Otherwise omit the unsupported statement and notify the author in the handoff or an author-only source comment. Do not render `unknown`, `not verified`, TODOs, or placeholder values unless the user explicitly requests a visibly incomplete draft. Describe missing evidence in the report only when its absence is itself a relevant, author-approved finding or problem. Do not block unrelated improvements merely because every fact cannot be independently verified.

## Select Research Content

The weekly report is for research progress, problems, and plans.
Move standalone software, tooling, administrative, and workflow updates out of the report; suggest sharing them briefly in project meetings without sending them or creating a separate deliverable unless requested.
Retain a technical detail only when necessary to explain a research finding, its validity, or a research blocker, and lead with that research consequence.
For example, a corrected evaluation bug belongs when it changes the reported result; adding a notebook or reorganizing a repository is not itself research progress.
Do not fill a quiet research week with maintenance activity or invented findings.

## Shape the Report

Use PPP as a communication model rather than a form to fill mechanically.

- **Progress** explains meaningful changes in research results or understanding and the evidence that supports them.
- **Problems** explains research uncertainty, obstacles, failed or incomplete responses, constraints, or decisions that need input.
- **Plans** prioritizes next research actions and makes expected outputs, success criteria, dependencies, or fallbacks concrete when useful.
- **Abstract** summarizes the most important change, evidence, unresolved issue, and direction already supported by the body. Draft or revise it after the body when doing so improves consistency.

Sections, subsections, lists, equations, tables, and figures are optional communication choices. Keep only structures that help the reader understand the week.

Order points by research importance within each section, not by the sequence of activities.
Lead each substantive point with its claim or finding, give the strongest relevant evidence, then state the implication for the research question, limitation, decision, or next step.
Keep supporting details subordinate to the main point through short paragraphs, informative headings, or nested lists where helpful.
Combine related observations and remove repeated explanations; do not bury the result beneath a long progress log.
Preserve the distinction between a demonstrated result and a hypothesis when writing the lead claim.

## Enforce the Two-Page Limit

The complete report must fit within two A4 pages per person per week, including the abstract, figures, tables, and references.
Two pages are a maximum, not a quota; do not pad a shorter report.
For drafting and finalization tasks, check the rendered page count and revise overlength content within the authorized scope before declaring it ready.
For review-only tasks, identify the necessary cuts and any exception without changing the source.

Reduce content in this order, then rebuild and reassess:

1. Remove non-research updates, chronological activity logs, repeated background, and low-priority detail.
1. Consolidate related claims and supporting evidence; use the clearest compact prose, table, or figure and remove redundant displays.
1. Keep only the context, evidence, limitations, and next steps needed to assess the research; leave nonessential supporting detail in its source records, with a reference when useful.

Preserve the standard readable typography, margins, and hierarchy.
Do not meet the limit by shrinking text, crowding the layout, hiding essential caveats, or moving overflow into an appendix within the report.

Exceed two pages only when every reasonable cut or reorganization has been exhausted and further reduction would remove indispensable evidence or qualifications, or make a research result, problem, or plan misleading or impossible to assess.
Keep the excess to the minimum necessary.
In the author handoff, state the actual page count, identify the indispensable content, and explain why further reduction would compromise the research meaning or evidence.
A busy week, many projects, a lengthy draft, or a preference for detail is not sufficient justification.
If necessity cannot be established, treat the excess as unresolved revision work, not a compliant final report.

## Revise Without Overclaiming

When supporting material is available, check important claims against it and correct inconsistencies. When only a draft is available:

- improve clarity, flow, concision, organization, grammar, and presentation without changing factual meaning;
- preserve the author's language, voice, degree of certainty, and research priorities while applying the report's focus, hierarchy, and length requirements within the requested scope;
- flag internal contradictions, unexplained metrics, unsupported causal wording, or missing context;
- do not add stronger conclusions or apparent verification merely to make the report sound more persuasive.

If only a PDF is available, determine whether the user wants feedback on the rendered artifact or an editable reconstruction. Do not imply that reconstructed LaTeX is the original source.

## Review Proportionately

Check research focus, the progression from claim to evidence to implication, and the two-page limit alongside factual traceability, PPP balance, decision usefulness, and readability.
For a focused review, address the requested issue and flag material report-policy problems without silently expanding into a full rewrite.
Preserve essential evidence and scientific uncertainty during cuts; apply the narrow exception above only when no reasonable shorter presentation remains.
