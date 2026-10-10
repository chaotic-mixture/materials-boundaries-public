"""PROPOSAL: separate optional-core offline job; existing 83-test job is unchanged."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import venv

CI = Path(__file__).resolve().parent
ROOT = CI.parent


def run(*command, cwd, env):
    print('+', ' '.join(map(str, command)), flush=True)
    subprocess.run(list(map(str, command)), cwd=cwd, env=env, check=True)


def main():
    if sys.version_info < (3, 11):
        raise SystemExit('Python 3.11+ is required')
    env = os.environ.copy()
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
    env['PIP_NO_INPUT'] = '1'
    # Do not permit an inherited key to change offline fixture behavior.
    for key in ('MP_API_KEY', 'PMG_MAPI_KEY', 'MAPI_KEY'):
        env.pop(key, None)
    with tempfile.TemporaryDirectory(prefix='experimental-platform-ci-') as temp:
        work = Path(temp)
        build = work / 'build-env'
        runtime = work / 'runtime-env'
        wheels = work / 'wheels'
        wheels.mkdir()
        for path in (build, runtime):
            venv.EnvBuilder(with_pip=True, system_site_packages=False).create(path)
        builder = build / 'bin/python'
        python = runtime / 'bin/python'
        run(builder, '-m', 'pip', 'install', '--no-deps', '--only-binary=:all:', '-r', CI / 'build-requirements.txt', cwd=work, env=env)
        # No isolated resolver may silently choose a different build backend.
        run(builder, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation', '--wheel-dir', wheels,
            ROOT / 'federation', ROOT / 'query-service', ROOT / 'lifecycle', ROOT, ROOT.parents[1], ROOT.parents[1] / 'formal-catalog', cwd=work, env=env)
        run(python, '-m', 'pip', 'install', '--no-deps', '--only-binary=:all:', 'pip==26.2.1', cwd=work, env=env)
        run(python, '-m', 'pip', 'install', '--no-deps', '--only-binary=:all:', '-r', ROOT / 'requirements-lock.txt', cwd=work, env=env)
        local_wheels = sorted(wheels.glob('*.whl'))
        if len(local_wheels) != 6:
            raise RuntimeError('Expected exactly six local package wheels')
        run(python, '-m', 'pip', 'install', '--no-index', '--no-deps', *local_wheels, cwd=work, env=env)
        run(python, '-m', 'pip', 'check', cwd=work, env=env)
        env['PYTHONPATH'] = str(CI)  # Only the offline guard, never package source roots.
        checker = CI / 'check_catalog.py'
        run(python, checker, '--wheel-dir', wheels, cwd=work, env=env)
    print('Experimental platform CI passed; live integrations and publication were not run.', flush=True)


if __name__ == '__main__':
    main()
