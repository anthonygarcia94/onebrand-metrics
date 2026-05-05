import requests
import os

# ============================================================
# Project OneBrand — Metrics Sheet Updater
# Reads summary field values from all 14 K&Z OneBrand
# asset sheets and writes totals into the Dashboard
# Metrics sheet. Designed to run on a daily schedule.
# ============================================================

# API token read from environment variable — never hardcode
API_TOKEN = os.environ.get("SMARTSHEET_API_TOKEN")

BASE_URL = "https://api.smartsheet.com/2.0"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

SHEETS = {
    "Growth Marketing":     8218401167069060,
    "Events Brand Pgms":    6675193647812484,
    "CS Tech Sales":        5051180613848964,
    "Operations":           5367853921292164,
    "Field Operations":     6250576001060740,
    "IT Systems":           7235111354322820,
    "Shared Services":      5403651399962500,
    "Procurement":          7693547573563268,
    "Human Resources":      902645932838788,
    "Legal Compliance":     5580320584716164,
    "Product Mgmt":         6320592557920132,
    "RND Atonometrics":     4068792744234884,
    "RND Solar":            1097191845220228,
    "RND Met Road Wthr":    6007145844658052,
}

METRIC_NAMES = ["Total", "Done", "In Progress", "In Review", "To Do",
                "Roadblocked", "Overdue", "At Risk",
                "Tier 1", "Tier 2", "Tier 3",
                "Tier 1 Done", "Tier 2 Done", "Tier 3 Done"]

METRICS_ROW_MAP = {
    "Total":        "Total Assets",
    "Done":         "Complete",
    "In Progress":  "In Progress",
    "In Review":    "In Review",
    "To Do":        "Not Started",
    "Roadblocked":  "Roadblocked",
    "Overdue":      "Overdue",
    "At Risk":      "At Risk",
    "Tier 1":       "Tier 1",
    "Tier 2":       "Tier 2",
    "Tier 3":       "Tier 3",
    "Tier 1 Done":  "Tier 1 Done",
    "Tier 2 Done":  "Tier 2 Done",
    "Tier 3 Done":  "Tier 3 Done",
}

def get_summary_fields(sheet_name, sheet_id):
    url = f"{BASE_URL}/sheets/{sheet_id}/summary/fields"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"  ❌ Could not read summary for {sheet_name}: {response.status_code}")
        return {}
    fields = response.json().get("data", [])
    return {f["title"]: (f.get("objectValue") or 0) for f in fields}

def get_metrics_sheet():
    url = f"{BASE_URL}/sheets?includeAll=true"
    response = requests.get(url, headers=HEADERS)
    sheets = response.json().get("data", [])
    metrics_sheet = next(
        (s for s in sheets if "Dashboard Metric" in s.get("name", "")), None
    )
    if not metrics_sheet:
        print("❌ Metrics sheet not found")
        return None

    sheet_id = metrics_sheet["id"]
    url = f"{BASE_URL}/sheets/{sheet_id}"
    response = requests.get(url, headers=HEADERS)
    sheet_data = response.json()
    columns = sheet_data.get("columns", [])
    rows = sheet_data.get("rows", [])

    metric_col_id = next((c["id"] for c in columns if c["title"] == "Metric"), None)
    value_col_id  = next((c["id"] for c in columns if c["title"] == "Value"), None)

    row_map = {}
    for row in rows:
        for cell in row.get("cells", []):
            if cell.get("columnId") == metric_col_id:
                label = cell.get("value", "")
                if label:
                    row_map[label] = row["id"]

    return {
        "sheet_id":      sheet_id,
        "metric_col_id": metric_col_id,
        "value_col_id":  value_col_id,
        "row_map":       row_map
    }

def update_completion_by_sheet(sheet_id, metric_col_id, value_col_id, row_map):
    rows_to_update = []
    for sheet_name, asset_sheet_id in SHEETS.items():
        row_id = row_map.get(sheet_name)
        if not row_id:
            continue
        values = get_summary_fields(sheet_name, asset_sheet_id)
        done_count = int(values.get("Done", 0))
        rows_to_update.append({
            "id": row_id,
            "cells": [{"columnId": value_col_id, "value": done_count}]
        })

    if rows_to_update:
        url = f"{BASE_URL}/sheets/{sheet_id}/rows"
        requests.put(url, headers=HEADERS, json=rows_to_update)

def update_pct_complete(sheet_id, value_col_id, row_map, totals):
    pct = 0
    if totals.get("Total", 0) > 0:
        pct = round((totals["Done"] / totals["Total"]) * 100, 1)
    row_id = row_map.get("% Complete")
    if row_id:
        url = f"{BASE_URL}/sheets/{sheet_id}/rows"
        requests.put(url, headers=HEADERS, json=[{
            "id": row_id,
            "cells": [{"columnId": value_col_id, "value": pct}]
        }])
        print(f"  % Complete: {pct}%")

def update_metrics_sheet(sheet_info, totals):
    sheet_id     = sheet_info["sheet_id"]
    value_col_id = sheet_info["value_col_id"]
    row_map      = sheet_info["row_map"]

    rows_to_update = []
    for summary_field, row_label in METRICS_ROW_MAP.items():
        row_id = row_map.get(row_label)
        if not row_id:
            continue
        value = totals.get(summary_field, 0)
        rows_to_update.append({
            "id": row_id,
            "cells": [{"columnId": value_col_id, "value": value}]
        })

    if rows_to_update:
        url = f"{BASE_URL}/sheets/{sheet_id}/rows"
        response = requests.put(url, headers=HEADERS, json=rows_to_update)
        if response.status_code == 200:
            print("  ✅ Core metrics updated")
        else:
            print(f"  ❌ Update failed: {response.status_code}")

    # Update completion by sheet and % complete
    update_completion_by_sheet(sheet_id, sheet_info["metric_col_id"],
                               value_col_id, row_map)
    update_pct_complete(sheet_id, value_col_id, row_map, totals)

def main():
    print("=" * 60)
    print("Project OneBrand — Daily Metrics Updater")
    print("=" * 60)

    if not API_TOKEN:
        print("❌ SMARTSHEET_API_TOKEN environment variable not set.")
        exit(1)

    print("\n📊 Reading summary fields from all 14 sheets...")
    totals = {metric: 0 for metric in METRIC_NAMES}

    for sheet_name, sheet_id in SHEETS.items():
        values = get_summary_fields(sheet_name, sheet_id)
        if values:
            for metric in METRIC_NAMES:
                totals[metric] += int(values.get(metric, 0))
            print(f"  ✅ {sheet_name}: Total={int(values.get('Total',0))}, "
                  f"Done={int(values.get('Done',0))}, "
                  f"Tier1={int(values.get('Tier 1',0))}, "
                  f"Tier2={int(values.get('Tier 2',0))}, "
                  f"Tier3={int(values.get('Tier 3',0))}")

    print("\n📝 Updating metrics sheet...")
    sheet_info = get_metrics_sheet()
    if not sheet_info:
        exit(1)

    update_metrics_sheet(sheet_info, totals)

    print("\n" + "=" * 60)
    print("✅ Done. Dashboard metrics are up to date.")
    print("=" * 60)

if __name__ == "__main__":
    main()
