import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_nursing_home_staffing_ct as current_builder
import build_nursing_home_staffing_history_ct as history_builder


class NursingHomeStaffingHistoryBuilderTests(unittest.TestCase):
    def test_history_metadata_uses_stable_source_identifiers(self):
        with tempfile.TemporaryDirectory(prefix="history-source-") as source_temp:
            source_root = Path(source_temp) / "pbj"
            source_root.mkdir()
            source_path = source_root / "PBJ_Daily_Nurse_Staffing_Q1_2026.csv"
            row = {
                "STATE": "CT",
                "PROVNUM": "075001",
                "PROVNAME": "Fixture Facility",
                "CITY": "Hartford",
                "WorkDate": "2026-01-01",
                "MDScensus": "10",
            }
            row.update({column: "1" for column in current_builder.NURSE_HOUR_COLUMNS})
            row.update({column: "0" for column in current_builder.CONTRACT_HOUR_COLUMNS})
            with source_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        *current_builder.REQUIRED_CANONICAL_COLUMNS,
                        "WorkDate",
                        *current_builder.CONTRACT_HOUR_COLUMNS,
                    ],
                )
                writer.writeheader()
                writer.writerow(row)

            with tempfile.TemporaryDirectory(prefix="history-staging-") as staging_temp:
                staging_root = Path(staging_temp)
                inventory = history_builder.stage_quarter_sources(source_root, staging_root, ["2026Q1"])
                preview_result = history_builder.build_history_export(
                    staging_root,
                    Path("data/testing/nursing_home_staffing_history_ct_preview.json"),
                    inventory,
                    "CMS PBJ test source",
                    "2026-09-24",
                )
                production_result = history_builder.build_history_export(
                    staging_root,
                    Path("data/nursing_home_staffing_history_ct.json"),
                    inventory,
                    "CMS PBJ test source",
                    "2026-09-24",
                )

            expected_source = "source_data/pbj/PBJ_Daily_Nurse_Staffing_Q1_2026.csv"
            self.assertEqual(preview_result["data_quality"]["output_path"], "data/testing/nursing_home_staffing_history_ct_preview.json")
            self.assertEqual(production_result["data_quality"]["output_path"], "data/nursing_home_staffing_history_ct.json")
            self.assertEqual(production_result["data_quality"]["input_files"], [expected_source])
            self.assertEqual(production_result["pbj_source_inventory"][0]["source_file"], expected_source)
            self.assertNotIn("staged_csv", production_result["pbj_source_inventory"][0])

            serialized = json.dumps(production_result)
            self.assertNotIn(source_temp, serialized)
            self.assertNotIn(staging_temp, serialized)
            self.assertNotRegex(serialized, r"[A-Za-z]:[/\\]")
            self.assertNotRegex(serialized, r"/(?:Users|home|tmp|var/tmp)/")
            self.assertNotRegex(serialized, r'"\\\\\\\\[^\"]*"')


    def test_production_exports_have_stable_output_paths(self):
        root = Path(__file__).resolve().parents[1]
        expected_paths = {
            "nursing_home_staffing_ct.json": "data/nursing_home_staffing_ct.json",
            "nursing_home_staffing_history_ct.json": "data/nursing_home_staffing_history_ct.json",
        }
        for filename, expected_path in expected_paths.items():
            with self.subTest(filename=filename):
                serialized = (root / "data" / filename).read_text(encoding="utf-8")
                data = json.loads(serialized)
                self.assertEqual(data["data_quality"]["output_path"], expected_path)
                self.assertNotIn("data/testing", serialized.lower())
                self.assertNotRegex(serialized, r"[A-Za-z]:[/\\]")
                self.assertNotRegex(serialized, r"/(?:Users|home|tmp|var/tmp)/")


if __name__ == "__main__":
    unittest.main()
