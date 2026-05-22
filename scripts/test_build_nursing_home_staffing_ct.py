import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_nursing_home_staffing_ct as generator


PBJ_COLUMNS = [
    "STATE",
    "PROVNUM",
    "PROVNAME",
    "CITY",
    "WorkDate",
    "MDScensus",
    "Hrs_RNDON",
    "Hrs_RNadmin",
    "Hrs_RN",
    "Hrs_LPNadmin",
    "Hrs_LPN",
    "Hrs_CNA",
    "Hrs_NAtrn",
    "Hrs_MedAide",
    "Hrs_RNDON_ctr",
    "Hrs_RNadmin_ctr",
    "Hrs_RN_ctr",
    "Hrs_LPNadmin_ctr",
    "Hrs_LPN_ctr",
    "Hrs_CNA_ctr",
    "Hrs_NAtrn_ctr",
    "Hrs_MedAide_ctr",
]

PROVIDER_COLUMNS = [
    "CMS Certification Number (CCN)",
    "Provider Name",
    "Provider Address",
    "Provider City",
    "Provider State",
    "Provider Zip Code",
    "Provider Phone Number",
    "Number of Certified Beds",
    "Ownership Type",
    "Case-Mix Nurse Aide Staffing Hours per Resident per Day",
    "Case-Mix LPN Staffing Hours per Resident per Day",
    "Case-Mix RN Staffing Hours per Resident per Day",
    "Case-Mix Total Nurse Staffing Hours per Resident per Day",
    "Overall Rating",
    "Health Inspection Rating",
    "Staffing Rating",
    "RN Staffing Rating",
    "QM Rating",
    "Long-Stay QM Rating",
    "Short-Stay QM Rating",
]

SNF_ENROLLMENT_COLUMNS = [
    "ENROLLMENT STATE",
    "NPI",
    "CCN",
    "ORGANIZATION NAME",
    "DOING BUSINESS AS NAME",
    "INCORPORATION DATE",
    "INCORPORATION STATE",
    "ORGANIZATION TYPE STRUCTURE",
    "PROPRIETARY_NONPROFIT",
    "NURSING HOME PROVIDER NAME",
    "AFFILIATION ENTITY NAME",
    "AFFILIATION ENTITY ID",
    "STATE",
]

QUALITY_MEASURES_CLAIMS_COLUMNS = [
    "CMS Certification Number (CCN)",
    "Provider Name",
    "State",
    "Measure Code",
    "Measure Description",
    "Resident type",
    "Adjusted Score",
    "Observed Score",
    "Expected Score",
    "Footnote for Score",
    "Used in Quality Measure Five Star Rating",
    "Measure Period",
    "Processing Date",
]


class NursingHomeStaffingGeneratorTests(unittest.TestCase):
    def build_from_rows(self, rows, provider_rows=None, snf_rows=None, quality_measure_rows=None):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_dir = temp_path / "pbj"
            input_dir.mkdir()
            csv_path = input_dir / "pbj.csv"
            output_path = temp_path / "out.json"

            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=PBJ_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)

            provider_by_ccn = {}
            provider_quality = None
            if provider_rows is not None:
                provider_path = temp_path / "provider_info.csv"
                with provider_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=PROVIDER_COLUMNS)
                    writer.writeheader()
                    writer.writerows(provider_rows)
                provider_by_ccn, provider_quality = generator.load_provider_info(provider_path)

            snf_by_ccn = {}
            snf_quality = None
            if snf_rows is not None:
                snf_path = temp_path / "snf_enrollments.csv"
                with snf_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=SNF_ENROLLMENT_COLUMNS)
                    writer.writeheader()
                    writer.writerows(snf_rows)
                snf_by_ccn, snf_quality = generator.load_snf_enrollments(snf_path)

            quality_measures_by_ccn = {}
            quality_measures_quality = None
            if quality_measure_rows is not None:
                quality_measures_path = temp_path / "quality_measures_claims.csv"
                with quality_measures_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=QUALITY_MEASURES_CLAIMS_COLUMNS)
                    writer.writeheader()
                    writer.writerows(quality_measure_rows)
                quality_measures_by_ccn, quality_measures_quality = generator.load_quality_measures_claims(
                    quality_measures_path
                )

            groups, facilities, quality = generator.load_pbj_rows(input_dir)
            data = generator.build_output(
                groups,
                facilities,
                quality,
                output_path,
                "test",
                "2026-05-18",
                provider_by_ccn,
                provider_quality,
                snf_by_ccn,
                snf_quality,
                quality_measures_by_ccn,
                quality_measures_quality,
            )
            errors = generator.validate_output(data)
            self.assertEqual(errors, [])
            return json.loads(json.dumps(data))

    def base_row(self, **overrides):
        row = {
            "STATE": "CT",
            "PROVNUM": "075999",
            "PROVNAME": "Test Home",
            "CITY": "Hartford",
            "WorkDate": "2025-10-01",
            "MDScensus": "10",
            "Hrs_RNDON": "1",
            "Hrs_RNadmin": "1",
            "Hrs_RN": "8",
            "Hrs_LPNadmin": "1",
            "Hrs_LPN": "9",
            "Hrs_CNA": "20",
            "Hrs_NAtrn": "1",
            "Hrs_MedAide": "1",
            "Hrs_RNDON_ctr": "0",
            "Hrs_RNadmin_ctr": "0",
            "Hrs_RN_ctr": "1",
            "Hrs_LPNadmin_ctr": "0",
            "Hrs_LPN_ctr": "1",
            "Hrs_CNA_ctr": "2",
            "Hrs_NAtrn_ctr": "0",
            "Hrs_MedAide_ctr": "0",
        }
        row.update(overrides)
        return row

    def provider_row(self, **overrides):
        row = {
            "CMS Certification Number (CCN)": "075999",
            "Provider Name": "Standardized Test Home",
            "Provider Address": "123 Main St",
            "Provider City": "West Hartford",
            "Provider State": "CT",
            "Provider Zip Code": "06107",
            "Provider Phone Number": "860-555-0100",
            "Number of Certified Beds": "120",
            "Ownership Type": "For profit - Corporation",
            "Case-Mix Nurse Aide Staffing Hours per Resident per Day": "2.50",
            "Case-Mix LPN Staffing Hours per Resident per Day": "0.80",
            "Case-Mix RN Staffing Hours per Resident per Day": "0.70",
            "Case-Mix Total Nurse Staffing Hours per Resident per Day": "4.00",
            "Overall Rating": "4",
            "Health Inspection Rating": "3",
            "Staffing Rating": "5",
            "RN Staffing Rating": "4",
            "QM Rating": "2",
            "Long-Stay QM Rating": "3",
            "Short-Stay QM Rating": "5",
        }
        row.update(overrides)
        return row

    def snf_row(self, **overrides):
        row = {
            "ENROLLMENT STATE": "CT",
            "NPI": "1234567890",
            "CCN": "075999",
            "ORGANIZATION NAME": "TEST LEGAL ORGANIZATION LLC",
            "DOING BUSINESS AS NAME": "TEST DBA",
            "INCORPORATION DATE": "01/15/2020",
            "INCORPORATION STATE": "CT",
            "ORGANIZATION TYPE STRUCTURE": "LLC",
            "PROPRIETARY_NONPROFIT": "P",
            "NURSING HOME PROVIDER NAME": "TEST HOME ENROLLMENT",
            "AFFILIATION ENTITY NAME": "TEST AFFILIATION",
            "AFFILIATION ENTITY ID": "A123",
            "STATE": "CT",
        }
        row.update(overrides)
        return row

    def quality_measure_row(self, **overrides):
        row = {
            "CMS Certification Number (CCN)": "075999",
            "Provider Name": "Standardized Test Home",
            "State": "CT",
            "Measure Code": "521",
            "Measure Description": "Percentage of short-stay residents who were rehospitalized after a nursing home admission",
            "Resident type": "Short Stay",
            "Adjusted Score": "18.2",
            "Observed Score": "20.1",
            "Expected Score": "19.3",
            "Footnote for Score": "",
            "Used in Quality Measure Five Star Rating": "Y",
            "Measure Period": "2024Q4-2025Q3",
            "Processing Date": "04/01/2026",
        }
        row.update(overrides)
        return row

    def test_zero_census_days_are_excluded_from_denominator_and_numerator(self):
        data = self.build_from_rows([
            self.base_row(WorkDate="2025-10-01", MDScensus="10"),
            self.base_row(WorkDate="2025-10-02", MDScensus="0", Hrs_RN="100", Hrs_CNA="100"),
        ])

        row = data["facility_quarterly_staffing"][0]
        self.assertEqual(row["resident_days"], 10)
        self.assertEqual(row["average_resident_census"], 10)
        self.assertEqual(row["metrics"]["total_nurse_hprd"], 4.2)
        self.assertEqual(row["data_quality"]["input_daily_row_count"], 2)
        self.assertEqual(row["data_quality"]["included_daily_row_count"], 1)
        self.assertEqual(row["data_quality"]["excluded_zero_census_day_count"], 1)

    def test_zero_nursing_hours_days_are_included_when_census_is_nonzero(self):
        zero_hours = self.base_row(
            WorkDate="2025-10-02",
            MDScensus="10",
            Hrs_RNDON="0",
            Hrs_RNadmin="0",
            Hrs_RN="0",
            Hrs_LPNadmin="0",
            Hrs_LPN="0",
            Hrs_CNA="0",
            Hrs_NAtrn="0",
            Hrs_MedAide="0",
            Hrs_RNDON_ctr="0",
            Hrs_RNadmin_ctr="0",
            Hrs_RN_ctr="0",
            Hrs_LPNadmin_ctr="0",
            Hrs_LPN_ctr="0",
            Hrs_CNA_ctr="0",
            Hrs_NAtrn_ctr="0",
            Hrs_MedAide_ctr="0",
        )
        data = self.build_from_rows([
            self.base_row(WorkDate="2025-10-01", MDScensus="10"),
            zero_hours,
        ])

        row = data["facility_quarterly_staffing"][0]
        self.assertEqual(row["resident_days"], 20)
        self.assertEqual(row["average_resident_census"], 10)
        self.assertEqual(row["metrics"]["total_nurse_hprd"], 2.1)
        self.assertEqual(row["data_quality"]["included_daily_row_count"], 2)
        self.assertEqual(row["data_quality"]["included_zero_nursing_hours_day_count"], 1)
        self.assertEqual(row["data_quality"]["excluded_zero_nursing_hours_day_count"], 0)

    def test_ct_direct_care_estimates_exclude_administrative_nursing_categories(self):
        data = self.build_from_rows([self.base_row()])
        row = data["facility_quarterly_staffing"][0]
        metrics = row["metrics"]

        self.assertEqual(metrics["total_nurse_hprd"], 4.2)
        self.assertEqual(metrics["ct_direct_care_total_hprd_estimate"], 3.9)
        self.assertEqual(metrics["ct_direct_care_licensed_nurse_hprd_estimate"], 1.7)
        self.assertEqual(metrics["ct_total_direct_care_difference_from_minimum"], 0.9)
        self.assertEqual(metrics["ct_licensed_direct_care_difference_from_minimum"], 0.86)
        self.assertFalse(metrics["ct_total_direct_care_below_minimum_estimate"])
        self.assertFalse(metrics["ct_licensed_direct_care_below_minimum_estimate"])

    def test_ct_total_direct_care_can_be_below_or_above_comparison_point(self):
        below = self.base_row(
            PROVNUM="075100",
            PROVNAME="Below Total Home",
            Hrs_RNDON="20",
            Hrs_RNadmin="20",
            Hrs_RN="5",
            Hrs_LPNadmin="20",
            Hrs_LPN="4",
            Hrs_CNA="15",
            Hrs_NAtrn="0",
            Hrs_MedAide="0",
        )
        above = self.base_row(
            PROVNUM="075101",
            PROVNAME="Above Total Home",
            Hrs_RNDON="0",
            Hrs_RNadmin="0",
            Hrs_RN="8",
            Hrs_LPNadmin="0",
            Hrs_LPN="9",
            Hrs_CNA="20",
            Hrs_NAtrn="1",
            Hrs_MedAide="1",
        )
        data = self.build_from_rows([below, above])
        rows = {row["ccn"]: row for row in data["facility_quarterly_staffing"]}

        self.assertEqual(rows["075100"]["metrics"]["total_nurse_hprd"], 8.4)
        self.assertEqual(rows["075100"]["metrics"]["ct_direct_care_total_hprd_estimate"], 2.4)
        self.assertTrue(rows["075100"]["metrics"]["ct_total_direct_care_below_minimum_estimate"])
        self.assertEqual(rows["075101"]["metrics"]["ct_direct_care_total_hprd_estimate"], 3.9)
        self.assertFalse(rows["075101"]["metrics"]["ct_total_direct_care_below_minimum_estimate"])

    def test_ct_licensed_direct_care_can_be_below_or_above_comparison_point(self):
        below = self.base_row(
            PROVNUM="075200",
            PROVNAME="Below Licensed Home",
            Hrs_RNDON="20",
            Hrs_RNadmin="20",
            Hrs_RN="3",
            Hrs_LPNadmin="20",
            Hrs_LPN="4",
            Hrs_CNA="30",
            Hrs_NAtrn="0",
            Hrs_MedAide="0",
        )
        above = self.base_row(
            PROVNUM="075201",
            PROVNAME="Above Licensed Home",
            Hrs_RNDON="0",
            Hrs_RNadmin="0",
            Hrs_RN="5",
            Hrs_LPNadmin="0",
            Hrs_LPN="4",
            Hrs_CNA="30",
            Hrs_NAtrn="0",
            Hrs_MedAide="0",
        )
        data = self.build_from_rows([below, above])
        rows = {row["ccn"]: row for row in data["facility_quarterly_staffing"]}

        self.assertEqual(rows["075200"]["metrics"]["total_nurse_hprd"], 9.7)
        self.assertEqual(rows["075200"]["metrics"]["ct_direct_care_licensed_nurse_hprd_estimate"], 0.7)
        self.assertTrue(rows["075200"]["metrics"]["ct_licensed_direct_care_below_minimum_estimate"])
        self.assertEqual(rows["075201"]["metrics"]["ct_direct_care_licensed_nurse_hprd_estimate"], 0.9)
        self.assertFalse(rows["075201"]["metrics"]["ct_licensed_direct_care_below_minimum_estimate"])

    def test_provider_info_successful_ccn_match_and_metadata_fill(self):
        data = self.build_from_rows([self.base_row()], [self.provider_row()])
        facility = data["facilities"][0]

        self.assertTrue(facility["provider_source_matched"])
        self.assertEqual(facility["provider_name"], "Standardized Test Home")
        self.assertEqual(facility["pbj_provider_name"], "Test Home")
        self.assertEqual(facility["address"], "123 Main St")
        self.assertEqual(facility["city"], "West Hartford")
        self.assertEqual(facility["zip_code"], "06107")
        self.assertEqual(facility["phone_number"], "860-555-0100")
        self.assertEqual(facility["certified_beds"], 120)
        self.assertEqual(facility["ownership_type"], "For profit - Corporation")
        self.assertEqual(facility["cms_overall_rating"], 4)
        self.assertEqual(facility["cms_health_inspection_rating"], 3)
        self.assertEqual(facility["cms_staffing_rating"], 5)
        self.assertEqual(facility["cms_rn_staffing_rating"], 4)
        self.assertEqual(facility["cms_qm_rating"], 2)
        self.assertEqual(facility["cms_long_stay_qm_rating"], 3)
        self.assertEqual(facility["cms_short_stay_qm_rating"], 5)
        self.assertEqual(facility["cms_rating_source"], "CMS Nursing Home Provider Information")
        self.assertEqual(data["data_quality"]["matched_facility_count"], 1)
        self.assertEqual(data["data_quality"]["unmatched_pbj_facility_count"], 0)
        self.assertTrue(data["data_quality"]["provider_rating_fields_available"])
        self.assertEqual(data["data_quality"]["provider_rating_missing_columns"], [])
        self.assertEqual(data["data_quality"]["facilities_with_overall_rating_count"], 1)
        self.assertEqual(data["data_quality"]["facilities_with_qm_rating_count"], 1)
        self.assertEqual(data["data_quality"]["facilities_with_staffing_rating_count"], 1)
        row = data["facility_quarterly_staffing"][0]
        self.assertTrue(row["benchmarks"]["case_mix_benchmark_available"])
        self.assertEqual(row["benchmarks"]["case_mix_total_nurse_hprd"], 4.0)
        self.assertEqual(row["benchmarks"]["case_mix_rn_hprd"], 0.7)
        self.assertEqual(row["benchmarks"]["case_mix_lpn_lvn_hprd"], 0.8)
        self.assertEqual(row["benchmarks"]["case_mix_nurse_aide_hprd"], 2.5)
        self.assertEqual(row["benchmarks"]["benchmark_source"], "CMS Nursing Home Provider Information")

    def test_provider_info_missing_rating_columns_does_not_break_generation(self):
        minimal_provider_columns = [column for column in PROVIDER_COLUMNS if "Rating" not in column]
        with tempfile.TemporaryDirectory() as temp_dir:
            provider_path = Path(temp_dir) / "provider_info.csv"
            with provider_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=minimal_provider_columns)
                writer.writeheader()
                writer.writerow({key: value for key, value in self.provider_row().items() if key in minimal_provider_columns})

            provider_by_ccn, provider_quality = generator.load_provider_info(provider_path)

        self.assertFalse(provider_quality["provider_rating_fields_available"])
        self.assertEqual(set(provider_quality["provider_rating_missing_columns"]), set(generator.PROVIDER_RATING_FIELDS))
        self.assertIsNone(provider_by_ccn["075999"]["cms_overall_rating"])

        data = self.build_from_rows([self.base_row()], [self.provider_row(**{
            "Overall Rating": "",
            "Health Inspection Rating": "",
            "Staffing Rating": "",
            "RN Staffing Rating": "",
            "QM Rating": "",
            "Long-Stay QM Rating": "",
            "Short-Stay QM Rating": "",
        })])
        self.assertIsNone(data["facilities"][0]["cms_overall_rating"])
        self.assertEqual(data["data_quality"]["facilities_with_overall_rating_count"], 0)

    def test_quality_measures_claims_merge_multiple_rows_by_ccn(self):
        data = self.build_from_rows(
            [self.base_row()],
            quality_measure_rows=[
                self.quality_measure_row(),
                self.quality_measure_row(**{
                    "Measure Code": "552",
                    "Measure Description": "Number of outpatient emergency department visits per 1000 long-stay resident days",
                    "Resident type": "Long Stay",
                    "Adjusted Score": "1.5",
                    "Observed Score": "1.6",
                    "Expected Score": "1.4",
                    "Footnote for Score": "Small denominator",
                    "Used in Quality Measure Five Star Rating": "N",
                }),
            ],
        )
        facility = data["facilities"][0]
        self.assertEqual(len(facility["quality_measures_claims"]), 2)
        measures = {row["measure_code"]: row for row in facility["quality_measures_claims"]}
        self.assertEqual(measures["521"]["adjusted_score"], 18.2)
        self.assertTrue(measures["521"]["used_in_qm_five_star_rating"])
        self.assertEqual(measures["552"]["footnote_for_score"], "Small denominator")
        self.assertFalse(measures["552"]["used_in_qm_five_star_rating"])
        self.assertEqual(data["data_quality"]["quality_measures_claims_row_count"], 2)
        self.assertEqual(data["data_quality"]["quality_measures_claims_ct_row_count"], 2)
        self.assertEqual(data["data_quality"]["facilities_with_quality_measures_claims_count"], 1)
        self.assertEqual(data["data_quality"]["quality_measures_claims_measure_count"], 2)
        self.assertEqual(data["data_quality"]["unmatched_quality_measure_ccn_count"], 0)

    def test_quality_measures_claims_ignores_non_ct_and_parses_blank_scores(self):
        data = self.build_from_rows(
            [self.base_row()],
            quality_measure_rows=[
                self.quality_measure_row(**{
                    "Adjusted Score": "",
                    "Observed Score": "not available",
                    "Expected Score": "",
                }),
                self.quality_measure_row(**{
                    "CMS Certification Number (CCN)": "395999",
                    "State": "PA",
                    "Measure Code": "522",
                }),
            ],
        )
        measures = data["facilities"][0]["quality_measures_claims"]
        self.assertEqual(len(measures), 1)
        self.assertIsNone(measures[0]["adjusted_score"])
        self.assertIsNone(measures[0]["observed_score"])
        self.assertIsNone(measures[0]["expected_score"])
        self.assertEqual(data["data_quality"]["quality_measures_claims_row_count"], 2)
        self.assertEqual(data["data_quality"]["quality_measures_claims_ct_row_count"], 1)

    def test_quality_measures_claims_unmatched_ccn_is_counted(self):
        data = self.build_from_rows(
            [self.base_row()],
            quality_measure_rows=[
                self.quality_measure_row(**{
                    "CMS Certification Number (CCN)": "075111",
                }),
            ],
        )
        self.assertEqual(data["facilities"][0]["quality_measures_claims"], [])
        self.assertEqual(data["data_quality"]["facilities_with_quality_measures_claims_count"], 0)
        self.assertEqual(data["data_quality"]["unmatched_quality_measure_ccn_count"], 1)

    def test_missing_quality_measures_file_does_not_break_existing_generation(self):
        data = self.build_from_rows([self.base_row()])
        self.assertEqual(data["facilities"][0]["quality_measures_claims"], [])
        self.assertFalse(data["data_quality"]["quality_measures_claims_file_supplied"])
        self.assertEqual(data["data_quality"]["quality_measures_claims_ct_row_count"], 0)

    def test_pbj_facility_without_provider_match_is_retained(self):
        data = self.build_from_rows([self.base_row()], [self.provider_row(**{
            "CMS Certification Number (CCN)": "075111"
        })])
        facility = data["facilities"][0]

        self.assertFalse(facility["provider_source_matched"])
        self.assertEqual(facility["provider_name"], "Test Home")
        self.assertEqual(facility["city"], "Hartford")
        self.assertEqual(facility["metadata_source"], "pbj")
        self.assertEqual(data["data_quality"]["matched_facility_count"], 0)
        self.assertEqual(data["data_quality"]["unmatched_pbj_facility_count"], 1)
        self.assertEqual(data["data_quality"]["unmatched_provider_info_row_count"], 1)
        row = data["facility_quarterly_staffing"][0]
        self.assertFalse(row["benchmarks"]["case_mix_benchmark_available"])
        self.assertIsNone(row["benchmarks"]["case_mix_total_nurse_hprd"])

    def test_blank_provider_fields_fall_back_to_pbj_values(self):
        data = self.build_from_rows([self.base_row()], [self.provider_row(**{
            "Provider Name": "",
            "Provider City": "",
            "Provider State": "",
        })])
        facility = data["facilities"][0]

        self.assertTrue(facility["provider_source_matched"])
        self.assertEqual(facility["provider_name"], "Test Home")
        self.assertEqual(facility["city"], "Hartford")
        self.assertEqual(facility["state"], "CT")

    def test_matched_provider_with_missing_benchmarks_keeps_nulls_and_notes(self):
        data = self.build_from_rows([self.base_row()], [self.provider_row(**{
            "Case-Mix Nurse Aide Staffing Hours per Resident per Day": "",
            "Case-Mix LPN Staffing Hours per Resident per Day": "",
            "Case-Mix RN Staffing Hours per Resident per Day": "",
            "Case-Mix Total Nurse Staffing Hours per Resident per Day": "",
        })])
        row = data["facility_quarterly_staffing"][0]

        self.assertFalse(row["benchmarks"]["case_mix_benchmark_available"])
        self.assertIsNone(row["benchmarks"]["case_mix_total_nurse_hprd"])
        self.assertIn(
            "Provider Information matched, but case-mix benchmark staffing fields were unavailable or blank.",
            row["data_quality"]["notes"],
        )

    def test_no_provider_file_leaves_benchmarks_null(self):
        data = self.build_from_rows([self.base_row()])
        row = data["facility_quarterly_staffing"][0]

        self.assertFalse(row["benchmarks"]["case_mix_benchmark_available"])
        self.assertIsNone(row["benchmarks"]["case_mix_total_nurse_hprd"])
        self.assertIsNone(row["benchmarks"]["benchmark_source"])

    def test_snf_enrollment_successful_ccn_match_adds_affiliation_context(self):
        data = self.build_from_rows([self.base_row()], [self.provider_row()], [self.snf_row()])
        facility = data["facilities"][0]

        self.assertTrue(facility["enrollment_source_matched"])
        self.assertEqual(facility["provider_name"], "Standardized Test Home")
        self.assertEqual(facility["enrollment_organization_name"], "TEST LEGAL ORGANIZATION LLC")
        self.assertEqual(facility["enrollment_doing_business_as_name"], "TEST DBA")
        self.assertEqual(facility["enrollment_proprietary_nonprofit"], "P")
        self.assertEqual(facility["enrollment_organization_type_structure"], "LLC")
        self.assertEqual(facility["affiliation_entity_name"], "TEST AFFILIATION")
        self.assertEqual(facility["affiliation_entity_id"], "A123")
        self.assertEqual(data["data_quality"]["matched_snf_enrollment_facility_count"], 1)
        self.assertEqual(data["data_quality"]["unmatched_pbj_facility_count_for_snf_enrollments"], 0)

    def test_pbj_facility_without_snf_enrollment_match_is_retained(self):
        data = self.build_from_rows([self.base_row()], [self.provider_row()], [self.snf_row(CCN="075111")])
        facility = data["facilities"][0]

        self.assertFalse(facility["enrollment_source_matched"])
        self.assertEqual(facility["provider_name"], "Standardized Test Home")
        self.assertEqual(facility["enrollment_organization_name"], "")
        self.assertEqual(data["data_quality"]["matched_snf_enrollment_facility_count"], 0)
        self.assertEqual(data["data_quality"]["unmatched_pbj_facility_count_for_snf_enrollments"], 1)
        self.assertEqual(data["data_quality"]["unmatched_snf_enrollment_row_count"], 1)

    def test_duplicate_snf_enrollment_ccn_counted_and_first_row_kept(self):
        data = self.build_from_rows([self.base_row()], [self.provider_row()], [
            self.snf_row(**{"ORGANIZATION NAME": "FIRST ORG"}),
            self.snf_row(**{"ORGANIZATION NAME": "SECOND ORG"}),
        ])
        facility = data["facilities"][0]

        self.assertEqual(facility["enrollment_organization_name"], "FIRST ORG")
        self.assertEqual(data["data_quality"]["snf_enrollments_duplicate_ccn_count"], 1)


if __name__ == "__main__":
    unittest.main()
