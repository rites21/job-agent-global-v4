# PROJECT_CONTEXT.md

## 1. Project Purpose

This repository contains a personal job-search agent for discovering, filtering, ranking, and reviewing software engineering jobs.

The agent is designed for a backend-focused Senior Software Engineer / SDE II profile and should optimize for:
- strong technical fit,
- realistic seniority,
- location / work-authorization compatibility,
- sponsorship / relocation signals,
- low-noise results,
- repeatable daily usage.

The current goal is NOT to auto-apply to jobs yet.

Current objective:
1. scrape jobs,
2. filter obvious mismatches locally,
3. rank the strongest candidates,
4. use Gemini for semantic JD/resume matching,
5. categorize jobs into useful application buckets,
6. save results for manual review and later application tracking.

---

## 2. Candidate Profile

Approximate experience:
- 5.5 years total software engineering experience.

Target roles:
- Senior Software Engineer
- Software Engineer II
- SDE II / SDE2
- Senior Backend Engineer
- Backend Engineer
- Senior Software Developer
- Platform Engineer, only when backend/platform work is the primary responsibility

Primary technical profile:
- Java
- Java 17
- Spring Boot
- REST APIs
- Microservices
- Distributed systems
- Kafka
- Redis
- SQL
- MySQL / PostgreSQL
- AWS
- Docker
- Multithreading / concurrency
- WebSockets
- Hibernate / JPA
- Spring Security
- CI/CD
- event-driven systems

Additional AI / modern backend exposure:
- LLM integration
- Agentic workflows
- RAG
- embeddings
- semantic search
- prompt engineering
- tool calling
- LangChain / Spring AI exposure

Roles that should usually be penalized or excluded:
- SDET / SET
- QA / Manual Testing
- Salesforce development
- Frontend-only
- Mobile-only
- Data Science
- ML Scientist
- ML-first roles
- DevOps / SRE / Release Engineering when it is the primary function
- Principal Engineer
- Staff Engineer
- Engineering Manager
- Architect
- Sales Engineer
- Developer Advocate

---

## 3. Search Strategy

The agent should NOT treat every geography equally.

Preferred approximate distribution for AI-analyzed jobs:

### India Priority: ~70%

Highest priority.

Preferred locations include:
- Bengaluru / Bangalore
- Hyderabad
- Pune
- Gurgaon / Gurugram
- Noida
- Delhi NCR
- Chennai
- Mumbai
- Remote India

These roles should receive priority because they do not require international work authorization or relocation.

### Global Sponsorship / Relocation: ~20%

Include international jobs when there is a meaningful signal such as:
- visa sponsorship,
- work-permit sponsorship,
- relocation assistance,
- relocation package,
- global mobility,
- skilled worker visa,
- immigration support,
- explicit willingness to sponsor.

Do not assume sponsorship when the JD is silent.

Potentially useful markets include:
- Germany
- Netherlands
- Ireland
- United Kingdom
- Canada
- Singapore
- UAE
- selected European markets
- other countries when the JD explicitly supports international relocation

### Genuine Global Remote: ~10%

Only count a foreign remote role as globally usable when the JD explicitly supports something like:
- worldwide remote,
- global remote,
- remote from India,
- India-compatible remote,
- APAC remote that includes India,
- cross-border employment,
- employer-of-record / contractor setup that supports India.

Do NOT treat the following as global remote:
- Remote - US
- Remote - Canada
- Remote - Ontario
- Remote - UK
- remote roles restricted to a specific country/state/province

"Remote" alone is not enough.

Do not force the 70/20/10 percentages if there are not enough high-quality jobs in one bucket.

---

## 4. Current Version

Current working version:
- V4 Gemini

Primary script:
- `job_agent_v4_gemini.py`

Current AI provider:
- Gemini

Environment variables:
- `GEMINI_API_KEY`
- `AI_PROVIDER=gemini`
- `GEMINI_MODEL=gemini-3.5-flash-lite`
- `AI_ANALYZE_LIMIT`
- `GENERATE_PACKAGES`
- `PACKAGE_LIMIT`

Current tested small-run configuration:

```bash
export AI_PROVIDER="gemini"
export GEMINI_MODEL="gemini-3.5-flash-lite"
export AI_ANALYZE_LIMIT=10

python3 job_agent_v4_gemini.py
```

Never commit API keys to the repository.

Never hardcode secrets in source files.

---

## 5. Resume Handling

The script expects one of:

- `resume.txt`
- `resume.pdf`

`resume.txt` is preferred when present.

For PDF extraction the project uses:

```python
from pypdf import PdfReader
```

Required dependency:

```bash
python3 -m pip install pypdf
```

The working run has already confirmed:

```text
Resume loaded         : YES
```

Gemini should always receive resume content when available.

---

## 6. Current Pipeline

Current approximate flow:

```text
ATS boards
   ↓
Greenhouse / Lever scraping
   ↓
all_jobs
   ↓
country detection
   ↓
eligibility signal
   ↓
rough_prefilter()
   ↓
rough_score()
   ↓
sort candidates
   ↓
top AI_ANALYZE_LIMIT
   ↓
Gemini semantic analysis
   ↓
SQLite cache
   ↓
CSV + JSON + database
```

Current successful full flow has already been validated with 10 Gemini-analyzed jobs.

---

## 7. Current Data Sources

Current configured boards include companies such as:
- Stripe
- Coinbase
- Databricks
- Cloudflare
- Brex
- Figma
- MongoDB
- Okta
- Elastic
- Reddit
- Pinterest
- Asana

Some board identifiers are currently stale / broken and return HTTP 404:
- Notion
- Ramp
- Rippling
- Postman
- BrowserStack

Do not let one broken board stop the whole run.

Continue scraping remaining sources when one board fails.

Do not rewrite the scraper merely because some board tokens are stale.

---

## 8. Current Output Files

Current V4 produces:

- `jobs_v4.db`
- `top_jobs_v4.csv`
- `ai_matches_v4.json`
- `application_packages.json` when package generation is enabled

Target V4.1 outputs should be:

- `jobs_v4.db`
- `top_jobs_v4.csv`
- `apply_now.csv`
- `review.csv`
- `skipped.csv`
- `ai_matches_v4.json`
- optional `application_packages.json`

Future optional reporting:
- HTML dashboard/report
- PDF summary report

The PDF, if added later, is only a report.
It does NOT mean that applications were submitted.

---

## 9. Gemini Output Contract

Gemini job analysis should preserve this logical schema:

```json
{
  "overall_fit": 0,
  "technical_fit": 0,
  "experience_fit": 0,
  "role_fit": 0,
  "location_eligibility": 0,
  "sponsorship_assessment": "UNKNOWN",
  "role_family": "",
  "strong_matches": [],
  "gaps": [],
  "red_flags": [],
  "evidence": [],
  "action": "REVIEW"
}
```

Allowed `sponsorship_assessment` values:
- `SUPPORTED`
- `POSSIBLE`
- `UNKNOWN`
- `NEGATIVE`
- `NOT_NEEDED`

Allowed `action` values:
- `APPLY_REVIEW`
- `REVIEW`
- `SKIP`

The AI must:
- avoid inventing candidate experience,
- avoid inventing sponsorship,
- avoid predicting hiring probability,
- distinguish role fit from keyword overlap,
- identify material skill gaps,
- penalize wrong role families,
- respect explicit work-authorization blockers.

---

## 10. Current Ranking Principles

Strong positive signals:
- Java
- Spring Boot
- backend engineering
- microservices
- distributed systems
- REST APIs
- Kafka
- Redis
- SQL
- AWS
- concurrency
- platform/backend engineering
- high-quality product engineering
- scalable backend systems

Negative signals:
- Salesforce-specific role
- SDET / QA
- Frontend
- Mobile
- Data Science
- ML-first
- Release Infrastructure
- SRE-first
- DevOps-first
- Staff / Principal / Manager
- location restrictions
- no sponsorship
- experience requirement materially above 5.5 years

Generic skills like Python, SQL, or AWS must not compensate for a major role-family mismatch.

---

## 11. Known Issues

### 11.1 Country Detection Bug

Known bad example:

```text
Location: Belgrade, Serbia
Detected country: United States
```

Reason:
- Serbia is missing from country/location mappings.
- When the location field does not resolve, current logic searches JD text.
- The JD may contain references to another country such as the US.

Required fix:
- explicit location should be authoritative whenever it can be resolved,
- expand country mappings,
- add Serbia,
- avoid letting incidental JD country references override the actual location.

### 11.2 Cache Invalidation Bug

Current job fingerprint is based mainly on:
- job title
- job location
- job description

This is insufficient.

If the resume or profile changes, old Gemini results can be reused incorrectly.

V4.1 cache fingerprint must include:
- normalized job data / JD,
- resume content,
- profile.json content,
- AI provider,
- model.

Changing any of those should invalidate the old semantic result.

### 11.3 Pre-ranking Can Be Better

Current `rough_score()` is relatively simple.

This means Gemini calls can be spent on:
- Release Infrastructure,
- Salesforce,
- weak platform matches,
- geography-restricted roles,

while better Java/backend jobs may exist deeper in the scraped set.

Before increasing to 100+ Gemini calls, improve deterministic pre-ranking.

### 11.4 Stale ATS Board Tokens

Some configured ATS boards currently return 404.

Do not block V4.1 on fixing all of them.
Treat stale boards as a separate discovery/source-maintenance task.

---

## 12. V4.1 Requirements

Do NOT rewrite the existing working scraper or Gemini integration unless necessary.

Implement these changes incrementally.

### A. Search Buckets

Each candidate should be classified into one of:

- `INDIA_PRIORITY`
- `GLOBAL_SPONSORSHIP`
- `GLOBAL_REMOTE`
- `LOW_PRIORITY`
- `INELIGIBLE`

Store the bucket in the job record and CSV outputs.

### B. Better Local Pre-ranking

Improve deterministic ranking before Gemini.

Suggested dimensions:
- role-family score,
- Java/Spring/backend stack score,
- distributed-systems score,
- seniority fit,
- experience requirement fit,
- location score,
- sponsorship score,
- remote eligibility score,
- explicit negative-role penalty.

The local ranker should be explainable.

Do not make it an opaque random weighted score.

### C. AI Candidate Distribution

For the AI stage, approximately target:
- 70% India,
- 20% sponsorship/relocation,
- 10% genuine global remote.

Do not force a bucket to fill its quota with weak jobs.

Strong jobs should always beat weak jobs.

### D. Country Detection

Fix Serbia and expand mappings sensibly.

Explicit location field should have stronger authority than incidental JD text.

### E. Cache Fingerprint

Cache should depend on:

```text
job + resume + profile + provider + model
```

### F. Output Splits

Generate:

#### `apply_now.csv`
Jobs with:
- strong role fit,
- no explicit eligibility blocker,
- action `APPLY_REVIEW`,
- useful application priority.

#### `review.csv`
Jobs where:
- some uncertainty remains,
- action is `REVIEW`.

#### `skipped.csv`
Jobs where:
- action is `SKIP`,
- or explicit mismatch / eligibility blocker exists.

Preserve `top_jobs_v4.csv` for backward compatibility.

---

## 13. SQLite / State Requirements

Database:
- `jobs_v4.db`

Current tables include:
- `jobs`
- `ai_cache`

Preserve existing job status when refreshing job data.

Future job/application statuses may include:

- `NEW`
- `REVIEWED`
- `APPLIED`
- `REFERRAL_REQUESTED`
- `INTERVIEW`
- `REJECTED`
- `ARCHIVED`

Do not implement automatic job applications yet.

The database should eventually prevent the same jobs from appearing as brand-new every day.

---

## 14. Application Package Feature

Current application package generation is optional.

It can generate things such as:
- tailored summary,
- resume bullets to emphasize,
- recruiter message,
- application question answers.

It must never invent:
- technologies,
- employers,
- metrics,
- work authorization,
- visa status,
- experience.

Keep this disabled by default while ranking quality is still being tuned.

---

## 15. AI Provider Strategy

Primary:
- Gemini

Current model:
- `gemini-3.5-flash-lite`

Possible future provider architecture:

```text
Gemini
   ↓ quota/error
DeepSeek
   ↓ failure
deterministic fallback matcher
```

Do NOT call multiple LLM providers on every job.

Possible later use:
- use a second model only for final top jobs,
- or as a fallback when Gemini is unavailable.

The existing JSON contract should remain provider-independent.

---

## 16. Required Console Summary

V4.1 should print clear statistics such as:

```text
Total scraped:
Candidates after hard filtering:
India candidates:
Sponsorship/relocation candidates:
Global remote candidates:
Low-priority candidates:
AI analyzed:
AI cache hits:
APPLY_REVIEW:
REVIEW:
SKIP:
```

Keep per-job progress output concise.

---

## 17. Testing Rules

Do not immediately test with 100+ AI calls after a major change.

Testing sequence:

### Step 1: Syntax

```bash
python3 -m py_compile job_agent_v4_gemini.py
```

or the new V4.1 filename.

No output means syntax is valid.

### Step 2: Small Run

```bash
export AI_ANALYZE_LIMIT=10
python3 job_agent_v4_gemini.py
```

Validate:
- Resume loaded = YES
- Gemini enabled
- 10 candidates analyzed
- country detection correct
- no unexpected fallback
- output CSVs created
- AI actions look reasonable

### Step 3: Cache Test

Run again without changes.

Expected:
- same jobs should use cache.

Then change resume/profile test data and confirm:
- old cache is not reused.

### Step 4: Larger Run

Only after reviewing 10-job results:

```bash
export AI_ANALYZE_LIMIT=100
python3 job_agent_v4_gemini.py
```

Do not scale before quality is validated.

---

## 18. Coding Rules for Codex

When making changes:

1. Read this entire file first.
2. Inspect current code before editing.
3. Do not rewrite working components without a clear reason.
4. Prefer small, testable changes.
5. Preserve current output compatibility when reasonable.
6. Preserve SQLite job status.
7. Never hardcode secrets.
8. Do not commit API keys.
9. Run `py_compile` after editing.
10. Show the diff / summarize exactly what changed.
11. Provide exact shell commands to test.
12. Do not enable auto-application.
13. Do not silently alter the candidate profile.
14. Do not silently broaden target roles.
15. Do not assume "remote" means globally remote.
16. Do not assume sponsorship unless the JD supports it.
17. Do not discard high-quality India jobs because of an artificial global quota.
18. Do not spend LLM calls on obvious mismatches that local logic can reject.

---

## 19. Git Workflow

Before major Codex edits, create a checkpoint:

```bash
git add .
git commit -m "working v4 gemini baseline"
```

After Codex changes:

```bash
git status
git diff
```

Review before committing.

Then:

```bash
git add .
git commit -m "v4.1 location ranking cache improvements"
```

Use Git as the exact history of code changes.

---

## 20. CHANGELOG_AGENT.md Recommendation

Maintain a separate:

```text
CHANGELOG_AGENT.md
```

Example:

```markdown
# Agent Changelog

## 2026-10-03

- Gemini API integration confirmed working.
- Resume PDF extraction confirmed working.
- 10-job Gemini run completed successfully.
- Known Serbia country detection bug identified.
- Resume/profile-aware cache invalidation planned.
- V4.1 India/global search bucketing planned.
```

Codex should append to this file after meaningful changes.

---

## 21. Current Known-Good Checkpoint

The following has been tested successfully:

```text
GLOBAL AI JOB AGENT — V4

AI semantic matching : ENABLED
AI provider/model     : gemini / gemini-3.5-flash-lite
Resume loaded         : YES
AI analyze limit      : 10
AI cache              : ENABLED
Application packages  : DISABLED
```

A 10-job fresh Gemini analysis completed successfully with:

```text
AI cache hits: 0
Saved: top_jobs_v4.csv
Saved: ai_matches_v4.json
```

The overall semantic matcher is functioning.

Do not replace it with a new architecture just because a cleaner refactor is possible.

Improve the current working system incrementally.

---

## 22. Immediate Next Task

The immediate V4.1 task is:

1. add India / sponsorship / global-remote buckets,
2. improve deterministic pre-ranking,
3. fix country detection,
4. make AI cache resume/profile-aware,
5. create split output CSVs,
6. preserve current Gemini behavior,
7. run `py_compile`,
8. test with `AI_ANALYZE_LIMIT=10`,
9. inspect results before scaling.

Do not auto-apply to jobs yet.

---

## 23. Prompt to Start a New Codex Session

Use:

```text
Read PROJECT_CONTEXT.md completely before making any changes.

Then inspect the current repository and the working
job_agent_v4_gemini.py implementation.

Continue from the current V4 Gemini baseline.

Implement only the immediate V4.1 task described in
PROJECT_CONTEXT.md.

Do not rewrite the scraper or working Gemini integration unless
the change is necessary.

Keep changes incremental and testable.

After editing:
1. run py_compile,
2. show/summarize the diff,
3. tell me exactly how to test with AI_ANALYZE_LIMIT=10,
4. update CHANGELOG_AGENT.md.
```

## 24. Current assisted application workflow

Follow `APPLICATION_WORKFLOW.md` for browser applications. This updates the earlier
research-only scope: factual form preparation is permitted, but every final
submission requires explicit user review/approval. Use `application_workflow.py`
for fresh database checks and verified outcome recording. Never mark APPLIED
until an actual success confirmation has been observed. Preserve `applied_at`
on subsequent job refreshes. The previous ten jobs are now recorded APPLIED in the database and must be
skipped. Their historical application dates are not inferred.
