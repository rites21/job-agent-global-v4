# Global AI Job Agent V4

This version improves the V3 job matcher with:

- Global Greenhouse/Lever discovery
- Stronger backend/software/platform role matching
- Explicit penalty for SDET/SET, frontend/mobile, ML/data-science and management roles
- Country detection from location and, cautiously, from JD text
- Work-authorization / sponsorship classification
- Semantic AI matching
- Concrete `gaps` and `red_flags`
- SQLite AI result cache so unchanged jobs are not re-analyzed every run
- Optional tailored application packages
- CSV + JSON output
- Human approval remains required before applying

## Setup

Copy your existing profile from V3:

```bash
cp ../job-agent-global-v3/profile.json .
```

If you do not have it, copy the example:

```bash
cp profile.example.json profile.json
```

Put your resume here:

```text
resume.pdf
```

or:

```text
resume.txt
```

Create the environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your OpenAI key:

```bash
export OPENAI_API_KEY="YOUR_KEY"
```

Optional:

```bash
export OPENAI_MODEL="gpt-5-mini"
export AI_ANALYZE_LIMIT=50
export GENERATE_PACKAGES=false
export PACKAGE_LIMIT=5
```

Run:

```bash
python3 job_agent_v4.py
```

## Outputs

- `top_jobs_v4.csv` — spreadsheet-friendly ranked jobs
- `ai_matches_v4.json` — full AI reasoning/evidence
- `jobs_v4.db` — persistent job history + AI cache
- `application_packages.json` — optional tailored application package

## Application packages

After reviewing the ranking, enable:

```bash
export GENERATE_PACKAGES=true
export PACKAGE_LIMIT=5
python3 job_agent_v4.py
```

For the best reviewed jobs it generates:

- tailored summary
- resume bullets to emphasize
- recruiter message
- initial application answer(s)

The agent is instructed not to invent experience, metrics, authorization, or technologies.

## Daily automation later

Once V4 is stable, the next layer can add:

1. More job sources/company career sites
2. Job deduplication across sources
3. Daily scheduled execution
4. Email/Telegram/Slack digest
5. Resume tailoring per job
6. Application tracker
7. Human approval workflow
8. MCP tool interface

Do not auto-submit applications without human approval.
