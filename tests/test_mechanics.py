import contextlib
import io
import json
import unittest
from materials_boundaries.mechanics import elastic_constants, stress_response, knowledge, main


class MechanicsTests(unittest.TestCase):
    def test_reference_conversion_and_round_trip(self):
        a = elastic_constants(young=210, poisson=0.3, assume_isotropic=True)['values']
        self.assertAlmostEqual(a['bulk'], 175)
        self.assertAlmostEqual(a['shear'], 80.76923076923077)
        b = elastic_constants(bulk=a['bulk'], shear=a['shear'], assume_isotropic=True)['values']
        self.assertAlmostEqual(b['young'], 210)
        self.assertAlmostEqual(b['poisson'], 0.3)

    def test_auxetic_is_valid(self):
        r = elastic_constants(young=100, poisson=-0.5, assume_isotropic=True)['values']
        self.assertAlmostEqual(r['bulk'], 100/6)
        self.assertEqual(r['shear'], 100)

    def test_rejects_missing_assumptions_unstable_and_ambiguous_inputs(self):
        for kwargs in [dict(young=1,poisson=0.3), dict(young=-1,poisson=0.3,assume_isotropic=True),
                       dict(young=1,poisson=0.5,assume_isotropic=True),dict(young=1,poisson=-1,assume_isotropic=True),
                       dict(bulk=0,shear=1,assume_isotropic=True),dict(young=1,poisson=.3,bulk=1,assume_isotropic=True)]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError): elastic_constants(**kwargs)

    def test_rejects_nonfinite_bool_and_overflow(self):
        for value in [True,'NaN','Infinity','1e1000','1e-1000']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                elastic_constants(young=value,poisson=.3,assume_isotropic=True)

    def test_hydrostatic_and_pure_shear(self):
        options = dict(bulk=100,shear=40,assume_isotropic=True)
        hydro = stress_response([.001,.001,.001,0,0,0],**options)
        for value in hydro['stress'][:3]: self.assertAlmostEqual(value,.3)
        shear = stress_response([0,0,0,0,0,.01],**options)
        self.assertEqual(shear['stress'],[0,0,0,0,0,.4])
        self.assertAlmostEqual(shear['strain_energy_density'],.002)

    def test_uniaxial_stress_from_lateral_contraction(self):
        result = stress_response([.001,-.0003,-.0003,0,0,0],young=210,poisson=.3,assume_isotropic=True)
        self.assertAlmostEqual(result['stress'][0],.210)
        for x in result['stress'][1:]: self.assertAlmostEqual(x,0,places=12)
        matrix=result['stiffness_matrix']
        self.assertEqual(matrix,[list(x) for x in zip(*matrix)])

    def test_units_scale_moduli_and_stress(self):
        a=stress_response([.001,0,0,0,0,0],young=210,poisson=.3,unit='GPa',assume_isotropic=True)
        b=stress_response([.001,0,0,0,0,0],young=210000,poisson=.3,unit='MPa',assume_isotropic=True)
        self.assertAlmostEqual(b['stress'][0],1000*a['stress'][0])

    def test_cli_and_knowledge(self):
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            self.assertEqual(main(['convert','--young','210','--poisson','.3','--assume-isotropic']),0)
        self.assertEqual(json.loads(stream.getvalue())['model_id'],'isotropic_elastic_constants_v1')
        self.assertEqual(len(knowledge()['models']),2)

    def test_strain_size_and_zero_state(self):
        with self.assertRaises(ValueError): stress_response([0],young=1,poisson=.3,assume_isotropic=True)
        r=stress_response([0]*6,young=1,poisson=.3,assume_isotropic=True)
        self.assertEqual(r['stress'],[0]*6)
        self.assertEqual(r['strain_energy_density'],0)
