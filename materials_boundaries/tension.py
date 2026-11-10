"""Traceable uniaxial tension scenarios, with case-local inputs and revisions."""
import argparse
from dataclasses import dataclass, replace
import json

from .database import Database
from .mechanics import UNITS, number, output, stress_response

NICKEL = "refprop_specialmetals_nickel200_annealed_youngs_modulus"
COPPER = "refprop_aurubis_c11000_mass_density"
RULES = {
    "free": ("sigma_x = E * epsilon_x", "lateral stresses are zero"),
    "fixed": ("isotropic_hooke_3d_v1", "lateral strains and all shear strains are zero"),
}


@dataclass(frozen=True)
class Case:
    record: str
    strain: str
    constraint: str
    assume_model: bool
    poisson: str | None = None


def evaluate(case, database):
    if case.record not in database.properties or case.constraint not in RULES:
        raise ValueError("Unknown property record or constraint")
    strain = number(case.strain)
    if strain < 0:
        raise ValueError("Tensile strain must be nonnegative")
    record = database.properties[case.record]
    value = record["reported_value"]
    rule, boundary = RULES[case.constraint]
    result = {
        "record": case.record, "state": record["material_state_id"],
        "source": record["source_document"], "conditions": record["conditions"],
        "scope": record["scope_note"], "evidence": record["evidence"],
        "inputs": vars(case).copy(), "rule": rule, "boundary": boundary,
        "selected_property": {"quantity": record["quantity"], "value": value},
        "engineering_allowable": False,
    }
    missing = []
    if not case.assume_model:
        missing.append("confirm record suitability and isotropic, small-strain linear elasticity")
    if (record["quantity"] != "youngs_modulus" or value["kind"] != "scalar"
            or value["unit_code"] not in UNITS):
        missing.append("compatible scalar Young's modulus")
    if case.constraint == "fixed" and case.poisson is None:
        missing.append("Poisson ratio for the selected state")
    if missing:
        return {**result, "status": "missing", "missing": missing}
    young = number(value["number"])
    if young <= 0:
        raise ValueError("Young's modulus must be positive")
    if case.constraint == "free":
        axial = output(young * strain)
    else:
        response = stress_response([strain, 0, 0, 0, 0, 0], young=young,
                                   poisson=case.poisson, unit=value["unit_code"],
                                   assume_isotropic=True)
        axial = response["stress"][0]
    return {**result, "status": "calculated", "axial_stress": axial, "unit": value["unit_code"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", default=NICKEL, help="Selected catalog property ID")
    parser.add_argument("--strain", required=True, help="Dimensionless axial tensile strain")
    parser.add_argument("--constraint", choices=RULES, default="free")
    parser.add_argument("--then", choices=RULES, help="Revise the same case's lateral constraint")
    parser.add_argument("--poisson", help="User-supplied Poisson ratio for this state")
    parser.add_argument("--assume-model", action="store_true",
                        help="Accept selected reference data and stable isotropic small-strain elasticity for this scenario")
    args = parser.parse_args(argv)
    case = Case(args.record, args.strain, args.constraint, args.assume_model, args.poisson)
    database = Database()
    try:
        history = [evaluate(case, database)]
        if args.then:
            history.append(evaluate(replace(case, constraint=args.then), database))
    except (ValueError, ArithmeticError) as exc:
        parser.error(str(exc))
    print(json.dumps({"prior_revisions": history[:-1], "current": history[-1]}, indent=2))


if __name__ == "__main__":
    main()
