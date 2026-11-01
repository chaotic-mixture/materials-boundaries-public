"""Keep the public exclusion scan intact while supporting UUID-like exponents."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from repair_porous_checkpoint import entry, encoded

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
WORK = ROOT.parent / 'growth-source-cache/jarvis-runtime-integration'


def assertions(raw):
    return [ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(raw))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr.startswith('assert')]


def main():
    cancellation = json.loads((WORK / 'jarvis-r2-cancellation.json').read_text(encoding='utf-8-sig'))
    if cancellation['round'] != 'jarvis-r2':
        raise ValueError('Wrong stopped predecessor round')
    archive = WORK / 'uuid-scan-predecessor-r2'
    if archive.exists():
        raise ValueError('Preserve prior repair evidence')
    test_path = 'tests/test_nist_reuse_provenance.py'
    bulk_path = 'tests/material_bulk_preservation.py'
    files_path = 'tests/jarvis_density_runtime/files-history.json'
    registry_path = 'tests/material_append_successors.py'
    registry_ledger_path = 'tests/jarvis_density_runtime/registry-history.json'
    helper_path = 'tests/jarvis_density_history.py'
    old = {p: (ROOT / p).read_bytes() for p in [test_path, bulk_path, files_path, registry_path, registry_ledger_path, helper_path]}
    if subprocess.check_output(['git', 'show', 'f13586759af6a391635fa81da20c73eb6a6c1c6c:' + test_path], cwd=ROOT) != old[test_path]:
        raise ValueError('Unexpected previous public fingerprint guard')
    text = old[test_path].decode('utf8')
    before = 'from decimal import Context, Decimal, InvalidOperation, localcontext'
    if text.count(before) != 1 or text.count('Context(prec=28)') != 1:
        raise ValueError('Unexpected public numeric context')
    text = text.replace(before, 'from decimal import Context, Decimal, InvalidOperation, MAX_EMAX, MIN_EMIN, localcontext', 1)
    text = text.replace('Context(prec=28)', 'Context(prec=28, Emax=MAX_EMAX, Emin=MIN_EMIN)', 1)
    test_raw = text.encode('utf8')
    if assertions(old[test_path]) != assertions(test_raw):
        raise AssertionError('An exclusion assertion changed')
    bulk = old[bulk_path].decode('utf8')
    before = "                    'schemas/reference_properties.schema.json'}:\n"
    if bulk.count(before) != 1:
        raise ValueError('Unknown finite legacy route')
    bulk = bulk.replace(before, "                    'schemas/reference_properties.schema.json',\n                    'tests/test_nist_reuse_provenance.py'}:\n", 1)
    bulk_raw = bulk.encode('utf8')
    manifest_path = BATCH / 'live-integration-manifest.json'
    manifest_raw = manifest_path.read_bytes()
    if sha256(manifest_raw).hexdigest() != '4bed3333d4c11916480667ceee0936d53947bdd7be78d869bc9c0b7908e08b22':
        raise ValueError('Unknown r2 working manifest')
    manifest = json.loads(manifest_raw)
    files = json.loads(old[files_path])
    original_eight = {p: value for p, value in files['updates'].items() if p != bulk_path}
    from material_append_history import recover_file
    baseline_bulk = recover_file(old[bulk_path], files['updates'][bulk_path])
    files['updates'][bulk_path] = entry(baseline_bulk, bulk_raw)
    files['updates'][test_path] = entry(old[test_path], test_raw)
    if any(files['updates'][p] != value for p, value in original_eight.items()):
        raise AssertionError('An original reviewed recovery entry changed')
    files_raw = encoded(files)
    old_files_sha = sha256(old[files_path]).hexdigest()
    registry = old[registry_path].decode('utf8')
    if registry.count(old_files_sha) != 1:
        raise ValueError('Unknown file-ledger registry pin')
    registry_raw = registry.replace(old_files_sha, sha256(files_raw).hexdigest(), 1).encode('utf8')
    baseline_registry = (Path(manifest['predecessor_backup']) / registry_path).read_bytes()
    registry_ledger_raw = encoded({'schema_version': 1, 'updates': {registry_path: entry(baseline_registry, registry_raw)}})
    helper = old[helper_path].decode('utf8')
    for key, raw in [('FILES', files_raw), ('REGISTRY', registry_ledger_raw)]:
        helper, count = re.subn(key + r"_SHA256 = '[0-9a-f]{64}'", key + "_SHA256 = '" + sha256(raw).hexdigest() + "'", helper)
        if count != 1:
            raise ValueError('Unknown helper digest binding')
    new = {test_path: test_raw, bulk_path: bulk_raw, files_path: files_raw,
           registry_path: registry_raw, registry_ledger_path: registry_ledger_raw, helper_path: helper.encode('utf8')}
    for p, raw in old.items():
        (archive / p).parent.mkdir(parents=True, exist_ok=True)
        (archive / p).write_bytes(raw)
    (archive / 'live-integration-manifest.json').write_bytes(manifest_raw)
    archived_manifest = BATCH / 'history-wiring-r2/live-integration-manifest.json'
    archived_manifest.parent.mkdir(parents=True, exist_ok=False)
    archived_manifest.write_bytes(manifest_raw)
    for p, raw in new.items():
        (ROOT / p).write_bytes(raw)
    manifest['updated_files'][test_path] = {'before_sha256': sha256(old[test_path]).hexdigest(), 'after_sha256': sha256(test_raw).hexdigest()}
    manifest['updated_files'][bulk_path]['after_sha256'] = sha256(bulk_raw).hexdigest()
    manifest['updated_files'][registry_path]['after_sha256'] = sha256(registry_raw).hexdigest()
    for p in [files_path, registry_ledger_path, helper_path]:
        manifest['added_files'][p] = sha256(new[p]).hexdigest()
    manifest['second_supplemental_predecessor_backup'] = {'directory': str(archive), 'extra_baseline_file': test_path,
                                                        'extra_baseline_sha256': sha256(old[test_path]).hexdigest()}
    manifest['last_repair'] = {'reason': 'Reproduced decimal.Overflow while scanning legitimate UUID fragments',
                              'scope': 'Extend only local Decimal exponent range; retain numeric regex, all paths, fingerprint inputs and every exclusion assertion',
                              'old_exclusion_assertion_ast_preserved': True, 'original_eight_file_history_entries_preserved': True}
    manifest_path.write_bytes(encoded(manifest))
    report = {'schema': 'jarvis-public-uuid-fingerprint-context-repair/1', 'status': 'repaired_pending_retest_and_independent_review',
              'cancelled_round': 'jarvis-r2', 'root_method': 'test_nist_reuse_provenance.PublicReuseBoundaryTests.test_excluded_coefficient_and_derived_numeric_fingerprints_are_absent',
              'reproduced_error': 'decimal.Overflow on a legitimate UUID tail interpreted as a numeric token',
              'source_uuids_or_material_values_changed': False, 'numeric_regex_or_scan_paths_changed': False,
              'exclusion_assertion_ast_preserved': True, 'exclusion_assertion_count': len(assertions(test_raw)),
              'forbidden_fixture_changed': False, 'reproduced_log_sha256': sha256((ROOT.parent / 'jarvis-public-reuse-reproduced-r2.log').read_bytes()).hexdigest(),
              'new_sha256': {p: sha256(raw).hexdigest() for p, raw in new.items()},
              'runtime_package_or_catalogs_changed': False, 'admitted_increment': 0}
    (BATCH / 'uuid-fingerprint-repair-r3.json').write_bytes(encoded(report))
    print(json.dumps({'status': report['status'], 'unchanged_exclusion_assertions': report['exclusion_assertion_count'],
                      'file_history_entries': len(files['updates']), 'source_uuids_changed': False}))


if __name__ == '__main__':
    main()
