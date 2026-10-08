"""Additive claim-local fail-fast guards never certify or cache a whole graph."""
import ast
from copy import deepcopy
import hashlib
import inspect
import io
from contextlib import contextmanager, redirect_stdout
import unittest
from unittest.mock import patch

from scripts import validate_catalogs as v


@contextmanager
def schema_visits(catalogs):
    """Observe actual instance-validation generators, not constructor calls."""
    original = v.Draft202012Validator.iter_errors
    top_level = {id(value): name for name, value in catalogs.items() if name in v.CATALOGS}
    visits = []
    def observed(self, instance, *args, **kwargs):
        name = top_level.get(id(instance))
        if name is not None:
            visits.append(name)
        yield from original(self, instance, *args, **kwargs)
    with patch.object(v.Draft202012Validator, 'iter_errors', observed):
        yield visits


class CatalogValidationFailFastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = v.load_catalogs(v.ROOT / 'materials_boundaries/data')

    def test_extracted_loop_is_ast_identical_to_v034_complete_claim_guard(self):
        # Exact loop from accepted 7e37be919ee97f1275249dcf745f9f55e951986a.
        function = ast.parse(inspect.getsource(v._validate_claim_family_identity_and_assumptions)).body[0]
        loops = [node for node in function.body if isinstance(node, ast.For)]
        self.assertEqual(len(loops), 1)
        digest = hashlib.sha256(ast.dump(loops[0], include_attributes=False).encode()).hexdigest()
        self.assertEqual(digest, '5b80dcf0dfe31b3dbd4fea14e4038925f0db0fa5cc4c032988581f163a9991ad')

    def test_every_successful_call_still_validates_every_schema_and_both_claim_guards(self):
        catalogs = deepcopy(self.original); before = deepcopy(catalogs)
        with schema_visits(catalogs) as visits, patch.object(
                v, '_validate_claim_family_identity_and_assumptions',
                wraps=v._validate_claim_family_identity_and_assumptions) as claim_guard:
            first = v.validate_catalogs(catalogs)
            first_visits = tuple(visits)
            visits.clear()
            second = v.validate_catalogs(catalogs)
        # Nested prediction branches may inspect the same envelope again.
        # Every catalog must still be visited afresh on each successful call.
        self.assertEqual(list(dict.fromkeys(first_visits)), list(v.CATALOGS))
        self.assertEqual(list(dict.fromkeys(visits)), list(v.CATALOGS))
        self.assertEqual(claim_guard.call_count, 4)
        self.assertEqual(first, second)
        self.assertEqual(catalogs, before)

    def test_bad_claim_rejects_before_other_schemas_without_success_or_mutation(self):
        catalogs = deepcopy(self.original)
        claim = next(r for r in catalogs['claims']['records'] if r['id'] == 'voigt_bulk')
        claim['required_assumptions'].pop(next(iter(claim['required_assumptions'])))
        before = deepcopy(catalogs); stdout = io.StringIO()
        with schema_visits(catalogs) as visits, redirect_stdout(stdout):
            with self.assertRaisesRegex(v.CatalogValidationError, 'claims.voigt_bulk: required assumptions'):
                v.validate_catalogs(catalogs)
        self.assertEqual(visits, ['claims'])
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(catalogs, before)

    def test_mixed_invalid_claim_and_material_has_explicit_claim_first_priority(self):
        catalogs = deepcopy(self.original)
        claim = next(r for r in catalogs['claims']['records'] if r['id'] == 'voigt_bulk')
        claim['required_assumptions'].pop(next(iter(claim['required_assumptions'])))
        catalogs['reference_properties']['records'][-1]['engineering_allowable'] = True
        with self.assertRaisesRegex(v.CatalogValidationError, 'claims.voigt_bulk: required assumptions'):
            v.validate_catalogs(catalogs)

    def test_valid_claims_do_not_hide_invalid_material_or_source_even_after_success(self):
        catalogs = deepcopy(self.original)
        v.validate_catalogs(catalogs)
        for kind, mutation in (
                ('reference_properties', lambda data: data['records'][-1].update(engineering_allowable=True)),
                ('sources', lambda data: data['records'][-1].update(title=None))):
            changed = deepcopy(catalogs); mutation(changed[kind]); before = deepcopy(changed)
            with self.subTest(kind=kind), self.assertRaises(v.CatalogValidationError):
                v.validate_catalogs(changed)
            self.assertEqual(changed, before)
        self.assertEqual(catalogs, self.original)

    def test_claim_mutation_after_success_is_not_covered_by_a_data_cache(self):
        catalogs = deepcopy(self.original)
        v.validate_catalogs(catalogs)
        claim = next(r for r in catalogs['claims']['records'] if r['id'] == 'voigt_bulk')
        claim['required_assumptions'].pop(next(iter(claim['required_assumptions'])))
        with self.assertRaisesRegex(v.CatalogValidationError, 'claims.voigt_bulk: required assumptions'):
            v.validate_catalogs(catalogs)
