## Project
Connecticut LTCOP Drafting and Reference Assistant

## Purpose
Build an internal draft-only web app that helps ombudsman staff work with de-identified case scenarios.

## Core functions
- summarize de-identified case scenarios
- generate checklist-aligned draft case notes
- validate required checklist elements
- summarize and draft emails
- surface relevant references from local source files

## Hard constraints
- no external AI calls in runtime app behavior
- no legal advice
- no advocacy recommendations
- no final NORS coding automation
- no PHI or identifying details
- all outputs must be labeled draft-only
- all logic must be deterministic where possible

## Build order
1. app shell
2. de-identified input form
3. case note drafting engine from JSON templates
4. checklist validation engine
5. email drafting/summarization module
6. local reference lookup panel
7. sample data and tests
8. polish UI

## Coding expectations
- prefer React + TypeScript
- keep logic modular
- place reusable logic in /src/lib
- store templates and rules in /data
- write readable code with comments where helpful
- propose next steps after each major milestone before making large architectural changes
