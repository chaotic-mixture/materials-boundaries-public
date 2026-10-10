"""Offline CLI for explicitly scoped formal project admissions."""
import argparse
import json
import sys
from .catalog import formal_project_catalog, select_formal_catalog


def main():
    parser = argparse.ArgumentParser(description="Formal project admissions with separate legacy and computed provenance")
    parser.add_argument("--list", action="store_true", help="List admissions; default is counts and policy")
    parser.add_argument("--query")
    parser.add_argument("--partition", choices=("legacy-source-qualified", "reviewed-computed"))
    parser.add_argument("--id", dest="record_id")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    if not 0 <= args.offset <= 10000 or not 1 <= args.limit <= 100:
        parser.error("Use offset 0-10000 and limit 1-100")
    try:
        snapshot = formal_project_catalog()
        result = select_formal_catalog(snapshot, query=args.query, partition=args.partition,
            record_id=args.record_id, offset=args.offset, limit=args.limit) if (
            args.list or args.query is not None or args.partition is not None or args.record_id is not None) else {
                key: value for key, value in snapshot.items() if key != "records"}
    except ValueError as exc:
        print(json.dumps({"error": "invalid_formal_catalog", "detail": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
