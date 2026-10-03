import csv

import json

import os

import re

import sqlite3

from datetime import datetime, timezone

from pathlib import Path



import requests
from application_workflow import url_key



PROFILE_FILE = "profile.json"

DB_FILE = "jobs_v4.db"

CSV_FILE = "top_jobs_v4.csv"

JSON_FILE = "ai_matches_v4.json"
APPLY_CSV_FILE = "apply_now.csv"
REVIEW_CSV_FILE = "review.csv"
SKIPPED_CSV_FILE = "skipped.csv"
NOT_ANALYZED_CSV_FILE = "not_analyzed.csv"

PACKAGES_FILE = "application_packages.json"

RESUME_TEXT_FILE = "resume.txt"

RESUME_PDF_FILE = "resume.pdf"



AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
AI_ANALYZE_LIMIT = int(os.getenv("AI_ANALYZE_LIMIT", "100"))
MIN_AI_ROUGH_SCORE = float(os.getenv("MIN_AI_ROUGH_SCORE", "55"))

GENERATE_PACKAGES = os.getenv("GENERATE_PACKAGES", "false").lower() == "true"

PACKAGE_LIMIT = int(os.getenv("PACKAGE_LIMIT", "5"))



BOARDS = [

    {"company": "Stripe", "ats": "greenhouse", "token": "stripe"},

    {"company": "Coinbase", "ats": "greenhouse", "token": "coinbase"},

    {"company": "Databricks", "ats": "greenhouse", "token": "databricks"},

    {"company": "Cloudflare", "ats": "greenhouse", "token": "cloudflare"},

    {"company": "Notion", "ats": "greenhouse", "token": "notion"},

    {"company": "Ramp", "ats": "greenhouse", "token": "ramp"},

    {"company": "Brex", "ats": "greenhouse", "token": "brex"},

    {"company": "Rippling", "ats": "greenhouse", "token": "rippling"},

    {"company": "Figma", "ats": "greenhouse", "token": "figma"},

    {"company": "MongoDB", "ats": "greenhouse", "token": "mongodb"},

    {"company": "Okta", "ats": "greenhouse", "token": "okta"},

    {"company": "Elastic", "ats": "greenhouse", "token": "elastic"},

    {"company": "Reddit", "ats": "greenhouse", "token": "reddit"},

    {"company": "Pinterest", "ats": "greenhouse", "token": "pinterest"},

    {"company": "Asana", "ats": "greenhouse", "token": "asana"},

    {"company": "Postman", "ats": "lever", "token": "postman"},

    {"company": "BrowserStack", "ats": "lever", "token": "browserstack"},

]



BAD_TITLE_WORDS = [

    "intern", "internship", "frontend", "ios", "android", "qa engineer",

    "manual tester", "designer", "data scientist", "machine learning scientist",

    "engineering manager", "software engineering manager", "principal engineer",

    "staff engineer", "architect", "solutions architect", "sales engineer",

    "developer advocate",

    "software engineer in test", "sdet", "quality engineer", "test automation",
    "salesforce", "front-end", "fullstack", "full stack", "mobile engineer",
    "ios engineer", "android engineer", "devops", "site reliability", "sre",
    "release engineer", "release engineering", "release infrastructure"

]



ROLE_FAMILIES = {

    "backend": [

        "backend", "back-end", "server-side", "platform", "distributed systems",

        "infrastructure", "core services", "api", "services engineer", "platform engineering",
        "backend engineering", "distributed systems engineer"

    ],

    "software": ["software engineer", "software developer", "sde", "software development"],

    "sdet": ["software engineer in test", "set", "sdet", "test automation", "quality engineer"],

    "frontend": ["frontend", "front-end", "react", "angular", "vue", "ios", "android"],

    "data": ["data engineer", "data platform", "analytics engineer"],

    "ml": ["machine learning", "ml engineer", "research scientist", "data scientist"],

    "devops": ["devops", "site reliability", "sre", "release infrastructure"],

    "security": ["security engineer", "application security", "security platform"],

}



SPONSORSHIP_PATTERNS = [

    "visa sponsorship", "visa sponsor", "sponsorship available", "sponsor work visa",

    "will sponsor", "immigration sponsorship", "skilled worker visa", "h-1b", "h1b",

    "work permit sponsorship", "sponsorship for this role"

]



NO_SPONSOR_PATTERNS = [

    "no sponsorship", "no visa sponsorship", "without sponsorship", "must have unrestricted",

    "must already have the right to work", "not eligible for sponsorship",

    "unable to sponsor", "we do not sponsor", "without visa sponsorship",

    "must be authorized to work", "must have authorization to work",

    "existing work authorization required"

]



WORK_AUTH_PATTERNS = [

    "authorized to work", "right to work", "work authorization", "legally authorized",

    "eligible to work", "employment authorization", "work permit"

]



REMOTE_PATTERNS = [

    "remote", "work from anywhere", "remote-first", "distributed team"

]



COUNTRY_PATTERNS = {
    "Serbia": ["serbia", "belgrade", "novi sad"],
    "India": ["india", "bengaluru", "bangalore", "hyderabad", "mumbai", "gurugram",
              "gurgaon", "pune", "delhi ncr", "delhi", "noida", "chennai", "kolkata"],
    "United States": ["united states", "usa", "u.s.", "us", "new york", "california", "texas", "washington",
                      "seattle", "san francisco", "bellevue", "austin", "mountain view", "palo alto",
                      "chicago", "boston", "denver", "atlanta", "los angeles", "portland", "raleigh"],
    "Canada": ["canada", "toronto", "vancouver", "ontario", "british columbia", "montreal", "ottawa", "calgary"],
    "United Kingdom": ["united kingdom", "uk", "london", "england", "manchester", "edinburgh", "scotland", "wales"],
    "Ireland": ["ireland", "dublin", "cork"],
    "Germany": ["germany", "berlin", "munich", "hamburg", "frankfurt"],
    "Netherlands": ["netherlands", "amsterdam", "rotterdam"],
    "France": ["france", "paris", "lyon"], "Spain": ["spain", "madrid", "barcelona"],
    "Portugal": ["portugal", "lisbon", "porto"], "Poland": ["poland", "warsaw", "krakow", "kraków"],
    "Norway": ["norway", "oslo"], "Switzerland": ["switzerland", "zurich", "zürich", "geneva"],
    "Sweden": ["sweden", "stockholm"], "Denmark": ["denmark", "copenhagen"],
    "Finland": ["finland", "helsinki"], "Australia": ["australia", "sydney", "melbourne", "brisbane", "perth"],
    "New Zealand": ["new zealand", "auckland", "wellington"], "Singapore": ["singapore"],
    "UAE": ["uae", "united arab emirates", "dubai", "abu dhabi"], "Japan": ["japan", "tokyo", "osaka"],
    "South Korea": ["south korea", "seoul"], "Brazil": ["brazil", "sao paulo", "são paulo", "rio de janeiro"],
    "Mexico": ["mexico", "mexico city"], "Argentina": ["argentina", "buenos aires"],
    "South Africa": ["south africa", "cape town", "johannesburg"], "Israel": ["israel", "tel aviv"],
    "Czechia": ["czechia", "czech republic", "prague"], "Austria": ["austria", "vienna"],
    "Belgium": ["belgium", "brussels"], "Romania": ["romania", "bucharest"],
    "Ukraine": ["ukraine", "kyiv", "kiev"],
}

INDIA_LOCATIONS = ("india", "bengaluru", "bangalore", "hyderabad", "pune", "gurgaon",
                   "gurugram", "noida", "delhi ncr", "new delhi", "chennai", "mumbai")
GLOBAL_REMOTE_TERMS = ("worldwide", "work from anywhere", "anywhere in the world", "global remote",
                       "remote - global", "remote worldwide", "india-eligible", "india eligible", "work from india",
                       "based anywhere", "remote anywhere")
STRONG_POSITIVE_TERMS = ("java", "spring boot", "backend", "back-end", "microservices",
                         "distributed systems", "rest api", "rest apis", "kafka", "redis", "sql",
                         "aws", "concurrency", "concurrent", "platform engineering", "backend engineering")
NEGATIVE_FUNCTION_TERMS = ("sdet", "software engineer in test", "test automation", "salesforce",
                           "frontend", "front-end", "mobile engineer", "ios engineer", "android engineer",
                           "machine learning", "data scientist", "devops", "site reliability", "sre",
                           "release engineer", "release engineering", "staff engineer", "principal engineer",
                           "engineering manager", "software engineering manager")



def clean_html(s):

    s = re.sub(r"\<script.*?\</script>", " ", s or "", flags=re.S | re.I)

    s = re.sub(r"\<style.*?\</style>", " ", s or "", flags=re.S | re.I)

    s = re.sub(r"<[^>]+>", " ", s or "")

    return re.sub(r"\s+", " ", s).strip()



def norm(s):

    return (s or "").lower()


def has_term(text, term):
    return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text) is not None



def fetch_greenhouse(board):

    url = f"https://boards-api.greenhouse.io/v1/boards/{board['token']}/jobs?content=true"

    r = requests.get(url, timeout=30, headers={"User-Agent": "PersonalJobResearchAgent/4.0"})

    r.raise_for_status()

    return [{

        "id": f"gh:{board['token']}:{j['id']}",

        "source": "Greenhouse",

        "company": board["company"],

        "title": j.get("title", ""),

        "location": (j.get("location") or {}).get("name", ""),

        "url": j.get("absolute_url", ""),

        "description": clean_html(j.get("content", "")),

    } for j in r.json().get("jobs", [])]



def fetch_lever(board):

    url = f"https://api.lever.co/v0/postings/{board['token']}?mode=json"

    r = requests.get(url, timeout=30, headers={"User-Agent": "PersonalJobResearchAgent/4.0"})

    r.raise_for_status()

    out = []

    for j in r.json():

        cat = j.get("categories") or {}

        out.append({

            "id": f"lever:{board['token']}:{j['id']}",

            "source": "Lever",

            "company": board["company"],

            "title": j.get("text", ""),

            "location": cat.get("location", ""),

            "url": j.get("applyUrl") or j.get("hostedUrl") or "",

            "description": clean_html(j.get("descriptionPlain") or j.get("description") or ""),

        })

    return out



def detect_country(job):

    location = norm(job.get("location"))

    location_hits = [country for country, patterns in COUNTRY_PATTERNS.items()
                     if any(re.search(r"\b" + re.escape(p) + r"\b", location) for p in patterns)]
    if len(location_hits) == 1:
        return location_hits[0]
    if len(location_hits) > 1:
        for country in ("Serbia", "India"):
            if country in location_hits:
                return country
        return "Unknown"
    # Only use JD text when location itself gives no usable country signal.
    text = norm(job.get("description"))[:12000]
    hits = [country for country, patterns in COUNTRY_PATTERNS.items()
            if any(re.search(r"\b" + re.escape(p) + r"\b", text) for p in patterns)]
    return hits[0] if len(hits) == 1 else "Unknown"


def is_india_location(job):
    location = norm(job.get("location"))
    return any(re.search(r"\b" + re.escape(p) + r"\b", location) for p in INDIA_LOCATIONS)


def has_sponsorship_or_relocation(job):
    text = norm((job.get("location") or "") + " " + (job.get("description") or ""))
    if any(p in text for p in NO_SPONSOR_PATTERNS):
        return False
    return any(p in text for p in SPONSORSHIP_PATTERNS)


def is_genuine_global_remote(job):
    location = norm(job.get("location"))
    description = norm(job.get("description"))
    text = location + " " + description
    if not any(p in text for p in REMOTE_PATTERNS):
        return False
    # A foreign country in the advertised location is a restriction, even when
    # company boilerplate mentions worldwide customers or global teams.
    if any(has_term(location, p) for country, patterns in COUNTRY_PATTERNS.items()
           if country != "India" for p in patterns):
        return False
    foreign_places = [p for country, patterns in COUNTRY_PATTERNS.items()
                      if country != "India" for p in patterns]
    foreign_places += ["emea", "europe", "eu", "north america"]
    places = "(?:" + "|".join(re.escape(p) for p in foreign_places) + ")"
    if re.search(r"\b" + places + r"(?:[- ]based)?[- ,]*(?:only|residents only)\b", text):
        return False
    if re.search(r"\bonly (?:in|within|from|for candidates in) (?:the )?" + places + r"\b", text):
        return False
    if re.search(r"\b(?:must|need to|required to) be (?:located|based|resident|residing) in (?:the )?"
                 + places + r"\b", text):
        return False
    if re.search(r"\b(?:remote|work remotely) (?:only |exclusively )?(?:within|in|from) (?:the )?"
                 + places + r"\b", description):
        return False
    # Match employment scope, not unrelated mentions of worldwide customers.
    if any(has_term(location, term) for term in GLOBAL_REMOTE_TERMS):
        return True
    return any(re.search(pattern, description) for pattern in (
        r"\b(?:work from anywhere|anywhere in the world|global remote|work from india|"
        r"india[- ]eligible|based anywhere|remote anywhere)\b",
        r"\bremote\s*(?:[-,:]\s*)?(?:(?:work|role|position|job|from|in)\s+)?(?:worldwide|globally|global)\b",
        r"\bworldwide\s+(?:remote|employment|hiring)\b",
        r"\b(?:candidates|applicants)\s+(?:from\s+)?worldwide\b",
    ))


def search_bucket(job):
    global_remote = is_genuine_global_remote(job)
    india_location = is_india_location(job) and not any(
        term in norm(job.get("location")) for term in ("work from india", "india eligible", "india-eligible"))
    if india_location or (job.get("country") == "India" and not global_remote):
        return "INDIA_PRIORITY"
    if has_sponsorship_or_relocation(job):
        return "GLOBAL_SPONSORSHIP"
    if global_remote:
        return "GLOBAL_REMOTE"
    return "LOW_PRIORITY / INELIGIBLE"



def eligibility_signal(job):

    text = norm((job.get("location") or "") + " " + (job.get("description") or ""))

    if any(p in text for p in NO_SPONSOR_PATTERNS):

        return "NO_SPONSOR"

    if any(p in text for p in SPONSORSHIP_PATTERNS):

        return "SPONSORSHIP_SIGNAL"

    if any(p in text for p in WORK_AUTH_PATTERNS):

        return "WORK_AUTH_SIGNAL"

    if any(p in text for p in REMOTE_PATTERNS):

        return "REMOTE_SIGNAL"

    return "UNKNOWN"



def role_family(job):

    title = norm(job["title"])

    text = title + " " + norm(job["description"][:7000])

    hits = []

    for family, patterns in ROLE_FAMILIES.items():

        if any(p in text for p in patterns):

            hits.append(family)

    return hits



def target_role_signal(job, profile):

    title = norm(job["title"])

    targets = [norm(x) for x in profile.get("target_roles", [])]

    return any(t in title for t in targets)



def rough_prefilter(job, profile):

    title = norm(job["title"])

    if any(x in title for x in BAD_TITLE_WORDS):

        # SET/SDET is explicitly not the target even though it may contain "software engineer".

        return False



    families = role_family(job)

    target = target_role_signal(job, profile)

    technical = any(x in (title + " " + norm(job["description"][:9000]))
                    for x in STRONG_POSITIVE_TERMS)
    return target or technical or "backend" in families or "software" in families



def local_features(job, profile):

    title = norm(job["title"])

    desc = norm(job["description"])

    text = title + " " + desc

    skills = [norm(x) for x in profile.get("skills", [])]

    matched = [s for s in skills if len(s) >= 3 and s in text]

    families = role_family(job)



    role_bonus = 0

    if target_role_signal(job, profile):

        role_bonus += 25

    if "backend" in families or "software" in families or "platform" in families:

        role_bonus += 12
    positive_hits = [term for term in STRONG_POSITIVE_TERMS if has_term(text, term)]
    role_bonus += min(36, 3 * len(positive_hits))
    # Penalize a function mismatch when the title identifies it as the job's focus.
    negative_hits = [term for term in NEGATIVE_FUNCTION_TERMS if has_term(title, term)]
    role_bonus -= min(65, 18 * len(negative_hits))
    experience_values = re.findall(r"\b(\d{1,2})\s*\+?\s*(?:years|yrs)\b", text)
    max_required_years = max((int(value) for value in experience_values), default=0)
    if max_required_years > 5.5:
        role_bonus -= min(35, int((max_required_years - 5.5) * 10))



    return {

        "title_target": target_role_signal(job, profile),

        "skill_hits": matched[:40],

        "skill_hit_count": len(matched),

        "families": families,

        "role_bonus": role_bonus,
        "positive_term_hits": positive_hits,
        "negative_term_hits": list(dict.fromkeys(negative_hits)),
        "max_required_years": max_required_years,

        "eligibility": eligibility_signal(job),

        "country": job["country"],

        "remote": any(x in text for x in REMOTE_PATTERNS),

        "experience_hint": re.findall(r"\b(?:[2-9]|10)\+?\s*(?:years|yrs)\b", text)[:8],

    }



def rough_score(job, profile):

    f = local_features(job, profile)

    return max(0, min(100, round(35 + f["skill_hit_count"] * 2.5 + f["role_bonus"])))


def select_for_analysis(pool_by_bucket, limit):
    """Prefer 70/20/10 among strong jobs; fill shortages by score across buckets."""
    if limit <= 0:
        return []
    order = ("INDIA_PRIORITY", "GLOBAL_SPONSORSHIP", "GLOBAL_REMOTE")
    pools = {bucket: sorted(
        (j for j in pool_by_bucket.get(bucket, []) if j["rough_score"] >= MIN_AI_ROUGH_SCORE),
        key=lambda j: -j["rough_score"]) for bucket in order}
    quotas = (round(limit * 0.70), round(limit * 0.20))
    quotas += (max(0, limit - sum(quotas)),)
    selected, chosen_ids = [], set()
    for bucket, quota in zip(order, quotas):
        for job in pools[bucket][:quota]:
            if job["id"] not in chosen_ids:
                selected.append(job)
                chosen_ids.add(job["id"])
    remaining = sorted((j for bucket in order for j in pools[bucket]
                        if j["id"] not in chosen_ids), key=lambda j: -j["rough_score"])
    for job in remaining:
        if len(selected) >= limit:
            break
        if job["id"] not in chosen_ids:
            selected.append(job)
            chosen_ids.add(job["id"])
    selected.sort(key=lambda j: (order.index(j["search_bucket"]), -j["rough_score"]))
    return selected[:limit]



def db():

    c = sqlite3.connect(DB_FILE)

    c.execute("""

        CREATE TABLE IF NOT EXISTS jobs(

            id TEXT PRIMARY KEY,

            source TEXT,

            company TEXT,

            title TEXT,

            location TEXT,

            country TEXT,

            url TEXT,

            description TEXT,

            rough_score REAL,

            ai_score REAL,

            fit_json TEXT,

            eligibility_signal TEXT,

            discovered_at TEXT,

            status TEXT DEFAULT 'NEW'

        )

    """)

    c.execute("""

        CREATE TABLE IF NOT EXISTS ai_cache(

            job_id TEXT PRIMARY KEY,

            job_fingerprint TEXT,

            model TEXT,

            result_json TEXT,

            analyzed_at TEXT

        )

    """)

    columns = {row[1] for row in c.execute("PRAGMA table_info(jobs)")}
    if "search_bucket" not in columns:
        c.execute("ALTER TABLE jobs ADD COLUMN search_bucket TEXT")
    if "applied_at" not in columns:
        c.execute("ALTER TABLE jobs ADD COLUMN applied_at TEXT")

    c.commit()

    return c



def resume_text():

    txt = Path(RESUME_TEXT_FILE)

    if txt.exists():

        return txt.read_text(encoding="utf-8")

    pdf = Path(RESUME_PDF_FILE)

    if pdf.exists():

        try:

            from pypdf import PdfReader

            return "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf)).pages)

        except Exception as e:

            print(f"Resume PDF could not be parsed: {e}")

    return ""



def ai_enabled():
    return AI_PROVIDER == "gemini" and bool(os.getenv("GEMINI_API_KEY"))

def active_model():
    return f"{AI_PROVIDER}:{GEMINI_MODEL}"

def fingerprint(job, profile, resume):
    import hashlib
    raw = json.dumps({
        "job_id": job["id"], "title": job["title"], "location": job["location"],
        "country": job.get("country"), "description": job["description"],
        "resume": resume, "profile": profile, "provider": AI_PROVIDER,
        "model": GEMINI_MODEL,
    }, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def get_cached_match(c, job, profile, resume):
    row = c.execute("SELECT job_fingerprint, model, result_json FROM ai_cache WHERE job_id=?", (job["id"],)).fetchone()
    if not row:
        return None
    fp, model, result_json = row
    if fp == fingerprint(job, profile, resume) and model == active_model():
        try:
            return json.loads(result_json)
        except Exception:
            return None
    return None

def save_cached_match(c, job, profile, resume, result):
    c.execute("""
        INSERT INTO ai_cache(job_id,job_fingerprint,model,result_json,analyzed_at)
        VALUES(?,?,?,?,?)
        ON CONFLICT(job_id) DO UPDATE SET
          job_fingerprint=excluded.job_fingerprint,
          model=excluded.model,
          result_json=excluded.result_json,
          analyzed_at=excluded.analyzed_at
    """, (job["id"], fingerprint(job, profile, resume), active_model(), json.dumps(result, ensure_ascii=False),
          datetime.now(timezone.utc).isoformat()))

def gemini_json(system, payload, temperature=0.1):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=json.dumps(payload, ensure_ascii=False),
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            response_mime_type="application/json",
        ),
    )
    text = (response.text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\\s*", "", text, flags=re.I)
        text = re.sub(r"\\s*```$", "", text)
    return json.loads(text)

def ai_match(job, profile, resume):
    prompt = {
        "candidate_profile": profile,
        "resume": resume[:16000],
        "job": {
            "company": job["company"], "title": job["title"], "location": job["location"],
            "country": job["country"], "eligibility_signal": job["eligibility_signal"],
            "description": job["description"][:22000],
        },
        "task": """Evaluate factual fit. Do not predict hiring probability and do not invent facts.
1. Candidate targets backend/software/platform roles.
2. Penalize SDET/SET, frontend/mobile, data-science/ML and management role mismatch.
3. Generic Python/SQL/AWS overlap must not compensate for major role mismatch.
4. Distinguish technical, experience, role-family, location and visa/work-authorization fit.
5. Remote does NOT mean the candidate can work from India.
6. Sponsorship wording is evidence, not a guarantee.
7. Identify concrete missing JD skills unsupported by the resume.
8. Give concise evidence from the supplied resume/JD.
9. APPLY_REVIEW only for genuinely strong role fit with no explicit eligibility blocker; otherwise REVIEW or SKIP."""
    }
    system = """You are a precise job-search matching engine.
Return ONLY valid JSON with exactly these keys:
overall_fit: integer 0-100
technical_fit: integer 0-100
experience_fit: integer 0-100
role_fit: integer 0-100
location_eligibility: integer 0-100
sponsorship_assessment: one of SUPPORTED, POSSIBLE, UNKNOWN, NEGATIVE, NOT_NEEDED
role_family: string
strong_matches: array of strings
gaps: array of strings
red_flags: array of strings
evidence: array of strings
action: one of APPLY_REVIEW, REVIEW, SKIP
Role fit is heavily weighted. Technical fit reflects required skills, not keyword overlap.
Experience fit should consider 5.5 years and requested seniority.
Location eligibility must reflect stated location/work-authorization language.
SDET/SET/different-function roles get low role_fit even with Java overlap."""
    return gemini_json(system, prompt, 0.1)

def fallback_match(job, profile):

    f = local_features(job, profile)

    technical = min(100, f["skill_hit_count"] * 5)

    role = max(0, min(100, 55 + f["role_bonus"]))

    exp = 90 if any(x in job["description"].lower() for x in ["5+ years", "5 years", "6+ years", "senior"]) else 70

    eligibility = 40 if f["eligibility"] in ("NO_SPONSOR", "WORK_AUTH_SIGNAL") else 70



    overall = round(

        technical * 0.35 +

        role * 0.35 +

        exp * 0.20 +

        eligibility * 0.10

    )



    gaps = []

    text = norm(job["description"])

    if "kubernetes" in text and "kubernetes" not in norm(" ".join(profile.get("skills", []))):

        gaps.append("Kubernetes")

    if any(x in text for x in ["react", "typescript", "frontend"]) and "frontend" not in norm(job["title"]):

        gaps.append("Frontend/TypeScript requirements")

    if "sdet" in f["families"] or "qa engineer" in norm(job["title"]):

        gaps.append("Primary role is test/QA rather than backend engineering")



    return {

        "overall_fit": overall,

        "technical_fit": technical,

        "experience_fit": exp,

        "role_fit": role,

        "location_eligibility": eligibility,

        "sponsorship_assessment": (

            "NEGATIVE" if f["eligibility"] == "NO_SPONSOR"

            else "UNKNOWN"

        ),

        "role_family": ",".join(f["families"]),

        "strong_matches": f["skill_hits"][:15],

        "gaps": gaps,

        "red_flags": [],

        "evidence": ["Deterministic fallback matcher used; configure GEMINI_API_KEY for semantic analysis."],

        "action": "REVIEW" if overall >= 65 else "SKIP",

    }



def save_job(c, j):

    c.execute("""

        INSERT INTO jobs(

            id,source,company,title,location,country,url,description,

            rough_score,ai_score,fit_json,eligibility_signal,discovered_at,search_bucket,status

        )

        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,COALESCE((SELECT status FROM jobs WHERE id=?),'NEW'))

        ON CONFLICT(id) DO UPDATE SET

            company=excluded.company,

            title=excluded.title,

            location=excluded.location,

            country=excluded.country,

            url=excluded.url,

            description=excluded.description,

            rough_score=excluded.rough_score,

            ai_score=excluded.ai_score,

            fit_json=excluded.fit_json,

            eligibility_signal=excluded.eligibility_signal,

            search_bucket=excluded.search_bucket,

            discovered_at=excluded.discovered_at

    """, (

        j["id"], j["source"], j["company"], j["title"], j["location"],

        j["country"], j["url"], j["description"], j["rough_score"],

        j["ai_score"], json.dumps(j["fit"], ensure_ascii=False),

        j["eligibility_signal"], j["discovered_at"], j["search_bucket"], j["id"]

    ))



def generate_application_package(job, fit, profile, resume):

    prompt = {

        "candidate_profile": profile,

        "resume": resume[:16000],

        "job": {

            "company": job["company"],

            "title": job["title"],

            "location": job["location"],

            "description": job["description"][:18000],

        },

        "fit": fit,

        "task": "Create a factual application package without inventing experience."

    }

    system = """

Return ONLY JSON:

{

  "tailored_summary": "2-4 sentences",

  "resume_bullets_to_emphasize": ["..."],

  "recruiter_message": "short LinkedIn/email message",

  "application_answers": [

    {"question": "Why are you interested in this role?", "answer": "..."}

  ]

}

Use only facts in the resume/profile. Do not invent metrics, employers, visas, authorization, or technologies.

"""

    return gemini_json(system, prompt, 0.2)


def main():

    profile = json.loads(Path(PROFILE_FILE).read_text(encoding="utf-8"))

    resume = resume_text()



    print("\n" + "=" * 110)

    print("                 GLOBAL AI JOB AGENT — V4.1")

    print("=" * 110)

    print(f"AI semantic matching : {'ENABLED' if ai_enabled() else 'DISABLED (fallback matcher)'}")

    print(f"AI provider/model     : {AI_PROVIDER} / {GEMINI_MODEL}")
    print(f"Resume loaded         : {'YES' if resume else 'NO'}")

    print(f"AI analyze limit      : {AI_ANALYZE_LIMIT}")

    print(f"AI cache              : ENABLED")

    print(f"Application packages  : {'ENABLED' if GENERATE_PACKAGES else 'DISABLED'}")



    c = db()

    all_jobs = []



    for board in BOARDS:

        try:

            jobs = fetch_greenhouse(board) if board["ats"] == "greenhouse" else fetch_lever(board)

            print(f"  {board['company']:<15}: {len(jobs)} jobs")

            all_jobs.extend(jobs)

        except Exception as e:

            print(f"  {board['company']:<15}: ERROR {e}")



    pool_by_bucket = {"INDIA_PRIORITY": [], "GLOBAL_SPONSORSHIP": [], "GLOBAL_REMOTE": []}
    applied_rows = c.execute("SELECT id, url FROM jobs WHERE UPPER(status)='APPLIED'").fetchall()
    applied_ids = {row[0] for row in applied_rows}
    applied_urls = {url_key(row[1] or '') for row in applied_rows}
    for j in all_jobs:
        if j['id'] in applied_ids or url_key(j['url']) in applied_urls:
            continue
        j["country"] = detect_country(j)
        j["eligibility_signal"] = eligibility_signal(j)
        j["search_bucket"] = search_bucket(j)
        j["rough_score"] = rough_score(j, profile)
        if j["search_bucket"] in pool_by_bucket and rough_prefilter(j, profile):
            pool_by_bucket[j["search_bucket"]].append(j)

    for jobs in pool_by_bucket.values():
        jobs.sort(key=lambda x: x["rough_score"], reverse=True)
    filtered_count = sum(len(jobs) for jobs in pool_by_bucket.values())
    bucket_counts = {bucket: len(jobs) for bucket, jobs in pool_by_bucket.items()}
    candidates = select_for_analysis(pool_by_bucket, AI_ANALYZE_LIMIT)
    analyzed_ids = {j["id"] for j in candidates}
    print(f"\nCollected: {len(all_jobs)} | candidates after filtering: {filtered_count} | AI selected: {len(candidates)}")
    print("AI selection mix: " + " | ".join(f"{b}: {sum(j['search_bucket'] == b for j in candidates)}" for b in pool_by_bucket))



    results = []

    cache_hits = 0
    ai_result_ids = set()



    for i, j in enumerate(candidates, 1):

        try:

            fit = get_cached_match(c, j, profile, resume) if ai_enabled() else None

            if fit:

                cache_hits += 1

            else:

                fit = ai_match(j, profile, resume) if ai_enabled() else fallback_match(j, profile)

                if ai_enabled():

                    save_cached_match(c, j, profile, resume, fit)

            if ai_enabled():
                ai_result_ids.add(j["id"])

        except Exception as e:

            print(f"  [{i:02}/{len(candidates)}] AI failed for {j['company']} / {j['title'][:55]}: {e}")

            fit = fallback_match(j, profile)

            fit["red_flags"] = fit.get("red_flags", []) + ["AI analysis failed; fallback result"]



        j["fit"] = fit

        j["ai_score"] = float(fit.get("overall_fit", 0))

        j["discovered_at"] = datetime.now(timezone.utc).isoformat()

        save_job(c, j)

        results.append(j)



        print(

            f"  [{i:02}/{len(candidates)}] "

            f"{j['ai_score']:>3.0f} | "

            f"{fit.get('action','REVIEW'):<11} | "

            f"{j['company']:<14} | "

            f"{j['title'][:52]}"

        )



    c.commit()

    applied_rows = c.execute("SELECT id, url FROM jobs WHERE UPPER(status)='APPLIED'").fetchall()
    applied_ids = {row[0] for row in applied_rows}
    applied_urls = {url_key(row[1] or '') for row in applied_rows}
    c.close()



    results.sort(key=lambda x: x["ai_score"], reverse=True)



    def write_jobs_csv(path, jobs):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow([
                "Company", "Role", "Location", "Country", "Search Bucket", "Pre-rank",
                "AI Fit", "Technical Fit", "Experience Fit", "Role Fit", "Location Eligibility",
                "Sponsorship", "Role Family", "Action", "Strong Matches", "Gaps", "Red Flags", "Apply URL"
            ])
            for j in jobs:
                fit = j.get("fit", {})
                w.writerow([
                    j["company"], j["title"], j["location"], j.get("country", "Unknown"),
                    j.get("search_bucket", search_bucket(j)), j.get("rough_score", ""),
                    fit.get("overall_fit", ""), fit.get("technical_fit", ""),
                    fit.get("experience_fit", ""), fit.get("role_fit", ""),
                    fit.get("location_eligibility", ""), fit.get("sponsorship_assessment", ""),
                    fit.get("role_family", ""), fit.get("action", ""),
                    "; ".join(fit.get("strong_matches", [])), "; ".join(fit.get("gaps", [])),
                    "; ".join(fit.get("red_flags", [])), j["url"],
                ])

    write_jobs_csv(CSV_FILE, results)
    apply_rows = [j for j in results if j["fit"].get("action") == "APPLY_REVIEW"
                  and j['id'] not in applied_ids and url_key(j['url']) not in applied_urls]
    review_rows = [j for j in results if j["fit"].get("action") == "REVIEW"]
    ai_skips = [j for j in results if j["id"] in ai_result_ids and j["fit"].get("action") == "SKIP"]
    not_analyzed = [j for jobs in pool_by_bucket.values() for j in jobs
                    if j["id"] not in analyzed_ids and j["rough_score"] >= MIN_AI_ROUGH_SCORE]
    skipped_rows = ai_skips
    write_jobs_csv(APPLY_CSV_FILE, apply_rows)
    write_jobs_csv(REVIEW_CSV_FILE, review_rows)
    write_jobs_csv(SKIPPED_CSV_FILE, skipped_rows)
    write_jobs_csv(NOT_ANALYZED_CSV_FILE, not_analyzed)



    with open(JSON_FILE, "w", encoding="utf-8") as f:

        json.dump(results, f, indent=2, ensure_ascii=False)



    packages = []

    if GENERATE_PACKAGES and ai_enabled():

        package_candidates = [

            j for j in results

            if j["fit"].get("action") == "APPLY_REVIEW"

        ][:PACKAGE_LIMIT]



        print(f"\nGenerating application packages for {len(package_candidates)} jobs...")

        for j in package_candidates:

            try:

                package = generate_application_package(j, j["fit"], profile, resume)

                packages.append({

                    "company": j["company"],

                    "role": j["title"],

                    "url": j["url"],

                    "fit": j["fit"],

                    "package": package,

                })

            except Exception as e:

                print(f"  Package failed: {j['company']} / {j['title']}: {e}")



        with open(PACKAGES_FILE, "w", encoding="utf-8") as f:

            json.dump(packages, f, indent=2, ensure_ascii=False)



    print("\n" + "=" * 110)

    print("TOP AI MATCHES")

    print("=" * 110)



    for j in results[:15]:

        fit = j["fit"]

        print(

            f"{fit.get('overall_fit',0):>3}/100 | "

            f"{fit.get('action','REVIEW'):<11} | "

            f"{j['company']:<14} | {j['title'][:55]}"

        )

        print(

            f"      {j['location']} | country={j['country']} | "

            f"role={fit.get('role_family')} | "

            f"sponsorship={fit.get('sponsorship_assessment')}"

        )

        print(

            f"      gaps={', '.join(fit.get('gaps', [])[:4]) or 'None identified'}"

        )



    print("-" * 110)
    action_counts = {action: sum(j["fit"].get("action") == action for j in results)
                     for action in ("APPLY_REVIEW", "REVIEW", "SKIP")}
    print("RUN STATS")
    print(f"Total scraped             : {len(all_jobs)}")
    print(f"Candidates after filtering: {filtered_count}")
    print(f"India candidates          : {bucket_counts['INDIA_PRIORITY']}")
    print(f"Sponsorship candidates    : {bucket_counts['GLOBAL_SPONSORSHIP']}")
    print(f"Global remote candidates  : {bucket_counts['GLOBAL_REMOTE']}")
    print(f"AI analyzed               : {len(results)}")
    print(f"AI cache hits             : {cache_hits}")
    print(f"APPLY_REVIEW count        : {action_counts['APPLY_REVIEW']}")
    print(f"REVIEW count              : {action_counts['REVIEW']}")
    print(f"SKIP count                : {action_counts['SKIP']}")
    print(f"Saved: {CSV_FILE}, {APPLY_CSV_FILE}, {REVIEW_CSV_FILE}, {SKIPPED_CSV_FILE}")
    print(f"Saved: {JSON_FILE} and {DB_FILE}")
    print(f"Saved: {NOT_ANALYZED_CSV_FILE} (qualifying candidates beyond AI_ANALYZE_LIMIT)")

    if GENERATE_PACKAGES and ai_enabled():

        print(f"Saved: {PACKAGES_FILE}")

    print("\nAI fit is profile/JD alignment, NOT a prediction of hiring success.")



if __name__ == "__main__":

    main()
