"""Native Windows/NTFS checks; skipped checks are never platform evidence."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest
from unittest.mock import patch

from materials_boundaries import ValidationError, load_json
from materials_boundaries.cli import main
from materials_boundaries.composite import validate_composite_report
from materials_boundaries.composite_export import ARTIFACTS, export_composite_report, save_composite_instance
from materials_boundaries.composite_intake import original_demo_instance
from materials_boundaries import _composite_windows as win


class WindowsSpellingTests(unittest.TestCase):
    def test_reject_ambiguous_names_before_normalization(self):
        for path in ('', b'bad', 'a\x00b', '..', 'a/../b', 'C:case.json', r'\case.json',
                     r'\\server\share\case.json', r'\\?\C:\case.json', r'\\.\C:\case.json',
                     r'C:\a:stream', 'report.', 'report ', 'NUL', 'nul.json', 'COM1.txt',
                     'LPT¹.txt', 'CONOUT$', 'CON .txt', 'COM1 .foo', 'a*', 'a?', 'a|', 'a\x01b', r'C:\name.\case.json'):
            with self.subTest(path=path), self.assertRaises(ValidationError):
                win._checked_spelling(path)

    def test_accept_ordinary_unicode_local_names(self):
        for path in ('case.json', './case.json', '研究/試験.json', r'C:\研究\試験.json',
                     'C:/case.json', 'normal.directory/file.txt', 'COM10.json'):
            with self.subTest(path=path):
                win._checked_spelling(path)

    @unittest.skipIf(os.name == 'nt', 'non-Windows guard only')
    def test_native_api_is_not_emulated_as_platform_support(self):
        with self.assertRaises(ValidationError):
            win._api()


class WindowsGuardLogicTests(unittest.TestCase):
    """Pure branch tests with fake API returns, never native-platform evidence."""
    class FakeAPI:
        def __init__(self, attributes=0x10, filesystem='NTFS', flags=0x00400000, drive=3):
            self.attributes, self.filesystem, self.flags, self.drive = attributes, filesystem, flags, drive
            self.closed = []
            self.open_requests = []
        def CreateFileW(self, *args):
            self.open_requests.append(args)
            return 123
        def GetFileInformationByHandle(self, handle, info):
            info._obj.attributes = self.attributes
            info._obj.volume = 7
            info._obj.index_low = 11
            return True
        def CloseHandle(self, handle):
            self.closed.append(handle)
            return True
        def GetDriveTypeW(self, path):
            return self.drive
        def GetVolumeInformationByHandleW(self, handle, name, size, serial, maximum, flags, filesystem, capacity):
            flags._obj.value = self.flags
            filesystem.value = self.filesystem
            return True

    def test_all_reparse_attributes_and_nondirectories_are_refused_and_closed(self):
        for attributes in (0x410, 0x400, 0x20):
            api = self.FakeAPI(attributes=attributes)
            with self.assertRaises(ValidationError):
                with win._open_directory(Path('ignored'), api):
                    self.fail('unsafe directory admitted')
            self.assertEqual(api.closed, [123])

    def test_directory_open_requests_data_read_and_excludes_delete_sharing(self):
        api = self.FakeAPI()
        with patch.object(win, '_directory_identity', return_value=(7, 11)):
            with win._open_directory(Path('ignored'), api):
                pass
        request, = api.open_requests
        self.assertEqual(request[1], 0x81)  # list-directory + read-attributes
        self.assertEqual(request[2], 0x3)   # share read/write, never delete
        self.assertEqual(request[4:6], (3, 0x02200000))
        self.assertEqual(api.closed, [123])

    def test_nonlocal_drives_rejected_before_open(self):
        for drive in (0, 1, 4, 5, 6):
            api = self.FakeAPI(drive=drive)
            with patch.object(win, '_api', return_value=api), self.assertRaises(ValidationError):
                with win._directory(Path.cwd()):
                    self.fail('unsupported drive admitted')
            self.assertEqual(api.closed, [])

    def test_non_ntfs_or_missing_hardlinks_rejected_and_root_closed(self):
        for filesystem, flags in (('ReFS', 0x00400000), ('FAT32', 0), ('NTFS', 0)):
            api = self.FakeAPI(filesystem=filesystem, flags=flags)
            with patch.object(win, '_api', return_value=api), patch.object(win, '_directory_identity', return_value=(7, 11)), self.assertRaises(ValidationError):
                with win._directory(Path.cwd()):
                    self.fail('unsupported filesystem admitted')
            self.assertEqual(api.closed, [123])


@unittest.skipUnless(os.name == 'nt', 'requires actual native Windows on local NTFS')
class NativeWindowsExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Use extended spelling for cleanup too, independent of MAX_PATH policy.
        self.addCleanup(lambda: shutil.rmtree(win._safe_path(self.root)) if self.root.exists() else None)
        self.case = original_demo_instance()
        # Failure here is a failed native test, not an unsupported-volume skip.
        with win._directory(win._safe_path(self.root)):
            pass

    def invoke(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def assert_report(self, path):
        self.assertEqual({p.name for p in path.iterdir()}, set(ARTIFACTS))
        validate_composite_report(load_json(path / 'bundle.json'))
        manifest = load_json(path / 'manifest.json')
        for name, entry in manifest['files'].items():
            data = (path / name).read_bytes()
            self.assertEqual(entry, {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})

    def test_blank_demo_report_replay_and_existing_output_refusal(self):
        for kind, extra in (('blank', []), ('demo', ['--original-demo'])):
            case = self.root / (kind + '.json')
            self.assertEqual(self.invoke(['composite', 'init', '--output', str(case)] + extra)[0], 0)
            before = case.read_bytes()
            self.assertEqual(self.invoke(['composite', 'init', '--output', str(case)] + extra)[0], 2)
            self.assertEqual(case.read_bytes(), before)
            for language in ('en', 'zh', 'ja', 'de'):
                report = self.root / (kind + '-' + language)
                self.assertEqual(self.invoke(['composite', 'report', str(case), '--output', str(report), '--lang', language])[0], 0)
                self.assert_report(report)
                self.assertEqual(self.invoke(['composite', 'verify', str(report / 'bundle.json'), '--json'])[0], 0)
                before = {p.name: p.read_bytes() for p in report.iterdir()}
                self.assertEqual(self.invoke(['composite', 'report', str(case), '--output', str(report)])[0], 2)
                self.assertEqual(before, {p.name: p.read_bytes() for p in report.iterdir()})

    def test_relative_and_unicode_paths(self):
        previous = Path.cwd()
        os.chdir(self.root)
        try:
            save_composite_instance(self.case, '試験-α.json')
            export_composite_report(self.case, '研究-ü')
            self.assert_report(Path('研究-ü'))
        finally:
            os.chdir(previous)

    def test_extended_length_local_path(self):
        # Internal extended spelling works without changing registry/policy.
        parent = self.root
        for number in range(6):
            parent /= str(number) + ('長' * 48)
            win._safe_path(parent).mkdir()
        self.assertGreater(len(str(parent)), 260)
        save_composite_instance(self.case, parent / 'case.json')
        export_composite_report(self.case, parent / 'report')
        extended = win._safe_path(parent / 'report')
        self.assert_report(extended)
        self.assertEqual(self.invoke(['composite', 'verify', str(extended / 'bundle.json'), '--json'])[0], 0)

    def test_every_pinned_ancestor_refuses_rename_and_handles_close(self):
        parent = self.root / 'parent'; parent.mkdir()
        leaf = parent / 'leaf'; leaf.mkdir()
        with win._directory(win._safe_path(leaf)):
            for target in (parent, leaf):
                with self.subTest(target=target), self.assertRaises(OSError):
                    target.rename(target.with_name(target.name + '-moved'))
        leaf.rename(parent / 'moved')
        parent.rename(self.root / 'renamed')

    def test_partial_directory_open_failure_closes_ancestors(self):
        parent = self.root / 'parent'; parent.mkdir()
        original = win._open_directory
        @contextmanager
        def fail(path, api):
            if path.name == 'missing':
                raise OSError('injected directory open failure')
            with original(path, api) as result:
                yield result
        with patch.object(win, '_open_directory', fail), self.assertRaises(OSError):
            with win._directory(win._safe_path(parent / 'missing')):
                pass
        parent.rename(self.root / 'renamed')

    def test_junction_ancestor_and_output_refused(self):
        outside = self.root / 'outside'; outside.mkdir()
        alias = self.root / 'junction'
        result = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(alias), str(outside)], capture_output=True)
        self.assertEqual(result.returncode, 0, repr(result.stderr))
        self.addCleanup(lambda: os.rmdir(alias) if alias.exists() else None)
        for target in (alias, alias / 'report'):
            with self.subTest(target=target), self.assertRaises((ValidationError, OSError)):
                export_composite_report(self.case, target)
        with self.assertRaises((ValidationError, OSError)):
            save_composite_instance(self.case, alias / 'case.json')
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlink_and_dangling_leaf_refused(self):
        outside = self.root / 'outside'; outside.mkdir()
        alias = self.root / 'alias'
        try:
            alias.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            if exc.winerror == 1314:
                self.skipTest('Windows symlink privilege unavailable; mandatory junction tests still run')
            raise
        for target in (alias, alias / 'report'):
            with self.assertRaises((ValidationError, OSError)):
                export_composite_report(self.case, target)
        dangling = self.root / 'case.json'
        dangling.symlink_to(self.root / 'missing.json')
        with self.assertRaises((ValidationError, OSError)):
            save_composite_instance(self.case, dangling)
        self.assertFalse((self.root / 'missing.json').exists())
        self.assertEqual(list(outside.iterdir()), [])

    def test_stage_write_failures_and_input_fsync_close_before_cleanup(self):
        for fail_at in range(1, 7):
            target = self.root / ('stage' + str(fail_at)); target.mkdir()
            original = win._stage_file; count = 0
            def fail(path, data, owned):
                nonlocal count
                original(path, data, owned); count += 1
                if count == fail_at:
                    raise OSError('injected staging failure')
            with patch.object(win, '_stage_file', side_effect=fail), self.assertRaises(OSError):
                export_composite_report(self.case, target)
            self.assertEqual(list(target.iterdir()), [])
        with patch.object(win.os, 'fsync', side_effect=OSError('injected partial write')), self.assertRaises(OSError):
            save_composite_instance(self.case, self.root / 'partial.json')
        self.assertFalse((self.root / 'partial.json').exists())
        self.assertFalse(any(p.name.startswith('.composite') for p in self.root.iterdir()))

    def test_publish_failure_manifest_last_rollback_all_positions(self):
        for fail_at in range(1, 7):
            target = self.root / ('publish' + str(fail_at)); calls = []
            original = win.os.link
            def fail(source, destination):
                calls.append(destination.name)
                if len(calls) == fail_at:
                    raise OSError('injected publication failure')
                return original(source, destination)
            with patch.object(win.os, 'link', side_effect=fail), self.assertRaises(OSError):
                export_composite_report(self.case, target)
            self.assertEqual(calls, list(ARTIFACTS)[:fail_at])
            self.assertFalse(target.exists())

    def test_published_replacement_and_unrelated_addition_preserved(self):
        target = self.root / 'replacement'; original = win.os.link; count = 0
        def fail(source, destination):
            nonlocal count
            count += 1
            if count == 2:
                (target / 'input.json').unlink()
                (target / 'input.json').write_text('keep replacement')
                raise OSError('injected publication failure')
            return original(source, destination)
        with patch.object(win.os, 'link', side_effect=fail), self.assertRaises(OSError):
            export_composite_report(self.case, target)
        self.assertEqual((target / 'input.json').read_text(), 'keep replacement')
        self.assertEqual(len(list(target.iterdir())), 1)
        target = self.root / 'addition'; original_stage = win._stage_file
        def add(path, data, owned):
            original_stage(path, data, owned)
            (target / 'unrelated.txt').write_text('keep')
        with patch.object(win, '_stage_file', side_effect=add), self.assertRaises(ValidationError):
            export_composite_report(self.case, target)
        self.assertEqual([p.name for p in target.iterdir()], ['unrelated.txt'])

    def test_staging_collision_and_replacement_are_not_deleted(self):
        token = 'a' * 32
        collision = self.root / ('.composite-input-' + token); collision.write_text('keep')
        with patch.object(win.secrets, 'token_hex', return_value=token), self.assertRaises(OSError):
            save_composite_instance(self.case, self.root / 'case.json')
        self.assertEqual(collision.read_text(), 'keep')
        target = self.root / 'report'; original = win._stage_file
        def replace(path, data, owned):
            original(path, data, owned)
            # Keep original inode alive to make replacement identity distinct.
            os.link(path, self.root / 'original-owned')
            path.unlink(); path.write_text('keep stage replacement')
            raise OSError('injected stage replacement')
        with patch.object(win, '_stage_file', side_effect=replace), self.assertRaises(OSError):
            export_composite_report(self.case, target)
        stage = next(target.iterdir())
        self.assertEqual((stage / 'input.json').read_text(), 'keep stage replacement')
        self.assertFalse((target / 'manifest.json').exists())

    def test_replaced_stage_is_rejected_before_publication(self):
        target = self.root / 'changed-stage'; original = win._stage_file
        def replace(path, data, owned):
            original(path, data, owned)
            if path.name == 'input.json':
                os.link(path, self.root / 'retained-original')
                path.unlink(); path.write_text('unrelated replacement')
        with patch.object(win, '_stage_file', side_effect=replace), self.assertRaises((ValidationError, OSError)):
            export_composite_report(self.case, target)
        self.assertFalse((target / 'input.json').exists())
        self.assertFalse((target / 'manifest.json').exists())
        stage = next(target.iterdir())
        self.assertEqual((stage / 'input.json').read_text(), 'unrelated replacement')

    def test_replaced_input_stage_is_rejected_before_publication(self):
        original = win._stage_file
        def replace(path, data, owned):
            original(path, data, owned)
            os.link(path, self.root / 'retained-original')
            path.unlink(); path.write_text('unrelated input replacement')
        with patch.object(win, '_stage_file', side_effect=replace), self.assertRaises(ValidationError):
            save_composite_instance(self.case, self.root / 'case.json')
        self.assertFalse((self.root / 'case.json').exists())
        stage = next(p for p in self.root.iterdir() if p.name.startswith('.composite-input-'))
        self.assertEqual(stage.read_text(), 'unrelated input replacement')

    def test_transient_cleanup_failure_rolls_back_manifest_and_retries(self):
        for operation in ('unlink', 'rmdir'):
            original = getattr(win.os, operation); failed = False
            def fail(path):
                nonlocal failed
                if not failed:
                    failed = True
                    raise OSError('injected one-time cleanup failure')
                return original(path)
            target = self.root / operation
            with patch.object(win.os, operation, side_effect=fail), self.assertRaises(OSError):
                export_composite_report(self.case, target)
            self.assertFalse(target.exists())

    def test_root_and_stage_open_failure_cleanup_and_release(self):
        original = win._open_directory
        for kind in ('root', 'stage'):
            target = self.root / kind; failed = False
            @contextmanager
            def fail(path, api):
                nonlocal failed
                matches = path.name == kind if kind == 'root' else path.name.startswith('.composite-stage-')
                if matches and not failed:
                    failed = True
                    raise OSError('injected open failure')
                with original(path, api) as value:
                    yield value
            with patch.object(win, '_open_directory', fail), self.assertRaises(OSError):
                export_composite_report(self.case, target)
            self.assertFalse(target.exists())
        renamed = self.root.with_name(self.root.name + '-renamed')
        self.root.rename(renamed); renamed.rename(self.root)

    def test_zero_file_identity_fails_closed_without_deleting_unknown_file(self):
        class NoIdentity:
            st_ino = 0
        target = self.root / 'unknown.json'
        with patch.object(win.os, 'fstat', return_value=NoIdentity()), self.assertRaises(OSError):
            save_composite_instance(self.case, target)
        self.assertFalse(target.exists())
        leftovers = list(self.root.iterdir())
        self.assertEqual(len(leftovers), 1)
        self.assertTrue(leftovers[0].name.startswith('.composite-input-'))

    def test_existing_empty_destination_and_staging_file_collision(self):
        target = self.root / 'empty'; target.mkdir()
        export_composite_report(self.case, target); self.assert_report(target)
        target = self.root / 'collision'; original = win._stage_file
        def collide(path, data, owned):
            path.write_text('unrelated staged collision')
            original(path, data, owned)
        with patch.object(win, '_stage_file', side_effect=collide), self.assertRaises(OSError):
            export_composite_report(self.case, target)
        stage = next(target.iterdir())
        self.assertEqual((stage / 'input.json').read_text(), 'unrelated staged collision')
        self.assertFalse((target / 'manifest.json').exists())


if __name__ == '__main__':
    unittest.main()
