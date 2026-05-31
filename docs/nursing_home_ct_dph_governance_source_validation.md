# CT DPH Governance Source Validation

Phase 10B.1 planning-only validation. No live application files, staffing calculations, generated export, or public UI behavior were changed.

## Files Reviewed

| File | Rows | Columns | Key fields | Purpose assessment |
|---|---:|---:|---|---|
| `Chronic_and_Convalescent_Nursing_Home.csv` | 189 | 10 | `LICENSE NO.`, facility name, address, city, ZIP, status, effective/expiration dates | Current CT DPH chronic and convalescent nursing home facility master. |
| `Nursing_Home_Management_History.csv` | 2,538 | 11 | `License No`, position, name, professional license, start date, termination date, relationship status | Facility leadership/role relationship history by CT DPH facility license. |
| `Nursing_Home_Administrator.csv` | 581 | 14 | administrator license number, first/last name, status, reason, issue/expiration dates | Current administrator license registry, useful for validation but not complete history. |
| `Nursing_Home_Management_Company.csv` | 24 | 10 | management company name, license number, address, status, effective/expiration dates | Licensed management-company registry. |
| `Nursing_Home_Management_Company (1).csv` | 24 | 10 | same as above | Byte-for-byte duplicate of `Nursing_Home_Management_Company.csv`; do not treat as separate source. |

## Facility Master

`Chronic_and_Convalescent_Nursing_Home.csv` appears suitable as the Connecticut-side facility master for future CT DPH integration.

- Row count: 189
- Unique normalized license numbers: 189
- Status values: 189 `ACTIVE`
- Effective date range: April 1, 2008 to February 1, 2026
- Expiration date range: December 31, 2025 to June 30, 2028
- Duplicate exact rows: 0

It can support a future `ct_facilities` table keyed by CT facility license number. It cannot by itself provide CMS CCN, historical operator-name changes, leadership role periods, or management-company assignments.

## Management History

`Nursing_Home_Management_History.csv` is the strongest newly discovered file for future governance timeline work.

| Position | Rows | Facilities represented |
|---|---:|---:|
| Administrator | 874 | 189 |
| Director of Nurses | 1,226 | 189 |
| Medical Director | 431 | 188 |
| President | 1 | 1 |
| Key Employee | 2 | 2 |
| Manager | 1 | 1 |
| Owner | 1 | 1 |
| Director | 2 | 2 |

Additional profile:

- Unique normalized facility licenses: 189
- Relationship statuses: 1,942 `Inactive`, 596 `active`
- Earliest date found: January 1, 1997
- Latest date found: December 31, 2026
- Rows with start date: 2,151
- Rows with termination date: 1,597
- Rows with both dates: 1,347
- Open-ended rows: 941
- Rows with termination date but no start date: 250
- Blank professional-license rows: 315
- TEMP-license rows: 141
- Facilities with usable Administrator history: 189
- Facilities with usable DON history: 189
- Facilities with usable Medical Director history: 188

The file can support future leadership-period modeling after cleaning. It cannot prove why staffing changed, and it cannot join to CMS PBJ data until a DPH-license-to-CMS-CCN crosswalk is validated.

## Facility Master To Management-History Join

Use CT facility license as the state-side join key.

Raw formats differ:

- Facility master: simple numeric values, such as `2525`
- Management history: prefixed values, such as `CCNH.000119C`

Recommended normalization:

1. Preserve the raw license value.
2. Extract digits from the raw value.
3. Remove leading zeroes.
4. Store the result as `state_facility_license_id`.

Join result:

- Facility master normalized licenses: 189
- Management history normalized licenses: 189
- Matched licenses: 189
- Unmatched facility-master rows: 0
- Unmatched management-history rows: 0

Name differences exist but license matching resolves them. Examples:

| License | Facility master name | Management history name |
|---|---|---|
| `1023` | CONNECTICUT BAPTIST HOMES, INC. | CONNECTICUT BAPTIST HOME INC. |
| `1057` | WEST HARTFORD HEALTH AND REHABILITATION CENTER | WEST HARTFORD HEALTH & REHABILITATION CENTER |
| `2024` | GLADEVIEW HEALTH CARE CTR | GLADEVIEW HEALTH CARE CENTER |

Do not rely on name-only matching when a license number is available.

## Administrator Registry Validation

`Nursing_Home_Administrator.csv` appears to be a current registry snapshot, not a complete historical archive.

- Row count: 581
- Unique normalized administrator licenses: 581
- Status values: 581 `ACTIVE`
- Issue date range: January 1, 1901 to April 14, 2026
- Expiration date range: February 28, 2026 to July 31, 2029
- Management-history Administrator rows: 874
- Administrator history rows with normalized non-TEMP license: 760
- History Administrator license matches to current registry: 663
- History Administrator license nonmatches: 97

Use normalized professional-license matching as the preferred validation method. Nonmatches should not invalidate management-history records because the administrator registry is current-state oriented and may omit expired, inactive, out-of-state, older, or otherwise non-current licenses.

Name matching should be secondary and manual-review oriented only.

## Management Company Registry

`Nursing_Home_Management_Company.csv` and `Nursing_Home_Management_Company (1).csv` are byte-for-byte identical. Use `Nursing_Home_Management_Company.csv` as the canonical copy.

Profile:

- Row count: 24
- Unique normalized management-company license numbers: 24
- Status values: 24 `ACTIVE`
- State counts: 14 CT, 4 MA, 4 NJ, 1 IA, 1 NC
- Effective date range: September 24, 2009 to November 26, 2025
- Expiration date range: September 30, 2026 to June 30, 2029

The file identifies licensed management companies. It does not contain explicit facility-to-company assignment fields. It cannot support a management-company explorer, facility management-company period table, or staffing comparison by management company without another assignment-period source.

Potential assignment sources to investigate later:

- CT DPH facility-management-company relationship or change files
- CT DSS cost reports and related-party or management-fee disclosures
- CMS detailed ownership/management fields
- CMS Change of Ownership and CHOW owner information
- Other verified public state records

## Data Quality Notes For Future Cleaning

- Treat missing start dates with termination dates as historical role-holder evidence but usually not usable for tenure-length calculations.
- Treat missing termination dates as open-ended/current only through the source snapshot date; do not convert the snapshot date into a confirmed end date.
- TEMP licenses are common enough to require explicit normalization and continuity rules.
- Multiple active same-facility same-role cases exist and often appear to be same-person duplicate/licensing artifacts. Flag, do not publish, until cleaned.
- Preserve raw records and build cleaned analytical periods as a separate layer.
- Avoid false merges of people with similar names; professional license numbers should control when available.

## Planning Conclusion

These CT DPH files are promising for a future governance timeline layer. The immediate enabling project is a CT DPH facility-license to CMS CCN crosswalk. After that, a facility-level governance timeline proof of concept can align PBJ staffing quarters with Administrator and Director of Nurses role periods.
