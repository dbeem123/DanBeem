# Connecticut Nursing Home Affiliation Entity Name Audit

Generated: 2026-05-19

## Purpose

This audit reviews the CMS SNF Enrollments `affiliation_entity_name` and `affiliation_entity_id` values currently merged into `data/nursing_home_staffing_ct.json`. The goal is to decide whether the Ownership / Affiliation Staffing Explorer can safely use the raw CMS affiliation names for the next analytics phase, or whether a normalization/display-label layer should be added first.

## Data Reviewed

- Source export reviewed: `data/nursing_home_staffing_ct.json`
- Facilities in generated export: 196
- Connecticut facilities with nonblank `affiliation_entity_name`: 108
- Unique nonblank affiliation entity names: 19
- Connecticut facilities with nonblank `affiliation_entity_id`: 108
- Unique nonblank affiliation entity IDs: 19
- Facilities with nonblank affiliation entity ID but blank affiliation entity name: 0

The current ownership explorer groups facilities by raw nonblank `affiliation_entity_name`.

## Audit Outcome

**Outcome A: No normalization needed before Phase 4D.**

The CMS affiliation names in the current generated export are sufficiently clean and stable for public statewide affiliation rankings and chain-performance tables, provided the UI continues to describe them as CMS SNF Enrollment affiliation entities and not as definitive proof of common control or day-to-day operations.

No generator or UI change is recommended for Phase 4C. A future display-label mapping can still be added later if public-facing wording needs polish, but the present data does not require a normalization or alias layer.

## Entity Inventory

| Raw affiliation entity name | Affiliation entity ID | CT facilities | Example linked facilities | Public display clean? | Normalization / alias concern |
|---|---:|---:|---|---|---|
| NATIONAL HEALTH CARE ASSOCIATES | 363 | 24 | BEACON BROOK CENTER FOR HEALTH & REHABILITATION; BETHEL HEALTH CARE CENTER; BLOOMFIELD CENTER FOR NURSING & REHABILITATION; CAMBRIDGE HEALTH AND REHABILITATION CENTER | Yes | No alias concern found |
| APPLE REHAB | 39 | 19 | APPLE REHAB AVON; APPLE REHAB COCCOMO; APPLE REHAB COLCHESTER; APPLE REHAB CROMWELL | Yes | No alias concern found |
| ICARE HEALTH NETWORK | 277 | 9 | 60 WEST; CHELSEA PLACE CARE CENTER LLC; FRESH RIVER HEALTHCARE; SILVER SPRINGS CARE CENTER | Yes | No alias concern found |
| AUTUMN LAKE HEALTHCARE | 56 | 8 | AUTUMN LAKE HEALTHCARE AT BUCKS HILL; AUTUMN LAKE HEALTHCARE AT CROMWELL; AUTUMN LAKE HEALTHCARE AT GLEN HILL; AUTUMN LAKE HEALTHCARE AT MADISON | Yes | No alias concern found |
| COMPLETE CARE | 157 | 8 | COMPLETE CARE AT FOX HILL; COMPLETE CARE AT GLENDALE; COMPLETE CARE AT GROTON REGENCY; COMPLETE CARE AT HARRINGTON COURT | Yes | No alias concern found |
| RYDERS HEALTH MANAGEMENT | 458 | 7 | AARON MANOR NURSING & REHABILITATION; BEL-AIR MANOR NURSING & REHABILITATION CENTER; CHESHIRE HOUSE HEALTH CARE FACILITY & REHAB CENTER; GREENTREE MANOR NURSING AND REHABILITATION CENTER | Yes | No alias concern found |
| CIVITA CARE CENTERS | 683 | 6 | CIVITA CARE CENTER AT CHESHIRE; CIVITA CARE CENTER AT DANBURY; CIVITA CARE CENTER AT LONG RIDGE; CIVITA CARE CENTER AT MILFORD | Yes | No alias concern found |
| ATHENA HEALTHCARE SYSTEMS | 52 | 5 | BAYVIEW HEALTH CARE; CIVITA CARE MEADOWBROOK; CIVITA CARE NORTHBRIDGE; CIVITA SHERIDEN WOODS | Yes | Possible branding ambiguity because several linked facility names begin with CIVITA, but the CMS affiliation name and ID are consistent |
| ATLAS HEALTHCARE | 598 | 5 | BRIDE BROOK REHABILITATION & NURSING CENTER; MANCHESTER REHABILITATION AND  HEALTHCARE CENTER; PENDLETON REHABILITATION AND NURSING CENTER; SUFFIELD HOUSE REHABILITATION AND HEALTHCARE CENTE | Yes | No alias concern found; one source facility name appears truncated as supplied |
| ESSENTIAL HEALTHCARE | 212 | 5 | ADVANCED CENTER FOR NURSING & REHABILITATION; NEW HAVEN CENTER FOR NURSING & REHABILITATION LLC; Southport Center For Nursing & Rehabilitation Llc; Torrington Center For Nursing & Rehabilitation LLC | Yes | No alias concern found |
| LIFE CARE SERVICES | 312 | 3 | AVALON HEALTH CARE CENTER AT STONERIDGE; ESSEX MEADOWS HEALTH CENTER; POMPERAUG WOODS HEALTH CENTER | Yes | Name is broad but clear enough as a CMS affiliation label |
| HIGHBRIDGE HEALTHCARE | 269 | 2 | ARDEN CARE CENTER; SAINT JOHN PAUL II CENTER | Yes | No alias concern found |
| ASCENTRIA CARE ALLIANCE | 49 | 1 | Lutheran Home Of Southbury Inc | Yes | Single-facility affiliation in CT; not a normalization issue |
| CAREONE | 109 | 1 | RIVER GLEN HEALTH CARE CENTER | Yes | Single-facility affiliation in CT; not a normalization issue |
| CENTER MANAGEMENT GROUP | 619 | 1 | VILLA AT STAMFORD, THE | Yes | Single-facility affiliation in CT; not a normalization issue |
| COVENANT LIVING | 168 | 1 | PILGRIM MANOR | Yes | Single-facility affiliation in CT; not a normalization issue |
| SENIOR LIVING COMMUNITIES | 470 | 1 | EVERGREEN WOODS | Yes | Name is broad but usable as a CMS affiliation label |
| THE MAYER FAMILY | 780 | 1 | WHITNEY REHABILITATION CARE CENTER | Mostly | Name appears to describe a family ownership/affiliation rather than a chain brand; display as CMS affiliation entity, not as a chain label |
| TRINITY HEALTH | 525 | 1 | SAINT MARY HOME | Yes | Single-facility affiliation in CT; not a normalization issue |

## Issue Checks

| Check | Result | Notes |
|---|---|---|
| Same `affiliation_entity_id` paired with multiple names | PASS | No cases found |
| Same raw `affiliation_entity_name` paired with multiple IDs | PASS | No cases found |
| Nearly identical names split by punctuation, spacing, capitalization, or suffix | PASS | No evident split labels among the 19 names |
| Facilities with affiliation entity IDs but blank names | PASS | 0 cases found |
| Vague or unclear names needing immediate friendly display label | PASS with notes | `THE MAYER FAMILY` and `SENIOR LIVING COMMUNITIES` are broad labels, but they are still understandable as CMS affiliation entity names |
| Names that may describe something other than a true chain / organizational grouping | PASS with caution | Some labels may represent families, management groups, or affiliation entities rather than chain brands. The UI should continue to use cautious "affiliation entity" language |
| Facility names suggesting a different brand than the CMS affiliation name | PASS with notes | Some Athena-linked CT facilities have CIVITA-branded facility names. This may reflect branding, transaction history, or source timing; the CMS affiliation name/ID pairing is internally consistent |

## Recommendation

Do not add a normalization, alias, or public display-label layer for Phase 4C.

For Phase 4D statewide affiliation rankings and chain-performance tables:

- Group by the existing raw `affiliation_entity_name` and retain `affiliation_entity_id` in the data model.
- Label rankings as "CMS SNF Enrollment affiliation entities" or "affiliation groups," not definitive chains.
- Preserve the existing caution that a shared affiliation entity does not prove common day-to-day operations, common control, poor care, harm, neglect, or regulatory violations.
- Re-run this audit whenever the SNF Enrollments source file is refreshed, because affiliation names and IDs may change over time.

## Readiness For Phase 4D

The project is ready to proceed to Phase 4D statewide affiliation rankings and chain-performance tables without adding a normalization layer first.

