# Connecticut Nursing Home Administrator Roster Source Validation

## Scope

Phase 11E.1 validates and documents the Connecticut Department of Public Health (DPH) Nursing Home Administrator license roster downloaded May 22, 2026. This is source validation and data-contract planning only. It does not create public runtime JSON, change the Facility Explorer, infer employment, or associate a licensee with a nursing home.

## Source confirmation

- Source agency: Connecticut Department of Public Health
- Source name: Nursing Home Administrator license roster
- Source filename: `Nursing_Home_Administrator_2026-05-22.csv`
- Roster and acquisition date used for validation: May 22, 2026
- Local source location: `source_data/ct_dph/Nursing_Home_Administrator_2026-05-22.csv`
- Exact file size: 63,982 bytes
- Encoding result: readable as UTF-8; no UTF-8 BOM is present, although the validator accepts one
- Git treatment: ignored by `.gitignore` through `source_data/*`; the raw CSV is not staged or committed

The validator uses May 22, 2026—not the current system date—as the reference date for expiration calculations.

## Complete source schema

The source contains 13 named columns. It contains no unnamed columns and no entirely blank columns.

| Source column | Source meaning / planned mapping | Blank rows |
| --- | --- | ---: |
| `LICENSE NO.` | License number; planned `license_number_raw` and normalized `license_number` | 0 |
| `FIRST NAME` | Source first name; planned preserved raw and normalized first-name fields | 0 |
| `LAST NAME` | Source last name; planned preserved raw and normalized last-name fields | 0 |
| `ADDRESS1` | Mailing address line 1 | 1 |
| `ADDRESS2` | Mailing address line 2 | 562 |
| `CITY` | Mailing city | 0 |
| `STATE` | Mailing state | 0 |
| `ZIP` | Raw mailing ZIP; planned raw and conservatively normalized ZIP fields | 0 |
| `COUNTY` | Mailing county as supplied by DPH | 112 |
| `STATUS` | License status | 0 |
| `REASON` | Administrative status reason | 0 |
| `ISSUE DATE` | Original issue date | 0 |
| `EXPIRATION DATE` | License expiration date | 0 |

There are no source fields for middle name or initial, suffix, full name, or country. Validation-only `middle_name` and `suffix` values are therefore empty, while `display_name` and `normalized_match_name` are derived only from the available first and last names. No source field has been renamed or reinterpreted without a documented mapping.

## Record and license-number findings

- Total source rows: 581
- Completely blank rows: 0
- Normalized validation records: 581
- Rows with a license number: 581
- Unique normalized license numbers: 581
- Duplicate normalized license values: 0
- Duplicate excess rows after normalization: 0
- Missing or malformed license numbers: 0
- Normalized license-number length: all 581 values are six characters

The current CSV already stores license numbers as six-character digit strings. Representative raw-to-normalized examples are `000050` → `000050`, `000297` → `000297`, and `000359` → `000359`. No current value uses spreadsheet formula-style wrapping and no unexpected value was found.

The validator nevertheless safely handles future values such as `="000050"`: it removes the formula-style wrapper and matching unnecessary quotation marks, keeps the value as a string, and preserves the leading zeros. It never converts a license number to an integer. Non-digit results are retained for review and flagged `unexpected_license_number_format`; none occur in this roster.

## Name findings

- Rows missing first or last name: 0
- Unique normalized comparison names: 580
- Duplicate normalized comparison-name values: 1
- Duplicate excess rows by normalized name: 1

The only repeated conservative comparison key is `CHRISTOPHER JOHNSON`. It occurs on source rows 169 and 290 with distinct license numbers `001527` and `001827` and different mailing states. This confirms that normalized-name equality must not be used to merge people.

Validation-only name normalization trims whitespace, collapses repeated spaces, preserves source punctuation in `display_name`, applies Unicode decomposition for comparison, removes combining marks, converts non-alphanumeric separators to spaces, collapses those spaces, and uppercases the comparison key. The source first and last names remain separately preserved.

Future matching must account for initials versus full middle names, suffixes, hyphenated names, apostrophes, previous names, spelling variation, and identical names belonging to different people. This roster lacks middle-name, suffix, and previous-name fields, so a name match cannot by itself establish identity or employment.

## Address, state, and ZIP findings

- Connecticut mailing state: 460 rows
- Non-Connecticut mailing state: 121 rows
- Missing mailing state: 0 rows
- Rows missing both street-address lines: 1
- Missing city: 0 rows
- Missing ZIP: 0 rows
- Country column: absent

The one record without a street-address line still supplies a city, state, and ZIP. State values are two-character U.S. state or District of Columbia codes. No explicitly non-U.S. address appears, but country cannot be independently validated because the roster has no country field.

| State | Rows | State | Rows |
| --- | ---: | --- | ---: |
| CT | 460 | NY | 30 |
| MA | 27 | FL | 17 |
| NJ | 7 | RI | 7 |
| SC | 6 | IL | 4 |
| NC | 4 | CA | 3 |
| MD | 3 | NH | 2 |
| VA | 2 | VT | 2 |
| WA | 2 | AZ | 1 |
| DC | 1 | DE | 1 |
| ME | 1 | TN | 1 |

### ZIP letter-O investigation

- ZIP values containing the letter `O`: 549
- Values safely corrected in validation-only normalized ZIPs: 549
- Unexpected formats after safe correction: 0
- Connecticut rows containing `O`: 460 of 460
- Connecticut normalized ZIPs matching five-digit or ZIP+4 form: 460 of 460
- Connecticut normalized ZIPs beginning with `06`: 460 of 460

Examples include `O6897` → `06897`, `O641O` → `06410`, `O6331-1916` → `06331-1916`, and the non-Connecticut value `1O465-3826` → `10465-3826`. Replacement is considered safe only when the trimmed, uppercased value consists of exactly five `[0-9O]` characters or a five-plus-four pattern separated by a hyphen and replacing `O` with `0` yields a valid numeric ZIP or ZIP+4 pattern. Every correction is flagged `zip_letter_o_corrected_to_zero`. The raw ZIP is always preserved and never overwritten.

A mailing address is correspondence information only. It is not evidence of employment location, practice location, or facility affiliation.

## License-status findings

All 581 rows have license status `ACTIVE`.

| Status reason | Rows |
| --- | ---: |
| `CURRENT` | 492 |
| `RENEWAL APPLICATION SENT` | 70 |
| `PRINT LICENSE` | 12 |
| `PRIOR DISCIPLINE` | 5 |
| `RENEWAL APPLICATION RECEIVED-INCOMPLETE` | 2 |

Each reason occurs only with `ACTIVE`, so the status-and-reason combination counts are identical to the table above. The roster's exact hyphenated value is `RENEWAL APPLICATION RECEIVED-INCOMPLETE`.

`ACTIVE` describes the license status in this roster. The reason supplies additional administrative context. `PRIOR DISCIPLINE` is retained exactly as source context and is not interpreted beyond the roster. An active license does not establish current employment, a mailing state does not establish where the licensee practices, and the roster does not establish which facility—if any—the administrator manages.

## Date findings

- Original issue date range: January 1, 1901 through April 14, 2026
- Expiration date range: February 28, 2026 through July 31, 2029
- Missing original issue dates: 0
- Invalid original issue dates: 0
- Missing expiration dates: 0
- Invalid expiration dates: 0
- Expiration dates before original issue dates: 0
- Records expired as of May 22, 2026: 13

All 13 past-expiration records are still represented by the source as `ACTIVE`. The validator reports both facts without attempting to resolve or reinterpret the source.

The cumulative future-expiration windows from May 22, 2026 are:

| Window | Records expiring on or after the roster date and within the window |
| --- | ---: |
| 30 days | 4 |
| 60 days | 25 |
| 90 days | 57 |
| 180 days | 151 |
| 365 days | 288 |

### Possible legacy issue date

Twenty-six records use `01/01/1901` as the original issue date. The repeated exact date, its age, and its separation from the rest of the licensing history suggest that it likely functions as a legacy or placeholder value, but the roster does not prove that interpretation. The validator preserves the source date and sets the validation-only flag `possible_legacy_issue_date`; it does not replace the date.

## Facility-affiliation limitations

The roster does not contain any of the following:

- facility or nursing-home name;
- employer;
- work address;
- facility license number;
- CMS Certification Number (CCN);
- National Provider Identifier (NPI); or
- Connecticut facility identifier.

Therefore, the roster cannot independently link administrators to nursing homes. It can support validation that a named person appears to hold an administrator license, subject to identity-matching uncertainty. A separate official source containing current facility-administrator relationships is required to establish current affiliation. Future name matching must keep license validation separate from employment confirmation. No administrator-to-facility links are created in this phase.

## Risks and caveats

- The roster is a May 22, 2026 snapshot and may not reflect later licensing changes.
- All records are `ACTIVE`, including 13 whose expiration dates precede the roster date; these fields must remain distinct.
- The 26 possible legacy dates must be retained and flagged rather than silently corrected.
- Most ZIP values contain `O`; safe normalized ZIPs must coexist with the exact raw value and correction flag.
- Identical normalized names can belong to different license records and people.
- Mailing geography cannot establish current employment, practice, or facility management.
- `PRIOR DISCIPLINE` is only a source status reason and carries no additional interpretation here.

## Data-contract readiness

The source has complete license numbers, first and last names, mailing states, cities, ZIP values, statuses, reasons, issue dates, and expiration dates. Its 581 license numbers are unique after conservative normalization. These findings support a future normalized builder dry run, provided raw fields and validation flags remain available and the resulting records are explicitly described as individual license records—not facility employment assignments. The proposed contract is documented in `docs/ct_nursing_home_administrator_roster_data_contract.md`; no runtime file was created in this phase.

## Reproduction

```text
python -m py_compile scripts/validate_ct_nursing_home_administrator_roster.py
python scripts/validate_ct_nursing_home_administrator_roster.py
python scripts/validate_ct_nursing_home_administrator_roster.py --verbose
```

The validator uses only the Python standard library, reads the ignored CSV without modifying it, contacts no external service, writes no runtime JSON, and fails if required source columns are absent.

## Recommended next phase

Phase 11E.2: Connecticut Administrator Roster Normalized Builder Dry Run and Facility-Affiliation Source Inventory.

That phase should create a testing-preview roster, inventory official sources that may identify current facility administrators, and compare CMS Provider Information, Care Compare, Connecticut DPH facility records, and other official state sources. It should continue to separate license validation from employment or facility affiliation and avoid public UI wiring until the relationship source and matching method are validated.
