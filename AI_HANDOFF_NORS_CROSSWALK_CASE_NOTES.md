# AI Handoff: NORS Crosswalk + Case Notes Checklist

This document is meant to catch up another AI system or engineering team quickly.

The goal is not to preserve the current UI at all costs. The goal is to preserve the useful work already done:

- the authority hierarchy
- the source discipline
- the NORS-first logic model
- the ambiguity handling approach
- the data-driven architecture

If you want to rebuild the product from scratch, that is fine. Please use this document and the linked source files as the starting point rather than treating the current MVP as the only acceptable implementation.

## 1. What This Project Is

This project is an internal decision-support tool for long-term care ombudsman work, centered on two initial use cases:

1. `NORS crosswalk`
   - move from plain-language complaint facts or a known NORS code to:
     - likely NORS complaint codes
     - relevant federal and state authority context
     - related-but-distinct issues worth additional investigation
     - human-review warnings where the facts are ambiguous

2. `Case notes checklist / drafting assistant`
   - help staff document ombudsman work more consistently
   - surface missing case-note elements
   - assemble structured narrative notes from defined sections/templates

This is intended to be:

- `NORS-first`
- `human-in-the-loop`
- `source-traceable`
- `closed-loop / data-driven`
- `not a black-box chatbot`

## 2. Current MVP State

The current NORS crosswalk and drafting/checklist flow are mostly static client-side tools that load local JSON files and apply deterministic matching and display logic.

Important practical point:

- for the current closed-loop MVP, there is `no live AI/token cost per run`
- if hosted on state infrastructure as a normal internal web app/static site, runtime cost should be minimal
- future AI cost would only appear if the project later adds:
  - live model calls
  - OCR
  - document upload / casefile analysis
  - embeddings / vector search
  - server-side summarization or drafting


## 3. High-Level Product Vision

The desired user experience is:

1. User starts with either:
   - a known NORS code, or
   - plain-language complaint facts / keywords

2. The system identifies likely topics and likely NORS codes.

3. The system displays:
   - primary likely authority references
   - Appendix PP / F-tag context where appropriate
   - related investigation considerations
   - workflow notes
   - handouts/resources
   - human-review flags

4. The system makes clear that:
   - NORS sources control complaint coding
   - regulations provide context
   - multiple complaints may exist in one case
   - the ombudsman remains the final decision-maker

## 4. Core Methodology

### 4.1 NORS-first hierarchy

The key rule is:

`NORS coding is determined from ACL/NORC NORS sources first.`

Regulatory sources such as:

- `42 CFR Part 483`
- `CMS Appendix PP`
- `F-tags`
- Connecticut statutes/regulations

are used after likely NORS issues are identified, as context and review support.

They do `not` drive the final NORS code.

### 4.2 Human-in-the-loop

The tool is not meant to:

- determine violations
- finalize complaint codes automatically
- replace ombudsman judgment

It is meant to:

- narrow likely issues
- organize authority sources
- show why the system matched something
- surface ambiguity and review warnings

### 4.3 Data-driven over freeform AI

The current direction is intentionally closer to a structured reference engine than a chat model.

The basic architecture is:

- source pack / source registry
- NORS hierarchy
- keyword maps
- topic maps
- authority maps
- knowledge-base batch overlays
- human-review flags
- deterministic ranking and grouping

This makes the system easier to:

- audit
- update
- explain
- keep aligned to official source material

### 4.4 Prefer warnings over unsupported precision

Where the authority bridge is weak, the preferred behavior is:

- omit the mapping, or
- mark it as contextual only, or
- emit a human-review flag

The project intentionally avoids pretending a weak source bridge is stronger than it is.

## 5. Current Source Hierarchy

The current locked source pack is in:

- [data/nors_source_pack_lock.json](data/nors_source_pack_lock.json)

At the time of writing it contains:

- `21` source-pack rows
- `9` source relationships
- `8` source-priority rules
- `2` human-review flags

The current hierarchy is:

1. `ACL NORS Tables 1-3` and `NORC NORS Parts 1-4`
   - controlling sources for NORS reporting and complaint coding

2. `NORS FAQs` and `quiz answer sheets`
   - high-value QA / ambiguity sources
   - cannot override ACL tables

3. `NORC Initial Certification Training Curriculum Modules 1-10`
   - broader ombudsman workflow, resident-first practice, complaint-processing, communication, facility visits, and documentation context
   - should be treated as an important supporting training layer
   - do not override ACL tables or NORS Parts 1-4 for reporting code selection

4. `CMS Appendix PP` and `F-tags`
   - regulatory/survey context only
   - not final NORS coding authority

5. `Connecticut statutes/regulations`
   - state overlay / local context

6. `45 CFR Part 1324` and ombudsman program authority
   - program/governance context
   - useful, but usually not the first authority shown to end users

## 6. Primary Authority Documents and Direct URLs

### 6.1 Controlling NORS coding sources

#### ACL Tables

- `ACL NORS Table 1: Case and Complaint Codes, Values, and Definitions`
  - https://acl.gov/sites/default/files/programs/2021-11/NORS%20Table%201%20Case%20Level%20%2010-31-2024.pdf

- `ACL NORS Table 2: Complaint Codes and Definitions`
  - https://acl.gov/sites/default/files/programs/2021-11/NORS%20Table%202%20Complaint%20Code%2010-31-2024.pdf

- `ACL NORS Table 3: State Program Information`
  - https://acl.gov/sites/default/files/programs/2021-11/NORS%20Table%203%20Program%20Information%2010-31-2024.pdf

#### NORC NORS training hub

- `NORS Hub`
  - https://ltcombudsman.org/omb_support/nors

#### NORC NORS Part 1

- `Part 1 Basic Principles`
  - https://ltcombudsman.org/uploads/files/support/NORS_Training_Part_1_FINAL_for_website.pdf

- `Part 1 Quiz`
  - https://ltcombudsman.org/uploads/files/support/nors-training-part-I-quiz.pdf

- `Part 1 Quiz Answer Sheet (Revised 2025)`
  - https://ltcombudsman.org/uploads/files/support/nors-training-part-I-quiz-answers.pdf

#### NORC NORS Part 2

- `Part 2 Basic Principles`
  - https://ltcombudsman.org/uploads/files/support/Part-II-Principles-9-28-11_0.pdf

- `Part 2 Complaint Coding Webinar Slides`
  - https://ltcombudsman.org/uploads/files/support/NORS_Part_II_Training_PPT.pdf

- `Part 2 Quiz`
  - https://ltcombudsman.org/uploads/files/support/nors-training-part-II-quiz.pdf

- `Part 2 Quiz Answer Sheet`
  - https://ltcombudsman.org/uploads/files/support/nors-training-part-II-quiz-answers.pdf

- `Part 2 Beyond the Basics Quiz Answer Sheet (Revised)`
  - https://ltcombudsman.org/uploads/files/support/nors-training-part-II-beyond-basics-quiz-answers.pdf

#### NORC NORS Part 3

- `Part 3 Revised NORS Data Collection Hub`
  - https://ltcombudsman.org/omb_support/nors/revised-nors-data-collection

- `Part 3 Quiz Answer Sheet`
  - https://ltcombudsman.org/uploads/files/support/nors-training-part-III-quiz-answers-verification-disposition-referral-and-closing-cases.pdf

#### NORC NORS Part 4

- `Part 4 Basic Principles`
  - https://ltcombudsman.org/uploads/files/support/NORS_Training_Part_IV_Basic_Principles.pdf

#### FAQs and interpretive guidance

- `NORS FAQs`
  - https://ltcombudsman.org/omb_support/nors/nors-faqs

- `Current NORC user-friendly complaint codes PDF`
  - https://ltcombudsman.org/uploads/files/support/nors-codes-and-definitions.pdf

- `Online NORS Training Course Launch Webinar Slides (2025)`
  - https://ltcombudsman.org/uploads/files/support/NORS_Course_Webinar_July_2025.pdf

Important note:

- `ACL Table 2` is the formal controlling complaint-code authority
- the current `nors-codes-and-definitions.pdf` is useful interpretive guidance and a user-friendly companion
- older versions of NORC complaint-code PDFs should not override the current ACL/NORC hierarchy

### 6.1.1 Initial certification curriculum and broader workflow context

These should be included in the handoff package. They are not the top coding authority, but they are important for understanding how ombudsman work is supposed to happen around intake, investigation, communication, documentation, and resident-directed advocacy.

#### Current curriculum hub and planning materials

- `Initial Certification Training Curriculum for Long-Term Care Ombudsman Programs (Modules 1-10 hub)`
  - https://ltcombudsman.org/omb_support/training/norc-curriculum

- `NORC Training Resources page`
  - https://ltcombudsman.org/omb_support/training

- `Introduction and Overview`
  - https://ltcombudsman.org/uploads/files/support/curriculum-overview.pdf

- `On-Demand Training Center`
  - https://consumervoice.talentlms.com

The NORC curriculum page notes that the curriculum materials, including introduction and planning documents, were updated as of `January 2025`.

#### The 10 current initial certification modules

1. `Module 1 - The State Long-Term Care Ombudsman Program: Roles, Responsibilities, and Authorities`
2. `Module 2 - The Resident and the Resident Experience`
3. `Module 3 - Putting the Resident First`
4. `Module 4 - Long-Term Care Settings, Residents' Rights, and Enforcement`
5. `Module 5 - Access & Communication`
6. `Module 6 - Facility Visits`
7. `Module 7 - Long-Term Care Ombudsman Program Complaint Processing: Intake and Investigation`
8. `Module 8 - Long-Term Care Ombudsman Program Complaint Processing: Analysis, Planning, Implementation, and Resolution`
9. `Module 9 - Challenging Complaints & Referral Agencies`
10. `Module 10 - Documentation`

For each module, the NORC curriculum page currently provides:

- trainee manual
- trainer guide
- PowerPoint

Recommendation for the handoff:

- include the curriculum hub itself as a required context source
- treat Modules 7, 8, and 10 as especially relevant to the complaint-processing and case-note portions of this project
- treat Modules 3, 4, 5, and 6 as especially relevant to resident-directed practice, rights framing, communication, and facility workflow
- treat Module 1 as foundational for ombudsman role boundaries and program authority

#### Why these modules matter in this project

They help explain the workflow around the coding engine:

- how the ombudsman approaches complaints
- how resident direction and consent shape action
- how investigations are conducted
- how analysis and planning occur
- how documentation should be structured

They should therefore be treated as a `supporting workflow/documentation authority layer`, even though they do not control final NORS code selection.

### 6.2 Federal regulatory context

- `42 CFR Part 483, Subpart B`
  - https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-G/part-483/subpart-B

- `CMS State Operations Manual Appendix PP`
  - https://www.cms.gov/Regulations-and-Guidance/Guidance/Manuals/Downloads/som107ap_pp_guidelines_ltcf.pdf

### 6.3 Connecticut overlay

- `Connecticut General Statutes Chapter 368v`
  - https://www.cga.ct.gov/current/pub/chap_368v.htm

- `Connecticut General Statutes Chapter 319l`
  - https://www.cga.ct.gov/current/pub/chap_319l.htm

- `Connecticut eRegulations 19-13-D8t`
  - https://eregulations.ct.gov/eRegsPortal/Browse/RCSA/Title_19Subtitle_19-13Section_19-13-d8t/

- `Connecticut Long-Term Care Ombudsman Program`
  - https://portal.ct.gov/ltcop

### 6.4 Ombudsman program authority

- `45 CFR Part 1324`
  - https://www.ecfr.gov/current/title-45/subtitle-B/chapter-XIII/subchapter-C/part-1324

In the current UI logic, Ombudsman program authority is intentionally pushed lower in the display order because it is not usually the primary citation the user needs first during code lookup.

## 7. Current Logic Model

The current crosswalk logic works roughly like this:

1. Load normalized JSON datasets.
2. Start with either:
   - selected NORS code
   - keyword/free-text concern language
3. Match to likely topics.
4. Merge topic matches from code-based and keyword-based paths.
5. Pull authority rows, knowledge-base rows, workflow notes, resource rows, and human-review flags.
6. Rank and group references by usefulness:
   - primary references
   - Appendix PP / F-tags
   - additional context
   - CT / Program
7. Show matched reasons and warnings to the user.

The logic is designed to answer:

- what is the likely NORS issue?
- what else should the ombudsman consider?
- what authority helps explain the issue?
- where is the ambiguity?

## 8. Key Repo Files to Use If Rebuilding

Per repo rules, the `/data` files should be treated as the source of truth wherever a normalized version exists.

### 8.1 Core crosswalk data

- `nors_hierarchy.json`
- `keyword_map.json`
- `nors_to_topic.json`
- `topic_to_authority.json`
- `crosswalk_catalog.json`
- `authority_index.json`
- `retrieval_rules.json`

### 8.2 Normalized / source-of-truth data under `/data`

- `data/nors_source_pack_lock.json`
- `data/source_registry.json`
- `data/reference_source_index.json`
- `data/nors_complaint_code_guidance.json`
- `data/nors_resource_catalog.json`
- `data/appendix_pp_tag_pages.json`
- `data/nors_case_level_guidance.json`

### 8.3 Knowledge-base overlays

There are currently `16` JSON knowledge-base batches:

- `data/nors_knowledge_base_batch1.json` through `data/nors_knowledge_base_batch16.json`

These batches have been used to add:

- source verification
- tooltip rows
- resource corrections
- ambiguity rules
- authority bridges
- human-review flags
- conservative repair passes after source-locking

Recent completed repair/integration areas include:

- `Batch 14`
  - care delay
  - incontinence care
  - staffing
  - retaliation
  - gross neglect

- `Batch 15`
  - room change
  - discharge / eviction
  - dignity
  - rights / preferences

- `Batch 16`
  - medications
  - chemical restraint
  - provider choice
  - outside-provider ambiguity guardrails
  - gross neglect

### 8.4 Case-note checklist / drafting assistant data

- `data/case_note_templates.json`
- `data/case_note_validation_rules.json`
- `data/draft_output_examples.json`
- `data/email_templates.json`

Current case-note logic is intentionally simple and structured:

- defined sections
- templated sentence assembly
- field-level validation rules
- checklist-style warnings for missing documentation

Examples from the current validation rules:

- missing problem description
- missing identity/confidentiality permission
- missing resident perspective
- missing desired outcome
- missing initial plan of action
- missing ombudsman actions

## 9. Current Runtime Architecture

Relevant files:

- `Assets/crosswalk.js`
- `Assets/shared.js`
- `tools/nors-crosswalk.html`
- `tools/drafting-assistant.html`
- `tools/responsible-use.html`

The crosswalk currently loads local JSON files using `fetch(...)` and applies client-side matching logic. It is not currently built as a live AI system.

That matters because it means:

- low operational complexity
- low marginal runtime cost
- high explainability
- easier state hosting and review

## 10. Important Design Guardrails

These are the core guardrails the project has converged on so far.

### 10.1 Coding guardrails

- Always start from NORS sources.
- Do not let F-tags determine the final NORS complaint code.
- Multiple complaints may exist in one case.
- Use ambiguity guidance and answer sheets to help, but do not let them override ACL tables.

### 10.2 UX guardrails

- Show why something matched.
- Group references by topic.
- Show primary references first.
- Collapse lower-value CT / Program references by default.
- Keep human-review flags visible where the bridge is weak.

### 10.3 Governance guardrails

- Treat the system as decision support, not autonomous decision-making.
- Preserve source traceability.
- Avoid unsupported precision.
- Keep the state governance / responsible-use layer separate from complaint-coding logic.

## 11. Questions We Want Expert Feedback On

If you are reviewing this as an AI/architecture expert, these are the main questions:

1. Does this overall methodology fit the use case well?
2. Is a structured rules/data model the right foundation, or would another architecture scale better?
3. Is the `NORS-first, regulations-second` hierarchy the right organizing principle?
4. Is topic-based organization the best way to structure the reference engine?
5. How should ambiguity be represented without overwhelming the user?
6. Should this remain one integrated tool, or become a small set of focused tools?
7. If rebuilding from scratch, what should be simplified?

## 12. Alternate Architecture Paths Worth Considering

If you decide not to build on the current MVP directly, these are the main alternatives worth evaluating:

1. `Structured rules engine`
   - closest to the current approach
   - strongest for explainability and auditability

2. `Rules + retrieval hybrid`
   - deterministic routing first
   - retrieval over approved sources second
   - strongest candidate if later casefile upload is desired

3. `Scenario library / guided branching`
   - very useful for training and QA
   - may be easier for nontechnical staff

4. `Knowledge graph`
   - useful if long-term goal is a dense network of complaint issues, authorities, and cross-references
   - may be heavier than necessary for the initial use case

5. `Workflow-first complaint intake assistant`
   - helpful if the project expands into intake, investigation tracking, and resolution support

The current intuition is that a `structured rules/data layer with optional retrieval later` is probably the best fit.

## 12.1 Practical authority layering recommendation

If another team or AI system rebuilds this from scratch, a useful mental model is:

1. `Coding authority`
   - ACL Tables 1-3
   - NORS Parts 1-4

2. `QA / ambiguity authority`
   - FAQs
   - quiz answer sheets

3. `Workflow / documentation authority`
   - Initial Certification Training Curriculum Modules 1-10
   - planning documents
   - related training overview pages

4. `Regulatory context authority`
   - 42 CFR Part 483
   - CMS Appendix PP
   - F-tags

5. `State overlay`
   - Connecticut statutes and regulations

6. `Program/governance authority`
   - 45 CFR Part 1324
   - state AI governance materials

That is probably the cleanest way to preserve all the context without muddying which sources actually control complaint coding.

## 13. Suggested Starting Point If Rebuilding

If starting over from scratch, the recommended order is:

1. Preserve the source hierarchy.
2. Preserve the locked source pack.
3. Normalize all authority documents into a clean source registry.
4. Keep NORS coding logic separate from regulatory-context logic.
5. Keep case-note checklist logic separate from complaint-code matching logic.
6. Build the UI around:
   - likely issue
   - why matched
   - authority trail
   - related considerations
   - human-review flags
7. Add AI only later, if needed, for:
   - summarization
   - casefile ingestion
   - drafting support
   - retrieval over uploaded documents

## 14. Bottom Line

The most important thing already accomplished here is not the current front end.

It is the emergence of a disciplined methodology:

- official-source-first
- NORS-first
- explainable
- modular
- human-in-the-loop
- cautious about ambiguity

If you choose to rebuild the application entirely, the hope is that this methodology and source architecture still carry forward.

## 15. Repo Notes

Relevant repo rule from `AGENTS.md`:

- use JSON files in `/data` as the source of truth for templates, validation rules, keyword maps, and reference indexes
- do not hardcode duplicate copies of these rules in UI components if a `/data` file exists
- prefer reusing a shared data loader for `/data` files

That rule should be preserved if the project continues in this repository.
