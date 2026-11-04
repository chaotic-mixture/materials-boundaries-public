"""Freeze concept-only review inputs; never modify runtime or native tables."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'pur-dma-tg-tga-followup-source-r1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    proposal = json.loads((HERE / 'CONTRACT_PROPOSAL_R1.json').read_text(encoding='utf-8'))
    source_entry = SOURCE / 'REVIEW_INPUTS_R1.json'
    approval = SOURCE / 'INDEPENDENT_SOURCE_REVIEW_R1.json'
    assert sha(source_entry) == proposal['source_entry_sha256']
    assert sha(approval) == proposal['source_approval_sha256']
    source_manifest = json.loads(source_entry.read_text(encoding='utf-8'))
    external = source_manifest['external_files_sha256']
    for path, digest in external.items():
        assert sha(Path(path)) == digest, path
    files = list(HERE.iterdir()) + [source_entry, approval, SOURCE / 'TGA_SOURCE_LEADS_R1.json', SOURCE / 'EXTRACTION_CAUTION_R1.json']
    files += [ROOT / name for name in (
        'materials_boundaries/material_references.py',
        'materials_boundaries/material_presentation.py',
        'materials_boundaries/data/material_locales.json',
        'schemas/reference_properties.schema.json',
    )]
    native = [ROOT / 'materials_boundaries/data' / name for name in ('materials.json', 'reference_properties.json', 'sources.json')]
    entry = {
        'schema': 'TGA-endpoint-contract-concept-review/1',
        'repo_files_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files) if p.is_file()},
        'native_files_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in native},
        'external_files_sha256': external,
        'scope': 'Contract concept and 28 partial role examples only;not implementation/mapping/native admission approval',
        'native_snapshot': proposal['native_snapshot'],
        'new_native_records': 0,
        'review_constraints': 'Readonly own inline hashes/JSON/source/primary-unit-reference checks only;no author helpers,suites,full graph/history,writes,push or installation',
    }
    output = HERE / 'REVIEW_INPUTS_R1.json'
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(entry, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps({'entry_sha256': sha(output), 'repo_files': len(entry['repo_files_sha256']), 'native_files': len(native), 'external_files': len(external)}))


if __name__ == '__main__':
    main()
