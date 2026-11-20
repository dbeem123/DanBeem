#!/usr/bin/env python3
"""Small client for the danbeem.xyz Connecticut Nursing Home Reporting API.

Meant for the self-hosted Hermes agent (and any script) that wants to read the
public, static JSON API without a browser. It only fetches files; all report
logic lives in scripts/build_reporting_api.py and the generated api/v1 files.

Standard library only. Examples:

  python3 scripts/reporting_api_client.py search "cherry brook"
  python3 scripts/reporting_api_client.py profile 075396
  python3 scripts/reporting_api_client.py report related-party-screening 075396
  python3 scripts/reporting_api_client.py summary facility-comprehensive 075396
  python3 scripts/reporting_api_client.py company mc-apple-health-care-inc
  python3 scripts/reporting_api_client.py --local api summary staffing-analysis 075396

Use --base URL to point at another host, or --local DIR to read a local api/
folder (the directory that contains v1/). Output is JSON except for `summary`.

Evidence rules: possible_association is not evidence of ownership, control or
conflict of interest, and "not in these datasets" is not "no problem".
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "https://danbeem.xyz"
REPORT_TYPES = ["facility-comprehensive", "ownership-network", "staffing-analysis",
                "financial-transparency", "regulatory-history", "related-party-screening",
                "management-company-portfolio"]
SUFFIXES = {"INC", "LLC", "LP", "LLP", "CORP", "CO", "LTD", "THE"}


def fetch(path, base, local):
    """Return parsed JSON for a path like /api/v1/index.json."""
    if local:
        rel = path[len("/api/"):] if path.startswith("/api/") else path.lstrip("/")
        fp = os.path.join(local, rel)
        try:
            with open(fp, encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            sys.exit("Not found (unknown id?): %s" % fp)
    url = base.rstrip("/") + path
    req = urllib.request.Request(url, headers={"User-Agent": "reporting-api-client/1.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            sys.exit("Not found (unknown id?): %s" % url)
        sys.exit("HTTP %s for %s" % (exc.code, url))
    except urllib.error.URLError as exc:
        sys.exit("Network error for %s: %s" % (url, exc.reason))


def normalize(text):
    """Normalize like the search index `key`: upper case, no punctuation, no INC/LLC style suffixes."""
    words = re.sub(r"[^A-Z0-9]+", " ", text.upper()).split()
    return " ".join(w for w in words if w not in SUFFIXES)


def check_ccn(ccn):
    if not re.fullmatch(r"[0-9A-Z]{6}", ccn):
        sys.exit("CCN must be 6 characters (digits/capitals), e.g. 075396")
    return ccn


def cmd_search(a):
    q = normalize(a.name)
    idx = fetch("/api/v1/search-index.json", a.base, a.local)
    hits = [e for e in idx["entries"] if q and q in e.get("key", "")]
    if not hits:
        print("Not in these datasets: no search-index entry matches %r." % a.name)
        return
    for e in hits[: a.limit]:
        print("%-28s %-12s %s  ccns=%s" % (e["type"], e["id"], e["name"], ",".join(e.get("ccns", []))))
    if len(hits) > a.limit:
        print("... %d more matches (use --limit)" % (len(hits) - a.limit))


def cmd_profile(a):
    print(json.dumps(fetch("/api/v1/facilities/%s/profile.json" % check_ccn(a.ccn), a.base, a.local), indent=2))


def cmd_report(a):
    print(json.dumps(load_report(a), indent=2))


def load_report(a):
    if a.type == "management-company-portfolio":
        return fetch("/api/v1/reports/management-company-portfolio/%s.json" % a.id, a.base, a.local)
    return fetch("/api/v1/reports/%s/%s.json" % (a.type, check_ccn(a.id)), a.base, a.local)


def cmd_company(a):
    print(json.dumps(fetch("/api/v1/management-companies/%s.json" % a.id, a.base, a.local), indent=2))


def cmd_summary(a):
    r = load_report(a)
    subj = r["subject"]
    print("%s: %s (%s)" % (r["report_type"], subj.get("facility_name") or subj.get("company_name"),
                           subj.get("ccn") or subj.get("company_id")))
    print("generated_at %s" % r["generated_at"])
    print("\nExecutive summary")
    for item in r["executive_summary"]:
        print("- [%s] %s" % (item["kind"], item["text"]))
    print("\nFindings")
    for f in r["findings"]:
        ev = f["evidence"][0] if f["evidence"] else {}
        src = "%s, %s, %s" % (ev.get("dataset", "?"), ev.get("reporting_period") or "period n/a",
                              ev.get("record_id", "?"))
        extra = " [formula: %s]" % f["formula"] if f.get("formula") else ""
        print("[%s] %s (source: %s)%s" % (f["kind"], f["statement"], src, extra))
    if r["missing_data"]:
        print("\nMissing data")
        for m in r["missing_data"]:
            print("- %s: %s" % (m["field"], m["reason"]))
    print("\nLimitations")
    for line in r["limitations"]:
        print("- %s" % line)
    print("\nNote: possible_association is not evidence of ownership, control or conflict of interest.")


def main(argv=None):
    p = argparse.ArgumentParser(description="Client for the danbeem.xyz CT Nursing Home Reporting API.")
    p.add_argument("--base", default=DEFAULT_BASE, help="API host (default %s)" % DEFAULT_BASE)
    p.add_argument("--local", metavar="DIR", help="read from a local api/ folder instead of the network")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="search facilities, companies and related-party names")
    s.add_argument("name")
    s.add_argument("--limit", type=int, default=25)
    s.set_defaults(fn=cmd_search)
    s = sub.add_parser("profile", help="facility profile JSON")
    s.add_argument("ccn")
    s.set_defaults(fn=cmd_profile)
    s = sub.add_parser("report", help="full report JSON")
    s.add_argument("type", choices=REPORT_TYPES)
    s.add_argument("id", metavar="CCN", help="CCN (or company id for management-company-portfolio)")
    s.set_defaults(fn=cmd_report)
    s = sub.add_parser("company", help="management company JSON")
    s.add_argument("id")
    s.set_defaults(fn=cmd_company)
    s = sub.add_parser("summary", help="executive summary and findings as text")
    s.add_argument("type", choices=REPORT_TYPES)
    s.add_argument("id", metavar="CCN", help="CCN (or company id for management-company-portfolio)")
    s.set_defaults(fn=cmd_summary)
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
