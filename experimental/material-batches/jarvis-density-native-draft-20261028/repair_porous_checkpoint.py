"""Repair two reproduced legacy byte routes, preserving exact predecessor guards."""
from copy import deepcopy
import difflib
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
WORK = ROOT.parent / 'growth-source-cache/jarvis-runtime-integration'
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT)]
from material_append_history import encoded, recover_file


def entry(before, after):
    a, b = before.decode('utf8').splitlines(True), after.decode('utf8').splitlines(True)
    offsets = [0]
    for line in a:
        offsets.append(offsets[-1] + len(line.encode('utf8')))
    edits = [{'offset': offsets[i], 'before': ''.join(a[i:j]), 'after': ''.join(b[k:l])}
             for tag, i, j, k, l in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if tag != 'equal']
    result = {'previous_sha256': sha256(before).hexdigest(), 'sha256': sha256(after).hexdigest(), 'edits': edits}
    if recover_file(after, result) != before:
        raise AssertionError('Exact recovery failed')
    return result


def main():
    cancellation = json.loads((WORK / 'jarvis-r1-cancellation.json').read_text(encoding='utf-8-sig'))
    if cancellation['round'] != 'jarvis-r1':
        raise ValueError('Wrong cancelled predecessor round')
    archive = WORK / 'porous-repair-predecessor-r1'
    if archive.exists():
        raise ValueError('Preserve previous repair evidence')
    bulk_path = 'tests/material_bulk_preservation.py'
    old_bulk = (ROOT / bulk_path).read_bytes()
    if sha256(old_bulk).hexdigest() != '32e2c40cfff5df4b3a78bebaf358fbef113240d08d67c7c3eb4bf1f8e0ff5db1':
        raise ValueError('Unknown reviewed pre-repair helper')
    needle = "    if filename == 'materials_boundaries/material_references.py':\n"
    bulk = old_bulk.decode('utf8')
    if bulk.count(needle) != 1:
        raise ValueError('Unknown existing finite numeric-helper route')
    bulk = bulk.replace(needle, "    if filename in {'materials_boundaries/material_references.py',\n                    'materials_boundaries/material_presentation.py',\n                    'schemas/reference_properties.schema.json'}:\n", 1)
    manifest_path = BATCH / 'live-integration-manifest.json'
    old_manifest_raw = manifest_path.read_bytes()
    if sha256(old_manifest_raw).hexdigest() != '2b8fc2ffac2379f6b6e84f13e3347720d86babbf816c1164e7fedb97f8053d61':
        raise ValueError('Unknown original wiring manifest')
    manifest = json.loads(old_manifest_raw)
    files_path = 'tests/jarvis_density_runtime/files-history.json'
    registry_path = 'tests/material_append_successors.py'
    registry_ledger_path = 'tests/jarvis_density_runtime/registry-history.json'
    helper_path = 'tests/jarvis_density_history.py'
    old = {p: (ROOT / p).read_bytes() for p in [bulk_path, files_path, registry_path, registry_ledger_path, helper_path]}
    files = json.loads(old[files_path])
    if bulk_path in files['updates']:
        raise ValueError('Duplicate repair history entry')
    original_eight = deepcopy(files['updates'])
    files['updates'][bulk_path] = entry(old_bulk, bulk.encode('utf8'))
    for p, value in original_eight.items():
        if files['updates'][p] != value:
            raise AssertionError('An existing frozen recovery entry changed')
    file_raw = encoded(files)
    old_files_sha, new_files_sha = sha256(old[files_path]).hexdigest(), sha256(file_raw).hexdigest()
    registry = old[registry_path].decode('utf8')
    if registry.count(old_files_sha) != 1:
        raise ValueError('Unknown registry file-ledger pin')
    registry_raw = registry.replace(old_files_sha, new_files_sha, 1).encode('utf8')
    baseline_registry = (Path(manifest['predecessor_backup']) / registry_path).read_bytes()
    registry_ledger = json.loads(old[registry_ledger_path])
    registry_ledger['updates'][registry_path] = entry(baseline_registry, registry_raw)
    registry_ledger_raw = encoded(registry_ledger)
    helper = old[helper_path].decode('utf8')
    for key, value in [('FILES', file_raw), ('REGISTRY', registry_ledger_raw)]:
        helper, count = re.subn(key + r"_SHA256 = '[0-9a-f]{64}'", key + "_SHA256 = '" + sha256(value).hexdigest() + "'", helper)
        if count != 1:
            raise ValueError('Unknown helper pin: ' + key)
    new = {bulk_path: bulk.encode('utf8'), files_path: file_raw, registry_path: registry_raw,
           registry_ledger_path: registry_ledger_raw, helper_path: helper.encode('utf8')}
    for p, raw in old.items():
        (archive / p).parent.mkdir(parents=True, exist_ok=True)
        (archive / p).write_bytes(raw)
    (archive / 'live-integration-manifest.json').write_bytes(old_manifest_raw)
    archived_manifest_path = BATCH / 'history-wiring-r1/live-integration-manifest.json'
    archived_manifest_path.parent.mkdir(parents=True, exist_ok=False)
    archived_manifest_path.write_bytes(old_manifest_raw)
    for p, raw in new.items():
        (ROOT / p).write_bytes(raw)
    manifest['updated_files'][bulk_path] = {'before_sha256': sha256(old_bulk).hexdigest(), 'after_sha256': sha256(new[bulk_path]).hexdigest()}
    manifest['updated_files'][registry_path]['after_sha256'] = sha256(registry_raw).hexdigest()
    for p in [files_path, registry_ledger_path, helper_path]:
        manifest['added_files'][p] = sha256(new[p]).hexdigest()
    manifest['supplemental_predecessor_backup'] = {'directory': str(archive), 'extra_baseline_file': bulk_path,
                                                 'extra_baseline_sha256': sha256(old_bulk).hexdigest()}
    manifest['last_repair'] = {'reason': 'Two reproduced porous predecessor-byte subtest failures',
                              'scope': 'Extend existing exact checkpoint route to presentation code and property schema before unchanged original validators',
                              'existing_assertions_changed': False, 'existing_eight_file_recovery_entries_unchanged': True}
    manifest_path.write_bytes(encoded(manifest))
    record = {'schema': 'jarvis-porous-checkpoint-repair/1', 'status': 'repaired_pending_retest_and_independent_review',
              'cancelled_round': 'jarvis-r1', 'observed_failing_subtests': 2,
              'failing_root_method': 'test_material_porous_preservation.MaterialPorousPreservationTests.test_all_383_predecessor_files_round_trip_exactly',
              'reproduced_log_sha256': sha256((ROOT.parent / 'jarvis-porous-reproduced-r1.log').read_bytes()).hexdigest(),
              'pre_repair_backup': str(archive), 'updated_sha256': {p: sha256(raw).hexdigest() for p, raw in new.items()},
              'runtime_package_and_catalogs_changed': False, 'old_assertions_or_fixtures_changed': False,
              'admitted_increment': 0}
    (BATCH / 'porous-repair-r2.json').write_bytes(encoded(record))
    print(json.dumps({'status': record['status'], 'updated_test_history_files': len(new),
                      'runtime_package_and_catalogs_changed': False, 'admitted_increment': 0}))


if __name__ == '__main__':
    main()
