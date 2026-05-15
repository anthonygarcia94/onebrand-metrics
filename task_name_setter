"""
OneBrand K&Z — Daily Task Name Setter
======================================
Scans all 14 department sheets for new form submissions and sets
Task Name to: Asset Type [Descriptor]

Examples:
  Promotional: Branded Clothing [New T-Shirts With Logos]
  Print: Case Study [Solar Consumption Savings City of Denver]
  Digital: Social Media [Promoting Pyranometers Product Launch]

RULES:
  ✓ Only updates rows where Asset Type is filled in AND Task Name is blank
  ✓ Skips rows where Task Name already has a value (never overwrites)
  ✓ Skips header/parent rows automatically (they have no Asset Type)
  ✓ Processes in batches of 50 rows

TESTING:
  Set TEST_MODE = False  → only runs on Events Brand Programs
  Set TEST_MODE = False → runs on all 14 sheets

SCHEDULING (GitHub Actions):
  See .github/workflows/daily_task_name.yml for the daily schedule config.
  Store your API token as a GitHub secret: SMARTSHEET_API_TOKEN
"""

import requests
import os

# ── CONFIG ────────────────────────────────────────────────────────────────────

# Set to True to test on one sheet first, False to run on all 14
TEST_MODE = False

# API token — reads from environment variable (for GitHub Actions)
# or falls back to the value below for local/Colab use
API_TOKEN = os.environ.get("SMARTSHEET_API_TOKEN", "YOUR_API_TOKEN_HERE")

BASE_URL   = "https://api.smartsheet.com/2.0"
HEADERS    = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type":  "application/json"
}
BATCH_SIZE = 50

# ── SHEET IDs ─────────────────────────────────────────────────────────────────

TEST_SHEET_ID = 6675193647812484   # Events Brand Programs — test sheet

ALL_SHEET_IDS = [
    8218401167069060,   # Growth Marketing
    5051180613848964,   # Cust Service & Technical Sales
    6675193647812484,   # Events Brand Programs
    6250576001060740,   # Field Operations
     902645932838788,   # Human Resources
    7235111354322820,   # IT Systems
    5580320584716164,   # Legal & Compliance
    5367853921292164,   # Operations
    7693547573563268,   # Procurement
    6320592557920132,   # Product Management
    4068792744234884,   # RND Atonometrics
    6007145844658052,   # RND Met Road Weather
    1097191845220228,   # RND Solar
    5403651399962500,   # Shared Services
]

SHEET_IDS = [TEST_SHEET_ID] if TEST_MODE else ALL_SHEET_IDS

# ── HELPERS ───────────────────────────────────────────────────────────────────

def get_sheet(sheet_id):
    """Fetch full sheet including rows and columns."""
    resp = requests.get(
        f"{BASE_URL}/sheets/{sheet_id}",
        headers=HEADERS
    )
    resp.raise_for_status()
    return resp.json()


def get_col_id(columns, title):
    """Find a column ID by exact title match."""
    match = next((c for c in columns if c["title"] == title), None)
    if not match:
        raise ValueError(f"Column not found: '{title}'")
    return match["id"]


def get_cell_value(row, col_id):
    """Get the display value of a cell by column ID, or None if blank."""
    cell = next((c for c in row.get("cells", []) if c["columnId"] == col_id), None)
    if not cell:
        return None
    return cell.get("displayValue") or cell.get("value") or None


def build_task_name(asset_type, descriptor):
    """Combine asset type and descriptor into the Task Name."""
    if descriptor:
        return f"{asset_type} [{descriptor}]"
    return asset_type


def update_rows_batch(sheet_id, row_updates):
    """PUT a batch of row updates to the sheet."""
    resp = requests.put(
        f"{BASE_URL}/sheets/{sheet_id}/rows",
        headers=HEADERS,
        json=row_updates
    )
    if not resp.ok:
        print(f"    !! API error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    return resp.json()


# ── MAIN LOGIC ────────────────────────────────────────────────────────────────

def process_sheet(sheet_id):
    sheet      = get_sheet(sheet_id)
    sheet_name = sheet["name"]
    columns    = sheet["columns"]
    rows       = sheet.get("rows", [])

    print(f"\nSheet: {sheet_name}")
    print(f"  Total rows: {len(rows)}")

    # Get column IDs we care about
    task_name_col  = get_col_id(columns, "Task Name")
    asset_type_col = get_col_id(columns, "Asset Type")
    descriptor_col = get_col_id(columns, "What is this asset for")

    # Find rows that need updating:
    #   - Asset Type is filled in (it's a real form submission)
    #   - Task Name is blank (hasn't been set yet)
    rows_to_update = []
    for row in rows:
        asset_type = get_cell_value(row, asset_type_col)
        task_name  = get_cell_value(row, task_name_col)

        if asset_type and not task_name:
            descriptor = get_cell_value(row, descriptor_col)
            new_name   = build_task_name(asset_type, descriptor)
            rows_to_update.append({
                "id":    row["id"],
                "cells": [{
                    "columnId": task_name_col,
                    "value":    new_name
                }]
            })

    if not rows_to_update:
        print(f"  ✓ Nothing to update — all submissions already have Task Names")
        return 0

    print(f"  Found {len(rows_to_update)} row(s) to update")

    # Process in batches of BATCH_SIZE
    updated = 0
    for i in range(0, len(rows_to_update), BATCH_SIZE):
        batch = rows_to_update[i:i + BATCH_SIZE]
        update_rows_batch(sheet_id, batch)
        updated += len(batch)
        print(f"  ✓ Batch {i // BATCH_SIZE + 1}: updated {len(batch)} row(s)")

    return updated


# ── RUN ───────────────────────────────────────────────────────────────────────

mode_label = "TEST MODE — Events Brand Programs only" if TEST_MODE else "FULL RUN — all 14 sheets"
print(f"── Task Name Setter ── {mode_label} ──")

total_updated = 0
errors        = []

for sheet_id in SHEET_IDS:
    try:
        total_updated += process_sheet(sheet_id)
    except Exception as e:
        print(f"  ✗ Error on sheet {sheet_id}: {type(e).__name__}: {e}")
        errors.append(sheet_id)

print(f"\n── Summary ───────────────────────────")
print(f"  ✓ Rows updated: {total_updated}")
print(f"  Sheets run:     {len(SHEET_IDS)}")
if errors:
    print(f"  ✗ Errors:       {errors}")
print(f"──────────────────────────────────────\n")
