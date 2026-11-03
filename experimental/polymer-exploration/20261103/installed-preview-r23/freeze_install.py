"""Freeze completed isolated installation and the local application helpers."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
AREA = ROOT / 'experimental/polymer-exploration/20261103'
OUT = Path(__file__).resolve().parent
EXTERNAL = ROOT.parent / 'open-database-evidence'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    install = EXTERNAL / 'polymer-installed-preview-20261104-r23'
    preview = EXTERNAL / 'polymer-nbr-tear-native-preview-20261104-r23/native-tables'
    mapping = AREA / 'nbr-tear-native-r1'
    files = [p for p in OUT.iterdir() if p.is_file()]
    files += list((AREA / 'local-acceptance-r23').glob('*.py'))
    files += [mapping / name for name in ('REVIEW_INPUTS_R2.json', 'INDEPENDENT_MAPPING_REVIEW_R2.json')]
    external_files = list(install.glob('*.json')) + list(install.glob('*.log'))
    external_files += list((install / 'dist').glob('*.whl'))
    external_files += list((install / 'installed-export-tamas_benyei_santha_2025_nbr_rcf').glob('*'))
    result = {
        'schema': 'NBR-tear-install-and-application-review/1',
        'repo_files_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in files},
        'external_install_directory_hint': str(install),
        'external_evidence_sha256': {p.relative_to(install).as_posix(): sha(p) for p in external_files if p.is_file()},
        'external_preview_directory_hint': str(preview),
        'external_preview_files_sha256': {p.name: sha(p) for p in preview.glob('*.json')},
        'preview_snapshot': json.loads((mapping / 'REVIEW_INPUTS_R2.json').read_bytes())['combined_snapshot'],
        'native_applied': False,
        'full_history_regression': 'not_run',
        'pushed': False,
    }
    target = OUT / 'REVIEW_INPUTS_R23.json'
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'review_inputs_sha256': sha(target), 'repo_files': len(files), 'external_files': len(result['external_evidence_sha256'])}))


if __name__ == '__main__':
    main()
