"""Build data/ct_ltcop_act_reference.json: long-term care acts enacted 2021-2026.

Rows were compiled from the Office of Legislative Research (OLR) annual "Acts Affecting
Seniors" reports for 2021-2026, the Long Term Care Ombudsman Program's "Advocacy over the
years" page, and each act's CGA bill status page (which gives the bill number and the
public act PDF). Every source_url is the public act PDF on cga.ct.gov.

The list covers acts touching nursing homes, residential care homes, assisted living and
managed residential communities, home and community-based long-term care, the Ombudsman
program, conservatorship and long-term care financing. Minor provisions of large acts are
omitted; each summary is neutral and 30 words or fewer.

Run: python scripts/build_ct_ltcop_act_reference.py   (rewrites the JSON; --check compares)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ct_ltcop_act_reference.json"
TRACKER = ROOT / "data" / "ct_ltcop_legislative_tracker.json"
CGA = "https://www.cga.ct.gov"

OLR_REPORTS = [
    {"session": 2021, "title": "OLR 2021 Acts Affecting Seniors (2021-R-0109)",
     "url": CGA + "/olr/Documents/year/AA/2021AA-0109_2021%20Acts%20Affecting%20Seniors.pdf"},
    {"session": 2022, "title": "OLR 2022 Acts Affecting Seniors (2022-R-0118)",
     "url": CGA + "/olr/Documents/year/AA/2022AA-0118_2022%20Acts%20Affecting%20Seniors.pdf"},
    {"session": 2023, "title": "OLR 2023 Acts Affecting Seniors (2023-R-0149)",
     "url": CGA + "/2023/rpt/pdf/2023-R-0149.pdf"},
    {"session": 2024, "title": "OLR 2024 Acts Affecting Seniors (2024-R-0108)",
     "url": CGA + "/2024/rpt/pdf/2024-R-0108.pdf"},
    {"session": 2025, "title": "OLR 2025 Acts Affecting Seniors (2025-R-0098)",
     "url": CGA + "/olr/Documents/year/AA/2025AA-0098_2025%20Acts%20Affecting%20Seniors.pdf"},
    {"session": 2026, "title": "OLR 2026 Acts Affecting Seniors (2026-R-0085)",
     "url": CGA + "/2026/rpt/pdf/2026-R-0085.pdf"},
    {"session": None, "title": "Long Term Care Ombudsman Program, Advocacy over the years",
     "url": "https://portal.ct.gov/ltcop/advocacy-over-the-years"},
]

S, W, Q, O, D, C, M, A = ("staffing_workforce", "quality_oversight", "ownership_finance",
                          "discharge_rights", "closures_capacity", "community_settings",
                          "ombudsman_program", "aging_financing")

# (session, bill, act, act pdf path, title, topics, summary)
ROWS = [
    (2021, "SB 1030", "PA 21-185", "/2021/ACT/PA/PDF/2021PA-00185-R00SB-01030-PA.PDF",
     "An Act Concerning Nursing Homes and Dementia Special Care Units", [S, W, D],
     "Requires DPH to set at least three hours of direct care per resident day, up from 1.9, plus infection-control specialists, PPE supplies, family councils and social-connection care plans."),
    (2021, "SB 975", "PA 21-55", "/2021/ACT/PA/PDF/2021PA-00055-R00SB-00975-PA.PDF",
     "An Act Strengthening the Bills of Rights for Long-Term Care Residents and Authorizing the Use of Resident Technology for Virtual Visitation and Virtual Monitoring", [O, W, C],
     "Adds the right to treat one's living quarters as home, including private communication and virtual visitation and monitoring technology, for nursing home and assisted living residents."),
    (2021, "HB 6634", "PA 21-71", "/2021/ACT/PA/PDF/2021PA-00071-R00HB-06634-PA.PDF",
     "An Act Concerning Essential Support Persons and a State-Wide Visitation Policy for Residents of Long-Term Care Facilities", [O, W, M],
     "Lets residents designate an essential support person who may visit during restrictions, requires a statewide DPH visitation policy and adds Ombudsman duties on socialization and visitation."),
    (2021, "SB 973", "PA 21-194", "/2021/ACT/PA/PDF/2021PA-00194-R00SB-00973-PA.PDF",
     "An Act Strengthening the Voice of Residents and Family Councils", [M, O],
     "Requires agencies to tell the Ombudsman about long-term care proposals and regulations, and requires state long-term care task forces to include resident and family council representatives."),
    (2021, "HB 6666", "PA 21-121", "/2021/ACT/PA/PDF/2021PA-00121-R00HB-06666-PA.PDF",
     "An Act Concerning the Department of Public Health's Recommendations Regarding Various Revisions to the Public Health Statutes", [C, W, D],
     "DPH revisions: assisted living licensing for managed residential communities, dementia unit approval, bed positioning, emergency bed capacity, electronic citations and nursing home IV care."),
    (2021, "SB 1202", "PA 21-2 (June Special Session)", "/2021/ACT/PA/PDF/2021PA-00002-R00SB-01202SS1-PA.PDF",
     "An Act Concerning Provisions Related to Revenue and Other Items to Implement the State Budget for the Biennium Ending June 30, 2023", [A],
     "Budget implementer: raises the monthly personal needs allowance for Medicaid long-term care residents from $60 to $75 and cuts state-funded home care cost sharing from 9% to 4.5%."),
    (2021, "SB 1046", "PA 21-150", "/2021/ACT/PA/PDF/2021PA-00150-R00SB-01046-PA.PDF",
     "An Act Concerning Long-Term Care Insurance", [A],
     "Bars new long-term care insurance rate filings during a phased increase of 20% or more and requires affordable benefit options when such increases are filed."),
    (2021, "HB 6100", "PA 21-37", "/2021/ACT/PA/PDF/2021PA-00037-R00HB-06100-PA.PDF",
     "An Act Concerning Department of Consumer Protection Licensing and Enforcement, Antitrust Issues and the Palliative Use of Marijuana and Revisions to the Liquor Control Act", [C, S],
     "Requires homemaker-companion agencies to run national criminal background checks on prospective employees and bars hiring people with certain recent convictions."),
    (2021, "HB 6457", "PA 21-160", "/2021/ACT/PA/PDF/2021PA-00160-R00HB-06457-PA.PDF",
     "An Act Concerning Access to Recordings and Images from Technology Used by Nursing Home Residents for Virtual Visitation and Virtual Monitoring", [W, S],
     "Requires nursing homes to let an employee facing discipline based on a resident's virtual monitoring recording access that recording to respond."),
    (2021, "SB 895", "PA 21-192", "/2021/ACT/PA/PDF/2021PA-00192-R00SB-00895-PA.PDF",
     "An Act Concerning Changes to Various Pharmacy Statutes", [W],
     "Allows licensed long-term care pharmacies to use automated prescription dispensing machines in nursing homes, with nurses administering the dispensed medications."),

    (2022, "HB 5313", "PA 22-57", "/2022/ACT/PA/PDF/2022PA-00057-R00HB-05313-PA.PDF",
     "An Act Concerning Temporary Nursing Services Agencies, Reporting of Involuntary Transfers and Discharges from Nursing Homes and Residential Care Homes, Elder Abuse Training, Legal Rights of Long-Term Care Applicants and a Study of Managed Residential Community Issues", [S, O, M, C, A],
     "Creates registration and cost reporting for temporary nursing agencies, electronic reporting of involuntary discharges to the Ombudsman, elder abuse training, a Medicaid legal-rights advisory and an MRC working group."),
    (2022, "HB 5500", "PA 22-58", "/2022/ACT/PA/PDF/2022PA-00058-R00HB-05500-PA.PDF",
     "An Act Concerning the Department of Public Health's Recommendations Regarding Various Revisions to the Public Health Statutes", [W, O, C, S],
     "DPH revisions: infection-prevention specialist rules, residential care home discharge notice contacts, administrator infection-control training, strike staffing plans and an assisted living dementia-care task force."),
    (2022, "HB 5506", "PA 22-118", "/2022/ACT/PA/PDF/2022PA-00118-R00HB-05506-PA.PDF",
     "An Act Adjusting the State Budget for the Biennium Ending June 30, 2023, Concerning Provisions Related to Revenue, School Construction and Other Items to Implement the State Budget and Authorizing and Adjusting Bonds of the State", [M, A, C],
     "Budget adjustments: creates the Community Ombudsman program for home care, lowers state home care cost sharing to 3%, raises the community spouse asset minimum to $50,000."),
    (2022, "SB 286", "PA 22-145", "/2022/ACT/PA/PDF/2022PA-00145-R00SB-00286-PA.PDF",
     "An Act Concerning Elder Abuse Reporting Deadlines, Temporary Family Assistance, Certificates of Need for Long-Term Care Facilities and Civil Penalties for Nursing Homes That Fail to Use Rate Increases for Employee Wage Enhancements", [S, D, Q],
     "Shortens elder abuse reporting to 24 hours, lets DSS penalize nursing homes that do not use wage rate increases for staff wages, and allows small-house nursing home approvals."),
    (2022, "SB 173", "PA 22-121", "/2022/ACT/PA/PDF/2022PA-00121-R00SB-00173-PA.PDF",
     "An Act Concerning a Study of the Cost and Feasibility of Permitting the Community Spouse of an Institutionalized Medicaid Recipient to Retain the Maximum Amount of Allowable Assets", [A],
     "Requires a DSS study of letting the community spouse of an institutionalized Medicaid recipient keep combined assets up to the federal maximum."),
    (2022, "HB 5330", "PA 22-104", "/2022/ACT/PA/PDF/2022PA-00104-R00HB-05330-PA.PDF",
     "An Act Concerning Cannabis Advertising and the Department of Consumer Protection's Recommendations Regarding Various Revisions to the Consumer Protection Statutes", [C, A],
     "Bars homemaker-companion agency owners and staff, other than immediate family, from acting as a client's agent under a power of attorney, unless exempted for good cause."),
    (2022, "SB 9", "PA 22-146", "/2022/ACT/PA/PDF/2022PA-00146-R00SB-00009-PA.PDF",
     "An Act Concerning Additional Adjustments to the State Budget for the Biennium Ending June 30, 2023, a Community Ombudsman Program, Certain Municipal-Related Provisions, School Building Project Grants and High-Deductible Health Plans", [A, M],
     "Budget adjustments, including Community Ombudsman program provisions; bars state agencies from recovering or offsetting federal ARPA funds provided for home- and community-based services."),
    (2022, "SB 262", "SA 22-12", "/2022/ACT/SA/PDF/2022SA-00012-R00SB-00262-SA.PDF",
     "An Act Concerning a Study of Homemaker-Companion Agency Issues", [C],
     "Creates a task force to study homemaker-companion agency qualifications, complaint resolution and advertising."),

    (2023, "HB 5781", "PA 23-48", "/2023/ACT/PA/PDF/2023PA-00048-R00HB-05781-PA.PDF",
     "An Act Concerning Notice of a Proposed Involuntary Transfer or Discharge of a Nursing Facility Resident, Family Councils in Managed Residential Communities, Coordination of Dementia Services, Nursing Home Transparency and Homemaker-Companion Agencies", None,
     "Requires same-day Ombudsman notice of involuntary transfers or discharges, family councils in assisted living, a dementia services coordinator, a Medicaid rate guidebook and homemaker-companion agency rules."),
    (2023, "HB 6731", "PA 23-122", "/2023/ACT/PA/PDF/2023PA-00122-R00HB-06731-PA.PDF",
     None, None,
     "Expands when health care institutions, including nursing homes, need DPH approval for ownership changes and lowers the license-applicant ownership disclosure threshold to 5%."),
    (2023, "HB 6733", "PA 23-31", "/2023/ACT/PA/PDF/2023PA-00031-R00HB-06733-PA.PDF",
     "An Act Concerning the Department of Public Health's Recommendations Regarding Various Revisions to the Public Health Statutes", [C],
     "Allows assisted living services agencies to serve people who are not chronic and stable when a home health or hospice agency is involved or ancillary services are arranged."),
    (2023, "SB 956", "PA 23-39", "/2023/ACT/PA/PDF/2023PA-00039-R00SB-00956-PA.PDF",
     "An Act Requiring Discharge Standards Regarding Follow-Up Appointments and Prescription Medications for Patients Being Discharged from a Hospital or Nursing Home Facility", [O],
     "Requires hospital and nursing home discharge plans to list follow-up appointments and medications, and electronic prescription transmission for patients discharged home."),
    (2023, "SB 989", "PA 23-186", "/2023/ACT/PA/PDF/2023PA-00186-R00SB-00989-PA.PDF",
     "An Act Concerning Nonprofit Provider Retention of Contract Savings, Community Health Worker Medicaid Reimbursement and Studies of Medicaid Rates of Reimbursement, Nursing Home Transportation and Nursing Home Waiting Lists", [D, M],
     "Lets nursing homes transport nonambulatory residents to nearby family homes and creates an Ombudsman-convened working group on nursing home waiting lists."),
    (2023, "HB 6941", "PA 23-204", "/2023/ACT/PA/PDF/2023PA-00204-R00HB-06941-PA.PDF",
     "An Act Concerning the State Budget for the Biennium Ending June 30, 2025, and Making Appropriations Therefor, and Provisions Related to Revenue and Other Items Implementing the State Budget", [A, C],
     "Budget: schedules a HUSKY C eligibility expansion, aligns state supplement start dates for residential care home residents and allows PACE coverage under Medicaid."),
    (2023, "HB 6767", "PA 23-99", "/2023/ACT/PA/PDF/2023PA-00099-R00HB-06767-PA.PDF",
     "An Act Concerning the Department of Consumer Protection's Recommendations Regarding Licensing and Enforcement", [C],
     "Requires homemaker-companion agencies to give 60 days' notice of rate changes and notice before stopping services, and increases DCP oversight of ownership changes and closures."),
    (2023, "HB 6677", "PA 23-30", "/2023/ACT/PA/PDF/2023PA-00030-R00HB-06677-PA.PDF",
     "An Act Concerning Adult Day Centers", [A, C],
     "Requires DSS to plan wider adult day eligibility under the home care program for elders and allows a Medicaid state plan amendment covering PACE."),
    (2023, "SB 9", "PA 23-97", "/2023/ACT/PA/PDF/2023PA-00097-R00SB-00009-PA.PDF",
     "An Act Concerning Health and Wellness for Connecticut Residents", [S],
     "Requires DSS to establish a personal care attendant career pathways program to improve care quality and recruitment."),

    (2024, "HB 5046", "PA 24-141", "/2024/ACT/PA/PDF/2024PA-00141-R00HB-05046-PA.PDF", None, None,
     "Bars placing new admissions in rooms of more than two beds from July 2026; adds receivership, plan-of-correction penalties, assisted living fee notices and closure-transfer admission rules."),
    (2024, "HB 5001", "PA 24-39", "/2024/ACT/PA/PDF/2024PA-00039-R00HB-05001-PA.PDF", None, None,
     "Home care registry, presumptive Medicaid home care eligibility, photo badges, Care Compare links, a nursing home dashboard, MRC notices and consumer guide, and Ombudsman consent changes."),
    (2024, "SB 1", "PA 24-19", "/2024/ACT/PA/PDF/2024PA-00019-R00SB-00001-PA.PDF", None, None,
     "Defines direct care for the three-hour staffing minimum, requires workplace violence standards and home health worker safety rules, and bars refusing admission for past mental health services."),
    (2024, "HB 5457", "PA 24-17", "/2024/ACT/PA/PDF/2024PA-00017-R00HB-05457-PA.PDF", None, None,
     "Changes Medicaid-certified nursing home waiting list rules, including admitting applicants in order once an application is substantially completed."),
    (2024, "HB 5523", "PA 24-81", "/2024/ACT/PA/PDF/2024PA-00081-R00HB-05523-PA.PDF",
     "An Act Concerning Allocations of Federal American Rescue Plan Act Funds and Provisions Related to General Government, Human Services, Education and the Biennium Ending June 30, 2025", [A],
     "Budget adjustments: replaces the scheduled HUSKY C income limit increase with 159% of the TFA benefit and limits estate recovery for state humane institution care."),
    (2024, "SB 324", "PA 24-97", "/2024/ACT/PA/PDF/2024PA-00097-R00SB-00324-PA.PDF",
     "An Act Concerning Probate Court Operations and Administration", [A],
     "Sets procedures for notifying an out-of-state or unlocatable spouse, and certain relatives, of an involuntary conservatorship petition."),
    (2024, "HB 5308", "PA 24-34", "/2024/ACT/PA/PDF/2024PA-00034-R00HB-05308-PA.PDF",
     "An Act Concerning Absentee Voting for Certain Patients of Nursing Homes", [O],
     "Lets nursing home residents apply for absentee ballots in the six days before an election and name a designee to deliver them."),

    (2025, "HB 6771", "PA 25-16", "/2025/ACT/PA/PDF/2025PA-00016-R00HB-06771-PA.PDF", None, None,
     "Background checks for all long-term care facility hires, residential care home discharge notices to the Ombudsman portal, placement near family, waiting-list exceptions and an Alzheimer's task force."),
    (2025, "HB 6913", "PA 25-17", "/2025/ACT/PA/PDF/2025PA-00017-R00HB-06913-PA.PDF", None, None,
     "Bars nursing homes and assisted living facilities from discriminating against residents on listed grounds; requires notices, cultural competency training and physical privacy in care."),
    (2025, "HB 7287", "PA 25-168", "/2025/ACT/PA/PDF/2025PA-00168-R00HB-07287-PA.PDF",
     "An Act Concerning the State Budget for the Biennium Ending June 30, 2027, and Making Appropriations Therefor, and Provisions Related to Revenue and Other Items Implementing the State Budget", [Q, S, W, M, A],
     "Budget: scheduled a 6% revenue tax to replace the user fee (repealed in 2026 first), funds wage-linked rate increases, a quality metrics program and wider Community Ombudsman scope."),
    (2025, "SB 1501", "PA 25-48", "/2025/ACT/PA/PDF/2025PA-00048-R00SB-01501-PA.PDF", None, None,
     "Creates a probate working group on conservator payment, fees and compensation, and widens certified-mail notice to relatives in involuntary conservatorship cases."),
    (2025, "HB 6442", "PA 25-15", "/2025/ACT/PA/PDF/2025PA-00015-R00HB-06442-PA.PDF", None, None,
     "Requires nursing homes with U.S. Department of Veterans Affairs contracts to admit eligible veterans regardless of the waiting list."),
    (2025, "HB 6978", "PA 25-96", "/2025/ACT/PA/PDF/2025PA-00096-R00HB-06978-PA.PDF", None, None,
     "DPH revisions, including revised grounds for disciplining licensed health care institutions, with civil penalties up to $25,000."),
    (2025, "SB 1380", "PA 25-154", "/2025/ACT/PA/PDF/2025PA-00154-R00SB-01380-PA.PDF", None, None,
     "Bars health care providers from knowingly discriminating in providing care based on listed characteristics, making it a discriminatory practice under CHRO laws."),
    (2025, "SB 1221", "PA 25-30", "/2025/ACT/PA/PDF/2025PA-00030-R00SB-01221-PA.PDF",
     "An Act Making Changes to the Connecticut Retirement Security Program", [S],
     "Extends the Connecticut Retirement Security Program to certain personal care attendants in state-funded programs, such as the home care program for elders, from July 1, 2026."),

    (2026, "HB 5142", "PA 26-28", "/2026/ACT/PA/PDF/2026PA-00028-R00HB-05142-PA.PDF", None, None,
     "Lets residential care home residents use their own virtual monitoring technology with notice and roommate consent, and narrows nursing home liability immunity while extending it to these homes."),
    (2026, "SB 125", "PA 26-103", "/2026/ACT/PA/PDF/2026PA-00103-R00SB-00125-PA.PDF", None, None,
     "Requires annual nursing home reports on investment-entity owners from 2027, licensee-control attestations from 2028, possible surety bonds and a DSS report on care quality."),
    (2026, "HB 5141", "PA 26-44", "/2026/ACT/PA/PDF/2026PA-00044-R00HB-05141-PA.PDF", None, None,
     "Requires assisted living services agencies serving managed residential communities to give employees annual training on residents' fear of retaliation for complaints."),
    (2026, "HB 5562", "PA 26-72", "/2026/ACT/PA/PDF/2026PA-00072-R00HB-05562-PA.PDF", None, None,
     "Adds DSS abuse-reporting contacts to MRC rights postings, adopts two federal nursing home resident-rights rules by reference, and broadens long-term care planning studies."),
    (2026, "SB 123", "PA 26-74", "/2026/ACT/PA/PDF/2026PA-00074-R00SB-00123-PA.PDF", None, None,
     "Requires hearings before assisted living fee increases over 10%, free PPE for home health aides, a bed-moratorium exception for new Medicaid beds and new MDS audit procedures."),
    (2026, "SB 1", "PA 26-68", "/2026/ACT/PA/PDF/2026PA-00068-R00SB-00001-PA.PDF", None, None,
     "Budget adjustments: repeals the planned 6% nursing home tax, adds performance and high-Medicaid payments, PDPM phase-in, a small-house two-bed waiver, unlicensed facility penalties and a caregiver tax credit."),
    (2026, "SB 477", "PA 26-76", "/2026/ACT/PA/PDF/2026PA-00076-R00SB-00477-PA.PDF", None, None,
     "Lets DSS set bed need at a lower occupancy for relocations to meet the two-bed limit, waives the limit for certain state-established homes and amends wage-increase rules."),
    (2026, "HB 5514", "PA 26-13", "/2026/ACT/PA/PDF/2026PA-00013-R00HB-05514-PA.PDF", None, None,
     "Public health revisions, including a DPH working group on whether licensing managed residential communities would improve residents' health, safety and well-being."),
    (2026, "HB 5406", "PA 26-35", "/2026/ACT/PA/PDF/2026PA-00035-R00HB-05406-PA.PDF", None, None,
     "Veterans measures, including a task force on encouraging Medicaid-certified nursing homes to contract with the U.S. Department of Veterans Affairs."),
    (2026, "SB 478", "PA 26-93", "/2026/ACT/PA/PDF/2026PA-00093-R00SB-00478-PA.PDF", None, None,
     "Long-term care insurance: new loss reporting, Insurance Commissioner investigation and discipline authority, and an optional report on refund and cancellation requirements."),
    (2026, "SB 400", "PA 26-87", "/2026/ACT/PA/PDF/2026PA-00087-R00SB-00400-PA.PDF", None, None,
     "Probate court changes, including general audits of a conservator's financial management and clarified notice for involuntary conservatorship hearings."),
    (2026, "HB 5143", "PA 26-50", "/2026/ACT/PA/PDF/2026PA-00050-R00HB-05143-PA.PDF", None, None,
     "Requires at least eight hours of annual paid training for homemaker-companion agency employees from January 2027, using DCP-approved programs."),
    (2026, "HB 5044", "PA 26-3", "/2026/ACT/PA/PDF/2026PA-00003-R00HB-05044-PA.PDF", None, None,
     "Sets state immunization standards of care and requires DPH nursing home rules on respiratory virus immunization based on them."),
    (2026, "HB 5561", "PA 26-146", "/2026/ACT/PA/PDF/2026PA-00146-R00HB-05561-PA.PDF", None, None,
     "Requires a five-year Medicaid rate review process starting by January 2027 and a working group on paying spouses who provide personal care."),
    (2026, "HB 5003", "PA 26-12", "/2026/ACT/PA/PDF/2026PA-00012-R00HB-05003-PA.PDF",
     "An Act Concerning Workforce Development and Working Conditions in the State", [S],
     "Lets DDS and DSS give direct care employees facing discipline, or their union, access to virtual monitoring evidence under confidentiality conditions."),
    (2026, "HB 5485", "SA 26-12", "/2026/ACT/SA/PDF/2026SA-00012-R00HB-05485-SA.PDF",
     "An Act Concerning Supported Decision-Making Study", [A],
     "Creates a working group to study supported decision-making for people with disabilities and older adults, reporting by December 31, 2026."),
]


H = "home_community_care"
# Topic added after the first build: acts that touch home care, waivers, CFC, PACE or HUSKY C.
EXTRA_TOPICS = {
    "2021-sb1202": [H], "2022-hb5506": [H], "2022-sb9": [H], "2022-sb262": [H], "2023-hb6941": [H], "2023-hb6677": [H],
    "2023-hb6767": [H], "2023-sb9": [H], "2024-hb5523": [H], "2025-hb7287": [H], "2025-sb1221": [H], "2026-hb5143": [H],
    "2026-sb123": [H], "2026-hb5003": [H],
}


def bill_id(session: int, bill: str) -> str:
    kind, num = bill.split()
    return f"{session}-{kind.lower()}{num}"


def build() -> dict:
    tracker = json.loads(TRACKER.read_text(encoding="utf-8"))
    past = {b["id"]: b for b in tracker["bills_past"]}
    rows = []
    for session, bill, act, path, title, topics, summary in ROWS:
        rid = bill_id(session, bill)
        known = past.get(rid)
        if known:
            if known.get("public_act") and not act.startswith(known["public_act"]):
                raise SystemExit(f"{rid}: act {act} disagrees with bills_past {known['public_act']}")
            title = title or known["title"]
            topics = topics or known["topics"]
        topics = list(topics) + [t for t in EXTRA_TOPICS.get(rid, []) if t not in topics]
        if not title or not topics:
            raise SystemExit(f"{rid}: needs a title and topics")
        rows.append({"id": rid, "session": session, "bill": bill, "public_act": act, "title": title,
                     "summary": summary, "topics": topics, "source_url": CGA + path})
    rows.sort(key=lambda r: (r["session"], int(re.search(r"-(\d+)", r["public_act"]).group(1))))
    return {
        "schema_version": "ct-ltcop-act-reference-1.0",
        "last_updated": "2026-11-03",
        "scope": "Connecticut public and special acts, 2021-2026, touching nursing homes, residential care homes, assisted living and managed residential communities, home and community-based long-term care, the Long Term Care Ombudsman Program, conservatorship or long-term care financing. Minor provisions of large acts are omitted.",
        "disclaimer": "Summaries are neutral descriptions, not positions of the Long Term Care Ombudsman Program. Read the public act for exact provisions and effective dates.",
        "sources": OLR_REPORTS,
        "acts": rows,
    }


def main() -> int:
    data = build()
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        if OUT.read_text(encoding="utf-8") != text:
            print("ct_ltcop_act_reference.json is out of date; run the builder.")
            return 1
        print(f"Act reference up to date: {len(data['acts'])} acts.")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(data['acts'])} acts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
