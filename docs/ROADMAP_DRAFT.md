# danbeem.xyz roadmap

**DRAFT by Claude, updated 2026-11-27, for Daniel to edit.** Lines marked ✏️ are guesses or blanks only Daniel can fill. Once Daniel approves it, this file is the reference for what gets built. If an idea is not on it, it is not built yet.

## How this file is used (the rules)

1. **One page, kept current.** Every section below has a one-line *vision*, *done means*, and a short *Now / Next / Later / Not doing* list. Update it in the same PR as the work.
2. **Ideas go to the parking lot first** (bottom of this file, or a GitHub issue labeled `idea`). Writing an idea down is the only thing that happens to it the day you have it.
3. **Only "Now" items get built.** At most **two** "Now" items across the whole site at a time. To start something new, finish or move an existing "Now" item down first. (Read-only audits, bug fixes to live pages, and prototypes that touch no live page may run alongside.)
4. **Every PR names its roadmap item** ("Roadmap: NORS tools / Now 1"). Claude and Codex refuse work that has no item, and add it to the parking lot instead.
5. **Finish or retire.** A page is *Live* (linked, maintained), *In progress* (on Now/Next), *Prototype* (unlinked, not maintained) or *Retired*. Prototypes either get a roadmap item within a month or move to an archive folder.
6. **Big decisions** go in `docs/DECISIONS.md` (date, decision, why) so the "why" survives.
7. **Before the first push of any NORS page**, run the pre-publication checklist (bottom of this file).

## Site purpose

danbeem.xyz is Daniel's personal project site. Its main work is **CT Long-Term Care Advocacy · independent research**: public, source-cited tools for Connecticut long-term care (staffing, inspections, ownership, cost reports, legislation, NORS casework), plus a few personal projects. Everything public on CMS and in Connecticut public data should be usable here, connected and explained.

**Identity rule (Daniel, 2026-11-23):** the site is independent research. It never presents itself as the Connecticut Long Term Care Ombudsman Program (LTCOP) or speaks for it. Pages that track LTCOP's own published work (annual reports, published bill list, quoted published positions) keep LTCOP as their subject or source, labelled as an independent summary.

---

## Site-wide Now (maximum two), approved by Daniel 2026-11-27

Chosen because both NORS Now items are waiting on Daniel's input (phrase sheet and open questions) and the 2027 session opens in January:
1. **Legislative tracker, Phase 1** (section 3).
2. **NORS: connect sources to every code** (section 1, Now 1). Continues as soon as Daniel's phrase sheet is in.

Moved down until a slot opens: NORS plain-language examples (section 1, Now 2) and staffing 0026 (section 2).

---

## 1. NORS casework tools (crosswalk, Drafting Assistant, hub)

**Vision:** an ombudsman types what the resident is saying, or picks a NORS code from its description. The tool shows the exact regulation citation and text to cite to an administrator, the CMS Intent passage to explain the right to a resident, and the Appendix PP examples and "cite elsewhere" cues. The tag's NORS links are labeled **Fits** or **Also consider**. The ombudsman chooses the code, then carries the code and citations into a case note checked against the NORC Case Notes Checklist, for entry in WellSky. SNF only.

**The ombudsman's vocabulary comes first:** results lead with the regulation citation and the CMS example language people already know. F-tag numbers and NORS codes are labels, not the way in.

**Done means:** every NORS code has verbatim, source-locked text and reviewed links to regulation, Appendix PP and Connecticut/federal authority; the crosswalk shows a discernment view; plain-language example complaints exist for every code; the Drafting Assistant hands the chosen code and citations into a checklist-checked case note; a deployment-readiness package exists for the state.

**Rules that don't change:** NORS Table 2 text decides the code; F-tags, Appendix PP, regulations and CT law are context links ("may relate"), never a final code; exact quotes only, with locators and hashes; deterministic local data, no AI in the tool; no storage; synthetic data only on the public site; the ombudsman makes every coding decision. Ranking is labeled "closest match to your words," never "most likely." Connecticut AI policy compliance is shown and never described as approved.

### Done (local, 2026-11-16)
- Source pack locked (105 files); Appendix PP extracted per tag (204 tags, CMS short titles).
- Reviewed F-tag ↔ NORS links: 199 reviewed (124 Fits, 75 Also consider) and 282 rejected; 121 tags and 47 of 60 codes covered; batches 1-6 triaged and approved.
- Key-element and "cite elsewhere" cue extraction (348 passages, 76 cues); example-evidence audit of dropped links (339 candidates triaged).
- CFR layer: 1,231 subsection records with hashes; mapping to tags in progress (about 360 more mappable).
- Pilot plain-language examples (D03, D05, F05) with near-misses; staged drafts for most other codes.

### Now
1. **Connect sources to every NORS code.**
   - Connecticut and federal ombudsman authority layer (CGS 19a-550, 19a-532, 319l, 17b-411, regs 19-13-D8t/D8v, 45 CFR 1324) with verified citations and proposed code links.
   - CFR-to-tag mapping fix (5-word-sequence overlap; 360 new mappings; four citation bugs).
   - The 13 codes Appendix PP cannot cover (G02, G03, H01, H03, K01-K06, L01-L03): **waiting on Daniel's phrase sheet** (`docs/daniel_phrase_sheet_uncovered_codes_20261116.csv`).
2. **Plain-language examples, done carefully** (paused under the site-wide limit). Fix the D03/D05/F05 pilot, test on held-out queries, and scale in waves only if the held-out misses drop. Daniel reviews.

### Next
- **UI audit and redesign (read-only first):** landing page with the casework tools first; one search box over three panels (regulation, Appendix PP examples and CMS Intent, NORS code cards); a "Cite and explain" panel; Drafting Assistant as a numbered flow (Facts, Check codes, Review, Draft).
- **Discernment view built** on the chosen prototype.
- **Case note handoff** into the Drafting Assistant with the NORC checklist.
- **Hub and one home page card, then publish** (after the pre-publication checklist).

### Later
- Ranking boosts only after they pass the official-scenario regression and the held-out set; weights visible, off by default.
- Case-fact narrowing; WellSky entry helper (synthetic examples only); Drafting Assistant parity (Table 1 fields); readiness package for the State Ombudsman and BITS.
- Appendix Z (emergency preparedness) only if it becomes in scope.

### Not doing
Generative AI in the tool, semantic search, uploads, saving drafts, RCH content, real case data, any claim of state approval.

**Open questions for Daniel:** (1) Does a case carry one NORS complaint code or several? (2) Confirm the 104 reviewed-links records naming you as reviewer. (3) Which of the 5 reversals and the F575/F604 rejections do you want revisited later?

## 2. Staffing suite (`/staffing/`)
**Vision:** for any CT nursing home, see staffing, inspections, ownership, management, administrators and money in one connected, cited place.
**Pages (Live):** Explorer, Statewide comparison, Change over time, Persistent patterns, Ownership/affiliation, Methodology, CT staffing rules, Daily minimums, Inspections, Administrator search, Management companies, Cost reports, Cost report insights, Cost Reports 101, Facility reports (`/staffing/reports/`), static reporting API (`/api/`).

### Done since 2026-11-16
- Daily minimums page (2026-11-20).
- Static reporting API, Reports page and AI handoff notes (2026-11-20/21).
- Facility reports: charts, tables and readable key numbers; financial reports carry their own numbers and screen out misread years; DSS review changes and Medicaid revenue kept apart from reported spending; last 6 homes matched by address and payer-day counts (2026-11-22).
- Staffing menu grouped into six choices (2026-11-22).
- Cost Reports 101: plain-language guide, key dates set by law with citations and direct-source links, interactive timeline (2026-11-22).

### Now
- *(paused under the site-wide limit)* publish 0026 (DSS cost centers and statewide averages). Not yet on the live site as of 2026-11-27.

### Next ✏️ pick one
- Tie cost-report owners to CMS ownership, so money and owners connect.
- Direct-care dollars compared with actual staffing hours per home.
- Quarterly PBJ refresh.

### Later
Management fees from cost reports; RCH cost reports.

### Not doing ✏️

## 3. Legislative tracker (`/legislation/`)
**Vision:** policy storylines (staffing floors and ratios, direct-care spending, CFC/waivers/HUSKY C/PACE, ...) with bills as events, neutral history back as far as each topic goes, and a separate layer that quotes published LTCOP positions verbatim (linked and dated). Daniel's own recommendations are labelled as his independent research.

**Status:** landing page, 2026 and 2027 session pages, 12 storylines, 58-act reference library and testimony builder are live. 2027 is pre-session with 0 bills.

### Done
- Read-only audit and architecture plan for the 2027 platform (2026-11-23, kept in private planning).
- Decision: the policy portfolio is Daniel's own independent research, not Program work. Private drafts stay off the public repo; publishing goes through a fail-closed export with validators.
- Rebrand to CT Long-Term Care Advocacy; disclaimers and the testimony placeholder updated (commit `a23ee0f`).

### Now (approved 2026-11-27)
- **Phase 1 foundation: done 2026-11-27.** Rules file (`data/ct_policy_rules.json`), six empty public files, validator and content scan (`scripts/validate_ct_policy.py`), fail-closed export (`scripts/export_public_policy.py`), 20 fail-case tests, CI gate (`.github/workflows/legislation-validate.yml`), new topic "Dignity, autonomy and quality of life", runbook (`docs/ct_policy_runbook.md`).
- **Next in Now:** fill `data/ct_ltc_authorities.json` with verified Connecticut and federal law (exact quotes, sources, dates); then the policy explorer pages (Phase 3) with neutral research records only.

### Next
- 2027 session tracking as bills are filed; a shareable page per storyline.
- Positions runbook and validator reworded to "published positions (quoted)".

### Later
Regulatory tracker (scope ✏️: DPH/DSS rulemaking only, or also CMS rules and DSS transmittals).

**Open questions for Daniel:** should Legislation join the top navigation? Implementation scope: only acts linked to policies, or all 58?

## 4. Annual impact dashboards (`/dashboards/`)
**Vision:** an independent, plain-language summary of what the CT LTCOP reports it did each year, from its published annual reports.
**Status:** 2024 and 2025 live, titled "independent summary".
**Next:** 2026 when the federal NORS fiscal-year data is published.

## 5. BeemOps pages (`/beemops/`: calendar, library, studio)
**Vision:** ✏️ Daniel's private creative studio: make songs, images, speech and short videos on his own GPU, from the website or from Discord, and keep them in a private library.

### Done since 2026-11-16
- Homepage and BeemOps pages redesigned; Open Studio buttons go to the create page (2026-11-21).
- Studio video (2026-11-26/27): choose Standard or Reference H3 video model; "Characters & places" with up to 3 Library pictures; the same choice from Discord with clickable buttons; finished-video check fixed; owner never limited.

### Now (bug fixes, outside the two-item limit)
- Photo upload fix: big phone photos scaled down instead of refused. Built and tested, **waiting for Daniel to run the installer**.
- Confirm a Reference H3 render from Discord and a "Characters & places" render from the website.

### Next ✏️
- Lighter page effects if the site still feels slow.
- Move AI files and outputs to the X: drive once everything works.

## 6. Bird Cam (`/birds/`) and Glizzy (`glizzy.danbeem.xyz`)
**Vision:** ✏️ **Status:** ✏️

---

## Pre-publication checklist (NORS pages)
- [ ] Only synthetic examples on every public page; no real names, facilities or case facts.
- [ ] Connecticut AI policy wording is accurate and never claims approval.
- [ ] Responsible Use page matches what the tool now does.
- [ ] Every "Fits" and "Also consider" label has its quoted passage; no draft or proposed data renders.
- [ ] No external requests, no browser storage (the source UI check passes).
- [ ] Branch reconciliation re-run; push the newer branch; Daniel reviews locally first (`python -m http.server 8000 --bind 127.0.0.1`).
- [ ] Unverified Connecticut citations resolved (confidentiality statute numbers, 19a-550 subsections, 17b-411 currency).
- [ ] Wording follows the identity rule: independent research, never presented as the Program.

## Cleanup waiting on Daniel ✏️
- **Unlinked prototypes in `/tools/`** (past the one-month rule): Case Timeline Builder, Complaint Priority Matrix, Contact Card Builder, Facility Scorecard, Meeting Minutes Generator, Quick Intake Triage, Resident Check-In, Text to Speech, Visit Planner, Volunteer Shift Coverage, the old `drafting-reference-assistant.html`. Outreach Email Builder has one link. Claude's suggestion: archive all except any you actively use.
- **`tools/ct-ltcop-regional-coverage-map.html`** calls itself a "working draft" of LTCOP region assignments: keep public, archive, or remove?
- **Old CT LTCOP logo files** in `Assets/branding/` are unused but still reachable by URL: OK to delete?
- `data/current_tool_context_registry.json` still lists the old logo path (stale).

The `/tools/nursing-home-*.html` pages are redirects to `/staffing/tools/` and stay.

## Parking lot (ideas, not scheduled)
- 2026-11-14: plain-language bridge map (word pairs): tested, did not improve results; do not pursue unless examples fail.
- 2026-11-16: Daniel's casework phrase list per code (feeds the examples).
- 2026-11-23: private policy drafts behind Cloudflare Access, if web views are wanted.
- ✏️ add ideas here, one line each, with the date.
