"""Installed-core wheel licenses and offline catalog regression boundary."""
import argparse
from email.parser import BytesParser
import importlib
from pathlib import Path
import sys
import unittest
import zipfile
from check_offline import PACKAGES, require

ROOT = Path(__file__).resolve().parents[1]

def main():
    require(getattr(sys, '_platform_ci_offline', False), 'Offline guard failed to load')
    import socket
    try: socket.getaddrinfo('ci-guard.invalid', 443)
    except RuntimeError as error: require('Offline fixture CI' in str(error), 'Wrong guard failure')
    else: raise RuntimeError('Network guard did not block DNS')
    parser=argparse.ArgumentParser();parser.add_argument('--wheel-dir',type=Path,required=True);args=parser.parse_args()
    packages={**PACKAGES, 'materials_boundaries': ROOT.parents[1]}
    wheels=sorted(args.wheel_dir.glob('*.whl'))
    require(len(wheels)==5, 'Expected exactly five locally built wheels')
    for name,source in packages.items():
        version=('0.35.0' if name=='materials_boundaries' else '0.5.0.dev0' if name in {'materials_boundaries_query_service','materials_boundaries_platform_experimental'} else '0.1.0')
        matches=list(args.wheel_dir.glob(name+'-'+version+'-*.whl'))
        require(len(matches)==1, 'Missing or duplicate local wheel: '+name)
        with zipfile.ZipFile(matches[0]) as wheel:
            metadata=BytesParser().parsebytes(wheel.read(next(n for n in wheel.namelist() if n.endswith('.dist-info/METADATA'))))
            for filename in ('LICENSE','THIRD_PARTY_NOTICES.md'):
                require(filename in metadata.get_all('License-File',[]), 'Missing license metadata')
                members=[n for n in wheel.namelist() if '.dist-info/' in n and n.endswith('/'+filename)]
                require(len(members)==1 and wheel.read(members[0])==(source/filename).read_bytes(), 'License bytes mismatch')
    for name in ('materials_boundaries','materials_query','materials_federation','materials_platform','materials_lifecycle'):
        module=importlib.import_module(name)
        require(Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), 'Source import instead of installed wheel: '+name)
    suite=unittest.TestLoader().discover(str(ROOT/'query-service/catalog-tests'))
    require(suite.countTestCases()>=78, 'Expected at least 78 local catalog tests')
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    require(result.wasSuccessful() and not result.skipped and not result.expectedFailures, 'Optional core tests did not fully pass')
    print('Installed optional-core offline catalog suite passed; no browser/live/deployment claim.')

if __name__=='__main__':main()
