# DanBeem Ombudsman Tools and Resource Lab

Static ombudsman workflow tools focused on drafting support, NORS crosswalk reference lookup, responsible-use transparency, and related internal utilities.

## Setup & Running

Start a simple local static file server:

```bash
# Windows (PowerShell)
python -m http.server 8000

# Or with Node
npx http-server -p 8000
```

Then open:

- **Landing Page:** http://localhost:8000/index.html
- **Drafting Assistant:** http://localhost:8000/tools/drafting-assistant.html
- **NORS Crosswalk:** http://localhost:8000/tools/nors-crosswalk.html
- **Responsible Use:** http://localhost:8000/tools/responsible-use.html
- **Impact Dashboard:** http://localhost:8000/dashboards/impact-2024.html

## Current Architecture

- **Frontend:** Static HTML/CSS/JS
- **Data model:** Local JSON files, especially under `data/`
- **Crosswalk logic:** Shared loader and matching logic in `Assets/crosswalk.js`
- **Theme:** Dark glass UI with accessible focus states and semantic structure

## Current Primary Workflow

### Landing Page

- entry point for the featured tools
- links to the current NORS/drafting workflow

### Drafting & Reference Assistant

- structured case-note drafting support
- checklist review and validation
- inline topic/reference support driven by local data

### NORS Crosswalk Tool

- NORS code lookup
- keyword / concern lookup
- authority trail grouped by topic
- review support, trace output, and human-review flags

### Responsible Use & Sources

- source registry
- source-pack transparency
- workflow guardrails
- glossary and review flags

### Impact Dashboard

- annual-review dashboard and report links

## Data-Driven Source Of Truth

Per repo rules, use JSON files in `/data` as the source of truth whenever a normalized version exists.

Important files include:

- `data/nors_source_pack_lock.json`
- `data/source_registry.json`
- `data/nors_resource_catalog.json`
- `data/case_note_templates.json`
- `data/case_note_validation_rules.json`
- `data/current_tool_context_registry.json`

## Deployment Notes

- the current NORS crosswalk and drafting workflow are closed-loop and local-data driven
- there is no required backend for the current primary workflow
- production hosting can remain a static-site deployment as long as the app stays in this architecture

## Notes

- **No live AI dependency required for the current NORS/drafting flow**
- **Informational only** guardrails are built into the workflow
- **Human review remains required**
- **Source transparency is part of the product**

## Contact & Support

For issues or questions, use the repository history and source-of-truth data files as the starting point.
