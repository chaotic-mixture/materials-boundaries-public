"""Acquire an official public PDF externally; no native data writes."""
from pathlib import Path
import hashlib
import json
import urllib.request

EXT = Path('F:/材料边界/open-database-evidence/polymer-nr-work-to-break-20261104-r1')
URL = 'https://mdpi-res.com/d_attachment/molecules/molecules-30-03035/article_deploy/molecules-30-03035.pdf'


def main():
    EXT.mkdir(exist_ok=False)
    with urllib.request.urlopen(urllib.request.Request(URL, headers={'User-Agent': 'materials-boundaries-source-audit/1.0'}), timeout=30) as response:
        content = response.read()
        receipt = {'requested_url': URL, 'final_url': response.url, 'status': response.status,
                   'content_type': response.headers.get('Content-Type'), 'bytes': len(content),
                   'sha256': hashlib.sha256(content).hexdigest()}
    assert content.startswith(b'%PDF-')
    with (EXT / 'article-r1.pdf').open('xb') as stream:
        stream.write(content)
    with (EXT / 'ACQUISITION_R1.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
