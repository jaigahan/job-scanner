"""
Scrapes specific organization careers pages directly.

Each org's careers page has a unique HTML structure, so we use a generic approach:
fetch the page, extract all links that look like job postings, and tag each with
the track the org belongs to.

This is intentionally lossy — direct scraping of corporate Workday/Taleo sites is
fragile, and the goal is breadth-of-coverage rather than perfect parsing. The
LinkedIn/Indeed scrapes via JobSpy will catch most of these orgs anyway; this
direct layer is a backup for the ones that don't post to aggregators.
"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

JOB_LINK_HINTS = [
    "job", "career", "position", "opening", "opportunity", "posting",
    "requisition", "req", "/r/", "/jobs/", "/careers/"
]


def looks_like_job_link(href: str, text: str) -> bool:
    """Heuristic: does this link look like it points to a specific job posting?"""
    if not href:
        return False
    href_lower = href.lower()
    text_lower = (text or "").lower().strip()

    skip_terms = ["login", "sign in", "privacy", "cookie", "terms", "about us",
                  "contact", "faq", "search", "filter", "language", "français"]
    if any(term in text_lower for term in skip_terms):
        return False

    has_hint = any(hint in href_lower for hint in JOB_LINK_HINTS)

    looks_like_title = (
        len(text_lower) > 8
        and len(text_lower) < 120
        and any(role_word in text_lower for role_word in [
            "research", "manager", "officer", "analyst", "specialist",
            "director", "coordinator", "lead", "advisor", "strategist",
            "writer", "facilitator", "developer", "scientist", "designer",
            "consultant", "policy", "program", "planner"
        ])
    )

    return has_hint or looks_like_title


def scrape_org_page(name: str, url: str, track: str) -> list[dict]:
    """Fetch one careers page and extract candidate job postings."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ⚠ Failed to fetch {name}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    base = url

    postings = []
    seen_urls = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)

        if not looks_like_job_link(href, text):
            continue

        full_url = urljoin(base, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        if len(text) < 5:
            continue

        postings.append({
            "title": text[:200],
            "organization": name,
            "location": "Toronto, ON",
            "url": full_url,
            "source": "direct_scrape",
            "track": track,
        })

        if len(postings) >= 30:
            break

    return postings


def scrape_all_orgs(orgs: list[dict], include_weekly: bool = False) -> list[dict]:
    """Scrape configured org careers pages.

    By default only scrapes orgs marked priority='daily'.
    If include_weekly=True (typically on Mondays), also scrapes priority='weekly' orgs.
    """
    all_postings = []
    for org in orgs:
        priority = org.get("priority", "daily")
        if priority == "weekly" and not include_weekly:
            continue
        print(f"  → {org['name']} ({priority})")
        postings = scrape_org_page(
            name=org["name"],
            url=org["url"],
            track=org.get("track", "other"),
        )
        print(f"    found {len(postings)} candidate postings")
        all_postings.extend(postings)
    return all_postings
