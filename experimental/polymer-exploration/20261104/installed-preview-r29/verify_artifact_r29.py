"""Check wheel/installed RECORD and complete exported objects without rebuilding."""
from pathlib import Path
import base64,csv,hashlib,io,json,marshal,sys,zipfile,importlib.util,types

ROOT=Path(__file__).resolve().parents[4]
EXT=ROOT.parent/'open-database-evidence'
INSTALL=EXT/'polymer-installed-preview-20261104-r29'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(b):return base64.urlsafe_b64encode(hashlib.sha256(b).digest()).decode().rstrip('=')

def main():
    wheel,=list((INSTALL/'dist').glob('*.whl'))
    with zipfile.ZipFile(wheel) as z:
        record,=[n for n in z.namelist() if n.endswith('.dist-info/RECORD')]
        wheel_rows=list(csv.reader(io.StringIO(z.read(record).decode())))
        checked=0
        for name,h,size in wheel_rows:
            if not h:
                assert name==record and not size
                continue
            assert h.startswith('sha256=')
            data=z.read(name);assert digest(data)==h.split('=',1)[1] and len(data)==int(size)
            checked+=1
    site=INSTALL/'venv/Lib/site-packages'
    record,=site.glob('materials_boundaries-*.dist-info/RECORD')
    rows=list(csv.reader(io.StringIO(record.read_text(encoding='utf-8'))))
    hashed=0;pyc=0
    for name,h,size in rows:
        p=(site/name).resolve();assert p.is_relative_to(INSTALL/'venv')
        data=p.read_bytes()
        if h:
            assert h.startswith('sha256=') and digest(data)==h.split('=',1)[1] and len(data)==int(size),name
            hashed+=1
        elif p==record.resolve():assert not size
        else:
            assert name.startswith('materials_boundaries/') and p.suffix=='.pyc' and not size
            assert data[:4]==importlib.util.MAGIC_NUMBER
            code=marshal.loads(data[16:]);source=Path(code.co_filename)
            assert source.is_relative_to(site/'materials_boundaries')
            expected=compile(source.read_bytes(),code.co_filename,'exec',dont_inherit=True,optimize=0)
            def equal_code(actual,wanted):
                assert actual==wanted
                for name in dir(actual):
                    if name.startswith('co_') and not callable(getattr(actual,name)):
                        assert getattr(actual,name)==getattr(wanted,name),name
                for a,b in zip(actual.co_consts,wanted.co_consts):
                    if isinstance(a,types.CodeType):equal_code(a,b)
            equal_code(code,expected)
            pyc+=1
    assert checked==71 and hashed==76 and pyc==50
    before=EXT/'polymer-pbs-dsc-native-preview-20261104-r1/source-export/records.jsonl'
    after=INSTALL/'installed-export-ewurum_mcdonald_2025_pbs_lignin/records.jsonl'
    assert before.read_bytes()==after.read_bytes()
    result={'status':'artifact_records_and_complete_export_passed','wheel_sha256':sha(wheel),'wheel_RECORD_hashed_files':checked,'wheel_RECORD_rows':len(wheel_rows),'installed_RECORD_hashed_files':hashed,'installed_RECORD_rows':len(rows),'generated_unhashed_pyc_equal_source':pyc,'complete_source_export_objects':28,'preview_snapshot':'82e9840bca99bc36b273c1df7542f5d1019d4be3141df4584432eef88e399abc','native_applied':False,'full_history_regression':'not_run','pushed':False}
    with (INSTALL/'ARTIFACT_RECORDS_AND_EXPORT_R29.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(result))

if __name__=='__main__':main()
