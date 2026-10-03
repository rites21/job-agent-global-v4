"""Status tracking for the human-reviewed browser application workflow.

This module records observed outcomes; it does not infer success from a click.
"""
import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import re

ROOT = Path(__file__).resolve().parent
DB_FILE = ROOT / 'jobs_v4.db'


def connect(db_path=DB_FILE):
    path = Path(db_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f'Existing jobs database required: {path}')
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    columns = {r['name'] for r in c.execute('PRAGMA table_info(jobs)')}
    if not {'id', 'status'}.issubset(columns):
        c.close()
        raise ValueError('Expected jobs table with id and status')
    if 'applied_at' not in columns:
        c.execute('ALTER TABLE jobs ADD COLUMN applied_at TEXT')
    c.commit()
    return c


def clean_url(url):
    url = url.strip()
    match = re.fullmatch(r'\[[^\]]*\]\((https?://.+)\)', url)
    return match.group(1) if match else url


def url_key(url):
    parsed = urlsplit(clean_url(url))
    host = (parsed.hostname or '').removeprefix('www.')
    gh_id = parse_qs(parsed.query).get('gh_jid', [None])[0]
    if not gh_id and host in {'mongodb.com', 'databricks.com', 'okta.com'}:
        match = re.search(r'(?:/|-)(\d+)/?$', parsed.path)
        gh_id = match.group(1) if match else None
    return (host, gh_id) if gh_id else (host, parsed.path.rstrip('/'), parsed.query)


def resolve_job(c, identifier):
    row = c.execute('SELECT * FROM jobs WHERE id=?', (identifier,)).fetchone()
    if row:
        return row
    key = url_key(identifier)
    matches = [r for r in c.execute('SELECT * FROM jobs') if url_key(r['url'] or '') == key]
    if len(matches) != 1:
        raise ValueError('Job URL must identify exactly one database row; use its job id')
    return matches[0]


def applied(c, identifier):
    return (resolve_job(c, identifier)['status'] or '').upper() == 'APPLIED'


def ranked_jobs(csv_path=ROOT / 'apply_now.csv', db_path=DB_FILE, limit=10):
    """Preserve CSV rank, remove duplicates, and re-read status on each yield."""
    if limit <= 0:
        return
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    seen, count = set(), 0
    for rank, row in enumerate(rows, 1):
        url = clean_url(row['Apply URL'])
        c = connect(db_path)
        try:
            try:
                job = resolve_job(c, url)
            except ValueError as error:
                print(f'BLOCKED rank {rank}: {error}: {url}')
                continue
            if job['id'] in seen or (job['status'] or '').upper() == 'APPLIED':
                continue
            seen.add(job['id'])
            result = dict(row, job_id=job['id'], rank=rank, status=job['status'])
            result['Apply URL'] = url
        finally:
            c.close()
        yield result
        count += 1
        if count >= limit:
            break


def record_outcome(identifier, *, approved=False, submitted=False, confirmed=False,
                   confirmation='', confirmation_url='', db_path=DB_FILE):
    """Call only after inspecting the browser following a submission attempt.

    confirmed=True requires explicit success text for this application, with no
    validation errors. Approval, clicking Submit, or a changed URL alone is not
    confirmation. The browser operator supplies the observed evidence.
    """
    success = approved and submitted and confirmed and bool(confirmation.strip()) and bool(confirmation_url.strip())
    c = connect(db_path)
    try:
        with c:
            job = resolve_job(c, identifier)
            if (job['status'] or '').upper() == 'APPLIED':
                return dict(job)  # Never overwrite the original applied_at.
            if success:
                timestamp = datetime.now(timezone.utc).isoformat()
                c.execute("UPDATE jobs SET status='APPLIED', applied_at=? WHERE id=? AND UPPER(COALESCE(status,''))!='APPLIED'",
                          (timestamp, job['id']))
            elif submitted:
                c.execute("UPDATE jobs SET status='APPLICATION_BLOCKED' WHERE id=? AND UPPER(COALESCE(status,''))!='APPLIED'", (job['id'],))
            result = dict(c.execute('SELECT * FROM jobs WHERE id=?', (job['id'],)).fetchone())
        print(json.dumps({'company': result['company'], 'role': result['title'],
                          'timestamp': result['applied_at'], 'status': result['status'],
                          'confirmation_status': 'CONFIRMED' if success else 'NOT_CONFIRMED',
                          'confirmation': confirmation, 'confirmation_url': confirmation_url}, ensure_ascii=False))
        return result
    finally:
        c.close()


def load_application_materials():
    # Conflicting/malformed JSON is an error; never invent or silently merge facts.
    return {'application_profile': json.loads((ROOT / 'application_profile.json').read_text()),
            'profile': json.loads((ROOT / 'profile.json').read_text()),
            'resume': (ROOT / 'resume.pdf').resolve(strict=True)}
