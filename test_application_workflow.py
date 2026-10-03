import contextlib
import csv
import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import application_workflow as workflow
import job_agent_v4_1_gemini as agent


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.db_path = self.folder / 'jobs.db'
        with patch.object(agent, 'DB_FILE', str(self.db_path)):
            c = agent.db()
        for n, status in [(1, 'NEW'), (2, 'APPLIED'), (3, 'NEW')]:
            c.execute('INSERT INTO jobs(id,company,title,url,status) VALUES(?,?,?,?,?)',
                      (str(n), 'MongoDB', 'Backend Engineer', f'https://www.mongodb.com/careers/job/?gh_jid={n}', status))
        c.commit(); c.close()
        self.csv_path = self.folder / 'apply_now.csv'
        with self.csv_path.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['Company', 'Role', 'Apply URL'])
            w.writeheader()
            for n in [2, 1, 1, 3]:
                w.writerow({'Company': 'MongoDB', 'Role': 'Backend Engineer', 'Apply URL': f'https://www.mongodb.com/careers/jobs/{n}'})

    def record(self, identifier='1', **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return workflow.record_outcome(identifier, db_path=self.db_path, **kwargs)

    def test_confirmation_gate_and_timestamp(self):
        self.assertEqual(self.record(approved=True)['status'], 'NEW')
        blocked = self.record(approved=True, submitted=True, confirmed=True)
        self.assertEqual(blocked['status'], 'APPLICATION_BLOCKED')
        self.assertIsNone(blocked['applied_at'])
        result = self.record(approved=True, submitted=True, confirmed=True,
                             confirmation='Application received', confirmation_url='https://example.com/thanks')
        self.assertEqual(result['status'], 'APPLIED')
        self.assertTrue(result['applied_at'].endswith('+00:00'))
        self.assertEqual(self.record(submitted=True)['applied_at'], result['applied_at'])
        with sqlite3.connect(self.db_path) as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM jobs').fetchone()[0], 3)

    def test_batch_order_dedup_and_fresh_status(self):
        batch = workflow.ranked_jobs(self.csv_path, self.db_path, 10)
        self.assertEqual(next(batch)['job_id'], '1')
        self.record('3', approved=True, submitted=True, confirmed=True,
                    confirmation='Received', confirmation_url='https://example.com/thanks')
        self.assertEqual(list(batch), [])
        self.assertEqual(list(workflow.ranked_jobs(self.csv_path, self.db_path, 0)), [])

    def test_legacy_migration_is_idempotent(self):
        legacy = self.folder / 'legacy.db'
        with sqlite3.connect(legacy) as c:
            c.execute('CREATE TABLE jobs(id TEXT PRIMARY KEY,status TEXT)')
            c.execute("INSERT INTO jobs VALUES('old','APPLIED')")
        for _ in range(2):
            c = workflow.connect(legacy)
            self.assertEqual(tuple(c.execute('SELECT status,applied_at FROM jobs').fetchone()), ('APPLIED', None))
            c.close()

    def test_generator_excludes_applied_and_refresh_preserves_history(self):
        c = sqlite3.connect(self.db_path)
        c.execute("UPDATE jobs SET applied_at='2026-01-01T00:00:00+00:00' WHERE id='2'")
        j = dict(id='2',source='Test',company='MongoDB',title='Backend Engineer',location='India',country='India',
                 url='https://www.mongodb.com/careers/job/?gh_jid=2',description='Java backend',rough_score=90,
                 ai_score=90,fit={},eligibility_signal='UNKNOWN',discovered_at='now',search_bucket='INDIA_PRIORITY')
        agent.save_job(c,j); c.commit()
        self.assertEqual(c.execute("SELECT status,applied_at FROM jobs WHERE id='2'").fetchone(),
                         ('APPLIED','2026-01-01T00:00:00+00:00'))
        c.close()
        jobs = [dict(j,id=str(n),url=f'https://www.mongodb.com/careers/job/?gh_jid={n}') for n in [2,1,3]]
        (self.folder/'profile.json').write_text('{}')
        previous = Path.cwd()
        try:
            os.chdir(self.folder)
            with patch.object(agent,'DB_FILE',str(self.db_path)), patch.object(agent,'BOARDS',[{'company':'Test','ats':'greenhouse'}]), \
                    patch.object(agent,'fetch_greenhouse',return_value=jobs), patch.object(agent,'rough_score',return_value=90), \
                    patch.object(agent,'ai_enabled',return_value=False), patch.object(agent,'GENERATE_PACKAGES',False), \
                    patch.object(agent,'fallback_match',return_value={'overall_fit':90,'action':'APPLY_REVIEW'}), \
                    contextlib.redirect_stdout(io.StringIO()):
                agent.main()
            with open('apply_now.csv') as f:
                urls = [r['Apply URL'] for r in csv.DictReader(f)]
            self.assertEqual(len(urls),2)
            self.assertNotIn(j['url'],urls)
        finally:
            os.chdir(previous)


if __name__ == '__main__':
    unittest.main()
