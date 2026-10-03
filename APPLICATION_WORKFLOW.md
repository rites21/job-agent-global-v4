# Reviewed application workflow

This file defines the browser operator's workflow. The Python helpers track state;
 they do not drive or verify browser pages themselves. Never treat their flags as
 a substitute for observing actual browser confirmation.

1. Read `PROJECT_CONTEXT.md`, `application_profile.json`, `profile.json`, and
   `resume.pdf`. Use only factual information from these files. Pause on missing
   or conflicting facts, salary, notice period, authorization, sponsorship,
   demographic questions, consent, and legal declarations.
2. Get the batch with `python3 open_apply_jobs.py --limit 10`. CSV row order is
   authoritative. The database, not the CSV, decides whether a job is APPLIED.
   Unknown/ambiguous database matches are blocked, never opened blindly.
3. Immediately before each browser open, re-read that exact job in `jobs_v4.db`.
   Skip APPLIED. Also recheck before any submission to avoid a concurrently
   completed manual application. Keep one active application at a time.
4. Open the Apply URL through the browser tools. Fill factual fields and upload
   `resume.pdf`. STOP before final Submit and show the draft for user review.
   Filling/uploading is not submission, and approval is not success.
5. Only after the user approves that specific application, click Submit. Wait
   for a clear success page or message for that job. Inspect for validation
   errors. A spinner, a click, HTTP response, changed URL, or cleared form alone
   is not enough. Do not retry an unclear submission automatically.
6. On observed success, immediately run:

   ```bash
   python3 mark_applied.py 'EXACT_JOB_ID' --approved --submitted --confirmed \
     --confirmation 'EXACT OBSERVED SUCCESS MESSAGE' \
     --confirmation-url 'ACTUAL CONFIRMATION PAGE URL'
   ```

   This atomically sets `status=APPLIED` and `applied_at` to a UTC timestamp and
   prints company, role, timestamp, status and confirmation evidence. Never pass
   placeholders or invented evidence. Verify the printed result before continuing.
7. For a failed/unclear attempted submission, record its actual reason:

   ```bash
   python3 mark_applied.py 'EXACT_JOB_ID' --approved --submitted \
     --confirmation 'OBSERVED VALIDATION ERROR OR UNCLEAR CONFIRMATION'
   ```

   This sets APPLICATION_BLOCKED, not APPLIED. If no submission was attempted,
   leave status unchanged. If database recording fails after successful submission,
   stop and reconcile the result; never submit again just to repair tracking.
8. Continue to the next ranked job only after recording the result. Each next
   application still needs its own review and approval. Stop immediately if asked.

`python3 open_apply_jobs.py --open --limit 10` is a manual, one-tab-at-a-time
opener. It pauses for NEXT/STOP; it does not fill or submit forms. In an assisted
Codex session, use browser tools and the steps above instead.

Applied rows are retained permanently. Existing APPLIED rows with an unknown
application date retain a null `applied_at`; do not invent past timestamps.
The previous ten application rows are now APPLIED in the database and were
removed from apply_now.csv. Do not reopen them. Never infer historical dates.
