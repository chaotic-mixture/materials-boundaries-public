"""Audit a committed catalog transition against the exact Git base."""
import argparse
import json
import subprocess
from pathlib import Path

TABLE = "materials_boundaries/data/reference_properties.json"


def check(old, new, decisions):
    def ids(rows):
        keys = {row["id"] for row in rows}
        if len(keys) != len(rows):
            raise ValueError("Duplicate property ID")
        return keys
    before, after = ids(old), ids(new)
    missing = before - after
    if set(decisions) != missing:
        raise ValueError(f"Missing IDs or stale decisions: {sorted(missing ^ set(decisions))}")
    for key, decision in decisions.items():
        action = decision.get("action")
        if not str(decision.get("evidence") or "").strip():
            raise ValueError(f"Missing evidence for {key}")
        if action in ("rename", "merge") and decision.get("target") in after:
            continue
        if action != "remove":
            raise ValueError(f"Invalid disposition for {key}")
    return len(missing)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base")
    args = parser.parse_args()
    baseline = subprocess.check_output(["git", "show", f"{args.base}:{TABLE}"])
    manifest = Path("docs/catalog-transitions") / (args.base + ".json")
    decisions = json.loads(manifest.read_bytes()) if manifest.exists() else {}
    count = check(json.loads(baseline)["records"], json.loads(Path(TABLE).read_bytes())["records"], decisions)
    print(f"Verified transition against {args.base}, {count} documented removals")


if __name__ == "__main__":
    main()
