#!/usr/bin/env python3
"""Synthetic local template checks only. No project tests, commands, network or publication."""
from copy import deepcopy
import hashlib
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tempfile
sys.dont_write_bytecode = True
from dispatch_preflight import inspect_manifest
from jsonschema.exceptions import ValidationError

# Fixed rejection oracles: an unrelated earlier rejection is a failure, not a pass.
EXPECTED_REJECTIONS = {
    'deny_draft': {'error_type': 'ValueError', 'message_prefix': 'Not dispatchable: status must be ready, never draft or archival'},
    'deny_archival': {'error_type': 'ValueError', 'message_prefix': 'Not dispatchable: status must be ready, never draft or archival'},
    'placeholder_output': {'error_type': 'ValidationError', 'validator': 'anyOf', 'instance_path': []},
    'placeholder_command': {'error_type': 'ValidationError', 'validator': 'anyOf', 'instance_path': []},
    'empty_sources': {'error_type': 'ValidationError', 'validator': 'minItems', 'instance_path': ['selection', 'source_ids']},
    'duplicate_record_ids': {'error_type': 'ValidationError', 'validator': 'uniqueItems', 'instance_path': ['selection', 'record_ids']},
    'wildcard_write': {'error_type': 'ValidationError', 'validator': 'pattern', 'instance_path': ['write_paths', 0]},
    'traversal_write': {'error_type': 'ValidationError', 'validator': 'pattern', 'instance_path': ['write_paths', 0]},
    'uncovered_output': {'error_type': 'ValueError', 'message_prefix': 'Outputs must be unique and covered by exact write paths'},
    'all_inputs_optional': {'error_type': 'ValidationError', 'validator': 'contains', 'instance_path': ['inputs']},
    'input_hash_mismatch': {'error_type': 'ValueError', 'message_prefix': 'Required input hash mismatch:'},
    'missing_consumer_file': {'error_type': 'ValueError', 'message_prefix': 'Required input missing:'},
    'input_escape': {'error_type': 'ValueError', 'message_prefix': 'Path escapes workspace:'},
    'wrong_interpreter': {'error_type': 'ValueError', 'message_prefix': 'Run preflight with the exact declared interpreter invocation path'},
    'resolved_interpreter_alias_rejected': {'error_type': 'ValueError', 'message_prefix': 'Run preflight with the exact declared interpreter invocation path'},
    'wrong_python_prefix': {'error_type': 'ValueError', 'message_prefix': 'Declared Python environment prefix differs from the running environment'},
    'unapproved_required_check': {'error_type': 'ValidationError', 'validator': 'const', 'instance_path': ['checks', 0, 'execution_authorized']},
    'missing_resume_reference': {'error_type': 'ValidationError', 'validator': 'type', 'instance_path': ['authority', 'resume_authorization_reference']},
    'next_stage_action': {'error_type': 'ValueError', 'message_prefix': 'Action is outside selected stage'},
    'credential_action': {'error_type': 'ValidationError', 'validator': 'const', 'instance_path': ['authority', 'credential_actions_allowed']},
    'network_candidate': {'error_type': 'ValueError', 'message_prefix': 'Network is outside this bounded lane'},
    'unresolved_decision': {'error_type': 'ValidationError', 'validator': 'maxItems', 'instance_path': ['unresolved']},
    'wrong_baseline_hash': {'error_type': 'ValueError', 'message_prefix': 'Baseline bytes mismatch: materials'},
    'runtime_missing_approval': {'error_type': 'ValidationError', 'validator': 'contains', 'instance_path': ['independent_review', 'approval_receipts']},
    'runtime_self_approval': {'error_type': 'ValueError', 'message_prefix': 'Approval absent or self-reviewed'},
    'runtime_untyped_source_substitution': {'error_type': 'ValueError', 'message_prefix': 'Exact candidate_packet input is required'},
    'runtime_wrong_subject': {'error_type': 'ValueError', 'message_prefix': 'Approval does not bind the exact typed gate subject'},
    'publication_null_target': {'error_type': 'ValidationError', 'validator': 'type', 'instance_path': ['authority', 'publication_target']},
    'publication_main_target': {'error_type': 'ValidationError', 'validator': 'pattern', 'instance_path': ['authority', 'publication_target']},
    'publication_missing_implementation_review': {'error_type': 'ValidationError', 'validator': 'contains', 'instance_path': ['independent_review', 'approval_receipts']},
    'implementation_subject_author_mismatch': {'error_type': 'ValueError', 'message_prefix': 'Implementation subject image/author mismatch'},
    'publication_unknown_ci': {'error_type': 'ValidationError', 'validator': 'minItems', 'instance_path': ['authority', 'required_ci']},
    'false_unittest_pip_install': {'error_type': 'ValueError', 'message_prefix': 'Unittest kind/entrypoint mismatch'},
    'false_build_script_tokens': {'error_type': 'ValueError', 'message_prefix': 'Build kind/entrypoint or preinstalled-dependency flags mismatch'},
    'unittest_no_pointer': {'error_type': 'ValidationError', 'validator': 'type', 'instance_path': ['checks', 0, 'inventory_json_pointer']},
    'unittest_wrong_selector': {'error_type': 'KeyError', 'message_prefix': "'absent'"},
    'inline_code': {'error_type': 'ValueError', 'message_prefix': 'Inline code is outside supported check patterns'},
    'shell_operator': {'error_type': 'ValueError', 'message_prefix': 'Script check must directly name a Python script'},
    'self_review_assignment': {'error_type': 'ValueError', 'message_prefix': 'Reviewer is not independent/assigned'},
    'dirty_tracked_checkout': {'error_type': 'ValueError', 'message_prefix': 'Tracked checkout is dirty'},
    'duplicate_json_keys': {'error_type': 'ValueError', 'message_prefix': 'Duplicate JSON key: status'},
}

POSITIVE_CASES = {
    "ready_candidate_nonexecuting", "ready_runtime_with_independent_receipt",
    "ready_publication_preconditions_only", "ready_exact_unittest_inventory_without_execution",
    "ready_independent_candidate_review",
}

def observed_gate(error, root):
    if isinstance(error, ValidationError):
        return {"error_type": "ValidationError", "validator": error.validator,
                "instance_path": list(error.absolute_path)}
    return {"error_type": type(error).__name__,
            "message": str(error).splitlines()[0].replace(str(root), "SYNTHETIC_WORKSPACE").replace(sys.executable, "PYTHON_EXECUTABLE")}

def gate_matches(expected, observed):
    for key, value in expected.items():
        if key == "message_prefix":
            if not observed.get("message", "").startswith(value):
                return False
        elif observed.get(key) != value:
            return False
    return True

def control_for(name):
    if name.startswith("runtime_"):
        return "ready_runtime_with_independent_receipt"
    if name.startswith("publication_") or name == "implementation_subject_author_mismatch":
        return "ready_publication_preconditions_only"
    if name.startswith("unittest_") or name == "false_unittest_pip_install":
        return "ready_exact_unittest_inventory_without_execution"
    if name == "self_review_assignment":
        return "ready_independent_candidate_review"
    return "ready_candidate_nonexecuting"


def main():
    outcomes = []
    with tempfile.TemporaryDirectory(prefix='mb-template-preflight-') as tmp:
        root = Path(tmp); repo = root / 'fixture'; repo.mkdir()
        def write(path, content):
            p = repo / path; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(content.encode('utf-8')); return p
        def sha(p):
            return hashlib.sha256(p.read_bytes()).hexdigest()
        for name in ['materials','reference_properties','sources']:
            write('materials_boundaries/data/' + name + '.json', '{}\n')
        write('guide.md', 'Synthetic local command reference: scripts/check_fixture.py\n')
        write('scripts/check_fixture.py', "raise RuntimeError('Task command must never execute in preflight')\n")
        evidence = write('selected-evidence.json', '{"synthetic": true}\n')
        candidate = write('candidate-packet.json', '{"schema": "formulation-prepared-packet/1", "synthetic": true}\n')
        inventory = write('inventory.json', '{"current": ["fixture.Tests.test_one"]}\n')
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=repo, stderr=subprocess.DEVNULL).decode().strip()
        git('init','-q'); git('add','.'); git('-c','user.name=Template QA','-c','user.email=qa@example.invalid','commit','-qm','Synthetic fixture')
        commit = git('rev-parse','HEAD'); tree = git('rev-parse','HEAD^{tree}')
        # Compare raw bytes with committed blobs; do not relax or repin the production guard.
        fixture_bytes_match = all((repo/'materials_boundaries/data'/f'{n}.json').read_bytes() ==
                                  subprocess.check_output(['git','show',commit+':materials_boundaries/data/'+n+'.json'],cwd=repo)
                                  for n in ['materials','reference_properties','sources'])
        def config_value(name):
            result = subprocess.run(['git','config','--get',name],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            return result.stdout.decode().strip() if result.returncode == 0 else None
        git_settings = {'core.autocrlf': config_value('core.autocrlf'), 'core.eol': config_value('core.eol')}
        m = json.loads(Path(__file__).with_name('task-input.example.json').read_text())
        m.update(status='ready',task_id='synthetic-preflight',objective='Inspect synthetic fixture only',
                 assignee_id='worker-one',artifact_author_id='author-one',unresolved=[],stop_boundary='Return one candidate and stop')
        m['repository'].update(baseline_commit=commit,baseline_tree=tree,checkout_commit=commit,checkout_tree=tree,
                              baseline_catalog_sha256={n:sha(repo/'materials_boundaries/data'/f'{n}.json') for n in ['materials','reference_properties','sources']})
        m['authority'].update(instruction_reference='Synthetic case only, not real user authority',resume_authorization_reference='Synthetic coordinator fixture',
                              allowed_actions=['read_inputs','write_candidate','run_approved_checks'])
        m['selection'].update(source_ids=['source_one'],record_ids=['record_one'],existing_contract_paths=['guide.md'])
        m['inputs']=[{'path':'selected-evidence.json','raw_sha256':sha(evidence),'purpose':'Synthetic input',
                      'consumer_path':str(evidence),'required':True,'role':'source_evidence'}]
        m['read_paths']=['guide.md'];m['write_paths']=['outputs/result.json'];m['outputs']=[{'path':'outputs/result.json','purpose':'Synthetic result'}]
        m['execution'].update(cwd=str(repo),python_executable=sys.executable,python_prefix=sys.prefix)
        m['limits']['max_changed_paths']=1
        m['independent_review'].update(reviewer_assignment='reviewer-one',reviewer_is_not_author=True)
        m['checks']=[{'id':'script_check','argv':[sys.executable,'scripts/check_fixture.py'],'verified_command_source':'guide.md',
                      'execution_authorized':True,'kind':'script','expected_inventory_path':None,'expected_inventory_sha256':None,
                      'inventory_json_pointer':None,'required_for_gate':True}]
        task = root / 'task.json'
        def record(name, expected_accept, actual_accept, observed):
            expected = {'kind': 'accepted_without_execution'} if expected_accept else EXPECTED_REJECTIONS[name]
            matched = gate_matches(expected, observed)
            outcomes.append({'case': name, 'status': 'executed', 'expected_dispatch_ready': expected_accept,
                             'observed_dispatch_ready': actual_accept, 'expected_gate': expected,
                             'observed_gate': observed, 'gate_matched': matched,
                             'control_case': None if expected_accept else control_for(name)})
        def case(name, change=lambda x:None, accept=False):
            value=deepcopy(m); change(value); task.write_bytes(json.dumps(value).encode('utf-8'))
            try:
                result=inspect_manifest(task,root)
                actual=result.get('dispatch_ready') is True
                observed={'kind':'accepted_without_execution'} if (actual and result.get('commands_executed') == 0 and
                          result.get('authorization_verified') is False) else {'kind':'unexpected_result'}
            except Exception as error:
                actual=False; observed=observed_gate(error,root)
            record(name,accept,actual,observed)
        case('ready_candidate_nonexecuting',accept=True)
        for status in ['draft','archival']:
            case('deny_'+status,lambda x,status=status:x.update(status=status))
        case('placeholder_output',lambda x:x['outputs'][0].update(path='REPLACE_OUTPUT.json'))
        case('placeholder_command',lambda x:x['checks'][0].update(argv=[sys.executable,'REPLACE_SCRIPT.py']))
        case('empty_sources',lambda x:x['selection'].update(source_ids=[]))
        case('duplicate_record_ids',lambda x:x['selection'].update(record_ids=['one','one']))
        case('wildcard_write',lambda x:x.update(write_paths=['scripts/**']))
        case('traversal_write',lambda x:x.update(write_paths=['../../outside']))
        case('uncovered_output',lambda x:x.update(write_paths=[]))
        case('all_inputs_optional',lambda x:[i.update(required=False,consumer_path=None,raw_sha256=None) for i in x['inputs']])
        case('input_hash_mismatch',lambda x:x['inputs'][0].update(raw_sha256='0'*64))
        case('missing_consumer_file',lambda x:x['inputs'][0].update(consumer_path=str(root/'missing')))
        case('input_escape',lambda x:x['inputs'][0].update(consumer_path='/etc/passwd'))
        case('wrong_interpreter',lambda x:x['execution'].update(python_executable='/missing/python'))
        resolved_interpreter = str(Path(sys.executable).resolve())
        if os.path.normcase(os.path.abspath(resolved_interpreter)) != os.path.normcase(os.path.abspath(sys.executable)):
            case('resolved_interpreter_alias_rejected',lambda x:(x['execution'].update(python_executable=str(Path(sys.executable).resolve())),x['checks'][0]['argv'].__setitem__(0,str(Path(sys.executable).resolve()))))
        else:
            outcomes.append({'case':'resolved_interpreter_alias_rejected','status':'not_applicable',
                             'reason':'The current interpreter invocation has no distinct resolved alias target.',
                             'expected_dispatch_ready':False,'observed_dispatch_ready':None,'passed':None})
        case('wrong_python_prefix',lambda x:x['execution'].update(python_prefix='/synthetic-wrong-prefix'))
        case('unapproved_required_check',lambda x:x['checks'][0].update(execution_authorized=False))
        case('missing_resume_reference',lambda x:x['authority'].update(resume_authorization_reference=None))
        case('next_stage_action',lambda x:x['authority'].update(allowed_actions=['start_next_batch']))
        case('credential_action',lambda x:x['authority'].update(credential_actions_allowed=True))
        case('network_candidate',lambda x:x['authority'].update(network_allowed=True))
        case('unresolved_decision',lambda x:x.update(unresolved=['Identity unresolved']))
        case('wrong_baseline_hash',lambda x:x['repository']['baseline_catalog_sha256'].update(materials='0'*64))
        def add_subject(x,role):
            subject = candidate if role=='candidate_packet' else write('implementation-subject.json',json.dumps({'commit':commit,'tree':tree,'author_id':'author-one','synthetic':True}))
            x['inputs'].append({'path':subject.name,'raw_sha256':sha(subject),'purpose':'Synthetic typed gate subject','consumer_path':str(subject),'required':True,'role':role})
            return subject
        def runtime(x):
            add_subject(x,'candidate_packet')
            x.update(stage='runtime_integration');x['authority']['allowed_actions']=['read_inputs','write_runtime']
        case('runtime_missing_approval',runtime)
        def approval(x,kind='candidate',self_review=False):
            subject = next(i for i in x['inputs'] if i['role']==('candidate_packet' if kind=='candidate' else 'implementation_subject'))
            r={'decision':'accept','stage':kind,'reviewer_id':'reviewer-one','author_id':'reviewer-one' if self_review else 'author-one',
               'subject_sha256':subject['raw_sha256'],'commit':commit,'tree':tree}
            p=write('approvals/'+kind+'.json',json.dumps(r))
            x['independent_review']['approval_receipts'].append({'stage':kind,'path':'approvals/'+kind+'.json','raw_sha256':sha(p),'subject_sha256':subject['raw_sha256']})
        case('ready_runtime_with_independent_receipt',lambda x:(runtime(x),approval(x)),accept=True)
        case('runtime_self_approval',lambda x:(runtime(x),approval(x,self_review=True)))
        case('runtime_untyped_source_substitution',lambda x:(runtime(x),approval(x),x['inputs'][-1].update(role='source_evidence')))
        case('runtime_wrong_subject',lambda x:(runtime(x),approval(x),x['independent_review']['approval_receipts'][0].update(subject_sha256='0'*64)))
        def publication(x):
            add_subject(x,'candidate_packet');add_subject(x,'implementation_subject')
            x.update(stage='publication');x['authority'].update(allowed_actions=['read_inputs','push_exact_reviewed_commit','observe_remote_and_ci'],network_allowed=True,publication_target='refs/heads/experimental/synthetic-fixture',required_ci=['fixture-ci']);x['checks']=[]
            approval(x);approval(x,'implementation')
        case('ready_publication_preconditions_only',publication,accept=True)
        case('publication_null_target',lambda x:(publication(x),x['authority'].update(publication_target=None)))
        case('publication_main_target',lambda x:(publication(x),x['authority'].update(publication_target='refs/heads/main')))
        case('publication_missing_implementation_review',lambda x:(publication(x),x['independent_review']['approval_receipts'].pop()))
        case('implementation_subject_author_mismatch',lambda x:(publication(x),x.update(artifact_author_id='different-author')))
        case('publication_unknown_ci',lambda x:(publication(x),x['authority'].update(required_ci=[])))
        def unittest(x):
            x['checks'][0].update(kind='unittest',argv=[sys.executable,'-m','unittest','fixture.Tests.test_one'],
                                  expected_inventory_path='inventory.json',expected_inventory_sha256=sha(inventory),inventory_json_pointer='/current')
        case('ready_exact_unittest_inventory_without_execution',unittest,accept=True)
        case('false_unittest_pip_install',lambda x:(unittest(x),x['checks'][0].update(argv=[sys.executable,'-m','pip','install','unittest'])))
        case('false_build_script_tokens',lambda x:x['checks'][0].update(kind='build',argv=[sys.executable,'scripts/check_fixture.py','pip','wheel','--no-index','--no-deps','--no-build-isolation']))
        case('unittest_no_pointer',lambda x:(unittest(x),x['checks'][0].update(inventory_json_pointer=None)))
        case('unittest_wrong_selector',lambda x:(unittest(x),x['checks'][0].update(inventory_json_pointer='/absent')))
        case('inline_code',lambda x:x['checks'][0].update(argv=[sys.executable,'-c','pass','scripts/check_fixture.py']))
        case('shell_operator',lambda x:x['checks'][0].update(argv=[sys.executable,'scripts/check_fixture.py; echo bad']))
        def independent(x):
            add_subject(x,'candidate_packet')
            x.update(stage='independent_candidate_review',assignee_id='reviewer-one');x['authority']['allowed_actions']=['read_inputs','write_review']
        case('ready_independent_candidate_review',independent,accept=True)
        case('self_review_assignment',lambda x:(independent(x),x.update(artifact_author_id='reviewer-one')))
        write('guide.md','Dirty tracked fixture\n');case('dirty_tracked_checkout')
        git('checkout','--','guide.md')
        # Strict parser must reject the intended duplicate-key defect, not another failure.
        task.write_bytes(b'{"status":"ready","status":"ready"}')
        try:
            result=inspect_manifest(task,root)
            record('duplicate_json_keys',False,True,{'kind':'unexpected_acceptance'})
        except Exception as error:
            record('duplicate_json_keys',False,False,observed_gate(error,root))
    expected_ids = set(EXPECTED_REJECTIONS) | POSITIVE_CASES
    actual_ids = [row['case'] for row in outcomes]
    assert len(actual_ids) == len(set(actual_ids)) and set(actual_ids) == expected_ids
    controls = {row['case']: (row['observed_dispatch_ready'] is True and row.get('gate_matched') is True and fixture_bytes_match)
                for row in outcomes if row['case'] in POSITIVE_CASES}
    for row in outcomes:
        if row['status'] != 'executed':
            continue
        control_passed = True if row['control_case'] is None else controls.get(row['control_case'],False)
        row['control_passed'] = control_passed
        row['passed'] = (row['expected_dispatch_ready'] == row['observed_dispatch_ready'] and
                         row['gate_matched'] and control_passed and fixture_bytes_match)
    executed = [row for row in outcomes if row['status'] == 'executed']
    report={'scope':'Synthetic local template checks only; no Materials Boundaries tests, task argv, network or publication executed',
            'platform':sys.platform,'python_version':platform.python_version(),
            'fixture_encoding':'UTF-8 bytes with explicitly authored LF; no platform text-mode translation',
            'git_settings':git_settings,'fixture_bytes_equal_committed_baseline':fixture_bytes_match,
            'planned_cases':len(outcomes),'cases':len(executed),'case_count_definition':'cases counts executions only; not_applicable is never a pass',
            'passed':sum(row['passed'] for row in executed),'failed':sum(not row['passed'] for row in executed),
            'not_applicable':len(outcomes)-len(executed),
            'positive_controls_passed':sum(controls.values()),
            'negative_gates_certified':sum(row['passed'] for row in executed if not row['expected_dispatch_ready']),
            'unexpected_gate_rejections':[row['case'] for row in executed if not row['observed_dispatch_ready'] and not row['gate_matched']],
            'outcomes':outcomes}
    print(json.dumps(report,indent=2))
    return 0 if not report['failed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
