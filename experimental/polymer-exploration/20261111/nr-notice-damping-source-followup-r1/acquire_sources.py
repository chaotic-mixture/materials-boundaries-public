"""Read public primary source endpoints once,retain bytes outside the repository."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,urllib.request,urllib.error,sys
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
EXT=ROOT.parent/('open-database-evidence/polymer-nr-notice-damping-20261111-r2' if sys.argv[1:]==['--network-r2'] else 'open-database-evidence/polymer-nr-notice-damping-20261111-r1')
URLS={
 'publisher2025.html':'https://www.mdpi.com/1420-3049/30/14/3035',
 'publisher2025.pdf':'https://mdpi-res.com/d_attachment/molecules/molecules-30-03035/article_deploy/molecules-30-03035.pdf',
 'crossref2025.json':'https://api.crossref.org/works/10.3390/molecules30143035',
 'europepmc2025.xml':'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12300880/fullTextXML',
 'publisher2024.html':'https://www.mdpi.com/2076-3417/14/22/10525',
 'crossref2024.json':'https://api.crossref.org/works/10.3390/app142210525'}
def get(item):
    name,url=item
    request=urllib.request.Request(url,headers={'User-Agent':'MaterialsBoundariesSourceAudit/2026','Accept':'*/*'})
    try:
        with urllib.request.urlopen(request,timeout=30) as response:
            raw=response.read();status=response.status;headers=dict(response.headers);final_url=response.url
        with (EXT/name).open('xb') as f:f.write(raw)
        return name,dict(url=url,final_url=final_url,status=status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),headers=headers,saved_path_hint=str(EXT/name),scope='Acquired bytes;body validation and source inspection separate')
    except urllib.error.HTTPError as e:
        raw=e.read();p=EXT/(name+'.http-error-body')
        with p.open('xb') as f:f.write(raw)
        return name,dict(url=url,status=e.code,error=str(e),body_sha256=hashlib.sha256(raw).hexdigest(),saved_path_hint=str(p),source_body_verified=False,retry=False)
    except Exception as e:return name,dict(url=url,error_type=type(e).__name__,error=str(e),source_body_verified=False,retry=False)
def main():
    assert sys.argv[1:] in ([],['--network-r2'])
    EXT.mkdir(exist_ok=False)
    with ThreadPoolExecutor(max_workers=3) as executor:results=dict(executor.map(get,URLS.items()))
    with (EXT/'ACQUISITION_R1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(results,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({n:{k:v for k,v in obj.items() if k in ('status','bytes','sha256','error_type','error')} for n,obj in results.items()},ensure_ascii=False))
if __name__=='__main__':main()
