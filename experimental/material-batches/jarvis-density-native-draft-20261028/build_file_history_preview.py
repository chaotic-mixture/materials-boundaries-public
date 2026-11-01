"""Bind prospective code and document images to exact live predecessors."""
import argparse
import difflib
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--preview', type=Path, required=True)
    args = parser.parse_args()
    stage, preview = args.stage.resolve(), args.preview.resolve()
    if not preview.is_relative_to(ROOT.parent / 'growth-source-cache'):
        raise ValueError('External preview required')
    if (BATCH / 'file-history-preview.json').exists():
        raise ValueError('Preserve existing frozen preview')
    sys.path[:0] = [str(stage), str(ROOT / 'tests'), str(ROOT)]
    from material_append_history import encoded, recover_file
    import material_bulk_preservation as bulk
    import materials_boundaries.material_references as references
    if not Path(references.__file__).resolve().is_relative_to(stage):
        raise ValueError('Isolated approved method required')
    manifest = json.loads((BATCH / 'draft-manifest.json').read_bytes())
    images = {}
    for rel, hashes in manifest['changes'].items():
        before, after = (ROOT / rel).read_bytes(), (stage / rel).read_bytes()
        if sha256(before).hexdigest() != hashes['baseline_sha256'] or sha256(after).hexdigest() != hashes['draft_sha256']:
            raise ValueError('Unreviewed method image: ' + rel)
        images[rel] = (before, after)
    old_readme = (ROOT / 'README.md').read_bytes()
    text = old_readme.decode('utf8')
    for old, new in [('**130 source records**', '**131 source records**'),
                     ('The 130 sources comprise 129 bibliographic/source records', 'The 131 sources comprise 130 bibliographic/source records'),
                     ('**1180 material identities**', '**3180 material identities**'),
                     ('**1181 source-scoped states**', '**3181 source-scoped states**'),
                     ('**1197 reference properties**', '**3197 reference properties**')]:
        if text.count(old) != 1:
            raise ValueError('Unexpected prior README marker: ' + old)
        text = text.replace(old, new, 1)
    marker = '<!-- material-catalog-summary:end -->\n'
    paragraph = ('\nThe local JARVIS working graph additionally contains 2,000 source-qualified hypothetical computational crystal-model identity candidates '
                 '(1,000 metal-family compositions and 1,000 inorganic compositions), each with one reported optimized-structure density. '
                 'The working-graph counts above include these pending candidates; they are not yet admitted quota entries. '
                 'Finite composition-based classification does not establish metallic electronic behavior, experimental existence or stable phases. '
                 'Historical preservation, full regression and installed checks remain pending. '
                 '[Frozen review and integration evidence](experimental/material-batches/jarvis-density-native-draft-20261028/README.md).\n')
    if text.count(marker) != 1:
        raise ValueError('Unexpected README summary marker')
    text = text.replace(marker, marker + paragraph, 1)
    text = text.replace('The local experimental Sanchez aluminium-alloy append adds', 'The preceding locally accepted Sanchez aluminium-alloy append added', 1)
    text = text.replace('The local experimental project inventory is **1204 = 1180 source-qualified identities + 24 reviewed computed records**.',
                        'That preceding local experimental checkpoint had 1204 project records: 1180 source-qualified identities plus 24 reviewed computed records.', 1)
    images['README.md'] = (old_readme, text.encode('utf8'))
    old_notice = (ROOT / 'THIRD_PARTY_NOTICES.md').read_bytes()
    notice = ('\n\n## JARVIS-DFT fixed Figshare v11 selected computational densities\n\n'
              'Kamal Choudhary, JARVIS-DFT 3D dataset, fixed version DOI '
              '[10.6084/m9.figshare.6815699.v11](https://doi.org/10.6084/m9.figshare.6815699.v11). '
              'The deposited dataset metadata marks [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). '
              'Selected file: `jdft_3d-9-24-2025.json.zip`, file ID 64391379; complete ZIP SHA-256 '
              '`f9e0a3309f0000d5de1ec9e49c93963109ea45e63f451103f8f6595d2eabf7f5`.\n\n'
              'Changes: selected reported density, composition and model facts structured with exact file/member/row bindings; '
              'one minimum-numeric-JID model per conservative reduced composition, unknown conditions preserved. '
              'No density was recomputed. No endorsement is implied. Hypothetical model identity and compositional metal-family classification '
              'do not establish experimental existence, stability, electronic behavior or cross-provider phase equivalence. '
              'Dataset licensing is separate from JARVIS software licensing. Parent database identifiers are citations only; '
              'parent database assets and the complete source archive are not redistributed.\n')
    images['THIRD_PARTY_NOTICES.md'] = (old_notice, old_notice + notice.encode('utf8'))

    def entry(before, after):
        a, b = before.decode('utf8').splitlines(True), after.decode('utf8').splitlines(True)
        offsets = [0]
        for line in a:
            offsets.append(offsets[-1] + len(line.encode('utf8')))
        edits = [{'offset': offsets[i], 'before': ''.join(a[i:j]), 'after': ''.join(b[k:l])}
                 for tag, i, j, k, l in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if tag != 'equal']
        result = {'previous_sha256': sha256(before).hexdigest(), 'sha256': sha256(after).hexdigest(), 'edits': edits}
        if recover_file(after, result) != before or recover_file(before, result) != before:
            raise AssertionError('Recovery failed')
        for unknown in [after + b' ', after[:-1], b'!' + after[1:]]:
            try:
                recover_file(unknown, result)
            except AssertionError:
                continue
            raise AssertionError('Unknown file image inherited approval')
        return result

    files = {'schema_version': 1, 'baseline_commit': 'f13586759af6a391635fa81da20c73eb6a6c1c6c',
             'baseline_scope': 'Exact accepted local Sanchez snapshot',
             'updates': {rel: entry(before, after) for rel, (before, after) in images.items()}}
    for rel, (_, after) in images.items():
        (preview / rel).parent.mkdir(parents=True, exist_ok=True)
        (preview / rel).write_bytes(after)
    # Only these unchanged supporting resources are needed by the truthful README normalizer.
    for name in ['claims.json', 'observations.json', 'computational_predictions.json', 'temperature_models.json']:
        shutil.copy2(ROOT / 'materials_boundaries/data' / name, preview / 'materials_boundaries/data' / name)
    ledger = bulk.load_ledger()
    old_normalized = bulk.truthful_readme(old_readme, ledger)
    new_normalized = bulk.truthful_readme(images['README.md'][1], ledger, root=preview)
    documents = {'schema_version': 1, 'updates': {
        'README.md': entry(old_normalized, new_normalized),
        'THIRD_PARTY_NOTICES.md': files['updates']['THIRD_PARTY_NOTICES.md']}}
    (BATCH / 'file-history-preview.json').write_bytes(encoded(files))
    (BATCH / 'document-history-preview.json').write_bytes(encoded(documents))
    receipt = {'schema': 'jarvis-prospective-file-document-recovery/1', 'status': 'producer_scoped_recovery_passed',
               'file_paths': list(images), 'file_recoveries_passed': len(images), 'unknown_file_images_rejected': 3 * len(images),
               'document_recoveries_passed': 2, 'unknown_document_images_rejected': 6,
               'truthful_readme_current_preview_counts_checked': True,
               'file_history_sha256': sha256(encoded(files)).hexdigest(),
               'document_history_sha256': sha256(encoded(documents)).hexdigest(),
               'live_runtime_changed': False, 'admitted_increment': 0,
               'pending': ['Independent file/document recovery review', 'Registry/helper exact recovery and wiring',
                           'Full historical suite', 'Live integration', 'Full regression and installed checks', 'Admission']}
    (BATCH / 'file-document-preview-validation.json').write_bytes(encoded(receipt))
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
