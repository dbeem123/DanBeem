# Current Framework Audit

This is the current audit snapshot of the repo's HTML tool surface and the context-source handoff structure.

The canonical machine-readable registry is:

- [data/current_tool_context_registry.json]([private local path omitted]

That file is now the special place where:

- all local HTML pages are inventoried
- active vs secondary vs non-primary pages are classified
- shared context/data files are listed
- external context URLs are grouped for handoff

## Current Summary

There are `17` HTML files in the repo.

### Active primary workflow

- [index.html]([private local path omitted]
- [tools/drafting-assistant.html]([private local path omitted]
- [tools/nors-crosswalk.html]([private local path omitted]
- [tools/responsible-use.html]([private local path omitted]

### Active secondary page in the current writing workflow

- [tools/outreach-email.html]([private local path omitted]

### Adjacent but separate pages

- [dashboards/impact-2024.html]([private local path omitted]

### Repo-present pages not linked from the current primary NORS workflow

- [tools/case-timeline.html]([private local path omitted]
- [tools/complaint-priority.html]([private local path omitted]
- [tools/contact-card-builder.html]([private local path omitted]
- [tools/drafting-reference-assistant.html]([private local path omitted]
- [tools/facility-scorecard.html]([private local path omitted]
- [tools/meeting-minutes.html]([private local path omitted]
- [tools/quick-intake.html]([private local path omitted]
- [tools/resident-checkin.html]([private local path omitted]
- [tools/text-to-speech.html]([private local path omitted]
- [tools/visit-planner.html]([private local path omitted]
- [tools/volunteer-shift.html]([private local path omitted]

## What The Current NORS Workflow Actually Uses

### Crosswalk / drafting core

The current NORS workflow is centered on:

- [Assets/crosswalk.js]([private local path omitted]
- [Assets/nors-help.js]([private local path omitted]
- [Assets/shared.js]([private local path omitted]

and the shared JSON/data layer:

- [nors_hierarchy.json]([private local path omitted]
- [keyword_map.json]([private local path omitted]
- [nors_to_topic.json]([private local path omitted]
- [topic_to_authority.json]([private local path omitted]
- [crosswalk_catalog.json]([private local path omitted]
- [authority_index.json]([private local path omitted]
- [retrieval_rules.json]([private local path omitted]
- the `data/nors_knowledge_base_batch*.json` files
- [data/source_registry.json]([private local path omitted]
- [data/nors_source_pack_lock.json]([private local path omitted]

### Case-note checklist / drafting layer

The drafting/checklist side depends directly on:

- [data/case_note_templates.json]([private local path omitted]
- [data/case_note_validation_rules.json]([private local path omitted]
- [data/email_templates.json]([private local path omitted]

## Important Audit Findings

1. The current NORS crosswalk and drafting workflow are still fundamentally `closed-loop` and local-data driven.
2. The active NORS workflow does `not` currently depend on live AI calls.
3. The most important external context pages are not stored as local HTML, because they are official external PDFs/pages.
4. Those external context URLs are now captured in:
   - [data/current_tool_context_registry.json]([private local path omitted]
   - [AI_HANDOFF_SOURCE_LINKS.md]([private local path omitted]
5. The repo contains several other HTML tools and prototypes that are real pages, but they are not part of the current primary NORS workflow.

## Why The New Registry Matters

You asked for a place where all context URLs are stored so you can always send out the current tool context.

That now exists in:

- [data/current_tool_context_registry.json]([private local path omitted]

Use that file when you need:

- the current live HTML inventory
- the current primary workflow pages
- the shared context/data files
- the grouped external source URLs behind the framework

It should be much easier to keep current than rebuilding a link packet from memory every time.
