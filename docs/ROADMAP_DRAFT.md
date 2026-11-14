# danbeem.xyz roadmap

**DRAFT by Claude, 2026-11-12, for Daniel to edit.** Lines marked ✏️ are guesses or blanks only Daniel can fill. Once Daniel approves it, this file is the reference for what gets built. If an idea is not on it, it is not built yet.

## How this file is used (the rules)

1. **One page, kept current.** Every section below has a one-line *vision*, *done means*, and a short *Now / Next / Later / Not doing* list. Update it in the same PR as the work.
2. **Ideas go to the parking lot first** (bottom of this file, or a GitHub issue labeled `idea`). Writing an idea down is the only thing that happens to it the day you have it.
3. **Only "Now" items get built.** At most **two** "Now" items across the whole site at a time. To start something new, finish or move an existing "Now" item down first.
4. **Every PR names its roadmap item** ("Roadmap: NORS tools / Now 1"). Claude and Codex refuse work that has no item, and add it to the parking lot instead.
5. **Finish or retire.** A page is *Live* (linked, maintained), *In progress* (on Now/Next), *Prototype* (unlinked, not maintained) or *Retired*. Prototypes either get a roadmap item within a month or move to an archive folder.
6. **Big decisions** go in `docs/DECISIONS.md` (date, decision, why) so the "why" survives.

## Site purpose ✏️

danbeem.xyz is Daniel's personal project site. Its main work is public, source-cited tools for Connecticut long-term care advocacy (staffing, inspections, ownership, cost reports, legislation, NORS casework), plus a few personal projects. Everything public on CMS and in Connecticut public data should be usable here, connected and explained.

---

## 1. NORS casework tools (crosswalk, Drafting Assistant, hub)
**Vision:** pick any NORS code, any F-tag, or search plain words, and see the exact NORS, Appendix PP and Connecticut text that connects them, then draft a clean case note. The staff member always makes the call. SNF only.
**Done means:** all 60 NORS codes and every Appendix PP tag have a card with verbatim, source-locked text; reviewed F-tag↔NORS context links; the Drafting Assistant builds from the full code list and the NORC Case Notes Checklist; a deployment-readiness package exists for the state.
**Rules that don't change:** NORS text decides the code; F-tags and law are context only; exact quotes only; no AI, no storage, synthetic data only on the public site.
- **Done (local, 2026-11-13):** source lock; Appendix PP extracted per tag (204 tags, CMS titles); term index; batch 1 (483.10, 483.12) reviewed: 89 links kept, 140 rejected; code cards, tag cards and selectors working with the medication pilot.
- **Now:** finish the Appendix PP example crosswalk for all remaining sections, batch by batch (483.15 admission/transfer; 483.20-21 assessment/care plan; 483.24-25 quality of care; 483.30-45 services; 483.70-90 administration and environment), each drafted, triaged and reviewed like batch 1. Search weighting fix.
- **Next (after every section is reviewed):** **plain-language example complaints per NORS code.** 5-6 invented complaints for each of the 60 codes (about 330-360), in varied voices (resident, family, staff, vague phone call), each quoting the Table 2 phrase it illustrates, plus 1-2 near-misses per code built from the "use code X instead" rules. Coding of every example reviewed by Daniel; labeled "illustrative example, project-written, coding reviewed by Daniel", never official NORS text. Purpose: match how people actually write, so search goes plain words -> example complaint -> NORS code (verbatim definition) -> reviewed F-tags and Appendix PP passages. Doubles as the test set for case-fact narrowing. Needs Daniel's approval of one rule change: matches to reviewed examples may count toward ranking codes, clearly labeled. Start with the D codes (about 54).
- **Then:** hub and one home page card; publish.
- **Later:** case-fact narrowing (facts entered for a case narrow the candidates using the "use X instead" rules, explain why each code may fit, ombudsman decides); Drafting Assistant parity (Table 1 fields, multiple complaints); readiness package for the State Ombudsman and BITS.
- **Not doing:** generative AI, semantic search, uploads, saving drafts, RCH content, real case data.
- **Plan of record:** `docs/` copy of NORS_TOOLS_DEVELOPMENT_PLAN_v1 (to add).

## 2. Staffing suite (`/staffing/`)
**Vision:** for any CT nursing home, see staffing, inspections, ownership, management, administrators and money in one connected, cited place.
**Pages (Live):** Explorer, Statewide comparison, Change over time, Persistent patterns, Ownership/affiliation, Methodology, CT staffing rules, Inspections, Administrator search, Management companies, Cost reports, Cost report insights.
- **Now:** publish 0026 (DSS cost centers and statewide averages).
- **Next:** ✏️ (candidates: direct-care dollars tied to staffing; tie cost-report owners to CMS ownership; quarterly PBJ refresh).
- **Later:** management fees from cost reports; RCH cost reports.
- **Not doing:** ✏️

## 3. Legislative tracker (`/legislation/`)
**Vision:** policy storylines (staffing floors and ratios, direct-care spending, CFC/waivers/HUSKY C/PACE, …) with bills as events, neutral history back as far as each topic goes, and a separate Ombudsman-position layer for testimony.
- **Now:** ✏️
- **Next:** ✏️ (2027 session prep; shareable page per storyline)
- **Later:** reference list of all LTC acts since 2021.

## 4. Annual impact dashboards (`/dashboards/`)
**Vision:** ✏️ one sentence. **Status:** 2024 and 2025 live. **Next:** ✏️ (2026 when NORS FFY data is out?)

## 5. BeemOps pages (`/beemops/`: calendar, library, studio)
**Vision:** ✏️ **Now / Next:** ✏️ (Studio video JPEG upload fix is pending in Codex.)

## 6. Bird Cam (`/birds/`) and Glizzy (`glizzy.danbeem.xyz`)
**Vision:** ✏️ **Status:** ✏️

---

## Page inventory (decide each ✏️)
Unlinked prototype pages in `/tools/` (nothing on the site links to them): Case Timeline Builder, Complaint Priority Matrix, Contact Card Builder, Facility Scorecard, Meeting Minutes Generator, Quick Intake Triage, Resident Check-In, Text to Speech, Visit Planner, Volunteer Shift Coverage, and the old `drafting-reference-assistant.html`. Outreach Email Builder has one link.
For each: **keep and add a roadmap item**, or **archive** (move to `/archive/`, keep the file, remove from the site). Claude's suggestion: archive all except any you actively use. ✏️

The `/tools/nursing-home-*.html` pages are redirects to `/staffing/tools/` and stay.

## Parking lot (ideas, not scheduled)
- ✏️ add ideas here, one line each, with the date.
