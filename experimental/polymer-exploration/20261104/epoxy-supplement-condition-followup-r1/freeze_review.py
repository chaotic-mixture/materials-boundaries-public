"""Freeze source-only follow-up; never change native data or old audit scopes."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
EXT = ROOT.parent / 'open-database-evidence/polymer-epoxy-supplement-20261104-r1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    validation = json.loads((HERE / 'VALIDATION_R1.json').read_bytes())
    assert validation['native_inputs_unchanged'] and validation['unknowns_filled'] == 0
    native = validation['native_before_sha256']
    assert all(sha(ROOT / name) == digest for name, digest in native.items())
    files = {path for path in HERE.iterdir() if path.is_file()}
    files |= {HERE.parent / 'local-acceptance-r37' / name for name in ('REVIEW_ACCEPTANCE_INPUTS_R37_R2.json', 'INDEPENDENT_ACCEPTANCE_REVIEW_R37_R2.json')}
    external = {path for path in EXT.iterdir() if path.is_file()}
    external |= {ROOT.parent / 'open-database-evidence/polymer-epoxy-20261103' / name
                 for name in ('tarasov2022-r1.pdf', 'method-visual-06.png', 'license-r11-01.png')}
    manifest = {'schema': 'existing-epoxy-supplement-source-review/1',
        'repo_files_sha256': {path.relative_to(ROOT).as_posix(): sha(path) for path in sorted(files)},
        'native_files_sha256': native,
        'external_files_sha256': {str(path): sha(path) for path in sorted(external)},
        'scope': 'Official3supplementPNG source/missingcondition/normalization/rights audit and unapplied source-metadata proposal;not new properties or admission',
        'native_applied': False, 'unknowns_filled': 0,
        'review_constraints': 'Readonly owninlinehash/JSON/directvisual/primarysource checks;no author helpers/testmodules/suites/fullgraph/history/write/install/push'}
    output = HERE / 'REVIEW_INPUTS_R1.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'entry_sha256': sha(output), 'repo_files': len(files), 'native_files': len(native), 'external_files': len(external)}))


if __name__ == '__main__':
    main()
