"""Explicit bounded NOMAD demonstration; no background requests or MP key loading."""
import argparse
import json
from pathlib import Path
from .models import Query
from .providers import NomadAdapter
from .review import review_package


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formula",required=True)
    parser.add_argument("--limit",type=int,default=1)
    parser.add_argument("--enrich-first",action="store_true",help="Read one public archive after search")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    query=Query(formula=args.formula,limit=args.limit)
    adapter=NomadAdapter()
    page=adapter.search(query)
    candidates=list(page.candidates)
    if args.enrich_first and candidates:
        candidates[0]=adapter.enrich_archive(candidates[0])
    data={"search":page.model_dump(mode="json"),"review":review_package(candidates)}
    args.output.write_text(json.dumps(data,indent=2,allow_nan=False)+"\n")
    print(f"Saved {len(candidates)} pending candidates; admitted 0, quota credit 0.")

if __name__ == "__main__": main()
