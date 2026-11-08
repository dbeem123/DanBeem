"""Support-service lines (dietary, laundry, housekeeping) from a DSS annual cost report (CSP-10, 18, 19, 20)."""
from cr_extract import find


def support_lines(P):
    r = {}
    # CSP-10 salaries: CCNH/RHNS column
    r["sal_head_dietitian"] = find(P, "10", r"Head Dietitian")[0]
    r["sal_food_supervisor"] = find(P, "10", r"Food Service Supervisor")[0]
    r["sal_dietary_workers"] = find(P, "10", r"Dietary Workers")[0]
    r["sal_head_housekeeper"] = find(P, "10", r"Head Housekeeper")[0]
    r["sal_housekeeping_workers"] = find(P, "10", r"Other Housekeeping Workers")[0]
    r["sal_laundry_supervisor"] = find(P, "10", r"Supervisor", within=(r"Laundry Service", r"Barber"))[0]
    r["sal_laundry_workers"] = find(P, "10", r"Other Laundry Workers")[0]
    # CSP-18 dietary (non-salary)
    r["diet_raw_food"] = find(P, "18", r"Raw Food")[0]
    r["diet_nonfood_supplies"] = find(P, "18", r"Non-?\s?Food Supplies")[0]
    r["diet_other_inhouse"] = find(P, "18", r"^\s*3\.\s*Other")[0]
    r["diet_purchased_services"] = find(P, "18", r"Purchased Services")[0]
    r["diet_other"] = find(P, "18", r"^\s*c\.\s*Other")[0]
    r["dietary_total"] = find(P, "18", r"Total Dietary")[0]
    # CSP-19 laundry
    r["laundry_purchased_services"] = find(P, "19", r"Purchased Services")[0]
    r["laundry_total"] = find(P, "19", r"Total Laundry")[0]
    # CSP-20 housekeeping
    r["hk_supplies"] = find(P, "20", r"Supplies\s*-?\s*Cleaning")[0]
    r["hk_purchased_services"] = find(P, "20", r"Purchased Services", within=(r"Housekeeping", r"Resident Care"))[0]
    r["housekeeping_total"] = find(P, "20", r"Total Housekeeping")[0]
    # CSP-22 maintenance, utilities and property
    r["plant_repairs"] = find(P, "22", r"^\s*a\.\s*Repairs\s*(&|and)\s*Maint")[0]
    r["plant_heat"] = find(P, "22", r"^\s*b\.\s*Heat\b")[0]
    r["plant_light_power"] = find(P, "22", r"Light\s*(&|and)\s*Power")[0]
    r["plant_water"] = find(P, "22", r"^\s*d\.\s*Water\b")[0]
    r["plant_equipment_lease"] = find(P, "22", r"Equipment Lease")[0]
    r["property_depreciation"] = find(P, "22", r"Total Depreciation")[0]
    r["property_amortization"] = find(P, "22", r"Total Amortization")[0]
    r["property_rent"] = find(P, "22", r"Rental payments")[0]
    r["property_tax_owner"] = find(P, "22", r"Real estate taxes paid by owner")[0]
    r["property_tax_lessor"] = find(P, "22", r"Real estate taxes paid by lessor")[0]
    r["property_tax_personal"] = find(P, "22", r"Personal property tax")[0]
    return r
