"""Unapplied exact source-only metadata mapping; all material facts unchanged."""
from pathlib import Path
import hashlib
import json
from copy import deepcopy
import sys
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
AUDIT = OUT.parent / 'nbr-method-figure-followup-r1'
EXT = ROOT.parent / 'open-database-evidence/polymer-nbr-source-metadata-preview-20261104-r1'
sys.path.insert(0, str(ROOT))
from materials_boundaries.database import Database, read_snapshot


def read(path):
    return json.loads(path.read_bytes())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    assert not EXT.exists()
    proposal = read(AUDIT / 'SOURCE_UPDATE_PROPOSAL_R1.json')
    review = read(AUDIT / 'INDEPENDENT_REVIEW_R1.json')
    assert review['decision'] == 'approved'
    assert review['review_inputs_sha256'] == sha(AUDIT / 'REVIEW_INPUTS_R1.json')
    before = Database()
    sid = proposal['source_id']
    assert before.sources[sid] == proposal['baseline_source']
    original = proposal['baseline_source']
    updated = proposal['proposed_source']
    assert set(original) == set(updated)
    assert [n for n in original if original[n] != updated[n]] == ['urls', 'claim_notes']
    assert updated['urls'][:-1] == original['urls'] and updated['claim_notes'][:-1] == original['claim_notes']
    data = deepcopy(before.data)
    rows = data['sources']['records']
    rows[rows.index(original)] = updated
    Draft202012Validator(read(ROOT / 'schemas/sources.schema.json'), format_checker=FormatChecker()).validate(data['sources'])
    after = Database(data)
    assert after.properties == before.properties and after.states == before.states
    assert after.identities == before.identities and after.grades == before.grades
    assert set(after.sources) == set(before.sources)
    assert all(after.sources[n] == s for n, s in before.sources.items() if n != sid)
    old_exports = list(before.records(source=sid))
    new_exports = list(after.records(source=sid))
    assert len(old_exports) == len(new_exports) == 12
    for old, new in zip(old_exports, new_exports):
        assert old['property'] == new['property'] and old['state'] == new['state']
        comparable = deepcopy(new)
        comparable['database_snapshot'] = old['database_snapshot']
        comparable['sources'] = old['sources']
        assert comparable == old
    EXT.mkdir(parents=True)
    after.export(EXT / 'source-export', source=sid)
    assert read_snapshot(EXT / 'source-export')[1] == {row['record_id']: row for row in new_exports}
    write(OUT / 'MAPPING_FACTS_R1.json', {'source_id': sid, 'baseline_source': original, 'source_record': updated, 'native_applied': False, 'new_material_property_state': 0, 'density_conditions_statistics': 'Unchanged;no hardness/abrasion method or counts transferred', 'fresh_PDF': False})
    write(OUT / 'VALIDATION_R1.json', {'scope': 'Unapplied source-only metadata mapping and12 joined exports', 'baseline_snapshot': before.snapshot, 'preview_snapshot': after.snapshot, 'source_schema_format': 'passed', 'source_updates': 1, 'URL_and_note_additions': [1, 1], 'all_properties_states_identities_grades_unchanged': True, 'joined_exports': 12, 'joined_export_roundtrip': 'exact', 'native_applied': False, 'new_material_property_state': 0, 'full_graph': 'not_run_unchanged_property_objects', 'full_history': 'not_run', 'installation': 'not_run', 'pushed': False})
    print(json.dumps({'source_only': sid, 'joined_exports': 12, 'new_properties_states': 0, 'preview_snapshot': after.snapshot, 'native_applied': False}))


if __name__ == '__main__':
    main()
