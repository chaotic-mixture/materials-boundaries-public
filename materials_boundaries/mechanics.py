"""Executable isotropic linear elasticity with explicit applicability assertions."""
import argparse
from decimal import Decimal, localcontext
from importlib.resources import files
import json
import math
from ._version import __version__

UNITS = ('Pa', 'MPa', 'GPa')
ORDER = ['xx', 'yy', 'zz', 'yz', 'xz', 'xy']


def knowledge():
    return json.loads(files('materials_boundaries').joinpath('data').joinpath('mechanics_models.json').read_bytes())


def number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError('Expected a finite numeric value')
    try:
        result = Decimal(str(value))
        converted = float(result)
    except (ValueError, ArithmeticError):
        raise ValueError('Expected a finite representable numeric value') from None
    if not result.is_finite() or not math.isfinite(converted) or (result != 0 and converted == 0):
        raise ValueError('Value is outside the finite floating-point range')
    return result


def output(value):
    result = float(value)
    if not math.isfinite(result) or (value != 0 and result == 0):
        raise ValueError('Result is outside the finite floating-point range')
    return result


def elastic_constants(*, young=None, poisson=None, bulk=None, shear=None, unit='GPa', assume_isotropic=False):
    if assume_isotropic is not True:
        raise ValueError('Explicit isotropic, small-strain, stable linear-elastic assumption required')
    if unit not in UNITS:
        raise ValueError('Supported modulus units: Pa, MPa, GPa')
    en = young is not None and poisson is not None and bulk is None and shear is None
    kg = bulk is not None and shear is not None and young is None and poisson is None
    if not (en or kg):
        raise ValueError('Supply exactly Young + Poisson OR bulk + shear')
    with localcontext() as ctx:
        ctx.prec = 50
        if en:
            e, nu = number(young), number(poisson)
            if e <= 0 or not Decimal(-1) < nu < Decimal('0.5'):
                raise ValueError('Stable isotropic elasticity requires E > 0 and -1 < nu < 0.5')
            k, g = e/(3*(1-2*nu)), e/(2*(1+nu))
        else:
            k, g = number(bulk), number(shear)
            if k <= 0 or g <= 0:
                raise ValueError('Stable isotropic elasticity requires K > 0 and G > 0')
            e, nu = 9*k*g/(3*k+g), (3*k-2*g)/(2*(3*k+g))
        result = {'young': output(e), 'poisson': output(nu), 'bulk': output(k),
                  'shear': output(g), 'lame_lambda': output(k-2*g/3)}
    if not -1 < result['poisson'] < 0.5:
        raise ValueError('Poisson ratio rounds onto a singular boundary; use less extreme inputs')
    return {'engine_version': __version__, 'model_id': 'isotropic_elastic_constants_v1',
            'unit': unit, 'values': result, 'assumptions': ['isotropic', 'small_strain', 'linear_elastic', 'stable'],
            'assumption_status': 'user_asserted_not_sample_verified', 'engineering_allowable': False}


def stress_response(strain, **kwargs):
    """Voigt order xx,yy,zz,yz,xz,xy; input shears are engineering gamma."""
    if not isinstance(strain, (list, tuple)) or len(strain) != 6:
        raise ValueError('Strain must contain six engineering-strain components')
    constants = elastic_constants(**kwargs)
    with localcontext() as ctx:
        ctx.prec = 50
        eps = [number(x) for x in strain]
        g = number(constants['values']['shear'])
        lam = number(constants['values']['lame_lambda'])
        trace = sum(eps[:3])
        stress = [2*g*x+lam*trace for x in eps[:3]] + [g*x for x in eps[3:]]
        energy = sum(s*x for s, x in zip(stress, eps))/2
        matrix = [[output(lam+(2*g if i == j else 0)) if i < 3 and j < 3 else
                   output(g) if i == j else 0.0 for j in range(6)] for i in range(6)]
    return {**constants, 'model_id': 'isotropic_hooke_3d_v1', 'component_order': ORDER,
            'shear_convention': 'engineering_strain_gamma_ij=2*epsilon_ij',
            'strain': [output(x) for x in eps], 'stress': [output(x) for x in stress],
            'stiffness_matrix': matrix, 'strain_energy_density': output(energy),
            'energy_unit': constants['unit'] + ' (= scaled J/m^3)',
            'scope': 'constitutive response; no yield, failure, large-strain or anisotropy prediction'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['knowledge', 'convert', 'stress'])
    for name in ('young', 'poisson', 'bulk', 'shear'):
        parser.add_argument('--'+name)
    parser.add_argument('--unit', choices=UNITS, default='GPa')
    parser.add_argument('--assume-isotropic', action='store_true', help='Assert isotropic, stable small-strain linear elasticity')
    parser.add_argument('--strain', nargs=6, metavar='VALUE', help='xx yy zz gamma_yz gamma_xz gamma_xy (dimensionless)')
    args = parser.parse_args(argv)
    try:
        if args.action == 'knowledge':
            result = knowledge()
        else:
            options = {n: getattr(args, n) for n in ('young', 'poisson', 'bulk', 'shear', 'unit', 'assume_isotropic')}
            result = stress_response(args.strain, **options) if args.action == 'stress' else elastic_constants(**options)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    except (ValueError, ArithmeticError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
