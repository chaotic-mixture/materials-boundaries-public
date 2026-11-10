"""Current public release checks, independent of archived byte-replay suites."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'tests')]
from materials_boundaries.database import Database


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for pattern in ('test_tension.py', 'test_mechanics.py', 'test_database*.py', 'test_engine.py',
                    'test_validation.py', 'test_release_metadata.py'):
        suite.addTests(loader.discover(str(ROOT/'tests'), pattern=pattern))
    if loader.errors:
        raise RuntimeError('\n'.join(loader.errors))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    print(json.dumps(Database().validate_scientific_contracts()), flush=True)
    print(json.dumps({'scope':'current_public_release', 'tests_run':result.testsRun,
                      'skipped':len(result.skipped), 'historical_replay':'not_run'}), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
