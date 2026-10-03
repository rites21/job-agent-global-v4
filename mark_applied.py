"""Record verified browser outcomes; never mark APPLIED from a URL alone."""
import argparse
from application_workflow import record_outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job', help='Exact database job id or application URL')
    parser.add_argument('--approved', action='store_true', help='User approved this specific submission')
    parser.add_argument('--submitted', action='store_true', help='Submit was clicked')
    parser.add_argument('--confirmed', action='store_true', help='Explicit success was observed, without validation errors')
    parser.add_argument('--confirmation', default='', help='Observed success message or failure reason')
    parser.add_argument('--confirmation-url', default='', help='Observed page URL after submission')
    args = parser.parse_args()
    if args.confirmed and not (args.approved and args.submitted and args.confirmation.strip() and args.confirmation_url.strip()):
        parser.error('Confirmed success requires approval, submission, success text and confirmation URL')
    record_outcome(args.job, approved=args.approved, submitted=args.submitted,
                   confirmed=args.confirmed, confirmation=args.confirmation,
                   confirmation_url=args.confirmation_url)


if __name__ == '__main__':
    main()
