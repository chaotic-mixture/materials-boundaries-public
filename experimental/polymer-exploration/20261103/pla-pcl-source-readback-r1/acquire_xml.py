"""Bounded read of the public official Europe PMC XML, with an access receipt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import urllib.request
import xml.etree.ElementTree as ET

URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7321633/fullTextXML'
EXPECTED = '1fc618818e73292837129bd4bf9885b71982974d5e7fead0056276fb28f8cb6b'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    out = Path(sys.argv[1]).resolve()
    assert not out.exists()
    out.mkdir(parents=True)
    receipt = {'url':URL,'attempts':1,'redirects_allowed':False,'limit_bytes':5_000_000,
               'timeout_seconds':45,'requested_at_utc':datetime.now(timezone.utc).isoformat(),
               'registered_XML_sha256':EXPECTED,'source_code_executed':False}
    try:
        request = urllib.request.Request(URL,headers={'User-Agent':'materials-boundaries-source-readback/1.0 (public scholarly XML)'})
        with urllib.request.build_opener(NoRedirect).open(request,timeout=45) as response:
            receipt['http_status'] = response.status
            content = response.read(5_000_001)
            assert response.status == 200 and response.geturl() == URL and len(content)<=5_000_000
        root = ET.fromstring(content)
        assert root.tag == 'article'
        ids = {node.get('pub-id-type'):node.text for node in root.findall('.//article-id')}
        assert ids.get('doi') == '10.3390/ma13112655'
        digest = hashlib.sha256(content).hexdigest()
        (out/'article.xml').write_bytes(content)
        receipt.update(status='official_XML_obtained',bytes=len(content),sha256=digest,
                       byte_equal_registered_XML=digest==EXPECTED,article_identifiers=ids,
                       latest_revision_correction_retraction_audit='not_performed')
    except Exception as error:
        receipt.update(status='not_obtained',error_type=type(error).__name__,error=str(error),
                       latest_revision_correction_retraction_audit='unknown')
    with (out/'ACCESS_RECEIPT_R1.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(receipt,stream,ensure_ascii=False,indent=2)
        stream.write('\n')
    print(json.dumps(receipt,ensure_ascii=False))


if __name__ == '__main__':
    main()
