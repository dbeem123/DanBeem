# Daily staffing by position

Open **Staffing → Facility Explorer → Daily staffing by position**. Select a facility, quarter, date and position. The link to the day retains the selection. The CSV contains every date and published position for the selected facility and quarter. The historical facility menu also includes homes outside the current directory.

## Coverage and interpretation

The release covers 632,591 reported facility-days at 216 Connecticut homes from 2017 Q4 through 2026 Q2. It includes 32 published PBJ job categories. The existing quarterly directory and daily data use the same CMS Certification Number. Each of the 6,930 facility-quarters reconciles to the existing published nursing totals, RN, LPN and aide hours per resident day within rounding. As in the quarterly series, the calculation uses days with positive census and complete nursing hours.

Across 20,241,909 role-day records containing all three hours fields, employee plus contract hours agreed with total hours within 0.02 hours. The remaining role-days retain their source exclusions or unavailable values.

CMS employee detail begins in 2020 Q2. Of 450,885 facility-days since then, 449,810 have positive, unflagged employee detail. The other 1,075 days show unavailable headcounts. In 2026 Q2, all 15,561 reported days have worker counts across 171 homes.

Workers are counted once per facility and day across roles and contract types, and once per position when reading a position row. Only positive hours without an exclusion flag qualify. CMS job identifiers refer to positions. Employee identifiers are omitted from all site files. Reported daily hours cannot establish a shift roster, time of day, or which residents received care. Minutes per resident are total role hours times 60 divided by daily census. A zero census yields an unavailable rate.

A missing value is distinct from a reported zero. The all-positions quarter chart displays a gap if any contributing role is unavailable. Annual dietary, housekeeping and laundry expenses come from the site's matched Connecticut cost reports. Those figures are dollars per resident day for the selected fiscal period.

[CMS PBJ methodology](https://data.cms.gov/resources/payroll-based-journal-methodology) · [CMS PBJ policy and job definitions](https://www.cms.gov/medicare/quality/nursing-home-improvement/staffing-data-submission)

## Refresh and verification

Save the CMS catalog from https://data.cms.gov/data.json as catalog.json in an input cache outside the website. The fetcher selects dated releases, filters Connecticut rows, and aggregates employee detail before it writes the cache. Quarter identifiers take the form 2026Q2. Use a fresh cache when refreshing a revised CMS release.

```powershell
python scripts/fetch_ct_daily_staffing.py $cache $quarters
python scripts/build_ct_daily_staffing.py --cache $cache --nurse-root $nurseRoot --latest $latestCtNurseCsv
python -X utf8 -m unittest discover -s scripts -p 'test_*.py'
python -X utf8 scripts/check_ct_daily_staffing_browser.py
```

Set $quarters to the quarter strings in the site's PBJ source inventory, $nurseRoot to the directory containing its historical Connecticut extracts, and $latestCtNurseCsv to the refreshed 2026 Q2 CSV for this release. Use the builder's --out option for a separate candidate output. Each facility-quarter is an independent gzip file loaded on demand. The index records source endpoints, input hashes, coverage and reconciliation counts for each quarter. The site uses its local data files for browsing.
