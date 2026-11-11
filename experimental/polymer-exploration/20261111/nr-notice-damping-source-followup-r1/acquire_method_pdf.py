"""Acquire the publicly linked method-reference article PDF without retry/bypass."""
from pathlib import Path
import hashlib,json,urllib.request,urllib.error
ROOT=Path(__file__).resolve().parents[4]
EXT=ROOT.parent/'open-database-evidence/polymer-nr-notice-damping-20261111-r2'
URL='https://mdpi-res.com/d_attachment/applsci/applsci-14-10525/article_deploy/applsci-14-10525.pdf'
def main():
    try:
        request=urllib.request.Request(URL,headers={'User-Agent':'MaterialsBoundariesSourceAudit/2026'})
        with urllib.request.urlopen(request,timeout=30) as response:raw=response.read();headers=dict(response.headers);status=response.status
        assert raw.startswith(b'%PDF-')
        with (EXT/'publisher2024.pdf').open('xb') as f:f.write(raw)
        result=dict(url=URL,status=status,headers=headers,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),pdf_signature_verified=True,selected_content_inspection='not_run')
    except Exception as e:result=dict(url=URL,error_type=type(e).__name__,error=str(e),source_body_verified=False,retry=False)
    with (EXT/'METHOD_PDF_ACQUISITION_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
