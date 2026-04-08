# Job Scanner

A free, automated daily job discovery system for Toronto-area roles in higher ed, nonprofits/foundations, government, and in-house corporate research/strategy.

## What it does

Every morning at 7am Toronto time, this script:
1. Scrapes LinkedIn and Indeed via JobSpy for your four search tracks
2. Scrapes ~30 high-priority organization careers pages every day, plus ~35 lower-priority ones on Mondays
3. Writes new postings to your Google Sheet, tagged with which track they belong to
4. Skips anything already in the sheet (so your edits and notes are preserved)

You read the sheet, decide what to apply to, and update the Status column as you go. **No AI scoring** — you review everything yourself and judge fit.

The four search tracks are:
- **Higher Ed / Nonprofit Research Enablement** — research officers, grant facilitators, knowledge mobilization, program managers at universities and hospital research institutes
- **Foundations / Nonprofits / Policy Organizations** — program officers, grants managers, impact & learning at foundations and policy bodies
- **Government (Federal / Provincial / Municipal)** — policy advisors, senior advisors, program consultants at OPS, federal departments, City of Toronto, Region of Peel, etc.
- **In-House Design Research / Strategy (Corporate)** — design researchers, UX researchers, insight managers, experience strategists at banks, insurance, retail, and tech companies

## One-time setup (about 45-60 minutes total)

### 1. Create a GitHub account (if you don't have one)
- https://github.com/signup — pick a username, verify your email. Free plan.

### 2. Set up Google Sheets access
This is the only external service you need. You'll create a "service account" — a robot Google account that writes to your sheet. **No credit card required.** The Sheets API is free forever.

**2a. Go to Google Cloud Console:**
- https://console.cloud.google.com
- If asked to pick a project, create a new one named `job-scanner`
- If you see a prompt for billing or credit card, skip/dismiss it — Sheets API does not need billing

**2b. Enable the required APIs:**
- In the left sidebar, click **APIs & Services → Library**
- Search for **"Google Sheets API"** → click the result → click **Enable**
- Go back to Library, search for **"Google Drive API"** → click → **Enable**
- (These are both free. No billing needed.)

**2c. Create a service account:**
- Go to **APIs & Services → Credentials**
- Click **+ Create Credentials → Service account**
- Name: `job-scanner-bot`
- Click **Create and Continue**, skip the optional Role step, click **Done**
- Click on the new service account in the list
- Go to the **Keys** tab
- Click **Add Key → Create new key → JSON → Create** 
- A JSON file downloads to your computer. **Keep it safe.** You'll paste its contents into GitHub in step 4.
- Copy the service account email — it looks like `job-scanner-bot@job-scanner-xxxxx.iam.gserviceaccount.com`

### 3. Create your Google Sheet
- Go to https://sheets.google.com and create a new sheet, name it `Job Scanner`
- In row 1, add these column headers exactly:
  ```
  Date Found | Track | Title | Organization | Location | Source | URL | Status | Notes
  ```
  (Each on its own column — Date Found in A1, Track in B1, Title in C1, etc.)
- Click **Share** (top right) → paste the service account email from step 2c → set to **Editor** → click **Send**
- Copy the sheet's URL from your browser. You need the long ID between `/d/` and `/edit`. For example, in `https://docs.google.com/spreadsheets/d/1ABCxyz123/edit` the ID is `1ABCxyz123`.

### 4. Fork this repo and add secrets
- On GitHub, create a new repository named `job-scanner` (or fork this one if you received it as a template)
- Make sure the repo is **Public** (so GitHub Actions stay free and unlimited)
- Upload all the files from the zip into your new repo
- Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**
- Add these two secrets:
  - `GOOGLE_SHEETS_CREDS` — paste the *entire contents* of the JSON file from step 2c (open it in a text editor, copy everything)
  - `SHEET_ID` — paste the sheet ID from step 3

### 5. Review config (optional)
- Open `config.yaml` in GitHub's web editor (pencil icon)
- Scan the keywords and org list — add/remove if you want
- Commit changes

### 6. Test it
- Go to the **Actions** tab in your repo
- You may see a message asking to enable workflows — click **I understand, enable them**
- Click **Daily Job Scan** in the left sidebar → **Run workflow** → **Run workflow** (green button)
- Wait 3-10 minutes, then check your Google Sheet for new rows

Done. From now on, it runs automatically every morning at 7am Toronto time.

## Day-to-day use

- Open the sheet each morning
- Sort by Track if you want to focus on one category at a time
- Update the Status column as you apply (Interested / Applied / Interview / Rejected / Offer)
- Add notes in the Notes column — your edits are never overwritten
- To add a new organization to monitor, edit `config.yaml` in GitHub and commit
- To change keywords, edit `config.yaml`

## Cost

- GitHub Actions: free (unlimited for public repos)
- Google Sheets API: free, no billing required
- **Total: $0/month, forever, with no credit card**

## When something breaks

Websites change their HTML occasionally and a scraper will stop returning results. When this happens:
- Check the Actions tab on GitHub — failed runs are marked with a red X
- Click the failed run to see the error
- Most fixes are small (a URL that moved). Open an issue or paste the error to Claude and ask for a fix.
