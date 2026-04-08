"""
Writes new postings to a Google Sheet, deduped against existing rows.
Never overwrites existing rows — only appends new ones.
User edits to Status, Notes, etc. are always preserved.
"""
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Column order in the sheet — must match what you set up in row 1
COLUMNS = [
    "Date Found", "Track", "Title", "Organization",
    "Location", "Source", "URL", "Status", "Notes"
]


def get_sheet(creds_json: str, sheet_id: str):
    """Open the Google Sheet using service account credentials."""
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet


def get_existing_urls(sheet) -> set[str]:
    """Pull all URLs already in the sheet so we can dedupe."""
    try:
        all_values = sheet.get_all_values()
        if len(all_values) <= 1:
            return set()
        headers = all_values[0]
        try:
            url_idx = headers.index("URL")
        except ValueError:
            print("  ⚠ 'URL' column not found in sheet headers")
            return set()
        urls = {row[url_idx].strip() for row in all_values[1:]
                if len(row) > url_idx and row[url_idx].strip()}
        return urls
    except Exception as e:
        print(f"  ⚠ Failed to read existing URLs: {e}")
        return set()


def append_postings(sheet, postings: list[dict]) -> int:
    """Append new postings to the sheet. Returns number of rows added."""
    if not postings:
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    rows = []
    for p in postings:
        rows.append([
            today,
            p.get("track", ""),
            p.get("title", ""),
            p.get("organization", ""),
            p.get("location", ""),
            p.get("source", ""),
            p.get("url", ""),
            "",  # Status — blank for user
            "",  # Notes — blank for user
        ])

    sheet.append_rows(rows, value_input_option="USER_ENTERED")
    return len(rows)


def write_new_postings(creds_json: str, sheet_id: str, postings: list[dict]) -> int:
    """End-to-end: open sheet, dedupe, append. Returns count of new rows added."""
    sheet = get_sheet(creds_json, sheet_id)
    existing = get_existing_urls(sheet)
    print(f"  {len(existing)} existing postings in sheet")

    new_postings = [p for p in postings if p.get("url", "").strip() not in existing]
    print(f"  {len(new_postings)} new postings to add (after dedupe)")

    if new_postings:
        # Sort by track so same-track jobs land together
        new_postings.sort(key=lambda p: p.get("track", ""))
        added = append_postings(sheet, new_postings)
        return added
    return 0
