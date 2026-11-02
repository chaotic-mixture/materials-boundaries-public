"""Source-qualified database access, independent of mechanics evaluation."""
from copy import deepcopy
from collections import Counter
from hashlib import sha256
from importlib.resources import files
import argparse
import json
from pathlib import Path

TABLES = ('materials', 'reference_properties', 'sources')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def index(rows, label):
    result = {}
    for row in rows:
        identifier = row.get('id')
        if not isinstance(identifier, str) or not identifier or identifier in result:
            raise ValueError('Missing or duplicate ID in ' + label)
        result[identifier] = row
    return result


class Database:
    """Load three tables once; validate joins without running history replay."""

    def __init__(self, data=None):
        self.data = deepcopy(data) if data is not None else {
            name: json.loads(files('materials_boundaries').joinpath('data').joinpath(name+'.json').read_bytes())
            for name in TABLES}
        materials = self.data['materials']
        self.identities = index(materials['identities'], 'identities')
        self.grades = index(materials['grades'], 'grades')
        self.states = index(materials['records'], 'states')
        self.properties = index(self.data['reference_properties']['records'], 'properties')
        self.sources = index(self.data['sources']['records'], 'sources')
        self.validate()
        self.snapshot = sha256(canonical(self.data)).hexdigest()

    def validate(self):
        for state in self.states.values():
            if state['identity_id'] not in self.identities:
                raise ValueError('Unknown identity: ' + state['id'])
            if state.get('grade_id') is not None and state['grade_id'] not in self.grades:
                raise ValueError('Unknown grade: ' + state['id'])
            ids = state['property_ids']
            if len(ids) != len(set(ids)):
                raise ValueError('Duplicate property link: ' + state['id'])
            for identifier in ids:
                if identifier not in self.properties or self.properties[identifier]['material_state_id'] != state['id']:
                    raise ValueError('Broken property link: ' + identifier)
        for prop in self.properties.values():
            if prop['material_state_id'] not in self.states or prop['source_id'] not in self.sources:
                raise ValueError('Broken state/source reference: ' + prop['id'])
            if prop['id'] not in self.states[prop['material_state_id']]['property_ids']:
                raise ValueError('Missing reverse property link: ' + prop['id'])
        def evidence_walk(value):
            if isinstance(value, dict):
                if 'source_id' in value and value['source_id'] not in self.sources:
                    raise ValueError('Unknown evidence source: ' + str(value['source_id']))
                for child in value.values():
                    evidence_walk(child)
            elif isinstance(value, list):
                for child in value:
                    evidence_walk(child)
        evidence_walk(self.data)

    def records(self, *, query='', quantity=None, category=None, source=None):
        """Yield detached records with complete native evidence and unknowns."""
        self._require_unchanged()
        for identifier in sorted(self.properties):
            prop = self.properties[identifier]
            state = self.states[prop['material_state_id']]
            identity = self.identities[state['identity_id']]
            if quantity is not None and prop['quantity'] != quantity:
                continue
            if category is not None and identity['category'] != category:
                continue
            if source is not None and prop['source_id'] != source:
                continue
            searchable = json.dumps([identity, state], ensure_ascii=False).casefold()
            if query.casefold() not in searchable:
                continue
            # Include secondary evidence sources, not only the primary citation.
            source_ids = {prop['source_id']}
            def collect(value):
                if isinstance(value, dict):
                    if 'source_id' in value:
                        source_ids.add(value['source_id'])
                    for child in value.values(): collect(child)
                elif isinstance(value, list):
                    for child in value: collect(child)
            grade = self.grades.get(state.get('grade_id'))
            collect([prop, state, identity, grade])
            yield deepcopy({'record_id': identifier, 'record_version': prop['version'],
                'database_snapshot': self.snapshot, 'identity': identity, 'state': state,
                'grade': grade, 'property': prop,
                'sources': [self.sources[s] for s in sorted(source_ids)],
                'review': {'transcription': prop.get('verification', {}).get('transcription_cross_check', 'unknown'),
                           'independent_scientific_review': prop.get('verification', {}).get('independent_scientific_review', False)},
                'rights_note': 'Source license metadata is preserved; the software license does not relicense sources.'})

    def summary(self, **filters):
        """Describe selected source records without inferring missing facts or approval."""
        identities = set(); states = set(); sources = {}
        categories = {}; quantities = Counter(); evidence = Counter()
        conditions = {}; uncertainty = Counter(); sample_counts = Counter()
        transcription = Counter(); scientific_review = Counter(); count = 0
        def label(value):
            return value if isinstance(value, str) and value else '__missing__'
        for record in self.records(**filters):
            count += 1
            identity, prop = record['identity'], record['property']
            identities.add(identity['id']); states.add(record['state']['id'])
            categories.setdefault(identity['category'], set()).add(identity['id'])
            quantities[label(prop.get('quantity'))] += 1
            evidence[label(prop.get('evidence_kind'))] += 1
            # Account for absent condition fields as well as explicit native statuses.
            native_conditions = prop.get('conditions', {})
            status_fields = {field for field, value in native_conditions.items()
                             if isinstance(value, dict) or value is None}
            for field in set(conditions) | status_fields:
                if field not in conditions:
                    conditions[field] = Counter({'__missing__': count - 1})
                value = native_conditions.get(field)
                conditions[field][label(value.get('status') if isinstance(value, dict) else None)] += 1
            uncertainty[label(prop.get('uncertainty_status'))] += 1
            sample = prop.get('sample_count')
            sample_counts[label(sample.get('relation') if isinstance(sample, dict) else None)] += 1
            transcription[label(record['review']['transcription'])] += 1
            review = record['review']['independent_scientific_review']
            scientific_review['true' if review is True else 'false' if review is False else '__missing__'] += 1
            for source in record['sources']:
                sources[source['id']] = source
        rights = Counter()
        for source in sources.values():
            license_info = source.get('license')
            rights[label(license_info.get('status') if isinstance(license_info, dict) else None)] += 1
        def ordered(counter):
            return dict(sorted((key, value) for key, value in counter.items() if value))
        return {'format': 'materials-database-summary/1', 'database_snapshot': self.snapshot,
                'filters': filters, 'property_records': count, 'material_identities': len(identities),
                'material_states': len(states), 'referenced_sources': len(sources),
                'identities_by_category': {k: len(v) for k, v in sorted(categories.items())},
                'properties_by_quantity': ordered(quantities),
                'properties_by_evidence_kind': ordered(evidence),
                'condition_statuses': {k: ordered(v) for k, v in sorted(conditions.items())},
                'uncertainty_statuses': ordered(uncertainty),
                'sample_count_relations': ordered(sample_counts),
                'transcription_statuses': ordered(transcription),
                'independent_scientific_review_flags': ordered(scientific_review),
                'source_license_statuses': ordered(rights),
                'scope': 'selected_property_records_and_their_joined_metadata',
                'review_status': 'descriptive_only_not_admission_or_release',
                'missing_status_label': '__missing__'}

    def validate_scientific_contracts(self):
        """Run existing source/condition/value contracts once, not history replay."""
        self._require_unchanged()
        from .material_references import validate_material_catalog
        validate_material_catalog(self.data['materials'], self.data['reference_properties'],
                                  self.data['sources'])
        return {'status': 'material_contracts_passed', 'snapshot': self.snapshot,
                'properties': len(self.properties), 'independent_scientific_review': False,
                'scope': 'current_material_graph_once_no_history_replay'}

    def _require_unchanged(self):
        if sha256(canonical(self.data)).hexdigest() != self.snapshot:
            raise ValueError('Database changed after construction; create a new Database snapshot')

    def export(self, destination, **filters):
        """Create a new deterministic JSONL snapshot and integrity manifest."""
        self._require_unchanged()
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=False)
        digest = sha256(); count = 0
        with (destination / 'records.jsonl').open('xb') as stream:
            for record in self.records(**filters):
                line = canonical(record) + b'\n'
                stream.write(line); digest.update(line); count += 1
        manifest = {'format': 'materials-database/1', 'database_snapshot': self.snapshot,
                    'record_count': count, 'filters': filters,
                    'files': {'records.jsonl': digest.hexdigest()},
                    'review_status': 'exported_local_snapshot_not_release_acceptance',
                    'source_rights': 'per_source_metadata_no_blanket_relicense'}
        (destination / 'manifest.json').write_bytes(canonical(manifest) + b'\n')
        return manifest


class ValidationSession:
    """An in-process validated baseline; no unsigned on-disk pass cache."""

    def __init__(self, database):
        baseline = Database(database.data)
        baseline.validate_scientific_contracts()
        self._source_digest = sha256(canonical(baseline.data['sources'])).hexdigest()
        self._keys = {}
        for prop in baseline.properties.values():
            state = baseline.states[prop['material_state_id']]
            identity = baseline.identities[state['identity_id']]
            self._keys[prop['id']] = self._key(prop, state, identity)
        self.snapshot = baseline.snapshot

    @staticmethod
    def _key(prop, state, identity):
        return sha256(canonical([prop, state, identity])).hexdigest()

    def validate(self, database):
        from .material_references import _validate_material_catalog
        candidate = Database(database.data)
        sources_same = sha256(canonical(candidate.data['sources'])).hexdigest() == self._source_digest
        counts = {'reused_property_checks': 0, 'executed_property_checks': 0}
        def reusable(prop, state, identity):
            match = sources_same and self._keys.get(prop['id']) == self._key(prop, state, identity)
            counts['reused_property_checks' if match else 'executed_property_checks'] += 1
            return match
        _validate_material_catalog(candidate.data['materials'], candidate.data['reference_properties'],
                                   candidate.data['sources'], property_is_valid=reusable)
        return {'status': 'incremental_material_contracts_passed',
                'before_snapshot': self.snapshot, 'after_snapshot': candidate.snapshot,
                'global_checks': 'executed', 'sources_changed': not sources_same, **counts}


def read_snapshot(directory):
    """Verify exported bytes before comparing them; never trust stale counts."""
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_bytes())
    raw = (directory / 'records.jsonl').read_bytes()
    if (manifest.get('format') != 'materials-database/1' or
            sha256(raw).hexdigest() != manifest['files']['records.jsonl']):
        raise ValueError('Snapshot format or checksum mismatch')
    records = {}
    for line in raw.splitlines():
        record = json.loads(line)
        identifier = record['record_id']
        if identifier in records or record['database_snapshot'] != manifest['database_snapshot']:
            raise ValueError('Duplicate record or mixed snapshot')
        if identifier != record['property']['id']:
            raise ValueError('Record/property ID mismatch')
        records[identifier] = record
    if len(records) != manifest['record_count']:
        raise ValueError('Snapshot record count mismatch')
    return manifest, records


def compare_snapshots(before, after):
    old_manifest, old = read_snapshot(before)
    new_manifest, new = read_snapshot(after)
    if old_manifest['filters'] != new_manifest['filters']:
        raise ValueError('Cannot compare snapshots with different filters')
    def content(record):
        return {k: v for k, v in record.items() if k != 'database_snapshot'}
    changed = sorted(k for k in old.keys() & new.keys()
                     if canonical(content(old[k])) != canonical(content(new[k])))
    added, deleted = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())
    affected_sources = sorted({s['id'] for key in set(changed + added + deleted)
        for records in (old, new) if key in records for s in records[key]['sources']})
    return {'format': 'materials-database-diff/1',
            'before_snapshot': old_manifest['database_snapshot'],
            'after_snapshot': new_manifest['database_snapshot'],
            'filters': new_manifest['filters'], 'added': added, 'modified': changed,
            'deleted': deleted, 'affected_sources': affected_sources,
            'review_required': bool(added or changed or deleted),
            'scientific_validation': 'not_performed', 'full_history_replay_started': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['query', 'summary', 'export', 'check', 'verify', 'diff', 'validate-update'])
    parser.add_argument('--query', default='')
    parser.add_argument('--quantity')
    parser.add_argument('--category')
    parser.add_argument('--source')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--before', type=Path)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--data-dir', type=Path, help='Directory containing the three native JSON tables')
    parser.add_argument('--scientific-contracts', action='store_true',
                        help='With check: run existing scientific data contracts once')
    args = parser.parse_args()
    if args.action == 'export' and args.output is None:
        parser.error('export requires --output (a new directory)')
    if args.action in {'verify', 'diff'}:
        if not args.snapshot or (args.action == 'diff' and not args.before):
            parser.error('verify requires --snapshot; diff also requires --before')
        result = (compare_snapshots(args.before, args.snapshot) if args.action == 'diff'
                  else {'status': 'snapshot_integrity_passed', 'manifest': read_snapshot(args.snapshot)[0]})
        print(json.dumps(result, ensure_ascii=False))
        return
    def from_directory(path):
        return Database({name: json.loads((path / (name+'.json')).read_bytes()) for name in TABLES})
    database = from_directory(args.data_dir) if args.data_dir else Database()
    if args.action == 'validate-update':
        if not args.before:
            parser.error('validate-update requires --before with the baseline native tables directory')
        print(json.dumps(ValidationSession(from_directory(args.before)).validate(database)))
        return
    filters = {k: getattr(args, k) for k in ('query', 'quantity', 'category', 'source')}
    if args.action == 'export':
        print(json.dumps(database.export(args.output, **filters), ensure_ascii=False))
    elif args.action == 'summary':
        print(json.dumps(database.summary(**filters), ensure_ascii=False))
    elif args.action == 'check':
        result = (database.validate_scientific_contracts() if args.scientific_contracts else
                  {'status': 'reference_integrity_passed', 'snapshot': database.snapshot,
                   'properties': len(database.properties), 'scientific_validation': 'not_performed'})
        print(json.dumps(result))
    else:
        for record in database.records(**filters):
            print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
