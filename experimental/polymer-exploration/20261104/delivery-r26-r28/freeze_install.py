"""Freeze actual final installation, native equality and consumer execution."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
EXTERNAL = ROOT.parent / 'open-database-evidence'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    names = ['REVIEW_INPUTS_R26_R28.json', 'INDEPENDENT_CONTENT_REVIEW_R26_R28.json',
             'build_and_verify_current.py', 'PACKAGE_GUARD_R26_R28.json', 'PACKAGE_INPUTS_R26_R28.json',
             'SOURCE_FACTS_R26_R28.json', 'INSTALLED_VALIDATION_R26_R28.json',
             'NATIVE_INSTALLED_EQUIVALENCE_R26_R28.json', 'CURRENT_CONSUMER_VALIDATION_R26_R28.json',
             'CURRENT_CONSUMER_EXECUTION_BINDING_R26_R28.json', 'FINAL_LOCAL_STATUS_R26_R28.zh.md',
             'verify_native_installed_current.py', 'verify_current_consumer.py', 'freeze_install.py']
    install = EXTERNAL / 'polymer-accepted-install-20261104-r26-r28'
    evidence = list(install.glob('*.json')) + list(install.glob('*.log')) + list((install / 'dist').glob('*.whl'))
    evidence += [p for folder in install.glob('installed-export-*') if folder.is_dir() for p in folder.iterdir() if p.is_file()]
    evidence += [EXTERNAL / 'polymer-consolidated-delivery-20261104-r26-r28/current-consumer/CURRENT_CONSUMER_VALIDATION_R26_R28.json',
                 EXTERNAL / 'polymer-consolidated-delivery-20261104-r26-r28/EXEC_TOOL_OBSERVATIONS_R26_R28.json']
    result = {'schema': 'polymer-r26-r28-final-install-consumer-review/1',
              'repo_files_sha256': {(OUT / name).relative_to(ROOT).as_posix(): sha(OUT / name) for name in names},
              'external_install_directory_hint': str(install),
              'external_files_sha256': {str(p): sha(p) for p in evidence},
              'native_snapshot': '19079de9d0a0ad0808d77f9dc2c7681c88c1facc4c43e72ae7980eb64f35c491',
              'scope': 'Actual final accepted-native package, 69 inputs/65 payload/6 metadata, provenance, native equality and actual in-process consumer; not HTTP, full platform, manifest or Git approval.',
              'pushed': False, 'merged_main': False, 'stable_release': False, 'deployed': False}
    target = OUT / 'REVIEW_INSTALL_INPUTS_R26_R28.json'
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'review_inputs_sha256': sha(target), 'repo_files': len(names), 'external_files': len(result['external_files_sha256'])}))


if __name__ == '__main__':
    main()
