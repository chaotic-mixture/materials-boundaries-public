import copy
from datetime import timedelta
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import httpx
from pydantic import ValidationError
from materials_federation.models import Query, Candidate, now
from materials_federation.normalize import normalize_mp, normalize_nomad
from materials_federation.providers import MaterialsProjectAdapter, NomadAdapter, AuthenticationRequired, ProviderError
from materials_federation.cache import ResultCache
from materials_federation.review import compare, review_package
from materials_federation.service import federated_search

FIXTURES = Path(__file__).parent / "fixtures"

def mp(): return json.loads((FIXTURES / "mp_summary.json").read_text())
def nomad(): return json.loads((FIXTURES / "nomad_archive_projected.json").read_text())

class AdapterTests(unittest.TestCase):
    def test_federation_retains_partial_auth_failure(self):
        transport=httpx.MockTransport(lambda r:httpx.Response(200,json={"data":[],"pagination":{}}))
        result=federated_search([MaterialsProjectAdapter(),NomadAdapter(transport=transport,fixture=True)],Query(formula="Si"))
        self.assertEqual(result.status,"partial")
        self.assertEqual(result.failures[0].kind,"authentication_required")
        self.assertEqual(len(result.pages),1)
        self.assertEqual(result.quota_credit,0)

    def test_query_requires_scope_and_hard_limit(self):
        for args in ({}, {"formula":"*"}, {"formula":"Si", "limit":26}, {"formula":"Si", "limit":True}):
            with self.assertRaises(ValidationError): Query(**args)

    def test_mp_no_implicit_credentials(self):
        with self.assertRaises(AuthenticationRequired):
            MaterialsProjectAdapter().search(Query(formula="Si"))

    def test_mp_computed_despite_experimental_database_link(self):
        c = normalize_mp(mp(), fixture=True)
        self.assertTrue(all(p.evidence_kind == "computed" for p in c.properties))
        self.assertIsNone(c.canonical_material_id)
        self.assertEqual(c.quota_credit, 0)
        self.assertEqual(c.review_status, "pending_review")
        self.assertEqual(c.identity_evidence["structure"].task_ids, ("mp-task-fixture",))
        self.assertEqual(next(p for p in c.properties if p.quantity=="band_gap").provenance.task_ids, ())
        self.assertEqual(c.source.license_identifier, "BY-C")
        self.assertEqual(c.properties[0].unit, "g/cm^3")

    def test_mp_rejects_deprecated_restricted_and_nonfinite(self):
        for key, value in (("deprecated",True), ("density",float("nan"))):
            d=mp();d[key]=value
            with self.assertRaises(ValueError): normalize_mp(d)
        d=mp();d["builder_meta"]["license"]="BY-NC"
        with self.assertRaises(ValueError): normalize_mp(d)

    def test_mp_bounded_client_contract(self):
        calls=[]
        def search(**kwargs): calls.append(kwargs);return [mp()]
        rester=SimpleNamespace(available_fields=list(mp()), search=search)
        client=SimpleNamespace(materials=SimpleNamespace(summary=rester),db_version="fixture-db")
        result=MaterialsProjectAdapter(client,fixture=True).search(Query(formula="Si",limit=1))
        self.assertFalse(calls[0]["include_gnome"])
        self.assertFalse(calls[0]["deprecated"])
        self.assertEqual(calls[0]["num_chunks"],1)
        self.assertEqual(calls[0]["chunk_size"],1)
        self.assertTrue(result.possibly_truncated)
        self.assertEqual(result.candidates[0].source.provider_version,"fixture-db")

    def test_mp_schema_drift_fails_closed(self):
        client=SimpleNamespace(materials=SimpleNamespace(summary=SimpleNamespace(available_fields=["material_id"])))
        with self.assertRaises(ProviderError): MaterialsProjectAdapter(client).search(Query(formula="Si"))

    def test_nomad_archive_units_provenance(self):
        c=normalize_nomad(nomad(),fixture=True)
        self.assertEqual(c.formula,"CaFe2Re")
        self.assertEqual(c.properties[0].unit,"kg/m^3")
        self.assertEqual(c.properties[0].evidence_kind,"computed")
        self.assertAlmostEqual(c.properties[0].value,9469.043880966017)
        self.assertLess(abs(c.structure["lattice_vectors"][0][0]),1e-8)
        self.assertEqual(c.source.license_identifier,"CC BY 4.0")
        self.assertIsNone(c.source.provider_version)
        self.assertEqual(c.external_references["processing_nomad_version"],"1.0.0")
        self.assertEqual(c.external_references["external_db"],"AFLOW")

    def test_missing_method_not_experiment(self):
        d=nomad();d["results"]["method"]={}
        self.assertEqual(normalize_nomad(d).properties[0].evidence_kind,"unknown")

    def test_missing_density_not_zero(self):
        d=nomad();d["results"]["properties"]["structures"]["structure_original"].pop("mass_density")
        self.assertEqual(normalize_nomad(d).properties,())

    def test_nomad_public_bounded_request(self):
        d=nomad();entry={**d["metadata"],"results":d["results"]}
        def handler(request):
            self.assertEqual(request.url.params["owner"],"public")
            self.assertEqual(request.url.params["page_size"],"1")
            self.assertNotIn("authorization",request.headers)
            return httpx.Response(200,json={"data":[entry],"pagination":{"next_page_after_value":"opaque-cursor"}})
        page=NomadAdapter(transport=httpx.MockTransport(handler),fixture=True).search(Query(formula="CaFe2Re",limit=1))
        self.assertEqual(page.next_cursor,"opaque-cursor")
        self.assertTrue(page.possibly_truncated)
        self.assertTrue(page.candidates[0].source.fixture)

    def test_nomad_error_is_not_empty_success(self):
        for code in (401,403,429,500):
            adapter=NomadAdapter(transport=httpx.MockTransport(lambda r: httpx.Response(code)))
            with self.assertRaises(ProviderError): adapter.search(Query(formula="Si"))

    def test_formula_not_identity_and_revision_not_new_material(self):
        a=normalize_mp(mp(),fixture=True)
        d=mp();d["material_id"]="mp-other-phase-fixture"
        b=normalize_mp(d,fixture=True)
        self.assertEqual(compare(a,b).relation,"candidate_matches")
        self.assertFalse(compare(a,b).may_merge)
        d=mp();d["band_gap"]=0.8
        self.assertEqual(compare(a,normalize_mp(d,fixture=True)).relation,"provider_revision")
        self.assertEqual(compare(a,a).relation,"same_provider_snapshot")

    def test_review_package_never_grants_admission(self):
        package=review_package([normalize_mp(mp(),fixture=True)])
        self.assertEqual(package["admission_status"],"not_admitted")
        self.assertEqual(package["quota_credit"],0)
        self.assertNotIn("trusted_manifest_digest",package)
        with self.assertRaises(ValidationError):
            Candidate.model_validate({**package["candidates"][0],"quota_credit":1})

    def test_reject_malformed_property_scalars(self):
        for value in (True, "2.3", {"value": 2.3}, float("inf")):
            d=mp();d["density"]=value
            with self.assertRaises(ValueError): normalize_mp(d)

    def test_modulus_averages_are_separate_fields(self):
        c=normalize_mp(mp(),fixture=True)
        fields={p.quantity:p for p in c.properties}
        self.assertEqual(fields["bulk_modulus_voigt"].value,90.0)
        self.assertEqual(fields["bulk_modulus_reuss"].value,89.0)
        self.assertEqual(fields["bulk_modulus_vrh"].value,89.5)
        self.assertEqual(fields["bulk_modulus_vrh"].provenance.field_path,"bulk_modulus.vrh")

    def test_fixture_cache_never_served_as_live(self):
        transport=httpx.MockTransport(lambda r: httpx.Response(200,json={"data":[],"pagination":{}}))
        q=Query(formula="Si");page=NomadAdapter(transport=transport,fixture=True).search(q)
        with tempfile.TemporaryDirectory() as folder:
            cache=ResultCache(Path(folder))
            key=cache.key("nomad",q,fixture=True)
            self.assertNotEqual(key,cache.key("nomad",q,fixture=False))
            cache.put(key,page)
            with self.assertRaises(ValueError): cache.get(key,fixture=False)

    def test_archive_identity_and_scope_guards(self):
        c=normalize_nomad(nomad(),fixture=True)
        transport=httpx.MockTransport(lambda r: httpx.Response(200,json={"data":{"archive":nomad()}}))
        enriched=NomadAdapter(transport=transport,fixture=True).enrich_archive(c)
        self.assertEqual(enriched.source.record_id,c.source.record_id)
        self.assertTrue(enriched.source.fixture)
        with self.assertRaises(ValueError): NomadAdapter().enrich_archive(c)
        d=nomad();d["metadata"]["entry_id"]="wrong-id"
        bad=httpx.MockTransport(lambda r: httpx.Response(200,json={"data":{"archive":d}}))
        with self.assertRaises(ProviderError): NomadAdapter(transport=bad,fixture=True).enrich_archive(c)

    def test_cache_hit_expiry_version_and_corruption(self):
        transport=httpx.MockTransport(lambda r: httpx.Response(200,json={"data":[],"pagination":{}}))
        q=Query(formula="Si");page=NomadAdapter(transport=transport,fixture=True).search(q)
        with tempfile.TemporaryDirectory() as folder:
            cache=ResultCache(Path(folder),ttl_seconds=60)
            key=cache.key("nomad",q,fixture=True)
            cache.put(key,page)
            self.assertEqual(cache.get(key,fixture=True).cache_status,"cache_hit")
            self.assertIsNone(cache.get(key,fixture=True,at=page.retrieved_at+timedelta(seconds=61)))
            self.assertNotEqual(key,cache.key("nomad",q,provider_version="new"))
            path=Path(folder)/(key+".json");d=json.loads(path.read_text());d["page"]["query"]["formula"]="Fe";path.write_text(json.dumps(d))
            with self.assertRaises(ValueError): cache.get(key,fixture=True)

if __name__ == "__main__": unittest.main()
