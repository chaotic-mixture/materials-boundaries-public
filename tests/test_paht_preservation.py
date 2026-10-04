"""Accepted v0.23 science and outputs, with only software version aligned."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from source_evidence_preservation import previous_record
from materials_boundaries.catalog import read_catalog
from materials_boundaries.catalog_output import render_catalog
from materials_boundaries import observation_visualization as view
from materials_boundaries import observation_temperature_plot as plot
from materials_boundaries._pa12_cf15_observation_contract import PA12_DATASET
ROOT=Path(__file__).resolve().parents[1]
BASE=json.loads((ROOT/'tests/fixtures/pre_paht_v0240.json').read_text())


def digest(v):return hashlib.sha256(v).hexdigest()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


class PAHTPreservationTests(unittest.TestCase):
    def test_all_prior_scientific_records_and_sources_remain_exact(self):
        for kind, hashes in BASE['record_sha256'].items():
            records={r['id']:r for r in read_catalog(kind)['records']}
            for rid,expected in hashes.items():
                with self.subTest(kind=kind,id=rid):
                    record=previous_record(kind, records[rid])
                    if kind=='claims':
                        # Disposable synthetic rehearsals add clearly synthetic
                        # evidence. Only that exact fixture addition may be removed.
                        fixture=json.loads((ROOT/'tests/fixtures/contributions/lefm.json').read_text())
                        added=fixture['evidence_addition']
                        if rid==added['claim_id'] and added['evidence'] in record['evidence']:
                            record['evidence'].remove(added['evidence'])
                    self.assertEqual(digest(canonical(record)),expected)
        for kind,fields in BASE['metadata_sha256'].items():
            actual=read_catalog(kind)
            for field,expected in fields.items():
                # Prediction appendability adds protocols/groups; compare only
                # accepted identities and order recorded independently below.
                baseline_ids=BASE.get('metadata_ids',{}).get(kind,{}).get(field)
                value=actual[field]
                if baseline_ids is not None:
                    index={x['id']:x for x in value};value=[index[x] for x in baseline_ids]
                self.assertEqual(digest(canonical(value)),expected)

    def test_all_old_locale_values_are_unchanged(self):
        for lang,hashes in BASE['locale_value_sha256'].items():
            values=read_catalog('locales')['languages'][lang]
            for key,expected in hashes.items():
                self.assertEqual(digest(values[key].encode()),expected,(lang,key))

    def test_old_selected_outputs_equal_with_only_engine_label_aligned(self):
        observations=read_catalog('observations')
        index={r['id']:r for r in observations['records']}
        observations['records']=[index[rid] for rid in BASE['inspection_selections']['all_old']]
        # Independent IDs make this proof insensitive to mixed catalog order.
        current_read=view.read_catalog
        def historical_reader(kind):
            if kind=='observations':
                return deepcopy(observations)
            catalog=current_read(kind)
            if kind=='sources':
                items={r['id']:r for r in catalog['records']}
                catalog['records']=[items[rid] for rid in BASE['record_sha256']['sources']]
            return catalog
        actual={}
        with patch('materials_boundaries.__version__',BASE['baseline_engine_version']), patch.object(view,'read_catalog',side_effect=historical_reader):
            for lang in ('en','zh','ja','de'):
                actual['catalog-'+lang]=digest(render_catalog(observations,'observations',lang).encode())
                for name,ids in BASE['inspection_selections'].items():
                    b=view.build_observation_inspection(ids)
                    outputs={'json':view.inspection_json(b),'csv':view.inspection_csv(b),
                        'html':view.render_observation_html(b,lang),'svg':view.render_observation_svg(b,lang),
                        'narrow.svg':view.render_observation_svg(b,lang,width=640)}
                    for ext,value in outputs.items():actual[name+'-'+lang+'.'+ext]=digest(value.encode())
                b=plot.build_observation_temperature_plot(dataset_id=PA12_DATASET)
                outputs={'json':plot.temperature_observation_plot_json(b),'csv':plot.temperature_observation_plot_csv(b),
                    'html':plot.render_observation_temperature_html(b,lang=lang),
                    'svg':plot.render_observation_temperature_svg(b,lang=lang),
                    'narrow.svg':plot.render_observation_temperature_svg(b,lang=lang,width=640)}
                for ext,value in outputs.items():actual['plot-'+lang+'.'+ext]=digest(value.encode())
        self.assertEqual(set(actual),set(BASE['old_output_sha256']))
        for name,value in actual.items():
            with self.subTest(output=name):self.assertEqual(value,BASE['old_output_sha256'][name])


if __name__=='__main__':unittest.main()
