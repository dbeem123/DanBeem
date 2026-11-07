"""Read the cost report period (start and end dates) from the first pages of a DSS annual report.

Most reports cover October 1 to September 30, but a home that changes owner, opens or closes files
for part of a year. Two places carry the dates: the certification on page 1 ("for the cost report
period beginning October 1, 2024 and ending June 14, 2025") and the "Period Covered: From To"
box on page 2.
"""
import datetime as dt
import re

MONTHS = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"])}
MON = r"([A-Z][a-z]{2,9})\s+(\d{1,2}),?\s*(\d{4})"
NUM = r"(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{2,4})"


def _month(word):
    w = word.lower()
    for name, n in MONTHS.items():
        # tolerate OCR/typing slips like "Septembe" or "Septembee"
        if w == name or (len(w) >= 5 and name.startswith(w[:5])):
            return n
    return None


def _date(y, m, d):
    y = int(y)
    if y < 100:
        y += 2000
    try:
        return dt.date(y, int(m), int(d))
    except ValueError:
        return None


def read_period(text, cost_year):
    """Return (start, end) as dates, or (None, None) if the dates can't be read or don't fit the cost year.
    The period must end within the cost year (October 1 of the prior year to September 30, allowing a
    few days' slip) and last between 1 and 367 days."""
    head = re.sub(r"\s+", " ", text[:15000])
    found = []
    m = re.search(r"period beginning\s+" + MON + r"\s+and\s+ending\s+" + MON, head, re.I)
    if m:
        a, b = _month(m.group(1)), _month(m.group(4))
        if a and b:
            found.append((_date(m.group(3), a, m.group(2)), _date(m.group(6), b, m.group(5))))
    m = re.search(r"Period Covered.{0,300}?" + NUM + r"\s+" + NUM, re.sub(r"[ \t]+", " ", text[:15000]), re.S)
    if m:
        found.append((_date(m.group(3), m.group(1), m.group(2)), _date(m.group(6), m.group(4), m.group(5))))
    lo, hi = dt.date(cost_year - 1, 9, 25), dt.date(cost_year, 10, 5)
    for start, end in found:
        if start and end and lo <= end <= hi and 1 <= (end - start).days <= 367:
            return start, end
    return None, None
