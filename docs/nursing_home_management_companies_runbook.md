# Connecticut nursing home management companies: runbook

The Management Companies page (`staffing/tools/nursing-home-management-companies.html`) and the
Facility Explorer "Management companies" section read `data/ct_nursing_home_management_companies.json`.

## Sources
- CMS Care Compare monthly archives (`nursing-homes_YYYY-MM-DD.zip`, data.cms.gov provider data,
  nursing homes topic). Each full release contains the Nursing Home Ownership file
  (`Ownership_Download.csv` to mid-2020, then `NH_Ownership*.csv`). Some small releases (for example
  2026-08-06) contain only provider information and are skipped.
- CT DPH eLicense roster export "Nursing Home Management Company" (license number, status, dates).
- Public site data: PBJ staffing history and `data/ct_nursing_home_administrators.json`.

Keep raw archives off the repo (Daniel's copies: `X:\danbeem-data\ownership\`). All intermediate files go
in ignored `data/testing/`.

## Rebuild
```powershell
python scripts/extract_ct_ownership_orgs.py data/testing/ownership <path>\nursing-homes_*.zip
python scripts/build_ct_management_relationships.py data/testing/ownership data/testing/ct_management_relationships_<latest>.json
copy "<DPH export>.csv" data\testing\ct_dph_management_companies.csv
python scripts/build_ct_management_companies.py --relationships data/testing/ct_management_relationships_<latest>.json
python scripts/validate_ct_management_companies.py
python scripts/test_ct_management_companies.py
```
Build the administrator data first: the management build links administrators of record by CCN.

## Rules
- Only CMS rows with Owner Type "Organization" are read. Individual owners, officers and managing
  employees are dropped at read, and addresses and ZIP codes are never kept.
- Management roles: OPERATIONAL/MANAGERIAL CONTROL and CONTRACTED MANAGING EMPLOYEE.
- A relationship missing from up to two consecutive releases and then listed again is one period.
- A period starts at the association date CMS reports (the earliest, if CMS later changed it) and ends at
  the last release listing it; the next release date is shown as "ended before".
- Organization names are joined only when they differ in punctuation or "&"/"and". Different legal
  suffixes (LLC, Inc, LLP) stay separate. People and companies are never merged on a guess.
- DPH license badges need an exact name match, or a reviewed entry in
  `data/ct_management_company_aliases.json` (`cms_name`, `dph_name`, `reviewed: true`, `note`).
  DPH-licensed companies with no CMS management listing are shown with no homes.

## Possible aliases awaiting review (November 2026)
- CMS "I CARE MANAGEMENT" (5 homes) and DPH "ICARE MANAGEMENT, LLC" (license 000030).
- CMS "LEGACY LIFECARE, INC." (1 home) and DPH "LEGACY LIFECARE MANAGEMENT" (license 000059).

## Later options
- CMS began listing "ADP of the SNF" (additional disclosable parties) in 2025; some management service
  providers appear only there (for example IM Management, LLC). Not included yet.
- DSS annual cost reports (2015-2025) disclose related-party management fees.
