"""Narrow the draft UUID fix to Emax, preserving old underflow semantics."""
from hashlib import sha256
import json
from pathlib import Path
import re

from repair_porous_checkpoint import entry, encoded
from repair_uuid_fingerprint_context import assertions
from material_append_history import recover_file

BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
WORK = ROOT.parent / 'growth-source-cache/jarvis-runtime-integration'


def main():
    archive = WORK / 'uuid-emax-refinement-predecessor-r3a'
    if archive.exists():
        raise ValueError('Preserve earlier refinement evidence')
    test = 'tests/test_nist_reuse_provenance.py'
    files = 'tests/jarvis_density_runtime/files-history.json'
    registry = 'tests/material_append_successors.py'
    regledger = 'tests/jarvis_density_runtime/registry-history.json'
    helper = 'tests/jarvis_density_history.py'
    paths = [test, files, registry, regledger, helper]
    old = {p: (ROOT / p).read_bytes() for p in paths}
    manifest = json.loads((BATCH / 'live-integration-manifest.json').read_bytes())
    text = old[test].decode('utf8')
    assert text.count('MAX_EMAX, MIN_EMIN, localcontext') == 1
    assert text.count('Emax=MAX_EMAX, Emin=MIN_EMIN') == 1
    text = text.replace('MAX_EMAX, MIN_EMIN, localcontext', 'MAX_EMAX, localcontext')
    text = text.replace('Emax=MAX_EMAX, Emin=MIN_EMIN', 'Emax=MAX_EMAX')
    new = {test: text.encode('utf8')}
    assert assertions(new[test]) == assertions(old[test])
    ledger = json.loads(old[files])
    baseline = recover_file(old[test], ledger['updates'][test])
    ledger['updates'][test] = entry(baseline, new[test])
    new[files] = encoded(ledger)
    oldpin = sha256(old[files]).hexdigest()
    assert old[registry].decode('utf8').count(oldpin) == 1
    new[registry] = old[registry].replace(oldpin.encode(), sha256(new[files]).hexdigest().encode())
    previous_registry = recover_file(old[registry], json.loads(old[regledger])['updates'][registry])
    new[regledger] = encoded({'schema_version': 1, 'updates': {registry: entry(previous_registry, new[registry])}})
    text = old[helper].decode('utf8')
    for key, path in [('FILES', files), ('REGISTRY', regledger)]:
        text, count = re.subn(key + r"_SHA256 = '[0-9a-f]{64}'", key + "_SHA256 = '" + sha256(new[path]).hexdigest() + "'", text)
        assert count == 1
    new[helper] = text.encode('utf8')
    for p, raw in old.items():
        (archive / p).parent.mkdir(parents=True, exist_ok=True)
        (archive / p).write_bytes(raw)
    for name in ['live-integration-manifest.json', 'uuid-fingerprint-repair-r3.json']:
        (archive / name).write_bytes((BATCH / name).read_bytes())
    for p, raw in new.items():
        (ROOT / p).write_bytes(raw)
        if p in manifest['updated_files']:
            manifest['updated_files'][p]['after_sha256'] = sha256(raw).hexdigest()
        else:
            manifest['added_files'][p] = sha256(raw).hexdigest()
    manifest['last_repair']['scope'] = 'Extend only Emax; preserve default Emin, numeric regex, scan paths, source UUIDs and every assertion'
    manifest['uuid_emax_refinement_archive'] = str(archive)
    (BATCH / 'live-integration-manifest.json').write_bytes(encoded(manifest))
    report = {'schema': 'jarvis-public-uuid-emax-refinement/1', 'status': 'pending_independent_review_and_focused_tests',
              'reason': 'Review found widening Emin would change the old underflow result of some synthetic finite tokens',
              'old_emin_and_underflow_semantics_preserved': True, 'source_values_changed': False,
              'assertions_preserved': len(assertions(new[test])), 'predecessor_archive': str(archive),
              'sha256': {p: sha256(raw).hexdigest() for p, raw in new.items()}, 'admitted_increment': 0}
    (BATCH / 'uuid-emax-refinement-r3.json').write_bytes(encoded(report))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
