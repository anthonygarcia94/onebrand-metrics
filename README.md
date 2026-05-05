# OneBrand Smartsheet Metrics Automation

Automatically updates the K&Z OneBrand dashboard metrics sheet daily using GitHub Actions.

## What it does
Reads summary field values (Total, Done, In Progress, etc.) from all 14 K&Z OneBrand asset sheets and writes the aggregated totals into the Dashboard Metrics sheet. This keeps both the PM Dashboard and Executive Snapshot current without any manual intervention.

## Schedule
Runs automatically Monday–Friday at 8:00 AM Mountain Time.
Can also be triggered manually from the Actions tab at any time.

## Setup

### 1. Add your Smartsheet API token as a GitHub Secret
1. Go to your GitHub repo → **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Name: `SMARTSHEET_API_TOKEN`
4. Value: paste your Smartsheet API token
5. Click **Add secret**

### 2. That's it
GitHub Actions will pick up the workflow automatically on the next scheduled run.

## Manual run
Go to **Actions → OneBrand Daily Metrics Update → Run workflow** to trigger it immediately.

## Files
- `update_metrics.py` — the main script
- `.github/workflows/daily_metrics.yml` — the schedule configuration
- `requirements.txt` — Python dependencies

## Adjusting the schedule
Edit the cron expression in `.github/workflows/daily_metrics.yml`:
- `"0 14 * * 1-5"` = 8 AM MT, weekdays only
- `"0 14 * * *"` = 8 AM MT, every day including weekends
- `"0 14,20 * * 1-5"` = 8 AM and 2 PM MT, weekdays
