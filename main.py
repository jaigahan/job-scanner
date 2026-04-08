"""
Main entry point for the job scanner.
Run this once a day. Reads config.yaml, scrapes all sources,
writes new postings to Google Sheets.

No scoring — user reviews all postings in the sheet and decides what to apply to.

Direct-scrape orgs are tiered by priority:
  - "daily"  → scraped every run
  - "weekly" → scraped only on Mondays
"""
import os
import sys
from datetime import datetime
import yaml

from scrapers.jobspy_scraper import scrape_jobspy_track, normalize_jobspy_results
from scrapers.direct_scraper import scrape_all_orgs
from tracker import write_new_postings


def load_config() -> dict:
    with open("config.yaml") as f:
        return yaml.safe_load(f)


def get_env_or_exit(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        print(f"❌ Missing required environment variable: {name}")
        sys.exit(1)
    return val


def dedupe_postings(postings: list[dict]) -> list[dict]:
    """Dedupe by URL, keeping the first occurrence."""
    seen = set()
    unique = []
    for p in postings:
        url = p.get("url", "").strip()
        if url and url not in seen:
            seen.add(url)
            unique.append(p)
    return unique


def main():
    print("=" * 60)
    print("JOB SCANNER — daily run")
    print("=" * 60)

    config = load_config()

    sheets_creds = get_env_or_exit("GOOGLE_SHEETS_CREDS")
    sheet_id = get_env_or_exit("SHEET_ID")

    all_postings = []

    # ─── Step 1: JobSpy scraping ───
    print("\n[1/3] Scraping LinkedIn and Indeed via JobSpy...")
    for track_name, track_config in config["tracks"].items():
        print(f"\n  Track: {track_config['label']}")
        df = scrape_jobspy_track(
            track_name=track_name,
            track_config=track_config,
            location=config["location"],
            lookback_days=config["lookback_days"],
        )
        normalized = normalize_jobspy_results(df)
        print(f"  → {len(normalized)} postings from this track")
        all_postings.extend(normalized)

    # ─── Step 2: Direct careers page scraping ───
    is_monday = datetime.now().weekday() == 0
    daily_count = sum(1 for o in config["direct_scrape_orgs"] if o.get("priority", "daily") == "daily")
    weekly_count = sum(1 for o in config["direct_scrape_orgs"] if o.get("priority", "daily") == "weekly")
    if is_monday:
        print(f"\n[2/3] Monday — scraping all {daily_count + weekly_count} organization careers pages "
              f"({daily_count} daily + {weekly_count} weekly)...")
    else:
        print(f"\n[2/3] Scraping {daily_count} daily-priority organization careers pages "
              f"(skipping {weekly_count} weekly — those run on Mondays)...")
    direct_postings = scrape_all_orgs(config["direct_scrape_orgs"], include_weekly=is_monday)
    print(f"  → {len(direct_postings)} candidate postings from direct scrapes")
    all_postings.extend(direct_postings)

    all_postings = dedupe_postings(all_postings)
    print(f"\n  Total unique postings: {len(all_postings)}")

    if not all_postings:
        print("\nNo postings found. Exiting.")
        return

    # ─── Step 3: Write to Google Sheet ───
    print(f"\n[3/3] Writing to Google Sheet...")
    added = write_new_postings(sheets_creds, sheet_id, all_postings)
    print(f"  → {added} new rows added to sheet")

    print("\n" + "=" * 60)
    print(f"Done. {added} new postings added to your tracker.")
    print("=" * 60)


if __name__ == "__main__":
    main()
