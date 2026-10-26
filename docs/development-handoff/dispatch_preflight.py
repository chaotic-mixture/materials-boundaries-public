#!/usr/bin/env python3
"""Read-only local manifest preflight. Never executes task commands or grants authority."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

PLACEHOLDER = re.compile(r'REPLACE_|PATH_TO_|YOUR_|PLACEHOLDER|\bTBD\b|\bTODO\b|<[^>]+>')
ACTIONS = {
    'candidate': {'read_inputs', 'write_candidate', 'run_approved_checks'},
    'independent_candidate_review': {'read_inputs', 'write_review', 'run_approved_checks'},
    'runtime_integration': {'read_inputs', 'write_runtime', 'run_approved_checks'},
    'validation': {'read_inputs', 'write_validation', 'run_approved_checks'},
    'independent_implementation_review': {'read_inputs', 'write_review', 'run_approved_checks'},
    'publication': {'read_inputs', 'push_exact_reviewed_commit', 'observe_remote_and_ci', 'write_validation'},
}


def strict_json(path):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('Duplicate JSON key: ' + key)
            out[key] = value
        return out
    def reject(value):
        raise ValueError('Nonfinite JSON token: ' + value)
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs, parse_constant=reject)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def relative_file(value):
    require(isinstance(value, str) and value and '\\' not in value,
            'Path must be a nonempty POSIX relative filename')
    p = PurePosixPath(value)
    require(not p.is_absolute() and str(p) == value and
            all(x not in ('.', '..', '.git', '.aws', '.codex') for x in p.parts) and
            not re.search(r'[*?\[\]{}:<>]', value), 'Unsafe/non-normalized path: ' + value)
    return value


def contained(root, path):
    resolved = path.resolve()
    require(resolved.is_relative_to(root), 'Path escapes workspace: ' + str(path))
    return resolved


def json_pointer(value, pointer):
    require(isinstance(pointer, str) and (pointer == '' or pointer.startswith('/')), 'Missing JSON pointer')
    for part in pointer.split('/')[1:] if pointer else []:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def inspect_manifest(manifest_path, workspace):
    from jsonschema import Draft202012Validator  # Existing dev dependency only; never install here.
    m = strict_json(manifest_path)
    schema = strict_json(Path(__file__).with_name('task-input.schema.json'))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(m)
    require(m['status'] == 'ready', 'Not dispatchable: status must be ready, never draft or archival')
    require(not PLACEHOLDER.search(json.dumps(m)), 'Unresolved placeholder anywhere in manifest')
    require(not m['unresolved'], 'Unresolved decisions remain')
    root = Path(workspace).resolve(strict=True)
    env = m['execution']
    require(Path(env['cwd']).is_absolute(), 'cwd must be consumer-local absolute path')
    cwd = contained(root, Path(env['cwd']))
    require(cwd.is_dir(), 'cwd is not a readable directory')
    require(Path(env['python_executable']).is_absolute() and
            os.path.normcase(os.path.abspath(env['python_executable'])) == os.path.normcase(os.path.abspath(sys.executable)),
            'Run preflight with the exact declared interpreter invocation path, without resolving venv symlinks')
    require(Path(env['python_prefix']).is_absolute() and
            os.path.normcase(os.path.abspath(env['python_prefix'])) == os.path.normcase(os.path.abspath(sys.prefix)),
            'Declared Python environment prefix differs from the running environment')
    require(env['dependencies'] == 'preinstalled-only', 'Dependency installation is outside this lane')
    stage = m['stage']; authority = m['authority']
    require(set(authority['allowed_actions']) <= ACTIONS[stage], 'Action is outside selected stage')
    require(not authority['credential_actions_allowed'], 'Credential actions forbidden')
    require(not authority['network_allowed'] or stage == 'publication', 'Network is outside this bounded lane')
    require(authority['resume_authorization_reference'], 'Coordinator resume/dispatch reference is missing')

    # Read-only Git commands are fixed here, never taken from the task manifest.
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=cwd, timeout=30)
    repo = m['repository']
    require(git('rev-parse', 'HEAD').decode().strip() == repo['checkout_commit'], 'Checkout commit mismatch')
    require(git('rev-parse', 'HEAD^{tree}').decode().strip() == repo['checkout_tree'], 'Checkout tree mismatch')
    require(not git('status', '--porcelain', '--untracked-files=no').strip(), 'Tracked checkout is dirty')
    require(git('rev-parse', repo['baseline_commit'] + '^{tree}').decode().strip() == repo['baseline_tree'],
            'Catalog baseline tree mismatch')
    for key, value in repo['baseline_catalog_sha256'].items():
        raw = git('show', repo['baseline_commit'] + ':materials_boundaries/data/' + key + '.json')
        require(hashlib.sha256(raw).hexdigest() == value, 'Baseline bytes mismatch: ' + key)

    writes = set(m['write_paths']); outputs = [x['path'] for x in m['outputs']]
    require(len(outputs) == len(set(outputs)) and set(outputs) <= writes, 'Outputs must be unique and covered by exact write paths')
    require(len(writes) <= m['limits']['max_changed_paths'], 'Write-path budget exceeded')
    for path in list(writes) + outputs + m['read_paths'] + m['selection']['existing_contract_paths']:
        target = contained(root, cwd / relative_file(path))
        require(target == (cwd / path).absolute(), 'Symlinked path is not an exact allowlist target: ' + path)
        require(not target.exists() or target.is_file(), 'A path names a directory: ' + path)
    for path in m['read_paths'] + m['selection']['existing_contract_paths']:
        require((cwd / path).is_file(), 'Required read path missing: ' + path)
    input_hashes = set(); input_paths = set(); subjects = {}
    require(any(x["required"] for x in m["inputs"]), "At least one actual required input is necessary")
    for item in m['inputs']:
        if not item['required']:
            continue
        require(item['consumer_path'] is not None, 'Required input not materialized')
        p = Path(item['consumer_path'])
        p = contained(root, p if p.is_absolute() else root / p)
        require(p.is_file(), 'Required input missing: ' + str(p))
        require(digest(p) == item['raw_sha256'], 'Required input hash mismatch: ' + str(p))
        input_hashes.add(item['raw_sha256']); input_paths.add(p)
        if item['role'] in {'candidate_packet', 'implementation_subject'}:
            require(item['role'] not in subjects, 'Duplicate gate subject role')
            subjects[item['role']] = (item['raw_sha256'], strict_json(p))
    require(all(contained(root, cwd / p) not in input_paths for p in writes), 'Immutable input is writable')
    if stage.startswith('independent_'):
        require(m['assignee_id'] != m['artifact_author_id'] and
                m['assignee_id'] == m['independent_review']['reviewer_assignment'], 'Reviewer is not independent/assigned')
        require(not writes.intersection(m['read_paths']), 'Review cannot modify inspected files')
        require(writes == set(outputs) and all(Path(p).suffix in {'.json', '.md'} and not (cwd / p).exists() for p in writes),
                'Independent review writes must be new review-only JSON/Markdown outputs')

    if stage in {'independent_candidate_review', 'runtime_integration', 'validation', 'independent_implementation_review', 'publication'}:
        require('candidate_packet' in subjects, 'Exact candidate_packet input is required')
        require(subjects['candidate_packet'][1].get('schema') == 'formulation-prepared-packet/1', 'Candidate subject is not a prepared packet')
    if stage in {'validation', 'independent_implementation_review', 'publication'}:
        require('implementation_subject' in subjects, 'Exact implementation_subject input is required')
        target = subjects['implementation_subject'][1]
        require(target.get('commit') == repo['checkout_commit'] and target.get('tree') == repo['checkout_tree']
                and target.get('author_id') == m['artifact_author_id'], 'Implementation subject image/author mismatch')
    required_gates = {'candidate'} if stage in {'runtime_integration', 'validation', 'independent_implementation_review'} else set()
    if stage == 'publication':
        required_gates = {'candidate', 'implementation'}
    approvals = {}
    for ref in m['independent_review']['approval_receipts']:
        p = contained(root, cwd / relative_file(ref['path']))
        require(p.is_file() and digest(p) == ref['raw_sha256'], 'Approval receipt missing/changed')
        receipt = strict_json(p)
        require(receipt['decision'] == 'accept' and all(isinstance(receipt.get(k), str) and receipt[k] for k in ('reviewer_id', 'author_id'))
                and receipt['reviewer_id'] != receipt['author_id'], 'Approval absent or self-reviewed')
        require(receipt['stage'] == ref['stage'] and ref['stage'] not in approvals, 'Approval stage duplicate/mismatch')
        role = 'candidate_packet' if ref['stage'] == 'candidate' else 'implementation_subject'
        require(role in subjects and receipt['subject_sha256'] == ref['subject_sha256'] == subjects[role][0],
                'Approval does not bind the exact typed gate subject')
        if ref['stage'] == 'implementation':
            require(receipt['commit'] == repo['checkout_commit'] and receipt['tree'] == repo['checkout_tree'],
                    'Implementation approval is not for this exact image')
            require(receipt['author_id'] == m['artifact_author_id'], 'Implementation approval author mismatch')
        approvals[ref['stage']] = receipt
    require(required_gates <= approvals.keys(), 'Missing independent gate receipt: ' + ', '.join(sorted(required_gates - approvals.keys())))
    if stage == 'publication':
        require(re.fullmatch(r'refs/heads/(?:experiment|experimental)/[A-Za-z0-9._/-]+', authority['publication_target'] or '')
                and '..' not in authority['publication_target'], 'Publication target is missing or outside experimental branch lane')
        require(authority['required_ci'] and authority['network_allowed'], 'Publication needs named post-push CI and network authority')
    else:
        require(authority['publication_target'] is None, 'Nonpublication task cannot carry a publication target')

    for check in m['checks']:
        require(check['execution_authorized'], 'Listed check is not authorized')
        tokens = check['argv']
        require(tokens and tokens[0] == env['python_executable'], 'Check does not use exact interpreter')
        args = tokens[1:]
        while args and args[0] in {'-B', '-X'}:
            if args[0] == '-B':
                args = args[1:]
            else:
                require(len(args) >= 2 and args[1] == 'utf8', 'Only documented -X utf8 is supported')
                args = args[2:]
        require(args and '-c' not in args, 'Inline code is outside supported check patterns')
        source = check['verified_command_source'].split(' at ', 1)[0]
        require((cwd / relative_file(source)).is_file(), 'Command reference is missing')
        if check['kind'] == 'unittest':
            require(args[:2] == ['-m', 'unittest'], 'Unittest kind/entrypoint mismatch')
            p = contained(root, cwd / relative_file(check['expected_inventory_path']))
            require(p.is_file() and digest(p) == check['expected_inventory_sha256'], 'Unittest inventory missing/changed')
            ids = json_pointer(strict_json(p), check['inventory_json_pointer'])
            require(isinstance(ids, list) and ids and all(isinstance(x, str) and x for x in ids) and len(ids) == len(set(ids)),
                    'Selected inventory must be a nonempty exact unique ID array')
        elif check['kind'] == 'build':
            require(args[:3] == ['-m', 'pip', 'wheel'] and {'--no-index', '--no-deps', '--no-build-isolation'} <= set(args),
                    'Build kind/entrypoint or preinstalled-dependency flags mismatch')
        else:
            require(args and args[0].endswith('.py'), 'Script check must directly name a Python script')
            script = contained(root, cwd / relative_file(args[0]))
            require(script.is_file() and args[0] in (cwd / source).read_text(encoding='utf-8'),
                    'Script is absent or not named in its command reference')
    return {'structure_valid': True, 'dispatch_ready': True, 'authorization_verified': False,
            'commands_executed': 0, 'note': 'Accidental-error guard only, not a sandbox or security validator. Actual current coordinator authorization and argv review are still required.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest'); p.add_argument('--workspace', required=True)
    args = p.parse_args()
    try:
        print(json.dumps(inspect_manifest(args.manifest, args.workspace), indent=2))
        return 0
    except Exception as error:
        print(json.dumps({'dispatch_ready': False, 'commands_executed': 0, 'error': str(error)}, indent=2))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
