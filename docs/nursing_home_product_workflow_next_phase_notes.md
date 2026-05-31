# Nursing Home Product Workflow Next Phase Notes

Phase 10A was planning only. Phase 10B added a narrow public source-currency strip and lightly emphasized the two current primary entry paths on the homepage: facility search and statewide facility scanning.

## Recommended Future Entry Points

1. Facility Search / Facility Dossier
   - Best for residents, families, advocates, or staff who know the nursing home name.
   - Leads to staffing trends, CMS ratings, quality measures, affiliation context, and future official survey/enforcement/source freshness modules.

2. Owner / Entity Search
   - Best for users starting with a reported owner, organization, manager, or corporate entity.
   - Should use CMS-reported owner/entity language and preserve distinctions among ownership, management, affiliation entity, chain, and related-party relationships.
   - Future route candidate: `tools/nursing-home-owner-entity-explorer.html`.

3. Connecticut Statewide Exploration
   - Best for scanning latest-quarter staffing, change over time, persistent patterns, affiliation summaries, future official CMS status indicators, and later ownership concentration or DSS context.

## Phase 10B Landing-Page Treatment

- The current homepage now labels Facility Explorer as the primary "Search for a Facility" path.
- The Statewide Facility Staffing Comparison card is also emphasized as the primary "View Connecticut Facilities" path.
- Change Over Time, Persistent Patterns, and Ownership / Affiliation remain available as deeper analytical views.
- Owner / Entity Search remains a future path and was not added to public navigation.

## Deeper Pathways

- Change Over Time and Persistent Patterns should remain analytical follow-up paths after a user identifies a question.
- Ownership / Affiliation should remain available but eventually be renamed or repositioned if a separate owner/entity explorer is built.
- Methodology should stay visible from every primary path.

## Future Review Packet Concept

A future `Prepare Review Packet` action could generate a copyable evidence-and-question packet. Suggested sections:

- what the data shows
- what it may suggest
- what it cannot prove
- questions for further review

This should remain a structured copy helper unless a later governance and security review approves any server-side AI integration.

## Governance Timeline Pathway

Phase 10B.1 added a future CT DPH governance pathway to the planning stack. This should not become a primary navigation path yet, but it could eventually enrich both Facility Search / Facility Dossier and Connecticut Statewide Exploration.

Possible future placement:

- Facility dossier: an expandable Governance Timeline section after staffing trend and ownership/affiliation context.
- Statewide exploration: a governance-stability screening view after crosswalk and role-period cleaning.
- Review packet: governance context can become a section alongside staffing trend, ownership/affiliation, survey/enforcement, and source caveats.

Owner / Entity Search should remain a separate concept from governance timeline work. DPH leadership roles, CMS-reported ownership, CMS affiliation entities, CMS chain performance, and CT DSS related-party relationships should not be collapsed into one "operator" concept.
