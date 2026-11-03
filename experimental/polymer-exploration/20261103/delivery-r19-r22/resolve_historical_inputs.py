"""Resolve every changed packet's repository pins without editing frozen inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
AREA = OUT.parent


def main():
    cache = {}

    def sha(path):
        path = path.resolve()
        if path not in cache: cache[path] = hashlib.sha256(path.read_bytes()).hexdigest()
        return cache[path]

    backups = list((OUT / 'pre-delivery-documents').rglob('*'))
    external = ROOT.parent / 'open-database-evidence'
    for stage in ('r19', 'r20', 'r21', 'r22'):
        backups += list((external / ('polymer-native-acceptance-20261103-' + stage) / 'baseline-tables').glob('*.json'))
    for folder in ('nr-shore-a-source-contract-proposal-r1/baseline-contract',
                   'sylgard-hardness-native-r1/r20-context', 'sylgard-hardness-native-r1/r1-format-context',
                   'sylgard-compression-source-contract-r1/baseline-contract'):
        backups += list((AREA / folder).rglob('*'))
    historical = {}
    for path in backups:
        if path.is_file(): historical.setdefault(sha(path), path)
    raw = subprocess.check_output(['git', 'status', '--porcelain=v1', '-z', '--untracked-files=all'], cwd=ROOT)
    entries = [entry for entry in raw.split(b'\0') if entry]
    assert not any(entry[:2] in (b'R ', b' R', b'C ', b' C') for entry in entries)
    paths = [ROOT / entry[3:].decode('utf-8') for entry in entries]
    contexts = {}
    for path in sorted(paths):
        if path.suffix != '.json' or not path.is_relative_to(ROOT / 'experimental'): continue
        obj = json.loads(path.read_bytes())
        if not isinstance(obj, dict): continue
        bindings = obj.get('repo_files_sha256')
        kind = 'repo_files_sha256'
        if path.name.startswith('PACKAGE_INPUTS'):
            bindings, kind = obj, 'package inputs'
        elif bindings is None and 'input_sha256_before_and_after' in obj:
            bindings, kind = obj['input_sha256_before_and_after'], 'historical test pre/post inputs'
        if bindings is None: continue
        resolved = {}
        for name, digest in bindings.items():
            assert isinstance(digest, str) and len(digest) == 64, (str(path), name)
            current = (ROOT / name).resolve()
            assert current.is_relative_to(ROOT)
            if current.is_file() and sha(current) == digest:
                target = current
            else:
                assert digest in historical, (str(path), name, digest)
                target = historical[digest]
            assert sha(target) == digest
            resolved[name] = {'sha256': digest, 'resolved_path_hint': str(target), 'current': target == current}
        contexts[path.relative_to(ROOT).as_posix()] = {'entry_sha256': sha(path), 'binding_kind': kind, 'resolved': resolved}
    result = {'schema': 'polymer-r19-r22-historical-input-resolution/1', 'contexts': contexts,
              'resolved_entries': sum(len(value['resolved']) for value in contexts.values()), 'unresolved_entries': 0,
              'policy': 'Frozen entries remain unchanged; core/schema/docs resolve to exact context archives, old native tables to exact recovery copies; pre/post test bindings included.'}
    with (OUT / 'HISTORICAL_INPUT_RESOLUTION_R19_R22.json').open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'contexts': len(contexts), 'resolved': result['resolved_entries'], 'unresolved': 0}))


if __name__ == '__main__':
    main()
