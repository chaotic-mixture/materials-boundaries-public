"""Verify retained external bindings and the fresh consolidated CLI evidence."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EXTERNAL = ROOT.parent / 'open-database-evidence'


def main():
    cache, files, contexts = {}, {}, {}

    def sha(path):
        path = path.resolve()
        if path not in cache: cache[path] = hashlib.sha256(path.read_bytes()).hexdigest()
        return cache[path]

    def add(path, digest, label, found):
        path = Path(path).resolve()
        assert path.is_relative_to(EXTERNAL) or path.is_relative_to(ROOT / 'materials_boundaries/data'), str(path)
        assert path.is_file() and sha(path) == digest, str(path)
        key = str(path)
        if key in files: assert files[key]['sha256'] == digest
        files[key] = {'sha256': digest, 'bytes': path.stat().st_size}
        found.append({'field': label, 'path_hint': key, 'sha256': digest})

    def visit_assets(obj, found):
        if isinstance(obj, list):
            for value in obj: visit_assets(value, found)
        elif isinstance(obj, dict):
            hint, digest = obj.get('path_hint'), obj.get('sha256')
            if isinstance(hint, str) and isinstance(digest, str) and len(digest) == 64:
                path = Path(hint).resolve()
                if path.is_relative_to(EXTERNAL): add(path, digest, 'asset path_hint', found)
            for value in obj.values(): visit_assets(value, found)

    raw = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=ROOT)
    for entry in raw.split(b'\0'):
        if not entry: continue
        path = ROOT / entry[3:].decode('utf-8')
        if path.suffix != '.json' or not path.is_relative_to(ROOT / 'experimental'): continue
        obj = json.loads(path.read_bytes())
        if not isinstance(obj, dict): continue
        found = []
        absolute = obj.get('external_files_sha256', {})
        for name, digest in absolute.items():
            assert Path(name).is_absolute()
            add(name, digest, 'external_files_sha256', found)
        for field, hint_field in [('external_evidence_sha256', 'external_install_directory_hint'),
                                  ('external_preview_files_sha256', 'external_preview_directory_hint'),
                                  ('recovery_files_sha256', 'recovery_directory_hint'),
                                  ('baseline_table_sha256', 'recovery_copy_hint')]:
            for name, digest in obj.get(field, {}).items():
                if field == 'baseline_table_sha256' and hint_field not in obj:
                    assert 'baseline_directory_hint' in obj, str(path)
                    hint_field = 'baseline_directory_hint'
                if hint_field in obj:
                    target = Path(obj[hint_field]) / name
                else:
                    candidates = [Path(n) for n, h in absolute.items() if Path(n).name == name and h == digest]
                    assert len(candidates) == 1, (str(path), field, name)
                    target = candidates[0]
                add(target, digest, field, found)
        visit_assets(obj, found)
        if found: contexts[path.relative_to(ROOT).as_posix()] = {'entry_sha256': sha(path), 'bindings': found}
    result = {'schema': 'polymer-delivery-retained-external-evidence/1', 'contexts': contexts,
              'files': files, 'unique_files': len(files), 'verified_bindings': sum(len(c['bindings']) for c in contexts.values()),
              'scope': 'Exact retained source/preview/installed/recovery bytes only; not scientific validity, new downloads, licence certification or latest notices. Diagnostic404 content remains diagnostic regardless of filename suffix.'}
    with (OUT / 'EXTERNAL_SOURCE_BINDING_R19_R22.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    current = EXTERNAL / 'polymer-consolidated-delivery-20261103-r19-r22'
    proof = [current / n for n in ('check.log', 'export.log', 'verify.log', 'REMOTE_BASELINE_R19_R22.json',
                                  'database-example/manifest.json', 'database-example/records.jsonl')]
    assert all(path.is_file() for path in proof)
    execution = {'schema': 'polymer-delivery-current-execution-binding/1',
                 'external_files_sha256': {str(path): sha(path) for path in proof},
                 'scope': 'Fresh consolidated graph/export/verify execution and previously observed remote baseline; remote ref must be rechecked before push.'}
    with (OUT / 'EXTERNAL_EXECUTION_BINDING_R19_R22.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(execution, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'contexts': len(contexts), 'unique_external_files': len(files),
                      'verified_bindings': result['verified_bindings'], 'current_execution_files': len(proof)}))


if __name__ == '__main__':
    main()
