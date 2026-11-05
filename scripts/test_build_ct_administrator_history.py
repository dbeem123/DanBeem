"""Offline tests use fabricated identities and temporary CSVs only."""
import csv
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import build_ct_administrator_history as history
import fetch_ct_administrator_license_status as intake


def facility(number="10", name="EXAMPLE GARDENS", street="1 SAMPLE RD"):
    return {"license_raw": number, "state_facility_license_id": number,
            "name": name, "address": street, "city": "EXAMPLETOWN", "zip": "06000",
            "status": "ACTIVE", "effective_date": "", "expiration_date": ""}


def cms(number="075001", name="EXAMPLE GARDENS", street="1 SAMPLE RD"):
    return {"ccn": number, "name": name, "address": street, "city": "EXAMPLETOWN", "zip": "06000"}


def role(row=2, license_number="NHA.00050", name="EXAMPLE PERSON", facility_number="CCNH.00010C",
         start="01/01/2020", end="", status="active", position="Administrator"):
    return {"source_row": row, "License No": facility_number, "Position": position,
            "Name": name, "License": license_number, "Start Date": start,
            "TerminationDate": end, "Relationship status": status}


def registry(number="000050", first="Example", last="Person", status="ACTIVE"):
    return {"LICENSE NO.": number, "FIRST NAME": first, "LAST NAME": last, "STATUS": status,
            "ISSUE DATE": "01/01/1990", "EXPIRATION DATE": "12/31/2027"}


def public(records=None):
    return {"schema_version": "ct-nha-license-crosscheck-1.0", "where": "credentialtype = '36'",
            "selected_fields": list(intake.FIELDS), "retrieved_at": "2026-11-04T12:00:00+00:00",
            "records": records or [{"name": "EXAMPLE PERSON", "credentialnumber": "50", "status": "EXPIRED",
                                     "issuedate": "1990-01-01T00:00:00.000",
                                     "expirationdate": "2026-01-01T00:00:00.000"}]}


def build(rows=None, registry_rows=None, public_data=None, facilities=None, cms_rows=None, decisions=None):
    return history.build_review(
        rows if rows is not None else [role()], registry_rows if registry_rows is not None else [registry()],
        facilities or [facility()], cms_rows or [cms()], public_data, [], "2026-05-22", decisions,
    )


class IdentityAndDates(unittest.TestCase):
    def test_current_credential_prefix_joins_registry_and_public(self):
        result = build([role(license_number="36.000050")], public_data=public())
        person = result["people"][0]
        self.assertEqual(person["id"], "nha-50")
        self.assertEqual(person["roles"][0]["license_raw"], "36.000050")
        self.assertEqual(result["summary"]["missing_registry_roles"], 0)
        self.assertEqual(person["license_status"], "EXPIRED")

    def test_type_only_and_other_credential_types_stay_unlinked(self):
        result = build([role(license_number="36"), role(3, "99.000050")])
        self.assertEqual(result["people"], [])
        self.assertEqual(len(result["unlinked_roles"]), 2)
        self.assertIn("ambiguous_type_only_license", result["unlinked_roles"][0]["flags"])
        self.assertIn("unsupported_credential_type", result["unlinked_roles"][1]["flags"])

    def test_current_compact_dates_are_unambiguous(self):
        result = build([role(start="20200131", end="20211201", status="Inactive")])
        r = result["people"][0]["roles"][0]
        self.assertEqual(r["start"], "2020-01-31")
        self.assertEqual(r["end"], "2021-12-01")

    def test_invalid_compact_date_is_flagged(self):
        result = build([role(start="20260230")])
        self.assertIn("invalid_start_date", result["people"][0]["roles"][0]["flags"])

    def test_license_not_name_controls_identity(self):
        result = build([role(), role(3, "00051")], [registry(), registry("00051")])
        self.assertEqual([p["id"] for p in result["people"]], ["nha-50", "nha-51"])
        self.assertEqual(len({p["name"] for p in result["people"]}), 1)

    def test_format_normalization_preserves_raw(self):
        result = build([role(license_number='="000050"', name="  EXAMPLE   PERSON  ")])
        p = result["people"][0]
        self.assertEqual(p["license_number"], "50")
        self.assertEqual(p["name"], "Example Person")
        self.assertEqual(p["roles"][0]["license_raw"], '="000050"')
        self.assertEqual(p["roles"][0]["facility_license"], "10")

    def test_name_variants_are_reviewed_not_discarded(self):
        result = build([role(), role(3, name="EXAMPLE FORMERNAME")])
        self.assertEqual(len(result["people"]), 1)
        self.assertIn("name_variation_review", result["people"][0]["flags"])
        self.assertEqual(len(result["people"][0]["roles"]), 2)

    def test_temp_and_blank_roles_do_not_merge(self):
        result = build([role(), role(3, "temp 50"), role(4, ""), role(5, "")])
        self.assertEqual(len(result["people"]), 1)
        self.assertEqual(len(result["people"][0]["roles"]), 1)
        self.assertEqual(len(result["unlinked_roles"]), 3)
        self.assertTrue(result["unlinked_roles"][0]["temporary"])
        self.assertEqual(result["summary"]["temporary_roles"], 1)

    def test_non_administrators_are_excluded(self):
        result = build([role(), role(3, position="Director of Nurses"), role(4, position="Medical Director")])
        self.assertEqual(result["summary"]["administrator_roles"], 1)
        self.assertEqual(result["summary"]["excluded_other_positions"], 2)

    def test_missing_dates_are_not_invented(self):
        result = build([role(start="", end="01/01/2021", status="Inactive"),
                        role(3, start="", status="Inactive"), role(4)])
        roles = {r["id"]: r for r in result["people"][0]["roles"]}
        self.assertIsNone(roles["dph-admin-row-2"]["start"])
        self.assertIn("end_without_start", roles["dph-admin-row-2"]["flags"])
        self.assertFalse(roles["dph-admin-row-3"]["open"])
        self.assertIn("end_not_recorded", roles["dph-admin-row-3"]["flags"])
        self.assertTrue(roles["dph-admin-row-4"]["open"])
        self.assertIn("end not recorded", history.markdown(result))
        self.assertNotIn("to present", history.markdown(result))

    def test_invalid_end_is_not_an_open_role(self):
        result = build([role(end="not-a-date")])
        r = result["people"][0]["roles"][0]
        self.assertIn("invalid_end_date", r["flags"])
        self.assertFalse(r["open"])
        self.assertNotIn("open_as_of_source", r["flags"])

    def test_future_and_reversed_dates_flagged(self):
        result = build([role(start="01/01/2028", end="01/01/2027")])
        flags = result["people"][0]["roles"][0]["flags"]
        self.assertIn("date_after_snapshot", flags)
        self.assertIn("end_before_start", flags)

    def test_same_license_overlaps_across_facilities(self):
        result = build([role(), role(3, facility_number="11")], facilities=[facility(), facility("11", "OTHER GARDENS", "2 OTHER RD")],
                       cms_rows=[cms(), cms("075002", "OTHER GARDENS", "2 OTHER RD")])
        self.assertEqual(result["summary"]["overlap_pairs"], 1)
        self.assertIn("overlapping_reported_dates", result["people"][0]["roles"][0]["flags"])

    def test_unknown_start_not_counted_as_proven_overlap(self):
        result = build([role(), role(3, facility_number="11", start="")],
                       facilities=[facility(), facility("11", "OTHER GARDENS", "2 OTHER RD")])
        self.assertEqual(result["summary"]["overlap_pairs"], 0)

    def test_multiple_active_records_flagged(self):
        result = build([role(), role(3, "00051")])
        self.assertEqual(result["summary"]["multiple_active_facilities"], 1)

    def test_registry_nonmatch_can_be_confirmed_publicly(self):
        result = build(registry_rows=[], public_data=public())
        self.assertEqual(result["summary"]["missing_registry_roles"], 1)
        self.assertEqual(result["unmatched_registry_licenses"][0]["public_crosscheck"], "found")
        self.assertEqual(result["people"][0]["license_status"], "EXPIRED")

    def test_status_conflict_preserves_both_snapshots(self):
        result = build(public_data=public())
        self.assertIn("license_status_differs_by_snapshot", result["people"][0]["flags"])
        self.assertEqual(len(result["people"][0]["license_observations"]), 2)

    def test_duplicate_public_license_not_arbitrarily_chosen(self):
        data = public()
        data["records"].append(dict(data["records"][0], status="ACTIVE"))
        result = build(public_data=data)
        self.assertIsNone(result["people"][0]["license_status"])
        self.assertIn("duplicate_license_observations", result["people"][0]["flags"])

    def test_stale_public_snapshot_refuses(self):
        data = public()
        data["retrieved_at"] = "2025-01-01T00:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "predates"):
            build(public_data=data)

    def test_license_source_date_is_explicit(self):
        self.assertEqual(build()["people"][0]["license_as_of"], "2026-05-22")
        self.assertEqual(build(public_data=public())["people"][0]["license_as_of"], "2026-11-04")

    def test_unknown_license_not_invalidated(self):
        result = build(registry_rows=[])
        self.assertIsNone(result["people"][0]["license_status"])
        self.assertEqual(result["unmatched_registry_licenses"][0]["public_crosscheck"], "not_checked")

    def test_missing_facility_refuses(self):
        with self.assertRaisesRegex(ValueError, "missing facility"):
            build([role(facility_number="999")])


class CrosswalkRules(unittest.TestCase):
    def test_reuses_existing_builder_without_leaking_business_locations(self):
        with patch.object(history.crosswalk, "build", wraps=history.crosswalk.build) as builder:
            result = build()
        builder.assert_called_once()
        self.assertEqual(result["crosswalk_review"][0]["candidate_ccn"], "075001")
        self.assertEqual(result["crosswalk_review"][0]["match_tier"], "auto_high")
        self.assertIsNone(result["people"][0]["roles"][0]["ccn"])
        history.assert_privacy(result)
        self.assertNotIn("SAMPLE RD", json.dumps(result))

    def test_only_reviewed_match_attached(self):
        result = build(decisions=[{"facility_license": "10", "ccn": "075001",
                                   "decision": "accepted", "note": "Reviewed official facility identity."}])
        self.assertEqual(result["people"][0]["roles"][0]["ccn"], "075001")

    def test_reject_stale_decision(self):
        with self.assertRaisesRegex(ValueError, "does not match"):
            build(decisions=[{"facility_license": "10", "ccn": "075002", "decision": "accepted", "note": "Reviewed"}])

    def test_note_required(self):
        with self.assertRaisesRegex(ValueError, "Invalid"):
            build(decisions=[{"facility_license": "10", "ccn": "075001", "decision": "accepted", "note": ""}])

    def test_weak_match_cannot_be_accepted(self):
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            build(cms_rows=[cms(name="UNRELATED", street="9 UNKNOWN RD")],
                  decisions=[{"facility_license": "10", "ccn": None, "decision": "accepted", "note": "Guess"}])

    def test_rejected_match_stays_unattached(self):
        result = build(decisions=[{"facility_license": "10", "ccn": "075001", "decision": "rejected", "note": "Not verified"}])
        self.assertIsNone(result["people"][0]["roles"][0]["ccn"])


class IntakeAndPrivacy(unittest.TestCase):
    def test_full_csv_pipeline_readback(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(history, "ROOT", Path(tmp)):
            root = Path(tmp)
            source = root / "source_data/ct_dph"
            source.mkdir(parents=True)
            (root / "data").mkdir()
            inputs = {
                "history": [role(), role(3, position="Director of Nurses")],
                "registry": [dict(registry(), ADDRESS1="123 EXAMPLE ROAD EXAMPLETOWN CT 06000")],
                "facilities": [{"LICENSE NO.": "10", "FACILITY NAME": "EXAMPLE GARDENS",
                                "ADDRESS": "1 SAMPLE RD", "CITY": "EXAMPLETOWN", "ZIP": "06000"}],
            }
            profile = {"source_files_profiled": []}
            for name, rows in inputs.items():
                path = source / (name + ".csv")
                with path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
                profile["source_files_profiled"].append({
                    "source_key": history.SOURCE_KEYS[name], "sha256": history.file_hash(path),
                })
            (root / "data/ct_dph_source_profile.json").write_text(json.dumps(profile), encoding="utf-8")
            (root / "data/nursing_home_staffing_ct.json").write_text(json.dumps({"facilities": [
                {"ccn": "075001", "provider_name": "EXAMPLE GARDENS", "address": "1 SAMPLE RD",
                 "city": "EXAMPLETOWN", "zip_code": "06000"}]}), encoding="utf-8")
            with patch("sys.argv", ["builder", "--source-as-of", "2026-05-22"]), contextlib.redirect_stdout(io.StringIO()):
                history.main()
            output = root / "data/testing/ct_administrator_history_review.json"
            result = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["summary"]["administrator_roles"], 1)
            self.assertEqual(result["summary"]["excluded_other_positions"], 1)
            self.assertEqual(result["crosswalk_review"][0]["candidate_ccn"], "075001")
            self.assertIsNone(result["people"][0]["roles"][0]["ccn"])
            history.assert_privacy(result)
            self.assertTrue(output.with_suffix(".md").is_file())
            self.assertFalse((root / "data/ct_nursing_home_administrators.json").exists())

    def test_source_hash_not_filename_controls_intake(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            profile = {"source_files_profiled": []}
            for idx, (label, key) in enumerate(history.SOURCE_KEYS.items()):
                path = root / f"renamed-{idx}.csv"
                path.write_text(label, encoding="utf-8")
                profile["source_files_profiled"].append({"source_key": key, "sha256": history.file_hash(path)})
            paths, _ = history.verified_inputs(root, profile)
            self.assertEqual(len(paths), 3)
            paths["history"].write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash-verified input missing"):
                history.verified_inputs(root, profile)

    def test_sensitive_columns_dropped_immediately(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic.csv"
            row = dict(registry(), ADDRESS1="123 EXAMPLE ROAD EXAMPLETOWN CT 06000", ADDRESS2="Unit 2",
                       CITY="EXAMPLETOWN", STATE="CT", ZIP="06000", SALARY="12345", EMAIL="fake@example.invalid")
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(row))
                writer.writeheader()
                writer.writerow(row)
            projected = history.read_projected_csv(path, history.REGISTRY_FIELDS)
            self.assertEqual(set(projected[0]), set(history.REGISTRY_FIELDS) | {"source_row"})
            result = build(registry_rows=projected)
            self.assertNotIn("123 EXAMPLE", json.dumps(result))
            self.assertNotIn("fake@example", json.dumps(result))
            history.assert_privacy(result)

    def test_required_and_duplicate_headers_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.csv"
            path.write_text("Name,Name\nExample,Example\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                history.read_projected_csv(path, ("Name",))
            with self.assertRaisesRegex(ValueError, "Missing"):
                history.read_projected_csv(path, history.REGISTRY_FIELDS)

    def test_privacy_checks_fields_and_values(self):
        for item in ({"ADDRESS1": "x"}, {"zip_code": "06000"}, {"salary": 10},
                     {"phone_number": "x"}, {"name": "123 EXAMPLE ROAD EXAMPLETOWN CT 06000"},
                     {"note": "ZIP: 06000"}, {"name": "fake@example.invalid"},
                     {"note": "203-555-0101"}):
            with self.subTest(item=item), self.assertRaises(ValueError):
                history.assert_privacy(item)
        history.assert_privacy({"license_number": "12345", "ccn": "075001", "start": "2020-01-01"})

    def test_no_public_output_or_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = build()
            with self.assertRaisesRegex(ValueError, "ignored"):
                history.write_review(result, root / "data/public.json", root)
            path = root / "data/testing/review.json"
            history.write_review(result, path, root)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["publication_status"], "private_review_required")
            with self.assertRaisesRegex(ValueError, "already exist"):
                history.write_review(result, path, root)

    def test_deterministic_twenty_person_sample(self):
        rows = [role(i + 2, str(i + 1), name=f"EXAMPLE PERSON {i}") for i in range(30)]
        a, b = build(rows), build(rows)
        self.assertEqual(len(a["sample_people_ids"]), 20)
        self.assertEqual(a["sample_people_ids"], b["sample_people_ids"])

    def test_raw_person_fields_rejected_even_in_crosscheck(self):
        data = public()
        data["records"][0]["address"] = "ignored?"
        with self.assertRaisesRegex(ValueError, "extra fields"):
            build(public_data=data)

    def test_output_path_cannot_escape_private_review_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "ignored"):
                history.write_review(build(), root / "data/testing/../public.json", root)


class PublicIntake(unittest.TestCase):
    def test_only_five_fields_and_bounded_pagination(self):
        calls = []
        def opener(url, timeout):
            query = parse_qs(urlsplit(url).query)
            self.assertEqual(query["$select"], [",".join(intake.FIELDS)])
            self.assertEqual(query["$where"], ["credentialtype = '36'"])
            self.assertEqual(timeout, 30)
            calls.append(query)
            rows = [{"name": "EXAMPLE", "credentialnumber": "50", "status": "ACTIVE"}]
            if query["$offset"] == ["1"]:
                rows = []
            return io.BytesIO(json.dumps(rows).encode())
        with patch.object(intake, "PAGE_SIZE", 1):
            result = intake.fetch(opener)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(result["records"]), 1)

    def test_unnumbered_applications_counted_not_name_linked(self):
        rows = [{"name": "EXAMPLE", "credentialnumber": "50"}, {"name": "EXAMPLE"}]
        result = intake.fetch(lambda *a, **k: io.BytesIO(json.dumps(rows).encode()))
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(result["unnumbered_records_excluded"], 1)

    def test_unrequested_field_refuses(self):
        with self.assertRaisesRegex(ValueError, "unrequested"):
            intake.fetch(lambda *a, **k: io.BytesIO(b'[{"credentialnumber":"50","address":"private"}]'))

    def test_empty_or_nonrecord_response_refuses(self):
        for body in (b'[]', b'{}', b'["not a row"]'):
            with self.subTest(body=body), self.assertRaises(ValueError):
                intake.fetch(lambda *a, **k: io.BytesIO(body))

    def test_intake_has_no_network_retry(self):
        calls = []
        def failing_opener(*args, **kwargs):
            calls.append(args)
            raise TimeoutError("dummy")
        with self.assertRaises(TimeoutError):
            intake.fetch(failing_opener)
        self.assertEqual(len(calls), 1)

    def test_bounded_pagination_rejects_truncation(self):
        with patch.object(intake, "PAGE_SIZE", 1), patch.object(intake, "MAX_PAGES", 2):
            with self.assertRaisesRegex(ValueError, "pagination"):
                intake.fetch(lambda *a, **k: io.BytesIO(b'[{"credentialnumber":"50"}]'))

    def test_snapshot_stays_private_and_immutable(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(intake, "ROOT", Path(tmp)):
            dest = Path(tmp) / "source_data/ct_dph/test.json"
            result = public()
            intake.save_snapshot(result, dest)
            with self.assertRaises(FileExistsError):
                intake.save_snapshot(result, dest)
            with self.assertRaisesRegex(ValueError, "ignored"):
                intake.save_snapshot(result, Path(tmp) / "data/public.json")


if __name__ == "__main__":
    unittest.main()
