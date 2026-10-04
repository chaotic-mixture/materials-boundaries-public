"""Local, manifest-last export: scoped failure cleanup, never broad atomicity."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from materials_boundaries import ValidationError, load_json
from materials_boundaries.cli import main
from materials_boundaries.composite import build_composite_report, validate_composite_report
from materials_boundaries.composite_export import (ARTIFACTS, _publish_artifacts,
    export_composite_report, save_composite_instance)
from materials_boundaries.composite_intake import original_demo_instance
import materials_boundaries.composite_export as export


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.case = original_demo_instance()

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_build_once_exact_fixed_artifacts_and_manifest(self):
        import materials_boundaries.composite as core
        original = core.evaluate
        with patch.object(core, 'evaluate', wraps=original) as call:
            result = export_composite_report(self.case, self.root/'report')
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result, {'artifacts': list(ARTIFACTS), 'exit_code': 0})
        target = self.root/'report'
        self.assertEqual(set(x.name for x in target.iterdir()), set(ARTIFACTS))
        self.assertEqual(load_json(target/'input.json'), self.case)
        validate_composite_report(load_json(target/'bundle.json'))
        manifest = load_json(target/'manifest.json')
        self.assertEqual(set(manifest['files']), set(ARTIFACTS)-{'manifest.json'})
        for name, entry in manifest['files'].items():
            data = (target/name).read_bytes()
            self.assertEqual(entry, {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        with self.assertRaises(ValidationError):
            export_composite_report(self.case, target)
        self.assertEqual(before, {p.name:p.read_bytes() for p in target.iterdir()})

    def test_determinism_and_locale_independent_machine_outputs(self):
        for lang in ('en', 'zh', 'ja', 'de'):
            for repeat in (1, 2):
                export_composite_report(self.case, self.root/f'{lang}{repeat}', lang=lang)
            for name in ARTIFACTS:
                self.assertEqual((self.root/f'{lang}1'/name).read_bytes(), (self.root/f'{lang}2'/name).read_bytes())
            for name in ('input.json','evaluation.json','bundle.json'):
                self.assertEqual((self.root/'en1'/name).read_bytes(), (self.root/f'{lang}1'/name).read_bytes())

    @unittest.skipUnless(os.name == "posix", "POSIX backend; native Windows coverage is separate")
    def test_symlink_output_and_ancestor_and_traversal_refused(self):
        outside = self.root/'outside'; outside.mkdir()
        alias = self.root/'alias'; alias.symlink_to(outside, target_is_directory=True)
        for path in (alias, alias/'new', self.root/'other'/'..'/'new'):
            with self.subTest(path=path), self.assertRaises((ValidationError,OSError)):
                export_composite_report(self.case, path)
        self.assertEqual(list(outside.iterdir()), [])
        (outside/'input.json').symlink_to(self.root/'untouched')
        with self.assertRaises((ValidationError,OSError)):
            save_composite_instance(self.case, outside/'input.json')
        self.assertFalse((self.root/'untouched').exists())

    def test_invalid_path_syntax_is_cli_error(self):
        for value in ('', 'bad\0path', '~materials_boundaries_unresolvable_user_xyz/case.json'):
            with self.subTest(value=value):
                self.assertEqual(self.invoke(['composite','init','--output',value])[0], 2)
        source = self.root/'too-deep.json'
        source.write_text('[' * 1500 + ']' * 1500)
        self.assertEqual(self.invoke(['composite','verify',str(source),'--json'])[0], 2)
        self.assertEqual(self.invoke(['composite','verify','bad\0path','--json'])[0], 2)

    def test_missing_parent_and_existing_file_refused(self):
        for path in (self.root/'missing'/'report',):
            with self.assertRaises(OSError):
                export_composite_report(self.case, path)
        existing=self.root/'exists'; existing.write_text('untouched')
        for operation in (lambda: export_composite_report(self.case,existing),
                          lambda: save_composite_instance(self.case,existing)):
            with self.assertRaises((ValidationError,OSError)):
                operation()
        self.assertEqual(existing.read_text(),'untouched')
        self.assertEqual([p.name for p in self.root.iterdir()],['exists'])

    @unittest.skipUnless(os.name == "posix", "POSIX backend; native Windows coverage is separate")
    def test_stage_failures_clean_only_own_data(self):
        for fail_at in range(1,7):
            target=self.root/f'stage{fail_at}'; target.mkdir()
            original=export._stage_file; calls=0
            def fail(fd,name,data):
                nonlocal calls
                calls+=1
                result=original(fd,name,data)
                if calls==fail_at:
                    raise OSError('injected staging failure')
                return result
            with patch.object(export,'_stage_file',side_effect=fail), self.assertRaises(OSError):
                export_composite_report(self.case,target)
            self.assertEqual(list(target.iterdir()), [])
        with patch.object(export.os,'fsync',side_effect=OSError('injected partial write')), self.assertRaises(OSError):
            save_composite_instance(self.case,self.root/'partial-input.json')
        self.assertFalse((self.root/'partial-input.json').exists())
        self.assertFalse(any(p.name.startswith('.composite') for p in self.root.iterdir()))

    @unittest.skipUnless(os.name == "posix", "POSIX backend; native Windows coverage is separate")
    def test_publish_failures_manifest_last_and_rollback(self):
        for fail_at in range(1,7):
            target=self.root/f'publish{fail_at}'
            original=export.os.link; calls=[]
            def fail(source,destination,**kwargs):
                calls.append(destination)
                if len(calls)==fail_at:
                    raise OSError('injected publish failure')
                return original(source,destination,**kwargs)
            with patch.object(export.os,'link',side_effect=fail), self.assertRaises(OSError):
                export_composite_report(self.case,target)
            self.assertEqual(calls,list(ARTIFACTS)[:fail_at])
            self.assertFalse(target.exists())

    @unittest.skipUnless(os.name == "posix", "POSIX backend; native Windows coverage is separate")
    def test_concurrent_unrelated_file_is_preserved(self):
        target=self.root/'concurrent'; original=export._stage_file
        def add_other(fd,name,data):
            result=original(fd,name,data)
            (target/'unrelated.txt').write_text('keep')
            return result
        with patch.object(export,'_stage_file',side_effect=add_other), self.assertRaises(ValidationError):
            export_composite_report(self.case,target)
        self.assertEqual([p.name for p in target.iterdir()],['unrelated.txt'])
        self.assertEqual((target/'unrelated.txt').read_text(),'keep')

    @unittest.skipUnless(os.name == "posix", "POSIX backend; native Windows coverage is separate")
    def test_rollback_does_not_delete_replacement(self):
        target=self.root/'replacement'; original=export.os.link; calls=0
        def replace_other(source,destination,**kwargs):
            nonlocal calls
            calls+=1
            if calls==2:
                (target/'input.json').unlink()
                (target/'input.json').write_text('concurrent replacement')
                raise OSError('injected failure after replacement')
            return original(source,destination,**kwargs)
        with patch.object(export.os,'link',side_effect=replace_other), self.assertRaises(OSError):
            export_composite_report(self.case,target)
        self.assertEqual((target/'input.json').read_text(),'concurrent replacement')
        self.assertEqual(len(list(target.iterdir())),1)

    @unittest.skipUnless(os.name == "posix", "POSIX backend; native Windows coverage is separate")
    def test_cleanup_failure_rolls_back_manifest_then_retries_owned_stage(self):
        original = export.os.unlink
        failed = False
        def once(name, **kwargs):
            nonlocal failed
            if not failed:
                failed = True
                raise OSError('injected one-time cleanup failure')
            return original(name, **kwargs)
        target = self.root/'cleanup'
        with patch.object(export.os, 'unlink', side_effect=once), self.assertRaises(OSError):
            export_composite_report(self.case, target)
        self.assertFalse(target.exists())
        failed = False
        with patch.object(export.os, 'unlink', side_effect=once), self.assertRaises(OSError):
            save_composite_instance(self.case, self.root/'init.json')
        self.assertEqual(list(self.root.iterdir()), [])

    @unittest.skipUnless(os.name == "posix", "POSIX backend; native Windows coverage is separate")
    def test_stage_open_failure_removes_created_empty_stage(self):
        original = export.os.open
        def fail(path, *args, **kwargs):
            if str(path).startswith('.composite-stage-'):
                raise OSError('injected stage descriptor exhaustion')
            return original(path, *args, **kwargs)
        target = self.root/'open-failure'
        with patch.object(export.os, 'open', side_effect=fail), self.assertRaises(OSError):
            export_composite_report(self.case, target)
        self.assertFalse(target.exists())

    @unittest.skipUnless(os.name == "posix", "POSIX backend; native Windows coverage is separate")
    def test_exclusive_name_collision_does_not_delete_other_input(self):
        collision=self.root/('.composite-input-'+'a'*32);collision.write_text('keep')
        with patch.object(export.secrets,'token_hex',return_value='a'*32), self.assertRaises(OSError):
            save_composite_instance(self.case,self.root/'input.json')
        self.assertEqual(collision.read_text(),'keep')

    def test_bad_input_language_and_artifact_names_write_nothing(self):
        bad=deepcopy(self.case);bad['extra']=1
        for operation in (lambda: export_composite_report(bad,self.root/'bad'),
                          lambda: export_composite_report(self.case,self.root/'lang',lang='xx'),
                          lambda: _publish_artifacts({'../escape':b'x'},self.root/'badnames')):
            with self.assertRaises((ValidationError, ValueError)):
                operation()
        self.assertEqual(list(self.root.iterdir()),[])

    def test_init_cli_blank_demo_and_non_tty(self):
        blank=self.root/'blank.json'
        self.assertEqual(self.invoke(['composite','init','--output',str(blank)])[0],0)
        case=load_json(blank)
        self.assertTrue(all(value is None for value in case['conditions'].values()))
        self.assertTrue(all(p['volume_fraction'] is None for p in case['phases']))
        self.assertEqual(self.invoke(['composite','init','--output',str(blank)])[0],2)
        demo=self.root/'demo.json'
        self.assertEqual(self.invoke(['composite','init','--original-demo','--output',str(demo)])[0],0)
        self.assertEqual(load_json(demo),self.case)
        self.assertEqual(self.invoke(['composite','init','--interactive','--output',str(self.root/'tty.json')])[0],2)
        self.assertFalse((self.root/'tty.json').exists())

    def test_cli_report_replay_and_status_codes(self):
        source=self.root/'case.json';save_composite_instance(self.case,source)
        for lang in ('en','zh','ja','de'):
            target=self.root/lang
            code,text,err=self.invoke(['composite','report',str(source),'--output',str(target),'--lang',lang])
            self.assertEqual((code,err),(0,''));self.assertEqual(json.loads(text)['artifacts'],list(ARTIFACTS))
            code,text,err=self.invoke(['composite','verify',str(target/'bundle.json'),'--json','--lang',lang])
            self.assertEqual(code,0);self.assertEqual(json.loads(text)['status'],'reproduced')
            bundle=load_json(target/'bundle.json');bundle['engine_version']='old'
            (target/'bundle.json').write_text(json.dumps(bundle))
            self.assertEqual(self.invoke(['composite','verify',str(target/'bundle.json'),'--json'])[0],4)
        source.write_text('{"a":1,"a":2}')
        self.assertEqual(self.invoke(['composite','report',str(source),'--output',str(self.root/'invalid')])[0],2)
        self.assertFalse((self.root/'invalid').exists())
        self.assertEqual(self.invoke(['composite','verify',str(source),'--json'])[0],2)

    def test_numerical_error_report_saved_before_exit_three(self):
        for p in self.case['phases']:
            for prop in ('bulk_modulus','shear_modulus'):
                p[prop]['value']=1e307
        source=self.root/'case.json';save_composite_instance(self.case,source)
        target=self.root/'overflow'
        self.assertEqual(self.invoke(['composite','report',str(source),'--output',str(target),'--unit','Pa'])[0],3)
        self.assertTrue((target/'manifest.json').exists())
        self.assertEqual(self.invoke(['composite','verify',str(target/'bundle.json'),'--json'])[0],0)


if __name__ == '__main__':
    unittest.main()
