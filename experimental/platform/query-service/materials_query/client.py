"""Bounded local batch client. Input: {\"queries\":[{\"formula\":\"Fe\",\"limit\":1}]}"""
import argparse
import json
from pathlib import Path
import httpx
from .app import BatchRequest

def main():
    p=argparse.ArgumentParser(description='Query a local service with a validated bounded batch')
    p.add_argument('input',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--port',type=int,default=8765)
    args=p.parse_args()
    if not 1 <= args.port <= 65535:
        p.error('Port must be between 1 and 65535')
    if args.input.stat().st_size > 32768:
        p.error('Input exceeds 32 KiB')
    request=BatchRequest.model_validate_json(args.input.read_text())
    with httpx.Client(timeout=180,trust_env=False,follow_redirects=False) as client:
        response=client.post(f'http://127.0.0.1:{args.port}/api/batch',json=request.model_dump())
        response.raise_for_status()
        result=response.json()
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(result['status'])
if __name__=='__main__':main()
