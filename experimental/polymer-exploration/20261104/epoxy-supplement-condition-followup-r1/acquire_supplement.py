"""Acquire public source assets externally; no native edits or redistribution."""
from pathlib import Path
import hashlib
import json
import sys
import urllib.request
import zipfile

EXT = Path('F:/材料边界/open-database-evidence/polymer-epoxy-supplement-20261104-r1')
URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9655627/supplementaryFiles'


def main():
    retry = sys.argv[1:] == ['--retry']
    assert not sys.argv[1:] or retry
    EXT.mkdir(exist_ok=retry)
    request = urllib.request.Request(URL, headers={'User-Agent': 'materials-boundaries-source-audit/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content = response.read()
            receipt = {'requested_url': URL, 'final_url': response.url, 'status': response.status,
                       'content_type': response.headers.get('Content-Type'), 'bytes': len(content),
                       'sha256': hashlib.sha256(content).hexdigest()}
        (EXT / 'supplementary-response.zip').write_bytes(content)
        with zipfile.ZipFile(EXT / 'supplementary-response.zip') as archive:
            receipt['archive_entries'] = [{'name': item.filename, 'size': item.file_size} for item in archive.infolist()]
        (EXT / ('ACQUISITION_R2.json' if retry else 'ACQUISITION_R1.json')).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps(receipt, ensure_ascii=False))
    except Exception as error:
        (EXT / ('ACQUISITION_FAILURE_R2.json' if retry else 'ACQUISITION_FAILURE_R1.json')).write_text(json.dumps({'url': URL, 'error_type': type(error).__name__, 'error': str(error)}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        raise


if __name__ == '__main__':
    main()
