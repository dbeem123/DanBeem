"""Order CMS monthly files by the release month in their name (NH_HealthCitations_Oct2026.csv -> 2026-10).

Alphabetical order is wrong for month names (Dec2026 sorts before Oct2026), so builders and validators use
this key. Files without a month-year suffix sort first, then by name.
"""
import re

MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def release_key(path):
    m = re.search(r"_([A-Za-z]{3})[A-Za-z]*(\d{4})\.csv$", str(path))
    if m and m.group(1).lower() in MONTHS:
        return (int(m.group(2)), MONTHS[m.group(1).lower()], str(path))
    return (0, 0, str(path))
