"""List ranked jobs by default; --open opens one job at a time for review."""
import argparse
import webbrowser
from application_workflow import connect, applied, ranked_jobs, load_application_materials


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()
    if args.open:
        load_application_materials()
    for job in ranked_jobs(limit=args.limit):
        # Fresh status check immediately before opening, even with a stale CSV.
        c = connect()
        try:
            if applied(c, job['job_id']):
                continue
        finally:
            c.close()
        print(f"{job['rank']:02}. {job['Company']} | {job['Role']} | {job['job_id']} | {job['Apply URL']}")
        if args.open:
            if not webbrowser.open_new_tab(job['Apply URL']):
                print('Browser could not be opened; stopping.')
                break
            print('Fill factual details, then STOP before Submit for user review.')
            if input('After review/status recording, type NEXT to continue, or STOP: ').strip().upper() != 'NEXT':
                break


if __name__ == '__main__':
    main()
