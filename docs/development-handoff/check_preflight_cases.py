#!/usr/bin/env python3
"""Synthetic local template checks only. No project tests, commands, network or publication."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
sys.dont_write_bytecode = True
from dispatch_preflight import inspect_manifest


def main():
    outcomes = []
    with tempfile.TemporaryDirectory(prefix='mb-template-preflight-') as tmp:
        root = Path(tmp); repo = root / 'fixture'; repo.mkdir()
        def write(path, content):
            p = repo / path; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding='utf-8'); return p
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
        def case(name, change=lambda x:None, accept=False):
            value=deepcopy(m); change(value); task.write_text(json.dumps(value))
            try:
                result=inspect_manifest(task,root); actual=True; detail=result['note']
            except Exception as e:
                actual=False; detail=str(e).splitlines()[0].replace(str(root), 'SYNTHETIC_WORKSPACE').replace(sys.executable, 'PYTHON_EXECUTABLE')
            outcomes.append({'case':name,'expected_dispatch_ready':accept,'observed_dispatch_ready':actual,'passed':actual==accept,'detail':detail})
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
        if str(Path(sys.executable).resolve()) != sys.executable:
            case('resolved_interpreter_alias_rejected',lambda x:(x['execution'].update(python_executable=str(Path(sys.executable).resolve())),x['checks'][0]['argv'].__setitem__(0,str(Path(sys.executable).resolve()))))
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
        # Strict parser must reject duplicate keys before schema or dispatch.
        task.write_text('{"status":"ready","status":"ready"}')
        try:
            inspect_manifest(task,root); accepted=True
        except Exception:
            accepted=False
        outcomes.append({'case':'duplicate_json_keys','expected_dispatch_ready':False,'observed_dispatch_ready':accepted,'passed':not accepted})
    report={'scope':'Synthetic local template cases only; no Materials Boundaries tests, task commands, network or publication executed',
            'cases':len(outcomes),'passed':sum(x['passed'] for x in outcomes),'failed':sum(not x['passed'] for x in outcomes),'outcomes':outcomes}
    print(json.dumps(report,indent=2))
    return 0 if not report['failed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
