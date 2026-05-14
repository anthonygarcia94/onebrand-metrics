import requests
import os

# ============================================================
# Project OneBrand — Budget Chart Data Updater
# Reads Estimated Cost (USD) and Actual Spend (USD) from
# all 14 K&Z OneBrand budget tracker sheets and writes
# department totals into the Budget Chart Data sheet.
# Designed to run on the same daily schedule as the
# metrics updater.
# ============================================================

API_TOKEN = os.environ.get("SMARTSHEET_API_TOKEN")

BASE_URL = "https://api.smartsheet.com/2.0"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

BUDGET_SHEETS = {
    "CS Tech Sales":     5791435776282500,
    "Events Brand Pgms": 3117457857269636,
    "Field Operations":  7339616867667844,
    "Growth Marketing":  5597217355157380,
    "Human Resources":   3486395547996036,
    "IT Systems":        7620112591835012,
    "Legal Compliance":  4330253542444932,
    "Operations":        7972351449714564,
    "Procurement":       654002055237508,
    "Product Mgmt":      8833853169815428,
    "RND Atonometrics":  1991557950427012,
    "RND Met Road Wthr": 4752466007510916,
    "RND Solar":         3539635962597252,
    "Shared Services":   742701719834500,
}

CHART_SHEET_ID = 4612295454838660

CHART_ROW_MAP = {
    "CS Tech Sales":     5371525748686724,
    "Events Brand Pgms": 3119725935001476,
    "Field Operations":  7623325562371972,
    "Growth Marketing":  1993826028158852,
    "Human Resources":   6497425655529348,
    "IT Systems":        4245625841844100,
    "Legal Compliance":  8749225469214596,
    "Operations":        164238679539588,
    "Procurement":       4667838306910084,
    "Product Mgmt":      2416038493224836,
    "RND Atonometrics":  6919638120595332,
    "RND Met Road Wthr": 1290138586382212,
    "RND Solar":         5793738213752708,
    "Shared Services":   3541938400067460,
}

EST_COL_ID    = 7465145986224004
ACTUAL_COL_ID = 1835646452010884


def get_department_totals(dept_name, sheet_id):
    url = f"{BASE_URL}/sheets/{sheet_id}?include=objectValue"
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"  ❌ Could not read {dept_name}: {response.status_code}")
        return 0, 0

    sheet_data = response.json()
    columns    = sheet_data.get("columns", [])
    rows       = sheet_data.get("rows", [])

    est_col = next(
        (c["id"] for c in columns if c["title"] == "Estimated Cost (USD)"), None
    )
    actual_col = next(
        (c["id"] for c in columns if c["title"] == "Actual Spend (USD)"), None
    )

    if not est_col or not actual_col:
        print(f"  ❌ Could not find financial columns in {dept_name}")
        return 0, 0

    total_est    = 0.0
    total_actual = 0.0

    for row in rows:
        for cell in row.get("cells", []):
            col_id = cell.get("columnId")
            value  = cell.get("value")
            if value is None:
                continue
            try:
                if col_id == est_col:
                    total_est += float(value)
                elif col_id == actual_col:
                    total_actual += float(value)
            except (ValueError, TypeError):
                continue

    return round(total_est, 2), round(total_actual, 2)


def update_chart_data_sheet(dept_totals):
    rows_to_update = []

    for dept_name, (est_total, actual_total) in dept_totals.items():
        row_id = CHART_ROW_MAP.get(dept_name)
        if not row_id:
            print(f"  ⚠️  No row mapping found for {dept_name} — skipping")
            continue
        rows_to_update.append({
            "id": row_id,
            "cells": [
                {"columnId": EST_COL_ID,    "value": est_total},
                {"columnId": ACTUAL_COL_ID, "value": actual_total},
            ]
        })

    if not rows_to_update:
        print("  ❌ No rows to update")
        return

    url      = f"{BASE_URL}/sheets/{CHART_SHEET_ID}/rows"
    response = requests.put(url, headers=HEADERS, json=rows_to_update)

    if response.status_code == 200:
        print("  ✅ Budget Chart Data sheet updated successfully")
    else:
        print(f"  ❌ Update failed: {response.status_code} — {response.text}")


def main():
    print("=" * 60)
    print("Project OneBrand — Budget Chart Data Updater")
    print("=" * 60)

    if not API_TOKEN:
        print("❌ SMARTSHEET_API_TOKEN environment variable not set.")
        exit(1)

    print("\n💰 Reading budget totals from all 14 department sheets...")
    dept_totals = {}

    for dept_name, sheet_id in BUDGET_SHEETS.items():
        est, actual = get_department_totals(dept_name, sheet_id)
        dept_totals[dept_name] = (est, actual)
        print(
            f"  ✅ {dept_name}: "
            f"Estimated=${est:,.2f}  Actual=${actual:,.2f}"
        )

    print("\n📝 Writing totals to Budget Chart Data sheet...")
    update_chart_data_sheet(dept_totals)

    print("\n" + "=" * 60)
    print("✅ Done. Budget chart data is up to date.")
    print("=" * 60)


if __name__ == "__main__":
    main()
