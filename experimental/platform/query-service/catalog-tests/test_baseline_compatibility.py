"""Exact baseline compatibility using real package bytes and synthetic reviews.

The predecessor fixtures reverse only exact evidence and presentation hunks.
All three complete 64-file trees are hashed by the production baseline validator;
neither the validator nor any digest calculation is replaced by these tests.
"""
from contextlib import closing, contextmanager
from copy import deepcopy
from hashlib import sha256
from importlib.resources import files
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from materials_query import computed_registry as registry
from test_computed_recovery import review_fixture as legacy_review
from test_computed_v2 import INPUT, review_fixture as rich_review


PIN_SHA256 = '259d5d0e87635fec6f87ce544c8a252494038cbb1643228eeb685d5501f17897'
PREDECESSOR_SHA256 = 'f485759f92bac90a655cbdf9328855c6a863552c258e645e63171dc3a625f82e'
SUCCESSOR_SHA256 = 'c22295a7e8ab4e360201eb57cb6fc13eba7f8b8ac5e419f35fcf42e8aa81a264'
PREDECESSOR_HUNK = b'''    """Stable factual signature; evidence/support array ordering is immaterial."""
    if isinstance(value, dict):
        return {key: _structural_signature(item, key) for key, item in sorted(value.items())}
    if isinstance(value, list):
        values = [_structural_signature(item) for item in value]
        if field in {"evidence", "supports"}:
'''
SUCCESSOR_HUNK = b'''    """Stable factual signature; repeated evidence and evidence/support order are immaterial."""
    if isinstance(value, dict):
        return {key: _structural_signature(item, key) for key, item in sorted(value.items())}
    if isinstance(value, list):
        values = [_structural_signature(item) for item in value]
        if field == "evidence":
            unique = {json.dumps(item, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":")): item for item in values}
            return [unique[key] for key in sorted(unique)]
        if field == "supports":
'''


PRESENTATION_PREDECESSOR_SHA256 = '55de108d53fea5ac74dbaad21807a8ff38247d534410d6513173664c56c7610c'
PRESENTATION_SUCCESSOR_SHA256 = 'd4a74cbf65db1f457b8df0e77ae56fa25379b3c5ff09fefb4a1e823cb9685050'
# Independent exact hunks; no production or preservation helper is imported.
PRESENTATION_REVERSE_EDITS = (
    (
        (
            b'from copy import deepcopy\n'
            b'import json\n'
            b'import math\n'
            b'\n'
            b'\n'
        ),
        (
            b'from copy import deepcopy\n'
            b'import json\n'
            b'\n'
            b'\n'
        ),
    ),
    (
        (
            b'\n'
            b'\n'
            b'def _same_json_value(left, right, depth=0):\n'
            b'    """Conservatively recognize unchanged plain JSON without coercing types."""\n'
            b'    if depth > 64 or type(left) is not type(right):\n'
            b'        return False\n'
            b'    if type(left) is dict:\n'
            b'        if (any(type(key) is not str for key in left)\n'
            b'                or any(type(key) is not str for key in right)\n'
            b'                or tuple(left) != tuple(right)):\n'
            b'            return False\n'
            b'        return all(_same_json_value(left[key], right[key], depth + 1) for key in left)\n'
            b'    if type(left) is list:\n'
            b'        return len(left) == len(right) and all(\n'
            b'            _same_json_value(a, b, depth + 1) for a, b in zip(left, right))\n'
            b'    if type(left) is float:\n'
            b'        return math.isfinite(left) and math.isfinite(right) and left.hex() == right.hex()\n'
            b'    if type(left) in (str, int, bool, type(None)):\n'
            b'        return left == right\n'
            b'    return False\n'
            b'\n'
            b'\n'
            b'def _resolved_graph(catalog: dict, kind: str) -> tuple[dict, dict, dict]:\n'
            b'    """Resolve a canonical subset against the complete validated offline graph.\n'
            b'\n'
            b'    Incoming records replace records of the same ID. Changed or uncertain\n'
            b'    inputs require full graph validation again. An exact unchanged subset\n'
            b'    reuses only the complete graph freshly read and validated in this call.\n'
            b'    Catalogues remain raw envelopes; resolved objects never become records.\n'
            b'    """\n'
        ),
        (
            b'\n'
            b'\n'
            b'def _resolved_graph(catalog: dict, kind: str) -> tuple[dict, dict, dict]:\n'
            b'    """Resolve a canonical subset against the complete validated offline graph.\n'
            b'\n'
            b'    Incoming records replace records of the same ID. The resulting entire\n'
            b'    graph is validated again, so display cannot bypass semantic protections.\n'
            b'    Catalogues remain raw envelopes; resolved objects never become records.\n'
            b'    """\n'
        ),
    ),
    (
        (
            b'    if not isinstance(catalog, dict) or set(catalog) != keys or catalog["schema_version"] != "1.0.0":\n'
            b'        raise ValueError("material presentation: invalid canonical catalogue envelope")\n'
            b'    original = materials if kind == "materials" else properties\n'
            b'    for key in keys - {"schema_version"}:\n'
            b'        incoming = catalog[key]\n'
        ),
        (
            b'    if not isinstance(catalog, dict) or set(catalog) != keys or catalog["schema_version"] != "1.0.0":\n'
            b'        raise ValueError("material presentation: invalid canonical catalogue envelope")\n'
            b'    target = deepcopy(materials if kind == "materials" else properties)\n'
            b'    for key in keys - {"schema_version"}:\n'
            b'        incoming = catalog[key]\n'
        ),
    ),
    (
        (
            b'        if len(identifiers) != len(set(identifiers)):\n'
            b'            raise ValueError(f"material presentation: duplicate {key} ID")\n'
            b'\n'
            b'    unchanged = (type(catalog) is dict and type(catalog["schema_version"]) is str\n'
            b'                 and all(type(key) is str for key in catalog))\n'
            b'    for key in keys - {"schema_version"}:\n'
            b'        incoming = catalog[key]\n'
            b'        if type(incoming) is not list:\n'
            b'            unchanged = False\n'
            b'            continue\n'
            b'        index = {item["id"]: (position, item) for position, item in enumerate(original[key])}\n'
            b'        previous_position = -1\n'
            b'        for item in incoming:\n'
            b'            if (type(item) is not dict or type(item["id"]) is not str\n'
            b'                    or item["id"] not in index):\n'
            b'                unchanged = False\n'
            b'                break\n'
            b'            position, original_item = index[item["id"]]\n'
            b'            if position <= previous_position or not _same_json_value(item, original_item):\n'
            b'                unchanged = False\n'
            b'                break\n'
            b'            previous_position = position\n'
            b'    if unchanged:\n'
            b'        return materials, properties, sources\n'
            b'\n'
            b'    target = deepcopy(original)\n'
            b'    for key in keys - {"schema_version"}:\n'
            b'        incoming = catalog[key]\n'
            b'        replacements = {item["id"]: item for item in incoming}\n'
            b'        existing = {item["id"] for item in target[key]}\n'
        ),
        (
            b'        if len(identifiers) != len(set(identifiers)):\n'
            b'            raise ValueError(f"material presentation: duplicate {key} ID")\n'
            b'        replacements = {item["id"]: item for item in incoming}\n'
            b'        existing = {item["id"] for item in target[key]}\n'
        ),
    ),
)


def manifest(root):
    return {p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and p.suffix in {'.py', '.json'}}


class BaselineCompatibility(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.fixture.cleanup)
        cls.fixture_root = Path(cls.fixture.name)
        cls.current_root = cls.fixture_root / 'current'
        cls.dedup_root = cls.fixture_root / 'dedup-predecessor'
        cls.original_root = cls.fixture_root / 'original'
        installed_root = Path(files('materials_boundaries'))
        for source in installed_root.rglob('*'):
            if source.is_file() and source.suffix in {'.py', '.json'}:
                target = cls.current_root / source.relative_to(installed_root)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
        raw = (cls.current_root / 'material_references.py').read_bytes()
        if sha256(raw).hexdigest() != SUCCESSOR_SHA256 or raw.count(SUCCESSOR_HUNK) != 1:
            raise AssertionError('Compatibility tests require the exact reviewed successor bytes')
        predecessor = raw.replace(SUCCESSOR_HUNK, PREDECESSOR_HUNK)
        if sha256(predecessor).hexdigest() != PREDECESSOR_SHA256:
            raise AssertionError('Reconstructed predecessor differs from the historical anchor')
        presentation = (cls.current_root / 'material_presentation.py').read_bytes()
        if sha256(presentation).hexdigest() != PRESENTATION_SUCCESSOR_SHA256:
            raise AssertionError('Compatibility tests require the exact presentation successor')
        for after, before in PRESENTATION_REVERSE_EDITS:
            if presentation.count(after) != 1:
                raise AssertionError('Presentation reversal hunk differs from the reviewed bytes')
            presentation = presentation.replace(after, before)
        if sha256(presentation).hexdigest() != PRESENTATION_PREDECESSOR_SHA256:
            raise AssertionError('Reconstructed presentation differs from the historical anchor')
        shutil.copytree(cls.current_root, cls.dedup_root)
        (cls.dedup_root / 'material_presentation.py').write_bytes(presentation)
        shutil.copytree(cls.dedup_root, cls.original_root)
        (cls.original_root / 'material_references.py').write_bytes(predecessor)
        cls.pin_bytes = files('materials_query').joinpath('pins/legacy_baseline.json').read_bytes()
        if sha256(cls.pin_bytes).hexdigest() != PIN_SHA256:
            raise AssertionError('Historical pin bytes must remain unchanged')
        cls.expected = json.loads(cls.pin_bytes)
        cls.original_identity = sha256(json.dumps(
            cls.expected, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
            allow_nan=False).encode()).hexdigest()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)

    @contextmanager
    def resources(self, core_root, query_root=None):
        # Only resource locations change. Production traversal, hashing, pin
        # authentication, full-manifest matching and database code remain live.
        def resource_root(package):
            if package == 'materials_boundaries':
                return core_root
            if package == 'materials_query' and query_root is not None:
                return query_root
            return files(package)
        with patch.object(registry, 'files', resource_root):
            yield

    def copied_root(self, original=False):
        target = self.work / ('original' if original else 'current')
        shutil.copytree(self.original_root if original else self.current_root, target)
        return target

    def make_registry(self, path, review, rich):
        options = {'input_file_bytes': INPUT} if rich else {}
        return registry.ComputedRegistry(path, review,
            trusted_review_sha256=registry.digest(review), **options)

    def review(self, rich, second=False):
        review = rich_review() if rich else legacy_review()
        if second:
            extra = deepcopy(review['records'][0])
            extra.update(candidate_id='second', provider_entry_id='entry2',
                source_url='https://nomad-lab.eu/prod/v1/gui/entry/id/entry2')
            review['records'].append(extra)
        return review

    def database_rows(self, path):
        with closing(sqlite3.connect(path)) as database:
            return {table: database.execute('SELECT * FROM ' + table + ' ORDER BY 1').fetchall()
                    for table in ('metadata', 'entries', 'admissions')}

    def assert_manifest_rejected(self, mutate):
        for source in (self.original_root, self.dedup_root, self.current_root):
            with self.subTest(manifest=source.name):
                root = self.work / source.name
                shutil.copytree(source, root)
                mutate(root)
                with self.resources(root), self.assertRaisesRegex(
                        ValueError, 'Installed legacy baseline differs'):
                    registry.baseline_digest()

    def test_original_and_corrected_manifests_keep_historical_identity(self):
        self.assertEqual(len(self.expected), 64)
        self.assertEqual(manifest(self.original_root), self.expected)
        expected_successor = dict(self.expected, **{'material_references.py': SUCCESSOR_SHA256})
        self.assertEqual(manifest(self.dedup_root), expected_successor)
        expected_successor['material_presentation.py'] = PRESENTATION_SUCCESSOR_SHA256
        self.assertEqual(manifest(self.current_root), expected_successor)
        self.assertEqual(self.expected['material_references.py'], PREDECESSOR_SHA256)
        self.assertEqual(self.expected['material_presentation.py'], PRESENTATION_PREDECESSOR_SHA256)
        self.assertEqual(registry.BASELINE_PIN, PIN_SHA256)
        for root in (self.original_root, self.dedup_root, self.current_root):
            with self.subTest(root=root.name), self.resources(root):
                self.assertEqual(registry.baseline_digest(), self.original_identity)

    def test_installed_package_uses_corrected_manifest_without_resource_override(self):
        self.assertEqual(manifest(Path(files('materials_boundaries'))), manifest(self.current_root))
        self.assertEqual(registry.baseline_digest(), self.original_identity)
        review = legacy_review()
        database = self.make_registry(self.work / 'installed.db', review, False)
        self.assertEqual(database.admit(['fixture-entry'])['baseline_version'], self.original_identity)

    def test_unknown_reference_bytes_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'material_references.py').write_bytes(
            (root / 'material_references.py').read_bytes() + b'\n# Unreviewed change\n'))

    def test_unknown_presentation_bytes_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'material_presentation.py').write_bytes(
            (root / 'material_presentation.py').read_bytes() + b'\n# Unreviewed change\n'))

    def test_presentation_only_hybrid_manifest_rejected(self):
        root = self.copied_root(original=True)
        (root / 'material_presentation.py').write_bytes(
            (self.current_root / 'material_presentation.py').read_bytes())
        hybrid = dict(self.expected, **{'material_presentation.py': PRESENTATION_SUCCESSOR_SHA256})
        self.assertEqual(manifest(root), hybrid)
        with self.resources(root), self.assertRaisesRegex(
                ValueError, 'Installed legacy baseline differs'):
            registry.baseline_digest()

    def test_changed_other_python_file_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / '_version.py').write_bytes(
            (root / '_version.py').read_bytes() + b'\n# Unreviewed change\n'))

    def test_changed_catalog_bytes_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'data/materials.json').write_bytes(
            (root / 'data/materials.json').read_bytes() + b' '))

    def test_missing_manifest_file_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'data/materials.json').unlink())

    def test_extra_manifest_file_rejected(self):
        self.assert_manifest_rejected(lambda root: (root / 'data/unreviewed.json').write_bytes(b'{}'))

    def test_replaced_pin_rejected(self):
        query_root = self.work / 'query'
        (query_root / 'pins').mkdir(parents=True)
        changed = dict(self.expected, **{'material_references.py': SUCCESSOR_SHA256})
        for raw in (self.pin_bytes + b' ', registry.canonical(changed)):
            with self.subTest(pin_sha256=sha256(raw).hexdigest()):
                (query_root / 'pins/legacy_baseline.json').write_bytes(raw)
                with self.resources(self.current_root, query_root), self.assertRaisesRegex(
                        ValueError, 'Baseline pin was replaced'):
                    registry.baseline_digest()

    def assert_old_database_reopens(self, rich, predecessor=None):
        path = self.work / 'historical.db'
        review = self.review(rich)
        candidate = review['records'][0]['candidate_id']
        with self.resources(self.original_root if predecessor is None else predecessor):
            old = self.make_registry(path, review, rich)
            before = old.admit([candidate])
        rows = self.database_rows(path)
        database_bytes = path.read_bytes()
        self.assertEqual(dict(rows['metadata'])['baseline'], self.original_identity)
        self.assertEqual(len(rows['entries']), 1)
        self.assertEqual(len(rows['admissions']), 1)
        with self.resources(self.current_root):
            reopened = self.make_registry(path, review, rich)
            self.assertEqual(reopened.snapshot(), before)
            self.assertEqual(self.database_rows(path), rows)
            self.assertEqual(path.read_bytes(), database_bytes)
            self.assertEqual(reopened.admit([candidate]), before)
            self.assertEqual(self.database_rows(path), rows)
            self.assertEqual(path.read_bytes(), database_bytes)

    def test_original_manifest_legacy_database_reopens_without_changes(self):
        self.assert_old_database_reopens(False)

    def test_original_manifest_v2_database_reopens_without_changes(self):
        self.assert_old_database_reopens(True)

    def test_dedup_predecessor_legacy_database_reopens_without_changes(self):
        self.assert_old_database_reopens(False, self.dedup_root)

    def test_dedup_predecessor_v2_database_reopens_without_changes(self):
        self.assert_old_database_reopens(True, self.dedup_root)

    def assert_new_registry_replay(self, rich):
        review = self.review(rich)
        path = self.work / 'new.db'
        # No resource adapter: this exercises the actual source or installed
        # package manifest selected by the caller's Python environment.
        created = self.make_registry(path, review, rich)
        self.assertEqual(created.snapshot()['records'], [])
        self.assertEqual(created.baseline, self.original_identity)
        admitted = created.admit([review['records'][0]['candidate_id']])
        self.assertEqual(admitted['records'], [review['records'][0]])
        self.assertEqual(created.admit([review['records'][0]['candidate_id']]), admitted)
        self.assertEqual(self.make_registry(path, review, rich).snapshot(), admitted)

    def test_new_legacy_registry_admission_and_replay(self):
        self.assert_new_registry_replay(False)

    def test_new_v2_registry_admission_and_replay(self):
        self.assert_new_registry_replay(True)

    def assert_failed_transaction_recovers(self, rich):
        path = self.work / 'interrupted.db'
        review = self.review(rich, second=True)
        with self.resources(self.original_root):
            historical = self.make_registry(path, review, rich)
            before = historical.admit([review['records'][0]['candidate_id']])
        rows = self.database_rows(path)
        with closing(sqlite3.connect(path)) as database, database:
            database.execute("CREATE TRIGGER fail_admission BEFORE INSERT ON admissions "
                             "WHEN NEW.id='second' BEGIN "
                             "SELECT RAISE(ABORT, 'synthetic transaction abort'); END")
        with self.resources(self.current_root):
            current = self.make_registry(path, review, rich)
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'synthetic transaction abort'):
                current.admit(['second'])
            self.assertEqual(self.database_rows(path), rows)
            self.assertEqual(current.snapshot(), before)
            reopened = self.make_registry(path, review, rich)
            self.assertEqual(reopened.snapshot(), before)
            with closing(sqlite3.connect(path)) as database, database:
                database.execute('DROP TRIGGER fail_admission')
            recovered = reopened.admit(['second'])
            self.assertEqual(len(recovered['records']), 2)
            self.assertEqual(recovered['baseline_version'], self.original_identity)
            self.assertEqual(reopened.admit(['second']), recovered)
            self.assertEqual(self.make_registry(path, review, rich).snapshot(), recovered)
            self.assertEqual(self.database_rows(path)['metadata'], rows['metadata'])

    def test_failed_legacy_transaction_rolls_back_and_reopens(self):
        self.assert_failed_transaction_recovers(False)

    def test_failed_v2_transaction_rolls_back_and_reopens(self):
        self.assert_failed_transaction_recovers(True)

    def test_rejected_unknown_baseline_leaves_existing_database_unchanged(self):
        root = self.copied_root()
        (root / 'material_references.py').write_bytes(b'# Unknown successor\n')
        for rich in (False, True):
            with self.subTest(rich=rich):
                review = self.review(rich)
                path = self.work / ('existing-v2.db' if rich else 'existing-legacy.db')
                with self.resources(self.original_root):
                    historical = self.make_registry(path, review, rich)
                    before = historical.admit([review['records'][0]['candidate_id']])
                database_bytes = path.read_bytes()
                with self.resources(root), self.assertRaisesRegex(
                        ValueError, 'Installed legacy baseline differs'):
                    self.make_registry(path, review, rich)
                self.assertEqual(path.read_bytes(), database_bytes)
                self.assertEqual(self.make_registry(path, review, rich).snapshot(), before)

    def test_registry_with_unknown_baseline_never_creates_database(self):
        root = self.copied_root()
        (root / 'material_references.py').write_bytes(b'# Unknown successor\n')
        for rich in (False, True):
            with self.subTest(rich=rich):
                path = self.work / ('new-v2.db' if rich else 'new-legacy.db')
                with self.resources(root), self.assertRaisesRegex(
                        ValueError, 'Installed legacy baseline differs'):
                    self.make_registry(path, self.review(rich), rich)
                self.assertFalse(path.exists())


if __name__ == '__main__':
    unittest.main()
