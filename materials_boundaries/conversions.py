"""Fixed isotropic elastic conversion; source formulas are never evaluated."""
from decimal import Context, Decimal, localcontext
import math

CONVERSION_RULE_ID = "isotropic_young_poisson_to_bulk_shear_v1"


def isotropic_moduli(youngs_modulus: float, poissons_ratio: float) -> tuple[float, float]:
    """Return K, G in the same units as E for a positive isotropic solid.

    Only E > 0 and -1 < nu < 0.5 are supported. Decimal arithmetic isolates
    calculations from ambient state; returned numbers are float approximations.
    """
    for name, value in (("youngs_modulus", youngs_modulus), ("poissons_ratio", poissons_ratio)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name}: expected a finite number")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise ValueError(f"{name}: expected a finite number")
    if youngs_modulus <= 0 or not -1 < poissons_ratio < 0.5:
        raise ValueError("positive isotropic conversion requires E > 0 and -1 < nu < 0.5")
    with localcontext(Context(prec=80)):
        e, nu = Decimal(str(youngs_modulus)), Decimal(str(poissons_ratio))
        bulk = float(e / (3 * (1 - 2 * nu)))
        shear = float(e / (2 * (1 + nu)))
    if not all(math.isfinite(v) and v > 0 for v in (bulk, shear)):
        raise ValueError("derived modulus is outside finite, positive float range")
    return bulk, shear
