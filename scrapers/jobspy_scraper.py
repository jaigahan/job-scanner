"""
Scrapes LinkedIn and Indeed via JobSpy for each search track.
JobSpy handles the messy stuff (LinkedIn auth, rate limiting, parsing).
"""
from jobspy import scrape_jobs
import pandas as pd


def scrape_jobspy_track(track_name: str, track_config: dict, location: str, lookback_days: int) -> pd.DataFrame:
    """Run JobSpy for one track's keywords. Returns a DataFrame of postings."""
    all_results = []

    for keyword in track_config["keywords"]:
        try:
            jobs = scrape_jobs(
                site_name=["linkedin", "indeed"],
                search_term=keyword,
                location=location,
                results_wanted=15,
                hours_old=lookback_days * 24,
                country_indeed="canada",
                linkedin_fetch_description=False,
            )
            if jobs is not None and len(jobs) > 0:
                jobs["track"] = track_name
                jobs["search_keyword"] = keyword
                all_results.append(jobs)
        except Exception as e:
            print(f"  ⚠ JobSpy failed for '{keyword}': {e}")

    if not all_results:
        return pd.DataFrame()

    combined = pd.concat(all_results, ignore_index=True)
    combined = combined.drop_duplicates(subset=["job_url"], keep="first")
    return combined


def normalize_jobspy_results(df: pd.DataFrame) -> list[dict]:
    """Normalize JobSpy DataFrame to our standard posting dict format."""
    if df.empty:
        return []

    postings = []
    for _, row in df.iterrows():
        posting = {
            "title": str(row.get("title", "")).strip(),
            "organization": str(row.get("company", "")).strip(),
            "location": str(row.get("location", "")).strip(),
            "url": str(row.get("job_url", "")).strip(),
            "source": str(row.get("site", "")).strip(),
            "track": str(row.get("track", "")).strip(),
            "search_keyword": str(row.get("search_keyword", "")).strip(),
        }
        if posting["url"] and posting["title"]:
            postings.append(posting)
    return postings
