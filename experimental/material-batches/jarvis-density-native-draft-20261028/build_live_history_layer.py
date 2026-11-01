"""Apply one exact review-bound working snapshot, with immutable predecessor backup."""
import argparse
import ast
import difflib
from hashlib import sha256
import json
from pathlib import Path
import sys

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
DIRECTORY = 'tests/jarvis_density_runtime/'


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Unexpected source checkpoint: ' + old[:100])
    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', type=Path, required=True)
    parser.add_argument('--backup', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    preview, backup = args.preview.resolve(), args.backup.resolve()
    if not args.apply or backup.exists() or not backup.is_relative_to(ROOT.parent / 'growth-source-cache'):
        raise ValueError('Explicit --apply and fresh external backup directory required')
    if (ROOT / DIRECTORY).exists() or (ROOT / 'tests/jarvis_density_history.py').exists():
        raise ValueError('Existing history layer must not be overwritten')
    sys.path[:0] = [str(ROOT / 'tests'), str(ROOT)]
    from material_append_history import encoded, recover_file
    review = json.loads((BATCH / 'independent-history-preview-review.json').read_bytes())
    for path, digest in review['reviewed_sha256'].items():
        if sha256((BATCH / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Changed independently reviewed preview: ' + path)
    data_raw = (BATCH / 'data-history-preview.json').read_bytes()
    data = json.loads(data_raw)
    documents_raw = (BATCH / 'document-history-preview.json').read_bytes()
    files = json.loads((BATCH / 'file-history-preview.json').read_bytes())
    updates, previous = {}, {}
    for key, rel in [('materials', 'materials_boundaries/data/materials.json'),
                     ('properties', 'materials_boundaries/data/reference_properties.json'),
                     ('sources', 'materials_boundaries/data/sources.json')]:
        old, new = (ROOT / rel).read_bytes(), (preview / rel).read_bytes()
        if sha256(old).hexdigest() != data['baseline_sha256'][key] or sha256(new).hexdigest() != data['current_sha256'][key]:
            raise ValueError('Changed complete catalog images: ' + rel)
        previous[rel], updates[rel] = old, new
    for rel, entry in files['updates'].items():
        old, new = (ROOT / rel).read_bytes(), (preview / rel).read_bytes()
        if sha256(old).hexdigest() != entry['previous_sha256'] or sha256(new).hexdigest() != entry['sha256']:
            raise ValueError('Changed code/document checkpoint: ' + rel)
        previous[rel], updates[rel] = old, new

    helper_path = 'tests/sanchez_al_mea_history.py'
    old_helper = (ROOT / helper_path).read_bytes()
    helper = old_helper.decode('utf8')
    helper = replace_once(helper, 'import json\n', 'import json\nimport jarvis_density_history as jarvis\n')
    helper = replace_once(helper, '    raw = {key: (root / path).read_bytes() for key, path in CATALOG_PATHS.items()}',
                          '    raw = {key: encoded(value) for key, value in jarvis.checkpoint_catalogs(root).items()}')
    helper = replace_once(helper, "    keys = [k for k, p in CATALOG_PATHS.items() if p == relative]",
                          "    raw = jarvis.checkpoint_bytes(relative, raw, root=root)\n    keys = [k for k, p in CATALOG_PATHS.items() if p == relative]")
    helper = replace_once(helper, '    previous = checkpoint_registry(root).FROZEN_SUCCESSORS\n',
                          '    actual = jarvis.predecessor_descriptors(actual, root=root)\n    previous = checkpoint_registry(root).FROZEN_SUCCESSORS\n')
    helper = replace_once(helper, "def checkpoint_document(relative, raw, *, root=ROOT):\n",
                          "def checkpoint_document(relative, raw, *, root=ROOT):\n    raw = jarvis.checkpoint_document(relative, raw, root=root)\n")
    previous[helper_path], updates[helper_path] = old_helper, helper.encode('utf8')

    test_path = 'tests/sanchez_al_mea_runtime/test_sanchez_runtime.py'
    old_test = (ROOT / test_path).read_bytes()
    test = old_test.decode('utf8')
    test = replace_once(test, 'import material_append_successors as successors\n',
                        'import material_append_successors as successors\nimport jarvis_density_history as jarvis\nsuccessors = jarvis.checkpoint_registry()\n')
    test = replace_once(test, "    return {key: json.loads((ROOT / name).read_bytes()) for key, name in history.CATALOG_PATHS.items()}",
                        '    return jarvis.checkpoint_catalogs(ROOT)')
    test = replace_once(test, '                raw = (ROOT / path).read_bytes()\n',
                        '                raw = jarvis.checkpoint_bytes(path, (ROOT / path).read_bytes(), root=ROOT)\n')
    assertions = lambda s: [ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(s))
                            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                            and n.func.attr.startswith('assert')]
    if assertions(test) != assertions(old_test.decode('utf8')):
        raise AssertionError('An existing Sanchez assertion changed')
    previous[test_path], updates[test_path] = old_test, test.encode('utf8')

    def entry(before, after):
        a, b = before.decode('utf8').splitlines(True), after.decode('utf8').splitlines(True)
        offsets = [0]
        for line in a:
            offsets.append(offsets[-1] + len(line.encode('utf8')))
        edits = [{'offset': offsets[i], 'before': ''.join(a[i:j]), 'after': ''.join(b[k:l])}
                 for tag, i, j, k, l in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if tag != 'equal']
        result = {'previous_sha256': sha256(before).hexdigest(), 'sha256': sha256(after).hexdigest(), 'edits': edits}
        if recover_file(after, result) != before:
            raise AssertionError('Exact file predecessor recovery failed')
        return result

    for path in [helper_path, test_path]:
        files['updates'][path] = entry(previous[path], updates[path])
    files_raw = encoded(files)
    data_sha, file_sha = sha256(data_raw).hexdigest(), sha256(files_raw).hexdigest()
    registry_path = 'tests/material_append_successors.py'
    old_registry = (ROOT / registry_path).read_bytes()
    registry = old_registry.decode('utf8')
    descriptor = ('    {"batch_id": "jarvis-density-native-draft-20261028",\n'
                  '     "data": ("tests/jarvis_density_runtime/data-history.json", "' + data_sha + '"),\n'
                  '     "files": ("tests/jarvis_density_runtime/files-history.json", "' + file_sha + '")},\n')
    registry = replace_once(registry, 'FROZEN_SUCCESSORS = (\n', 'FROZEN_SUCCESSORS = (\n' + descriptor)
    registry = replace_once(registry, '    from sanchez_al_mea_history import registry_ledger as sanchez_registry_ledger\n',
                            '    from jarvis_density_history import registry_ledger as jarvis_registry_ledger\n    from sanchez_al_mea_history import registry_ledger as sanchez_registry_ledger\n')
    registry = replace_once(registry, '    result = [sanchez_registry_ledger()] if has_sanchez else []\n',
                            '    has_jarvis = any(item["batch_id"] == "jarvis-density-native-draft-20261028" for item in descriptors)\n'
                            '    result = [jarvis_registry_ledger()] if has_jarvis else []\n'
                            '    result += [load_frozen(ROOT, *item["files"]) for item in descriptors if item["batch_id"] == "jarvis-density-native-draft-20261028"]\n'
                            '    result += [sanchez_registry_ledger()] if has_sanchez else []\n')
    registry = replace_once(registry, 'if descriptor["batch_id"] in {"sanchez-al-mea-revised-20261027",',
                            'if descriptor["batch_id"] in {"jarvis-density-native-draft-20261028", "sanchez-al-mea-revised-20261027",')
    previous[registry_path], updates[registry_path] = old_registry, registry.encode('utf8')
    registry_raw = encoded({'schema_version': 1, 'updates': {registry_path: entry(old_registry, updates[registry_path])}})
    template = (BATCH / 'jarvis_density_history.template.py').read_text(encoding='utf8')
    for key, value in [('DATA', data_raw), ('FILES', files_raw), ('REGISTRY', registry_raw), ('DOCUMENTS', documents_raw)]:
        template = replace_once(template, '@' + key + '_SHA@', sha256(value).hexdigest())
    additions = {DIRECTORY + 'data-history.json': data_raw, DIRECTORY + 'files-history.json': files_raw,
                 DIRECTORY + 'registry-history.json': registry_raw, DIRECTORY + 'document-history.json': documents_raw,
                 'tests/jarvis_density_history.py': template.encode('utf8')}
    for rel in additions:
        if (ROOT / rel).exists():
            raise ValueError('Refusing an existing new-layer file: ' + rel)
    # Complete the predecessor backup before changing a single existing file.
    for rel, raw in previous.items():
        (backup / rel).parent.mkdir(parents=True, exist_ok=True)
        (backup / rel).write_bytes(raw)
    backup_manifest = {'schema': 'jarvis-live-history-predecessor-backup/1',
                       'files': {rel: sha256(raw).hexdigest() for rel, raw in previous.items()}}
    (backup / 'manifest.json').write_bytes(encoded(backup_manifest))
    for rel, raw in {**additions, **updates}.items():
        (ROOT / rel).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / rel).write_bytes(raw)
    report = {'schema': 'jarvis-working-integration-history-layer/1',
              'status': 'applied_to_uncommitted_worktree_pending_validation', 'baseline_head': 'f13586759af6a391635fa81da20c73eb6a6c1c6c',
              'predecessor_backup': str(backup), 'backup_manifest_sha256': sha256(encoded(backup_manifest)).hexdigest(),
              'updated_files': {rel: {'before_sha256': sha256(previous[rel]).hexdigest(), 'after_sha256': sha256(raw).hexdigest()}
                                for rel, raw in updates.items()},
              'added_files': {rel: sha256(raw).hexdigest() for rel, raw in additions.items()},
              'existing_sanchez_assertion_ast_preserved': True,
              'existing_sanchez_assertion_count': len(assertions(test)),
              'pending': ['Independent registry/helper wiring review', 'Dedicated and historical tests', 'Full root regression', 'Installed checks', 'Final runtime acceptance'],
              'admitted_increment': 0, 'new_commit': None, 'push_performed': False, 'main_merge_performed': False, 'deployment_performed': False}
    (BATCH / 'live-integration-manifest.json').write_bytes(encoded(report))
    print(json.dumps({'status': report['status'], 'updated_files': len(updates), 'added_files': len(additions),
                      'unchanged_old_assertions': report['existing_sanchez_assertion_count'], 'admitted_increment': 0}))


if __name__ == '__main__':
    main()
