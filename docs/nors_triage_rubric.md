# NORS F-tag triage rubric (draft for consistent candidate review)

This rubric is derived only from the decisions and reviewer notes in:

- `nors_ftag_review_batch_1_claude_triage.csv`
- `nors_ftag_review_batch_2_claude_triage.csv`
- `nors_ftag_review_batch_3_claude_triage.csv`

It describes context-link review, not complaint coding. A link means a code may be relevant depending on case facts; it does not select a code for a case.

## Keep or add a candidate

Keep/add when the cited Appendix PP material and the Table 2 definition support a specific contextual relationship. Favor examples, key elements, severity passages, or an explicit Table 2 “Use” rule over a loose shared word. The triage records include these reasons:

- Batch 1, F550/D09, keep: “Appendix PP lists religious expression, voting etc.; D09 covers rights not in D1-D8”.
- Batch 1, F554/D01, keep: “choice in health care; IDT determination”. F554/F04 is separately kept with the note “medication handling side (safety, documentation)”.
- Batch 1, F602/A04, keep: “misappropriation for benefit of others”; F602/E02, keep: “loss/mismanagement of property”.
- Batch 1, F567/E02, keep: “mismanagement of resident funds”; F567/E01, keep: “deposits/charges against funds”.
- Batch 2, F622–F626/C03, add: “Daniel-approved add; extracted F-tag content is a relocation note only.” This is a recorded exception based on the approved triage, not a general license to infer links from relocation notes.
- Batch 3, F657/F03 and F658/F03, add: “Title and Table 2 care-plan phrase supplied as evidence.”

Keyword overlap by itself is insufficient. The three triage files contain both kept and dropped rows with `basis=keyword_match`, so they do **not** support the stricter claim that every keyword-match row must be dropped. Treat an unsupported lexical match as a drop when the reviewed record supplies no substantive rationale; if the fit remains plausible but unresolved, mark it `check` for human review rather than turning it into a confident link.

## Drop a candidate

Drop when the candidate does not describe the concern in the tag evidence, or when its support is only a broad/shared word and no contextual relationship is recorded. Batch 3 records the explicit decision reason “No candidate row; dropped per Daniel instruction.” Batch 1 and batch 2 often leave the drop `reviewer_note` blank; the CSVs record the drop decision but do not record an individual reason for every dropped pair. Do not invent a more specific reason for those rows.

## Evidence and Table 2 wording

The batch 1–3 sheets cite Appendix PP excerpts and Table 2 definitions. Prefer concrete Appendix PP examples, key-element passages, or severity passages. Read every quoted Table 2 “Use” sentence: when it expressly directs a complaint to another code or limits a code, that instruction takes priority over a term score. Keep quoted evidence verbatim and retain its locator. If the evidence is title-only, a relocation note, or otherwise weak, mark `check` and label the weakness; do not present it as a strong content match.

The recorded weak example is Batch 2 F660/D02: “Title-only, check; weak.” The reviewer explicitly did not import F660/C03. Batch 3 also preserves four keep decisions whose note is exactly “check”, and its F646/F03 manual addition is “check; title and Table 2 text supplied as evidence.” These records show that a plausible but uncertain association stays visibly checked.

Existing app links are not automatically proof of a substantive fit. In batch 1–3, existing links appear in the candidate sheets and some are kept with a `check` note; preserve the existing-link basis in the review record and mark uncertain links `check` rather than treating their prior presence as authority.

## No-candidate and Claude-review queue

Keep a tag with no clean match at zero generated candidates and report it as **needs Claude**. Do not fill the gap with the highest lexical score. The batch 3 triage has no generated candidate row for F635 (admission orders), F642 (assessment qualification), F646 (authority notification; a separate manual F03 add was directed and remains checked), and F661 (discharge information). The batch 3 report also lists F639 and F659 as lookup-only items with broad multi-code matches; those lookups were explicitly left undecided.

The 1–3 triage records do not establish a universal no-candidate rule for every MDS-administration, records, QAPI, or survey-process tag. Track such types as **needs Claude** when later batches yield no clean fit; do not claim the earlier CSVs resolved them.
