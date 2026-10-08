import argparse
import json
from pathlib import Path
from .workflow import Workflow, Response, read_json

def main():
    parser = argparse.ArgumentParser(description="Local review-bound NOMAD lifecycle; no publication")
    parser.add_argument("--store", required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("capture")
    capture.add_argument("--formula", required=True)
    capture.add_argument("--limit", type=int, default=25)
    capture.add_argument("--fixture", help="Exact HTTP JSON fixture with data list; absence requests bounded public NOMAD")
    stage = sub.add_parser("stage")
    stage.add_argument("acquisition")
    stage.add_argument("--baseline")
    review = sub.add_parser("review")
    review.add_argument("batch")
    review.add_argument("--approve", action="append", required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--contributor", required=True)
    review.add_argument("--rationale", required=True)
    review.add_argument("--rights-evidence", required=True)
    review.add_argument("--demo", action="store_true")
    build = sub.add_parser("build")
    build.add_argument("batch")
    build.add_argument("decision")
    build.add_argument("--trusted-decision-sha256", required=True)
    build.add_argument("--version", required=True)
    build.add_argument("--title", required=True)
    build.add_argument("--creator", action="append", required=True)
    inspect = sub.add_parser("inspect")
    inspect.add_argument("artifact")
    event = sub.add_parser("status-event")
    event.add_argument("release")
    event.add_argument("--record-id", required=True)
    event.add_argument("--kind", choices=["withdrawn", "superseded", "erratum"], required=True)
    event.add_argument("--reason", required=True)
    event.add_argument("--source-url", required=True)
    event.add_argument("--superseded-by")
    args = parser.parse_args()
    workflow = Workflow(args.store)
    if args.command == "capture":
        raw = Path(args.fixture).read_bytes() if args.fixture else None
        result = workflow.capture({"formula": args.formula, "limit": args.limit},
            fetch=(lambda url, **kwargs: Response(raw)) if args.fixture is not None else None, fixture=args.fixture is not None)
    elif args.command == "stage":
        result = workflow.stage(args.acquisition, baseline=args.baseline)
    elif args.command == "review":
        result = workflow.review(args.batch, approved_ids=args.approve, reviewer=args.reviewer,
            contributor=args.contributor, rationale=args.rationale, rights_evidence=args.rights_evidence, demo=args.demo)
    elif args.command == "build":
        result = workflow.build(args.batch, args.decision, trusted_decision_sha256=args.trusted_decision_sha256,
            version=args.version, title=args.title, creators=args.creator)
    elif args.command == "status-event":
        result = workflow.status_event(args.release, record_id=args.record_id, kind=args.kind,
            reason=args.reason, source_url=args.source_url, superseded_by=args.superseded_by)
    else:
        result = json.dumps(read_json(args.artifact), indent=2)
    print(result)

if __name__ == "__main__":
    main()
