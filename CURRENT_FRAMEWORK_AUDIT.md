# Current Framework Audit

This is the current audit snapshot of the repo's HTML tool surface and the context-source handoff structure.

The canonical machine-readable registry is:

- [data/current_tool_context_registry.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/data/current_tool_context_registry.json)

That file is now the special place where:

- all local HTML pages are inventoried
- active vs secondary vs non-primary pages are classified
- shared context/data files are listed
- external context URLs are grouped for handoff

## Current Summary

There are `17` HTML files in the repo.

### Active primary workflow

- [index.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/index.html)
- [tools/drafting-assistant.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/drafting-assistant.html)
- [tools/nors-crosswalk.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/nors-crosswalk.html)
- [tools/responsible-use.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/responsible-use.html)

### Active secondary page in the current writing workflow

- [tools/outreach-email.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/outreach-email.html)

### Adjacent but separate pages

- [dashboards/impact-2024.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/dashboards/impact-2024.html)

### Repo-present pages not linked from the current primary NORS workflow

- [tools/case-timeline.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/case-timeline.html)
- [tools/complaint-priority.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/complaint-priority.html)
- [tools/contact-card-builder.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/contact-card-builder.html)
- [tools/drafting-reference-assistant.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/drafting-reference-assistant.html)
- [tools/facility-scorecard.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/facility-scorecard.html)
- [tools/meeting-minutes.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/meeting-minutes.html)
- [tools/quick-intake.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/quick-intake.html)
- [tools/resident-checkin.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/resident-checkin.html)
- [tools/text-to-speech.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/text-to-speech.html)
- [tools/visit-planner.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/visit-planner.html)
- [tools/volunteer-shift.html](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/tools/volunteer-shift.html)

## What The Current NORS Workflow Actually Uses

### Crosswalk / drafting core

The current NORS workflow is centered on:

- [Assets/crosswalk.js](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/Assets/crosswalk.js)
- [Assets/nors-help.js](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/Assets/nors-help.js)
- [Assets/shared.js](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/Assets/shared.js)

and the shared JSON/data layer:

- [nors_hierarchy.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/nors_hierarchy.json)
- [keyword_map.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/keyword_map.json)
- [nors_to_topic.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/nors_to_topic.json)
- [topic_to_authority.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/topic_to_authority.json)
- [crosswalk_catalog.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/crosswalk_catalog.json)
- [authority_index.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/authority_index.json)
- [retrieval_rules.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/retrieval_rules.json)
- the `data/nors_knowledge_base_batch*.json` files
- [data/source_registry.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/data/source_registry.json)
- [data/nors_source_pack_lock.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/data/nors_source_pack_lock.json)

### Case-note checklist / drafting layer

The drafting/checklist side depends directly on:

- [data/case_note_templates.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/data/case_note_templates.json)
- [data/case_note_validation_rules.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/data/case_note_validation_rules.json)
- [data/email_templates.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/data/email_templates.json)

## Important Audit Findings

1. The current NORS crosswalk and drafting workflow are still fundamentally `closed-loop` and local-data driven.
2. The active NORS workflow does `not` currently depend on live AI calls.
3. The most important external context pages are not stored as local HTML, because they are official external PDFs/pages.
4. Those external context URLs are now captured in:
   - [data/current_tool_context_registry.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/data/current_tool_context_registry.json)
   - [AI_HANDOFF_SOURCE_LINKS.md](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/AI_HANDOFF_SOURCE_LINKS.md)
5. The repo contains several other HTML tools and prototypes that are real pages, but they are not part of the current primary NORS workflow.

## Why The New Registry Matters

You asked for a place where all context URLs are stored so you can always send out the current tool context.

That now exists in:

- [data/current_tool_context_registry.json](C:/Users/Dan/OneDrive/Documents/GitHub/DanBeem/data/current_tool_context_registry.json)

Use that file when you need:

- the current live HTML inventory
- the current primary workflow pages
- the shared context/data files
- the grouped external source URLs behind the framework

It should be much easier to keep current than rebuilding a link packet from memory every time.
