import csv

import json

import os

import re

import sqlite3

from datetime import datetime, timezone

from pathlib import Path



import requests



PROFILE_FILE = "profile.json"

DB_FILE = "jobs_v4.db"

CSV_FILE = "top_jobs_v4.csv"

JSON_FILE = "ai_matches_v4.json"

PACKAGES_FILE = "application_packages.json"

RESUME_TEXT_FILE = "resume.txt"

RESUME_PDF_FILE = "resume.pdf"



AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini").lower()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
AI_ANALYZE_LIMIT = int(os.getenv("AI_ANALYZE_LIMIT", "100"))

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

    "developer advocate"

]



ROLE_FAMILIES = {

    "backend": [

        "backend", "back-end", "server-side", "platform", "distributed systems",

        "infrastructure", "core services", "api", "services engineer"

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

    "will sponsor", "immigration sponsorship", "relocation support", "relocation assistance",

    "relocation package", "skilled worker visa", "h-1b", "h1b", "global mobility",

    "work permit sponsorship", "sponsorship for this role"

]



NO_SPONSOR_PATTERNS = [

    "no sponsorship", "without sponsorship", "must have unrestricted",

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

    "United States": ["united states", "usa", "u.s.", "new york", "california", "texas",

                      "washington", "seattle", "san francisco", "bellevue", "austin",

                      "mountain view", "palo alto", "chicago", "boston"],

    "Canada": ["canada", "toronto", "vancouver", "ontario", "british columbia", "montreal"],

    "United Kingdom": ["united kingdom", "uk", "london", "england", "manchester", "edinburgh"],

    "Ireland": ["ireland", "dublin", "cork"],

    "Germany": ["germany", "berlin", "munich", "hamburg"],

    "Netherlands": ["netherlands", "amsterdam"],

    "France": ["france", "paris"],

    "Spain": ["spain", "madrid", "barcelona"],

    "Portugal": ["portugal", "lisbon"],

    "Poland": ["poland", "warsaw", "krakow", "kraków"],

    "Norway": ["norway", "oslo"],

    "Switzerland": ["switzerland", "zurich", "zürich"],

    "Sweden": ["sweden", "stockholm"],

    "Denmark": ["denmark", "copenhagen"],

    "Finland": ["finland", "helsinki"],

    "Australia": ["australia", "sydney", "melbourne", "brisbane"],

    "New Zealand": ["new zealand", "auckland", "wellington"],

    "Singapore": ["singapore"],

    "UAE": ["uae", "united arab emirates", "dubai", "abu dhabi"],

    "Japan": ["japan", "tokyo"],

    "South Korea": ["south korea", "seoul"],

    "India": ["india", "bengaluru", "bangalore", "hyderabad", "mumbai", "gurugram",

              "gurgaon", "pune", "delhi", "noida", "chennai", "kolkata"],

}



def clean_html(s):

    s = re.sub(r"\<script.*?\</script>", " ", s or "", flags=re.S | re.I)

    s = re.sub(r"\<style.*?\</style>", " ", s or "", flags=re.S | re.I)

    s = re.sub(r"<[^>]+>", " ", s or "")

    return re.sub(r"\s+", " ", s).strip()



def norm(s):

    return (s or "").lower()



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

    for country, patterns in COUNTRY_PATTERNS.items():

        if any(re.search(r"\b" + re.escape(p) + r"\b", location) for p in patterns):

            return country



    # Only use JD text for country when the location field is ambiguous.

    text = norm(job.get("description"))[:12000]

    hits = []

    for country, patterns in COUNTRY_PATTERNS.items():

        if any(re.search(r"\b" + re.escape(p) + r"\b", text) for p in patterns):

            hits.append(country)

    return hits[0] if len(hits) == 1 else "Unknown"



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

    technical = any(x in (title + " " + norm(job["description"][:6000]))

                     for x in ["java", "spring", "backend", "microservices", "distributed", "platform", "kafka"])

    return target or technical or "backend" in families



def local_features(job, profile):

    title = norm(job["title"])

    desc = norm(job["description"])

    text = title + " " + desc

    skills = [norm(x) for x in profile.get("skills", [])]

    matched = [s for s in skills if len(s) >= 3 and s in text]

    families = role_family(job)



    # Strong role signal: backend/software/platform. Negative role signal: SDET/frontend/data/ML.

    role_bonus = 0

    if target_role_signal(job, profile):

        role_bonus += 25

    if "backend" in families or "software" in families or "platform" in families:

        role_bonus += 10

    if "sdet" in families or "frontend" in families or "ml" in families:

        role_bonus -= 35



    return {

        "title_target": target_role_signal(job, profile),

        "skill_hits": matched[:40],

        "skill_hit_count": len(matched),

        "families": families,

        "role_bonus": role_bonus,

        "eligibility": eligibility_signal(job),

        "country": job["country"],

        "remote": any(x in text for x in REMOTE_PATTERNS),

        "experience_hint": re.findall(r"\b(?:[2-9]|10)\\+?\s*(?:years|yrs)\b", text)[:8],

    }



def rough_score(job, profile):

    f = local_features(job, profile)

    return max(0, min(100, 25 + f["skill_hit_count"] * 2 + f["role_bonus"]))



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

def fingerprint(job):
    import hashlib
    raw = f"{job['title']}|{job['location']}|{job['description']}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def get_cached_match(c, job):
    row = c.execute("SELECT job_fingerprint, model, result_json FROM ai_cache WHERE job_id=?", (job["id"],)).fetchone()
    if not row:
        return None
    fp, model, result_json = row
    if fp == fingerprint(job) and model == active_model():
        try:
            return json.loads(result_json)
        except Exception:
            return None
    return None

def save_cached_match(c, job, result):
    c.execute("""
        INSERT INTO ai_cache(job_id,job_fingerprint,model,result_json,analyzed_at)
        VALUES(?,?,?,?,?)
        ON CONFLICT(job_id) DO UPDATE SET
          job_fingerprint=excluded.job_fingerprint,
          model=excluded.model,
          result_json=excluded.result_json,
          analyzed_at=excluded.analyzed_at
    """, (job["id"], fingerprint(job), active_model(), json.dumps(result, ensure_ascii=False),
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

            rough_score,ai_score,fit_json,eligibility_signal,discovered_at,status

        )

        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,COALESCE((SELECT status FROM jobs WHERE id=?),'NEW'))

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

            discovered_at=excluded.discovered_at

    """, (

        j["id"], j["source"], j["company"], j["title"], j["location"],

        j["country"], j["url"], j["description"], j["rough_score"],

        j["ai_score"], json.dumps(j["fit"], ensure_ascii=False),

        j["eligibility_signal"], j["discovered_at"], j["id"]

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

    print("                 GLOBAL AI JOB AGENT — V4")

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



    candidates = []

    for j in all_jobs:

        j["country"] = detect_country(j)

        j["eligibility_signal"] = eligibility_signal(j)

        j["rough_score"] = rough_score(j, profile)

        if rough_prefilter(j, profile):

            candidates.append(j)



    candidates.sort(key=lambda x: x["rough_score"], reverse=True)

    candidates = candidates[:AI_ANALYZE_LIMIT]



    print(f"\nCollected: {len(all_jobs)} | AI candidates: {len(candidates)}")



    results = []

    cache_hits = 0



    for i, j in enumerate(candidates, 1):

        try:

            fit = get_cached_match(c, j) if ai_enabled() else None

            if fit:

                cache_hits += 1

            else:

                fit = ai_match(j, profile, resume) if ai_enabled() else fallback_match(j, profile)

                if ai_enabled():

                    save_cached_match(c, j, fit)

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

    c.close()



    results.sort(key=lambda x: x["ai_score"], reverse=True)



    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:

        w = csv.writer(f)

        w.writerow([

            "Company", "Role", "Location", "Country", "AI Fit",

            "Technical Fit", "Experience Fit", "Role Fit",

            "Location Eligibility", "Sponsorship", "Role Family",

            "Action", "Strong Matches", "Gaps", "Red Flags", "Apply URL"

        ])

        for j in results:

            fit = j["fit"]

            w.writerow([

                j["company"], j["title"], j["location"], j["country"],

                fit.get("overall_fit"), fit.get("technical_fit"),

                fit.get("experience_fit"), fit.get("role_fit"),

                fit.get("location_eligibility"),

                fit.get("sponsorship_assessment"),

                fit.get("role_family"),

                fit.get("action"),

                "; ".join(fit.get("strong_matches", [])),

                "; ".join(fit.get("gaps", [])),

                "; ".join(fit.get("red_flags", [])),

                j["url"],

            ])



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

    print(f"AI cache hits: {cache_hits}")

    print(f"Saved: {CSV_FILE}")

    print(f"Saved: {JSON_FILE}")

    if GENERATE_PACKAGES and ai_enabled():

        print(f"Saved: {PACKAGES_FILE}")

    print("\nAI fit is profile/JD alignment, NOT a prediction of hiring success.")



if __name__ == "__main__":

    main()
